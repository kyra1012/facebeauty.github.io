import os
import cv2
import dlib
import numpy as np
from tqdm import tqdm

# ================= 配置区 =================
INPUT_DIR = "../deep_learning/raw_images"
OUTPUT_DIR = "../deep_learning/final_training_data"
PREDICTOR_PATH = "../preprocess/shape_predictor_68_face_landmarks.dat"

# 初始化
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def resize_with_padding(img, target_size=224):
    """防变形：黑边填充"""
    # 强制转为3通道
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    h, w = img.shape[:2]
    scale = min(target_size / h, target_size / w)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)

    x_offset = (target_size - new_w) // 2
    y_offset = (target_size - new_h) // 2
    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized_img

    return canvas


def sanity_check(x1, y1, x2, y2, face_rect, feature_type):
    """
    🛡️ 尺寸熔断机制：防止因为检测错误导致裁出全脸
    """
    crop_h = y2 - y1
    crop_w = x2 - x1
    face_h = face_rect.height()

    if crop_h <= 0 or crop_w <= 0: return False

    # 规则1：五官特写高度不应超过全脸高度的 60%
    if feature_type in ["eye_shape", "eyebrow_shape", "nose_shape", "lip_shape"]:
        if crop_h > face_h * 0.60:
            return False

    # 规则2：眼睛应该是宽扁的，不能是竖条
    if feature_type in ["eye_shape", "eyebrow_shape"]:
        if crop_h > crop_w:
            return False

    return True


def get_precise_crop_box(img, shape, feature_type, face_rect):
    h_img, w_img = img.shape[:2]
    pts = np.array([[p.x, p.y] for p in shape.parts()])

    x1, y1, x2, y2 = 0, 0, 0, 0

    # === 1. 眼眉 (宽视野) ===
    if feature_type == "eye_shape" or feature_type == "eyebrow_shape":
        indices = list(range(17, 27)) + list(range(36, 48))
        roi_pts = pts[indices]

        min_x, max_x = np.min(roi_pts[:, 0]), np.max(roi_pts[:, 0])
        min_y, max_y = np.min(roi_pts[:, 1]), np.max(roi_pts[:, 1])

        w_roi = max_x - min_x
        h_roi = max_y - min_y

        pad_y = int(h_roi * 0.4)
        pad_x = int(w_roi * 0.15)

        x1 = min_x - pad_x;
        x2 = max_x + pad_x
        y1 = min_y - pad_y;
        y2 = max_y + pad_y

    # === 2. 鼻子 ===
    elif feature_type == "nose_shape":
        nose_pts = pts[27:36]
        min_x, max_x = np.min(nose_pts[:, 0]), np.max(nose_pts[:, 0])
        min_y, max_y = np.min(nose_pts[:, 1]), np.max(nose_pts[:, 1])

        w_roi = max_x - min_x
        h_roi = max_y - min_y

        pad_x = int(w_roi * 0.25)
        pad_y = int(h_roi * 0.25)

        brow_center_y = (pts[21][1] + pts[22][1]) // 2
        y1 = min(min_y - pad_y, brow_center_y)
        y2 = max_y + pad_y
        x1 = min_x - pad_x
        x2 = max_x + pad_x

    # === 3. 嘴唇 ===
    elif feature_type == "lip_shape":
        indices = range(48, 68)
        roi_pts = pts[indices]
        x, y, w, h = cv2.boundingRect(roi_pts)
        pad_w = int(w * 0.20)
        pad_h = int(h * 0.40)
        x1 = x - pad_w;
        x2 = x + w + pad_w
        y1 = y - pad_h;
        y2 = y + h + pad_h

    # === 4. 脸型 (全脸) ===
    elif feature_type == "face_shape":
        fx, fy, fw, fh = face_rect.left(), face_rect.top(), face_rect.width(), face_rect.height()
        pad_top = int(fh * 0.60)
        pad_bottom = int(fh * 0.20)
        pad_side = int(fw * 0.20)
        x1 = fx - pad_side;
        y1 = fy - pad_top
        x2 = fx + fw + pad_side;
        y2 = fy + fh + pad_bottom

    else:
        return None

    # === 🛡️ 执行熔断检查 ===
    if not sanity_check(x1, y1, x2, y2, face_rect, feature_type):
        return None

    return safe_crop(img, x1, y1, x2, y2)


def safe_crop(img, x1, y1, x2, y2):
    h, w = img.shape[:2]
    pad_top = abs(min(0, y1))
    pad_bottom = max(0, y2 - h)
    pad_left = abs(min(0, x1))
    pad_right = max(0, x2 - w)

    x1 = max(0, x1);
    y1 = max(0, y1)
    x2 = min(w, x2);
    y2 = min(h, y2)

    crop = img[y1:y2, x1:x2]
    if crop.size == 0: return None

    if pad_top > 0 or pad_bottom > 0 or pad_left > 0 or pad_right > 0:
        try:
            crop = cv2.copyMakeBorder(crop, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT,
                                      value=[0, 0, 0])
        except:
            return None
    return crop


def process():
    print(f"🔪 启动 V6 裁切+重命名程序...")
    print(f"📂 读取: {INPUT_DIR}")
    print(f"📂 输出: {OUTPUT_DIR}")

    for main_cat in os.listdir(INPUT_DIR):
        main_in = os.path.join(INPUT_DIR, main_cat)
        if not os.path.isdir(main_in): continue

        for sub_cat in os.listdir(main_in):
            sub_in = os.path.join(main_in, sub_cat)
            sub_out = os.path.join(OUTPUT_DIR, main_cat, sub_cat)
            ensure_dir(sub_out)

            files = [f for f in os.listdir(sub_in) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            if not files: continue

            print(f"\n⚡ 处理: [{main_cat}/{sub_cat}]")
            success_count = 0

            for fname in tqdm(files, ncols=80):
                img_path = os.path.join(sub_in, fname)
                img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                if img is None: continue

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                rects = detector(gray, 1)
                if len(rects) == 0: continue

                face = max(rects, key=lambda r: r.width() * r.height())
                shape = predictor(gray, face)

                crop = get_precise_crop_box(img, shape, main_cat, face)

                if crop is not None and crop.size > 0:
                    try:
                        final_img = resize_with_padding(crop, target_size=224)

                        # === 🆕 核心新增：自动编号重命名 ===
                        # 格式：子分类名_0001.jpg (例如 peach_0001.jpg)
                        new_filename = f"{sub_cat}_{success_count + 1:04d}.jpg"
                        save_path = os.path.join(sub_out, new_filename)

                        cv2.imencode('.jpg', final_img)[1].tofile(save_path)
                        success_count += 1
                    except:
                        pass

            print(f"   ✅ 成功生成 {success_count} 张标准切片")

    print("\n🎉 全部完成！图片已清洗、裁切并重命名。")


if __name__ == "__main__":
    process()