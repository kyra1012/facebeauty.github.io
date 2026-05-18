import os
import requests
import cv2
import dlib
import torch
import shutil
import time
import numpy as np
import urllib3
from torchvision import models, transforms
from PIL import Image

# ================= 核心配置区 =================
# 1. 硬性指标：每个分类至少要成功下载多少张原图？
#    (脚本会一直爬，直到凑够这个数，或者百度没图了)
TARGET_RAW_COUNT = 120

# 2. AI 录取分数线 (0.60)
CONFIDENCE_THRESHOLD = 0.65

# 3. 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# 你的模型都在这里
SOURCE_DATA_DIR = os.path.join(BASE_DIR, "final_training_data")
# 最终成果存这里
NEW_DATA_DIR = os.path.join(BASE_DIR, "ex_raw_images")
# 模型文件
MODEL_DIR = os.path.join(BASE_DIR, "models")
# Dlib 预测器
PREDICTOR_PATH = os.path.join(PROJECT_ROOT, "preprocess", "shape_predictor_68_face_landmarks.dat")

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 伪装头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Referer': 'https://image.baidu.com/',
    'Connection': 'keep-alive',
}

# 关键词后缀策略 (针对国内源优化)
KEYWORD_SUFFIX = {
    "face_shape": "脸型 或者是 小红书 妆容 发型",
    "eye_shape": "眼型特写 或者是 微博 眼神 高清",
    "eyebrow_shape": "眉形设计 或者是 小红书 眉毛 特写",
    "nose_shape": "鼻型 侧颜 或者是 鼻子 高清",
    "lip_shape": "唇形 试色 或者是 嘴巴 特写",
}

# ================= 工具类定义 =================

# 1. Dlib 初始化
detector = dlib.get_frontal_face_detector()
if not os.path.exists(PREDICTOR_PATH):
    raise FileNotFoundError(f"❌ 找不到 Dlib 模型: {PREDICTOR_PATH}")
predictor = dlib.shape_predictor(PREDICTOR_PATH)


# 2. AI 判官类
class ModelJudge:
    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"   ⚖️ 加载模型: {os.path.basename(model_path)}")
        checkpoint = torch.load(model_path, map_location=self.device)
        self.classes = checkpoint['classes']
        self.model = models.resnet18(pretrained=False)
        self.model.fc = torch.nn.Linear(self.model.fc.in_features, len(self.classes))
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def judge(self, img_bgr):
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            output = self.model(input_tensor)
            probs = torch.nn.functional.softmax(output, dim=1)
            conf, idx = torch.max(probs, 1)
        return self.classes[idx.item()], conf.item()


# 3. 图像处理工具
def resize_with_padding(img, target_size=224):
    h, w = img.shape[:2]
    scale = min(target_size / h, target_size / w)
    nw, nh = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (nw, nh))
    canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
    x_off, y_off = (target_size - nw) // 2, (target_size - nh) // 2
    canvas[y_off:y_off + nh, x_off:x_off + nw] = resized
    return canvas


def get_crop(img, shape, feature_type):
    pts = np.array([[p.x, p.y] for p in shape.parts()])
    h_img, w_img = img.shape[:2]
    x1, y1, x2, y2 = 0, 0, 0, 0

    if feature_type in ["eye_shape", "eyebrow_shape"]:
        indices = list(range(17, 27)) + list(range(36, 48))
        roi = pts[indices]
        pad_y = int((np.max(roi[:, 1]) - np.min(roi[:, 1])) * 0.5)  # 稍微加大裁切范围
        pad_x = int((np.max(roi[:, 0]) - np.min(roi[:, 0])) * 0.2)
        x1, x2 = np.min(roi[:, 0]) - pad_x, np.max(roi[:, 0]) + pad_x
        y1, y2 = np.min(roi[:, 1]) - pad_y, np.max(roi[:, 1]) + pad_y
    elif feature_type == "nose_shape":
        roi = pts[27:36]
        brow_cy = (pts[21][1] + pts[22][1]) // 2
        w_roi, h_roi = np.max(roi[:, 0]) - np.min(roi[:, 0]), np.max(roi[:, 1]) - np.min(roi[:, 1])
        x1, x2 = np.min(roi[:, 0]) - int(w_roi * 0.3), np.max(roi[:, 0]) + int(w_roi * 0.3)
        y1, y2 = min(np.min(roi[:, 1]) - int(h_roi * 0.3), brow_cy), np.max(roi[:, 1]) + int(h_roi * 0.3)
    elif feature_type == "lip_shape":
        roi = pts[range(48, 68)]
        x, y, w, h = cv2.boundingRect(roi)
        x1, x2 = x - int(w * 0.25), x + w + int(w * 0.25)
        y1, y2 = y - int(h * 0.4), y + h + int(h * 0.4)
    elif feature_type == "face_shape":
        rect = detector(img, 1)[0]
        x1, x2 = rect.left() - int(rect.width() * 0.2), rect.right() + int(rect.width() * 0.2)
        y1, y2 = rect.top() - int(rect.height() * 0.6), rect.bottom() + int(rect.height() * 0.2)
    else:
        return None

    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w_img, x2), min(h_img, y2)
    if x2 <= x1 or y2 <= y1: return None
    return img[y1:y2, x1:x2]


