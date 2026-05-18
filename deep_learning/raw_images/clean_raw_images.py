import os
import cv2
import dlib
import numpy as np
from tqdm import tqdm

# ================= 配置区 =================
# 输入：原始杂乱的全脸图
INPUT_ROOT = "deep_learning/raw_images"
# 输出：整理好、裁切好的训练图
OUTPUT_ROOT = "deep_learning/processed_dataset"

# 核心参数：裁剪时周围保留的空间比例 (0.2 = 20%)
PADDING_RATIO = 0.20

# 初始化 dlib 检测器
detector = dlib.get_frontal_face_detector()


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def crop_with_padding(img, face_rect, padding=0.2):
    """
    智能裁剪函数：基于人脸框向外扩充一定比例
    """
    h_img, w_img = img.shape[:2]

    # 1. 获取原始人脸坐标
    x1, y1 = face_rect.left(), face_rect.top()
    x2, y2 = face_rect.right(), face_rect.bottom()

    w_face = x2 - x1
    h_face = y2 - y1

    # 2. 计算扩充量 (20%)
    pad_w = int(w_face * padding)
    pad_h = int(h_face * padding)

    # 3. 计算新的裁剪坐标 (注意不要超出图片边界)
    new_x1 = max(0, x1 - pad_w)
    new_y1 = max(0, y1 - pad_h)
    new_x2 = min(w_img, x2 + pad_w)
    new_y2 = min(h_img, y2 + pad_h)

    # 4. 执行裁剪
    return img[new_y1:new_y2, new_x1:new_x2]


def process_dataset():
    print(f"🚀 开始处理数据...")
    print(f"📂 输入目录: {INPUT_ROOT}")
    print(f"📂 输出目录: {OUTPUT_ROOT}")
    print(f"📐 裁剪留白: {PADDING_RATIO * 100}%")

    # 遍历所有分类文件夹 (face_shape, eye_shape...)
    for main_cat in os.listdir(INPUT_ROOT):
        main_input_path = os.path.join(INPUT_ROOT, main_cat)
        if not os.path.isdir(main_input_path): continue

        # 遍历子分类 (round, square...)
        for sub_cat in os.listdir(main_input_path):
            sub_input_path = os.path.join(main_input_path, sub_cat)
            if not os.path.isdir(sub_input_path): continue

            # 准备输出目录
            sub_output_path = os.path.join(OUTPUT_ROOT, main_cat, sub_cat)
            ensure_dir(sub_output_path)

            print(f"\n⚡ 正在处理: [{main_cat}/{sub_cat}]")

            valid_count = 0
            files = [f for f in os.listdir(sub_input_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

            # 进度条遍历
            for filename in tqdm(files, ncols=80):
                img_path = os.path.join(sub_input_path, filename)

                try:
                    # 读取图片 (支持中文路径)
                    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), -1)
                    if img is None: continue

                    # 转灰度加速检测
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    rects = detector(gray, 1)

                    if len(rects) == 0:
                        continue  # 没脸，跳过

                    # 取最大的一张脸
                    face = max(rects, key=lambda r: r.width() * r.height())

                    # === 核心：带留白的裁剪 ===
                    cropped_img = crop_with_padding(img, face, padding=PADDING_RATIO)

                    # 如果裁剪后图片太小(比如小于50x50)，丢弃
                    if cropped_img.shape[0] < 50 or cropped_img.shape[1] < 50:
                        continue

                    # === 核心：标准化重命名 ===
                    # 格式: 分类名_序号.jpg (例: round_001.jpg)
                    new_filename = f"{sub_cat}_{valid_count + 1:03d}.jpg"
                    save_path = os.path.join(sub_output_path, new_filename)

                    # 保存 (统一转JPG)
                    cv2.imencode('.jpg', cropped_img)[1].tofile(save_path)
                    valid_count += 1

                except Exception as e:
                    pass  # 遇到坏图直接跳过，不报错

            print(f"   ✅ 成功提取: {valid_count} 张")


if __name__ == "__main__":
    if not os.path.exists(INPUT_ROOT):
        print(f"❌ 错误: 找不到输入目录 {INPUT_ROOT}，请先运行爬虫脚本！")
    else:
        process_dataset()
        print("\n🎉 全部处理完成！")
        print(f"请前往 {OUTPUT_ROOT} 查看最终的训练数据。")