import os
import cv2
import dlib
import torch
import numpy as np
import time
import sys  # 引入 sys 用于强制刷新输出
from torchvision import models, transforms
from PIL import Image

# ================= 配置区 =================
SOURCE_DIRS = [
    r"C:\Users\86153\Desktop\FaceBeautyProject\dataset\Source_Images",
    r"C:\Users\86153\Desktop\FaceBeautyProject\deep_learning\raw_images"
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "ex_raw_images")
CONFIDENCE_THRESHOLD = 0.75

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MODEL_DIR = os.path.join(BASE_DIR, "models")
PREDICTOR_PATH = os.path.join(PROJECT_ROOT, "preprocess", "shape_predictor_68_face_landmarks.dat")

# =========================================

# 初始化 Dlib
print("⏳ [1/3] 正在加载 Dlib (人脸检测器)...")
detector = dlib.get_frontal_face_detector()
if not os.path.exists(PREDICTOR_PATH):
    raise FileNotFoundError(f"❌ 找不到 Dlib 模型: {PREDICTOR_PATH}")
predictor = dlib.shape_predictor(PREDICTOR_PATH)

FEATURES = ["face_shape", "eye_shape", "eyebrow_shape", "nose_shape", "lip_shape"]


class MultiModelJudge:
    def __init__(self):
        self.models = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"💻 [2/3] 计算设备: {self.device} (如果是 CPU 会比较慢，请耐心等待)")

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        print("⚙️ [3/3] 正在加载 5 个 AI 模型...")
        for feat in FEATURES:
            path = os.path.join(MODEL_DIR, f"{feat}.pth")
            if os.path.exists(path):
                checkpoint = torch.load(path, map_location=self.device)
                classes = checkpoint['classes']
                model = models.resnet18(pretrained=False)
                model.fc = torch.nn.Linear(model.fc.in_features, len(classes))
                model.load_state_dict(checkpoint['model_state_dict'])
                model.to(self.device)
                model.eval()
                self.models[feat] = {"model": model, "classes": classes}
                # print(f"   ✅ 加载: {feat}")
            else:
                print(f"   ⚠️ 警告: 缺失模型 {feat}")

    def predict(self, feature_name, img_bgr):
        if feature_name not in self.models: return None, 0.0
        model_info = self.models[feature_name]
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            output = model_info["model"](input_tensor)
            probs = torch.nn.functional.softmax(output, dim=1)
            conf, idx = torch.max(probs, 1)
        return model_info["classes"][idx.item()], conf.item()


def get_crop(img, shape, feature_type):
    pts = np.array([[p.x, p.y] for p in shape.parts()])
    h_img, w_img = img.shape[:2]
    x1, y1, x2, y2 = 0, 0, 0, 0
    if feature_type in ["eye_shape", "eyebrow_shape"]:
        indices = list(range(17, 27)) + list(range(36, 48))
        roi = pts[indices]
        pad_x = int((np.max(roi[:, 0]) - np.min(roi[:, 0])) * 0.2)
        pad_y = int((np.max(roi[:, 1]) - np.min(roi[:, 1])) * 0.4)
        x1, x2 = np.min(roi[:, 0]) - pad_x, np.max(roi[:, 0]) + pad_x
        y1, y2 = np.min(roi[:, 1]) - pad_y, np.max(roi[:, 1]) + pad_y
    elif feature_type == "nose_shape":
        roi = pts[27:36]
        w = np.max(roi[:, 0]) - np.min(roi[:, 0])
        x1, x2 = np.min(roi[:, 0]) - int(w * 0.3), np.max(roi[:, 0]) + int(w * 0.3)
        brow_cy = (pts[21][1] + pts[22][1]) // 2
        y1, y2 = min(np.min(roi[:, 1]), brow_cy), np.max(roi[:, 1]) + int(w * 0.2)
    elif feature_type == "lip_shape":
        roi = pts[range(48, 68)]
        x, y, w, h = cv2.boundingRect(roi)
        x1, x2, y1, y2 = x - int(w * 0.2), x + w + int(w * 0.2), y - int(h * 0.3), y + h + int(h * 0.3)
    elif feature_type == "face_shape":
        rect = detector(img, 1)[0]
        w, h = rect.width(), rect.height()
        x1, x2 = rect.left() - int(w * 0.15), rect.right() + int(w * 0.15)
        y1, y2 = rect.top() - int(h * 0.4), rect.bottom() + int(h * 0.15)
    else:
        return None
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w_img, x2), min(h_img, y2)
    if x2 <= x1 or y2 <= y1: return None
    return img[y1:y2, x1:x2]


def resize_padding(img, target_size=224):
    h, w = img.shape[:2]
    scale = min(target_size / h, target_size / w)
    nw, nh = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (nw, nh))
    canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
    x_off, y_off = (target_size - nw) // 2, (target_size - nh) // 2
    canvas[y_off:y_off + nh, x_off:x_off + nw] = resized
    return canvas


def collect_image_files(source_dirs):
    img_paths = []
    print("\n📂 正在递归扫描文件夹...")
    for root_dir in source_dirs:
        if not os.path.exists(root_dir):
            print(f"   ⚠️ 路径不存在: {root_dir}")
            continue
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    img_paths.append(os.path.join(root, file))
    return img_paths


def main():
    judge = MultiModelJudge()
    files = collect_image_files(SOURCE_DIRS)

    if not files:
        print("❌ 没找到图片！")
        return

    print(f"\n🚀 开始工作！待处理: {len(files)} 张")
    print(f"💡 提示: 处理一张图大概需要 0.5秒 - 2秒，请耐心观看输出流。\n")

    total_mined = {f: 0 for f in FEATURES}

    for i, path in enumerate(files):
        filename = os.path.basename(path)

        # 实时进度条 (强制刷新)
        print(f"[{i + 1}/{len(files)}] {filename[:20]:<20} ... ", end="", flush=True)

        try:
            # 1. 读图
            img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), -1)
            if img is None:
                print("❌ 坏图")
                continue

            # 转 RGB
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # 2. 检测脸
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            rects = detector(gray, 0)  # 0 = 不放大，追求速度

            if not rects:
                print("⚠️ 无脸")  # 没检测到脸
                continue

            face = max(rects, key=lambda r: r.width() * r.height())

            # 过滤小脸
            if face.width() < 50:
                print("⚠️ 脸太小")
                continue

            shape = predictor(gray, face)

            # 3. 挖掘
            mined_count = 0
            for feature in FEATURES:
                crop = get_crop(img, shape, feature)
                if crop is None or crop.size == 0: continue

                final_input = resize_padding(crop)
                pred_class, conf = judge.predict(feature, final_input)

                if pred_class and conf >= CONFIDENCE_THRESHOLD:
                    save_dir = os.path.join(OUTPUT_DIR, feature, pred_class)
                    if not os.path.exists(save_dir): os.makedirs(save_dir)

                    short_name = os.path.splitext(filename)[0][:10]
                    timestamp = int(time.time() * 1000) % 1000000
                    new_filename = f"Mined_{short_name}_{timestamp}.jpg"

                    cv2.imencode('.jpg', final_input)[1].tofile(os.path.join(save_dir, new_filename))
                    total_mined[feature] += 1
                    mined_count += 1

            if mined_count > 0:
                print(f"✅ 提取 {mined_count} 项")
            else:
                print("💤 无匹配项")

        except Exception as e:
            print(f"❌ 报错: {str(e)[:20]}")
            continue

    print("\n" + "=" * 40)
    print("📊 最终统计:")
    for feat, count in total_mined.items():
        print(f"   - {feat}: {count}")
    print(f"📂 结果已保存至: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()