# ================= 核心逻辑：死磕爬虫 =================

def crawl_images_until_target(keyword, save_dir, target_count):
    """
    死磕模式：一直翻页，直到 valid_count >= target_count
    """
    print(f"\n🔎 启动百度搜索: '{keyword}'")
    print(f"   🎯 目标: 至少成功下载 {target_count} 张有效图片")

    url = 'https://image.baidu.com/search/acjson'
    session = requests.Session()

    downloaded_count = 0
    page_index = 0
    max_empty_pages = 5  # 如果连续5页都没图，说明真没了，停止
    empty_pages = 0

    while downloaded_count < target_count:
        params = {
            'tn': 'resultjson_com_op',
            'ipn': 'rj',
            'word': keyword,
            'queryWord': keyword,
            'face': '1',  # 只要人脸
            'pn': page_index * 30,
            'rn': '30',
            'gsm': hex(page_index * 30)[2:],
            '1688648823296': ''
        }

        try:
            resp = session.get(url, params=params, headers=HEADERS, verify=False, timeout=10)
            try:
                json_data = resp.json()
            except:
                print("   ⚠️ 百度返回了非JSON数据，跳过本页")
                page_index += 1
                continue

            img_list = json_data.get('data', [])
            # 过滤掉空数据
            img_list = [item for item in img_list if item.get('thumbURL')]

            if not img_list:
                empty_pages += 1
                print(f"   ⚠️ 第 {page_index} 页无数据 ({empty_pages}/{max_empty_pages})")
                if empty_pages >= max_empty_pages:
                    print("   🛑 百度已经被掏空了，停止搜索。")
                    break
            else:
                empty_pages = 0  # 重置计数器

            print(f"   📄 第 {page_index} 页: 发现 {len(img_list)} 张链接 | 当前进度: {downloaded_count}/{target_count}")

            for item in img_list:
                if downloaded_count >= target_count: break

                img_url = item.get('thumbURL')
                try:
                    # 强力下载，忽略SSL
                    img_resp = requests.get(img_url, headers=HEADERS, verify=False, timeout=5)
                    if img_resp.status_code == 200 and len(img_resp.content) > 1000:  # 必须大于1KB
                        timestamp = int(time.time() * 100000)
                        filename = f"raw_{timestamp}.jpg"
                        filepath = os.path.join(save_dir, filename)

                        with open(filepath, 'wb') as f:
                            f.write(img_resp.content)

                        downloaded_count += 1
                        print(f"      ✅ 下载成功 [{downloaded_count}/{target_count}]", end='\r')
                except:
                    continue

            page_index += 1
            time.sleep(1)  # 稍微歇一下，防封太快

        except Exception as e:
            print(f"   ❌ 网络波动: {e}")
            time.sleep(2)
            continue

    print(f"\n   🎉 爬取结束！实际获得: {downloaded_count} 张")
    return downloaded_count


# ================= 核心逻辑：AI 筛选 =================

