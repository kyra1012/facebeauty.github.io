import os
import cv2
import glob
import shutil
import numpy as np  # 新增导入 numpy


def process_best_images():
    base_dir = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset\Best_Images"

    if not os.path.exists(base_dir):
        print(f"错误: 找不到路径 {base_dir}")
        return

    face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(face_cascade_path)

    failed_persons = []

    subdirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    total_folders = len(subdirs)

    print(f"总计找到 {total_folders} 个明星文件夹，开始处理...")

    for i, subdir in enumerate(subdirs):
        person_name = os.path.basename(subdir)
        print(f"[{i + 1}/{total_folders}] 正在处理: {person_name}")

        image_files = []
        for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.JPEG', '*.PNG'):
            image_files.extend(glob.glob(os.path.join(subdir, ext)))

        if not image_files:
            print(f"    -> 跳过: 文件夹中未找到图片")
            continue

        best_match_path = os.path.join(subdir, 'best_match.jpg')

        target_img_path = best_match_path if os.path.exists(best_match_path) else image_files[0]

        # 【修改点 1：使用 numpy 处理中文路径读取】
        try:
            img = cv2.imdecode(np.fromfile(target_img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            img = None

        if img is None:
            print(f"    -> 读取失败: {target_img_path}")
            failed_persons.append(person_name)
            continue

        img_h, img_w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

        if len(faces) == 0:
            print("    -> 失败: 未能识别出人脸或不清晰")
            failed_persons.append(person_name)
            if target_img_path != best_match_path:
                shutil.move(target_img_path, best_match_path)
            continue

        # 选出面积最大的人脸
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        x, y, w, h = faces[0]

        # ==========================================================
        # 【核心修改点：1:1 正方形裁剪逻辑】
        # ==========================================================
        # 1. 计算人脸中心点
        cx = x + w // 2
        cy = y + h // 2

        # 2. 确定正方形的边长：取人脸宽高中较大的一个，加上四周留白 (这里取 1.6 倍)
        side = int(max(w, h) * 1.6)

        # 3. 确保正方形边长不超过原图的【最短边】
        side = min(side, img_w, img_h)

        # 4. 根据中心点和边长，计算初始的左上角坐标
        new_x = cx - side // 2
        new_y = cy - side // 2

        # 5. 边界检测与平移调整 (保证框是完整的 1:1 正方形，且不越出原图)
        if new_x < 0:
            new_x = 0
        elif new_x + side > img_w:
            new_x = img_w - side

        if new_y < 0:
            new_y = 0
        elif new_y + side > img_h:
            new_y = img_h - side

        new_right = new_x + side
        new_bottom = new_y + side

        # 6. 判断跳过条件：如果原图已经是正方形(宽高差极小)，且要裁的区域基本覆盖全图，则直接跳过
        if abs(img_w - img_h) <= 5 and (side * side) >= (img_w * img_h * 0.90):
            print("    -> 尺寸已经是 1:1 正方形且比例合适，跳过裁剪")
            if target_img_path != best_match_path:
                shutil.move(target_img_path, best_match_path)
        else:
            # 执行 1:1 裁剪
            cropped_img = img[new_y:new_bottom, new_x:new_right]

            # 【修改点 2：使用 numpy 处理中文路径保存】
            cv2.imencode('.jpg', cropped_img)[1].tofile(best_match_path)

            if target_img_path != best_match_path and os.path.exists(target_img_path):
                os.remove(target_img_path)

            print("    -> 成功裁剪为 1:1 正方形并保存为 best_match.jpg")
        # ==========================================================

    print("\n" + "=" * 40)
    print("清洗与裁剪任务完成！")
    print(f"总计识别失败/不清晰 人数: {len(failed_persons)}")
    if failed_persons:
        print("名单如下 (你可以手动处理这些图片):")
        for name in failed_persons:
            print(f" - {name}")
    print("=" * 40)


if __name__ == "__main__":
    process_best_images()