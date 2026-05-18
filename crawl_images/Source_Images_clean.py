import os
import cv2
import hashlib
import numpy as np

# ================= 配置区域 =================
dataset_root = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset"
source_base = os.path.join(dataset_root, "Source_Images")
PADDING_RATIO = 0.3
VALID_EXTS = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')

# 加载 OpenCV 自带的人脸识别模型 (无需安装额外库)
# cv2.data.haarcascades 会自动找到安装路径
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


# ===========================================

def get_file_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None


def global_deduplication(root_folder):
    print("🔄 [Step 1] 正在执行全局去重...")
    unique_hashes = {}
    duplicates = []

    for current_root, dirs, files in os.walk(root_folder):
        for filename in files:
            if not filename.lower().endswith(VALID_EXTS): continue
            file_path = os.path.join(current_root, filename)
            file_hash = get_file_md5(file_path)
            if file_hash in unique_hashes:
                duplicates.append(file_path)
            else:
                unique_hashes[file_hash] = file_path

    for dup in duplicates:
        try:
            os.remove(dup)
        except:
            pass
    print(f"✅ 删除了 {len(duplicates)} 张重复图片。")
    return len(duplicates)


def opencv_crop_and_clean():
    print("\n✂️ [Step 2] 开始使用 OpenCV 进行人脸裁切...")
    total_processed = 0
    total_cropped = 0
    total_deleted = 0

    for current_root, dirs, files in os.walk(source_base):
        for filename in files:
            if not filename.lower().endswith(VALID_EXTS): continue

            file_path = os.path.join(current_root, filename)
            total_processed += 1

            try:
                # 读取图片
                img_array = np.fromfile(file_path, np.uint8)
                image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if image is None:
                    os.remove(file_path)
                    continue

                h, w, _ = image.shape
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                # === 核心：使用 OpenCV 检测人脸 ===
                # scaleFactor: 扫描精度, minNeighbors: 误检过滤
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

                if len(faces) == 0:
                    print(f"❌ 无人脸 - 删除: {filename}")
                    os.remove(file_path)
                    total_deleted += 1
                    continue

                # 取最大的一张脸
                faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
                x, y, fw, fh = faces[0]

                # === 裁切逻辑 ===
                center_x = x + fw // 2
                center_y = y + fh // 2
                box_size = max(fw, fh)
                new_size = int(box_size * (1 + PADDING_RATIO))

                x1 = max(0, center_x - new_size // 2)
                y1 = max(0, center_y - new_size // 2)
                x2 = min(w, center_x + new_size // 2)
                y2 = min(h, center_y + new_size // 2)

                cropped_img = image[y1:y2, x1:x2]

                # 保存
                cv2.imencode('.jpg', cropped_img)[1].tofile(file_path)
                total_cropped += 1

            except Exception as e:
                print(f"Err: {e}")

    print(f"\n🎉 处理完成！扫描: {total_processed}, 裁切: {total_cropped}, 删除: {total_deleted}")


if __name__ == "__main__":
    global_deduplication(source_base)
    opencv_crop_and_clean()