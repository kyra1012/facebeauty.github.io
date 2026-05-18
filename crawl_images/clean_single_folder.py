import os
import cv2
import hashlib
import numpy as np

TARGET_FOLDER_NAME = "金亚荣 (Yura)"

# 数据集根目录 (保持不变)
dataset_root = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset"
source_base = os.path.join(dataset_root, "Source_Images")

# 3. 裁切扩边比例 (0.3 表示向外扩30%)
PADDING_RATIO = 0.3
# ==========================================================

# 组合出该人的完整路径
target_path = os.path.join(source_base, TARGET_FOLDER_NAME)

# 加载 OpenCV 人脸识别模型
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')


def get_file_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None


def clean_single_folder():
    if not os.path.exists(target_path):
        print(f"❌ 找不到文件夹: {target_path}")
        print("请检查 TARGET_FOLDER_NAME 是否写对了？")
        return

    print(f"🚀 正在处理目标: {TARGET_FOLDER_NAME}")
    print(f"📂 路径: {target_path}")

    # ================= 1. 文件夹内去重 =================
    print("\n[Step 1] 正在检查重复图片...")
    hashes = {}
    duplicates = []

    # 获取所有图片文件
    files = [f for f in os.listdir(target_path) if f.lower().endswith(valid_exts)]

    for filename in files:
        file_path = os.path.join(target_path, filename)
        file_hash = get_file_md5(file_path)

        if file_hash in hashes:
            duplicates.append(file_path)
        else:
            hashes[file_hash] = file_path

    # 删除重复
    for dup in duplicates:
        try:
            os.remove(dup)
            print(f"  🗑️ 删除重复: {os.path.basename(dup)}")
        except:
            pass

    if not duplicates:
        print("  ✅ 没有发现重复图片。")

    # ================= 2. 人脸检测与裁切 =================
    print("\n[Step 2] 正在进行人脸裁切与清洗...")
    # 重新获取文件列表（因为刚才可能删除了）
    files = [f for f in os.listdir(target_path) if f.lower().endswith(valid_exts)]

    kept_files = []  # 记录处理成功的图片路径，用于最后重命名

    for filename in files:
        file_path = os.path.join(target_path, filename)

        try:
            # 读取图片
            img_array = np.fromfile(file_path, np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if image is None:
                os.remove(file_path)
                continue

            # 转灰度
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 检测人脸
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

            if len(faces) == 0:
                print(f"  ❌ 无人脸 - 删除: {filename}")
                os.remove(file_path)
                continue

            # 取最大的人脸
            faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
            x, y, w, h = faces[0]

            # 计算裁切范围 (带 Padding)
            img_h, img_w, _ = image.shape
            center_x = x + w // 2
            center_y = y + h // 2
            box_size = max(w, h)
            new_size = int(box_size * (1 + PADDING_RATIO))

            x1 = max(0, center_x - new_size // 2)
            y1 = max(0, center_y - new_size // 2)
            x2 = min(img_w, center_x + new_size // 2)
            y2 = min(img_h, center_y + new_size // 2)

            cropped = image[y1:y2, x1:x2]

            # 覆盖保存
            cv2.imencode('.jpg', cropped)[1].tofile(file_path)
            kept_files.append(file_path)
            # print(f"  ✂️ 已裁切: {filename}")

        except Exception as e:
            print(f"  ⚠️ 出错: {filename} ({e})")

    # ================= 3. 批量重命名 (1.jpg, 2.jpg...) =================
    print(f"\n[Step 3] 正在重命名 {len(kept_files)} 张图片...")

    # 为了防止命名冲突（比如 1.jpg 已存在），先全部重命名为临时名字
    temp_files = []
    for i, old_path in enumerate(kept_files):
        folder = os.path.dirname(old_path)
        ext = os.path.splitext(old_path)[1]
        # 临时名：temp_timestamp_index.jpg
        temp_name = f"temp_{i}{ext}"
        temp_path = os.path.join(folder, temp_name)

        os.rename(old_path, temp_path)
        temp_files.append(temp_path)

    # 再重命名为 1.jpg, 2.jpg...
    for i, temp_path in enumerate(temp_files, 1):
        folder = os.path.dirname(temp_path)
        ext = os.path.splitext(temp_path)[1]

        new_name = f"{i}{ext}"  # 结果: 1.jpg
        new_path = os.path.join(folder, new_name)

        os.rename(temp_path, new_path)

    print(
        f"✅ 处理完成！文件夹 '{TARGET_FOLDER_NAME}' 现在包含 {len(temp_files)} 张整齐的图片 (1.jpg ~ {len(temp_files)}.jpg)")


if __name__ == "__main__":
    clean_single_folder()