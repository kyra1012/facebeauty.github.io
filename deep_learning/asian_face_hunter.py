import os
import shutil
import cv2
import dlib
import ssl
import time
import logging
import numpy as np
# 引入两大爬虫引擎
from icrawler.builtin import BaiduImageCrawler, BingImageCrawler

# ================= 核心配置区 =================
# 1. 目标：我们要凑够多少张高质量正脸照？
TARGET_COUNT = 300

# 2. 存放位置 (可以直接喂给 mining_machine.py)
SAVE_DIR = r"C:\Users\86153\Desktop\FaceBeautyProject\raw_source"

# 3. 关键词策略 (中西合璧)
# 必应(Bing)用英文搜，质量极高
KEYWORDS_BING = [
    "Asian woman face close up high resolution",
    "Chinese beauty portrait photography",
    "Korean ID photo female",
    "Japanese female face frontal view",
    "Asian model makeup close up",
    "Asian skin test face",
    "Asian celebrity unretouched photos"
]

# 百度用中文搜，接地气
KEYWORDS_BAIDU = [
    "亚洲女性 证件照 高清",
    "最美证件照 韩国",
    "高清 妆容 模特 怼脸",
    "护肤 皮肤检测 对比图",
    "中国女明星 高清 生图",
    "整形 模版 脸型 正面"
]

# 4. Dlib 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
PREDICTOR_PATH = os.path.join(PROJECT_ROOT, "preprocess", "shape_predictor_68_face_landmarks.dat")

# ================= 核心修复与工具 =================

# 🛠️ 1. 全局禁用 SSL 验证 (解决报错的核心)
ssl._create_default_https_context = ssl._create_unverified_context

# 🛠️ 2. 压制日志
logging.getLogger('icrawler').setLevel(logging.ERROR)

# 初始化 Dlib
detector = dlib.get_frontal_face_detector()


def is_valid_face(img_path):
    """
    清洗函数：读取图片 -> 检查有没有脸 -> 检查脸够不够大
    """
    try:
        # 支持中文路径读取
        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), -1)
        if img is None: return False

        # 转灰度
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        rects = detector(gray, 1)
        if len(rects) == 0: return False  # 没脸，删

        # 取最大脸
        face = max(rects, key=lambda r: r.width() * r.height())
        if face.width() < 120: return False  # 脸太小(小于120像素)，删

        return True
    except:
        return False


def clean_data(folder):
    """遍历文件夹，删除不合格图片"""
    print(f"   🧹 正在执行 AI 安检 (去除无脸/侧脸/小图)...")
    files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

    current_valid = 0

    for f in files:
        path = os.path.join(folder, f)
        if is_valid_face(path):
            current_valid += 1
        else:
            try:
                os.remove(path)  # 不合格直接删
            except:
                pass

    return current_valid


def run_global_hunter():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    print(f"🚀 启动全球人脸猎人 (Bing + Baidu 联合搜索)...")
    print(f"🎯 目标: {TARGET_COUNT} 张高质量正脸素材")
    print(f"📂 仓库: {SAVE_DIR}")

    # 临时目录
    temp_root = os.path.join(BASE_DIR, "temp_global_bucket")
    if os.path.exists(temp_root): shutil.rmtree(temp_root)
    os.makedirs(temp_root)

    total_files = len(os.listdir(SAVE_DIR))

    # === 第一阶段：必应轰炸 (Bing) - 质量最高 ===
    print(f"\n{'=' * 40}")
    print(f"🌍 Phase 1: 必应国际版 (Bing) - 英文搜索")
    print(f"{'=' * 40}")

    for kw in KEYWORDS_BING:
        if total_files >= TARGET_COUNT: break
        print(f"🔎 Bing Searching: '{kw}'")

        kw_dir = os.path.join(temp_root, "bing_" + kw.replace(" ", "_")[:10])
        if not os.path.exists(kw_dir): os.makedirs(kw_dir)

        try:
            # 必应引擎
            bing = BingImageCrawler(downloader_threads=4, storage={'root_dir': kw_dir})
            bing.crawl(keyword=kw, max_num=60)  # 每个词搜60张
        except Exception as e:
            print(f"   Bing Error: {e}")

        # 转移文件
        downloaded = os.listdir(kw_dir)
        for f in downloaded:
            src = os.path.join(kw_dir, f)
            dst = os.path.join(SAVE_DIR, f"Bing_{int(time.time() * 1000)}_{f}")
            shutil.move(src, dst)

        # 实时清洗
        total_files = clean_data(SAVE_DIR)
        print(f"   📊 当前库存: {total_files} / {TARGET_COUNT}")

    # === 第二阶段：百度扫尾 (Baidu) - 中文补充 ===
    if total_files < TARGET_COUNT:
        print(f"\n{'=' * 40}")
        print(f"🇨🇳 Phase 2: 百度图片 (Baidu) - 中文搜索")
        print(f"{'=' * 40}")

        for kw in KEYWORDS_BAIDU:
            if total_files >= TARGET_COUNT: break
            print(f"🔎 Baidu Searching: '{kw}'")

            kw_dir = os.path.join(temp_root, "baidu_" + kw.replace(" ", "_")[:10])
            if not os.path.exists(kw_dir): os.makedirs(kw_dir)

            try:
                # 百度引擎
                baidu = BaiduImageCrawler(downloader_threads=4, storage={'root_dir': kw_dir})
                baidu.crawl(keyword=kw, max_num=60)
            except Exception as e:
                print(f"   Baidu Error: {e}")

            # 转移文件
            downloaded = os.listdir(kw_dir)
            for f in downloaded:
                src = os.path.join(kw_dir, f)
                dst = os.path.join(SAVE_DIR, f"Baidu_{int(time.time() * 1000)}_{f}")
                shutil.move(src, dst)

            # 实时清洗
            total_files = clean_data(SAVE_DIR)
            print(f"   📊 当前库存: {total_files} / {TARGET_COUNT}")

    # 清理垃圾
    if os.path.exists(temp_root): shutil.rmtree(temp_root)

    print(f"\n\n查找结束！")
    print(f"🏆 最终在 {SAVE_DIR} 中保留了 {total_files} 张高质量图片。")
    print(f"💡 这里的图片都是经过人脸检测的，质量很高。")
    print(f"👉 下一步：请运行 'mining_machine.py' 来挖掘这些图片里的五官！")


if __name__ == "__main__":
    run_global_hunter()