def process_downloaded_images(feature, class_name, raw_dir, judge):
    """读取 raw_dir 里的图，切脸，AI 鉴定，分发"""
    print(f"   🤖 AI 正在审核 {class_name} 的原始图片...")

    files = [f for f in os.listdir(raw_dir) if f.endswith('.jpg')]
    accepted_count = 0

    for fname in files:
        img_path = os.path.join(raw_dir, fname)
        try:
            # 读取 (支持中文路径)
            img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), -1)
            if img is None: continue

            # 转 RGB
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # 检测脸
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            rects = detector(gray, 1)
            if not rects: continue

            face = max(rects, key=lambda r: r.width() * r.height())
            shape = predictor(gray, face)

            # 裁切五官
            crop = get_crop(img, shape, feature)
            if crop is None or crop.size == 0: continue

            # 预处理并预测
            final_input = resize_with_padding(crop)
            pred_class, conf = judge.judge(final_input)

            # === 智能分拣策略 ===
            if conf >= CONFIDENCE_THRESHOLD:
                # 存入 AI 认为的类别文件夹
                save_dir = os.path.join(NEW_DATA_DIR, feature, pred_class)
                if not os.path.exists(save_dir): os.makedirs(save_dir)

                new_name = f"Auto_{pred_class}_from_{class_name}_{int(time.time() * 1000)}.jpg"
                cv2.imencode('.jpg', final_input)[1].tofile(os.path.join(save_dir, new_name))

                accepted_count += 1

                # 可选：打印日志
                # if pred_class == class_name:
                #     print(f"      ✅ 精准命中: {pred_class} ({conf:.2%})")
                # else:
                #     print(f"      🔀 意外收获: {pred_class} ({conf:.2%})")

        except Exception:
            continue

    print(f"   ✨ AI 筛选完成: {accepted_count} 张高质量图片已入库。")
    return accepted_count


# ================= 主程序 =================

def main():
    print("🚀 启动 Ultimate Crawler (V5.0 终极版)...")
    print(f"🎯 目标: 每个分类爬够 {TARGET_RAW_COUNT} 张 -> AI 筛选")

    # 临时文件夹
    temp_crawl_dir = os.path.join(BASE_DIR, "temp_crawl_bucket")

    # 1. 扫描有哪些任务
    features = [f for f in os.listdir(SOURCE_DATA_DIR) if os.path.isdir(os.path.join(SOURCE_DATA_DIR, f))]

    for feature in features:
        print(f"\n{'=' * 50}")
        print(f"🧩 处理大类: {feature}")
        print(f"{'=' * 50}")

        # 加载模型
        model_path = os.path.join(MODEL_DIR, f"{feature}.pth")
        if not os.path.exists(model_path):
            print(f"⚠️ 缺模型: {feature}.pth，跳过。")
            continue
        try:
            judge = ModelJudge(model_path)
        except Exception as e:
            print(f"❌ 模型坏了: {e}")
            continue

        feature_dir = os.path.join(SOURCE_DATA_DIR, feature)
        classes = [c for c in os.listdir(feature_dir) if os.path.isdir(os.path.join(feature_dir, c))]

        for class_name in classes:
            # 1. 构造搜索词
            suffix = KEYWORD_SUFFIX.get(feature, "高清 明星")
            keyword = f"{class_name} {suffix}"

            # 2. 爬取 (死磕模式)
            if os.path.exists(temp_crawl_dir): shutil.rmtree(temp_crawl_dir)
            os.makedirs(temp_crawl_dir)

            count = crawl_images_until_target(keyword, temp_crawl_dir, TARGET_RAW_COUNT)

            # 3. 如果一张都没爬到，就别筛选了
            if count == 0:
                print("   ⚠️ 没爬到图，跳过筛选。")
                continue

            # 4. AI 筛选
            process_downloaded_images(feature, class_name, temp_crawl_dir, judge)

    # 清理
    if os.path.exists(temp_crawl_dir): shutil.rmtree(temp_crawl_dir)

    # ================= 最终统计报告 =================
    print("\n\n" + "=" * 50)
    print("📊 最终战果统计 (ex_raw_images 文件夹)")
    print("=" * 50)

    total_new_images = 0
    if os.path.exists(NEW_DATA_DIR):
        for feature in os.listdir(NEW_DATA_DIR):
            f_path = os.path.join(NEW_DATA_DIR, feature)
            if os.path.isdir(f_path):
                print(f"\n📁 [{feature}]")
                for cls in os.listdir(f_path):
                    c_path = os.path.join(f_path, cls)
                    if os.path.isdir(c_path):
                        count = len(os.listdir(c_path))
                        total_new_images += count
                        print(f"   - {cls:<15}: {count} 张")

    print("-" * 50)
    print(f"🏆 总计新增高质量素材: {total_new_images} 张")
    print("=" * 50)
    print("💡 下一步：请人工快速浏览 'ex_raw_images' 文件夹，删除明显的错误图片，")
    print("   然后将其合并到 'final_training_data' 中重新训练！")


if __name__ == "__main__":
    main()