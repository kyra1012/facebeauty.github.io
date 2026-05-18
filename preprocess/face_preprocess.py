import os
import cv2
import dlib
import numpy as np
import pandas as pd
import pickle
import shutil  # ✨ 新增：用于复制文件
from imutils import face_utils
from tqdm import tqdm

# ================= 1. 路径配置 =================
CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_SCRIPT_DIR)

print(f"📂 项目根目录: {PROJECT_ROOT}")

PREDICTOR_PATH = os.path.join(CURRENT_SCRIPT_DIR, "shape_predictor_68_face_landmarks.dat")
RECOGNITION_PATH = os.path.join(CURRENT_SCRIPT_DIR, "dlib_face_recognition_resnet_model_v1.dat")
CSV_PATH = os.path.join(PROJECT_ROOT, "dataset", "csv", "data.xlsx")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "dataset", "Source_Images")

# ✨ 新增：最佳图片保存仓库
BEST_IMAGES_DIR = os.path.join(PROJECT_ROOT, "dataset", "Best_Images")
# 最终数据文件
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "star_features.pkl")


# ================= 2. 核心处理类 =================
class RobustFeatureExtractor:
    def __init__(self):
        print("⏳ 加载 AI 模型中...")
        if not os.path.exists(PREDICTOR_PATH):
            raise FileNotFoundError(f"❌ 找不到模型: {PREDICTOR_PATH}")

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(PREDICTOR_PATH)
        self.facerec = dlib.face_recognition_model_v1(RECOGNITION_PATH)
        print("✅ 模型加载完毕！")

    def try_detect_face(self, image):
        """尝试检测人脸，含自动补边框策略"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 1)

        if len(rects) > 0:
            return rects, image

        # Padding 策略
        h, w = image.shape[:2]
        pad_h = int(h * 0.40)
        pad_w = int(w * 0.40)
        padded_img = cv2.copyMakeBorder(image, pad_h, pad_h, pad_w, pad_w,
                                        cv2.BORDER_CONSTANT, value=[128, 128, 128])
        gray_padded = cv2.cvtColor(padded_img, cv2.COLOR_BGR2GRAY)
        rects_padded = self.detector(gray_padded, 1)

        if len(rects_padded) > 0:
            return rects_padded, padded_img
        return [], None

    def process_image(self, image_path):
        try:
            img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), -1)
            if img is None: return None

            # 缩放加速
            h, w = img.shape[:2]
            if w > 1000: img = cv2.resize(img, (1000, int(h * 1000 / w)))

            rects, final_img = self.try_detect_face(img)
            if len(rects) == 0: return None

            rect = max(rects, key=lambda r: r.width() * r.height())

            # 提取特征
            shape = self.predictor(cv2.cvtColor(final_img, cv2.COLOR_BGR2GRAY), rect)
            rgb_img = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)
            embedding = np.array(self.facerec.compute_face_descriptor(rgb_img, shape))

            shape_np = face_utils.shape_to_np(shape)
            geo_features = self.compute_geometric_features(shape_np)

            return {
                "embedding": embedding,
                "geo_features": geo_features,
                "image_path": image_path  # 这里暂时还是原路径
            }
        except Exception:
            return None

    def compute_geometric_features(self, shape):
        # ... (保持原本的几何计算逻辑) ...
        feats = {}
        eps = 1e-6
        # 眼睛
        l_w = np.linalg.norm(shape[36] - shape[39])
        l_h = (np.linalg.norm(shape[37] - shape[41]) + np.linalg.norm(shape[38] - shape[40])) / 2
        l_ratio = l_w / (l_h + eps)
        l_tilt = shape[36][1] - shape[39][1]
        r_w = np.linalg.norm(shape[42] - shape[45])
        r_h = (np.linalg.norm(shape[43] - shape[47]) + np.linalg.norm(shape[44] - shape[46])) / 2
        r_ratio = r_w / (r_h + eps)
        r_tilt = shape[42][1] - shape[45][1]
        feats['eyes_vector'] = np.array([(l_ratio + r_ratio) / 2, (l_tilt + r_tilt) / 2])
        # 鼻子
        nose_w = np.linalg.norm(shape[31] - shape[35])
        nose_h = np.linalg.norm(shape[27] - shape[33])
        feats['nose_vector'] = np.array([nose_w / (nose_h + eps)])
        # 嘴巴
        lip_fullness = np.linalg.norm(shape[51] - shape[62]) + np.linalg.norm(shape[66] - shape[57])
        lip_width = np.linalg.norm(shape[48] - shape[54])
        face_width = np.linalg.norm(shape[3] - shape[13])
        feats['mouth_vector'] = np.array([lip_fullness / (lip_width + eps), lip_width / (face_width + eps)])
        # 脸型
        jaw_w = np.linalg.norm(shape[4] - shape[12])
        cheek_w = np.linalg.norm(shape[2] - shape[14])
        face_h = np.linalg.norm(shape[8] - shape[27]) * 1.6
        feats['face_vector'] = np.array([jaw_w / (cheek_w + eps), face_h / (cheek_w + eps)])
        return feats


# ================= 3. 主逻辑 =================
def main():
    extractor = RobustFeatureExtractor()

    if not os.path.exists(CSV_PATH):
        print(f"❌ 找不到 CSV: {CSV_PATH}")
        return

    # 1. 创建总目录
    if not os.path.exists(BEST_IMAGES_DIR):
        os.makedirs(BEST_IMAGES_DIR)
        print(f"📂 创建归档目录: {BEST_IMAGES_DIR}")

    # 2. 读取并去重
    try:
        if CSV_PATH.endswith('.csv'):
            df = pd.read_csv(CSV_PATH)
        else:
            df = pd.read_excel(CSV_PATH)
    except Exception as e:
        print(f"❌ 读取表格失败: {e}")
        return

    original_count = len(df)
    df_unique = df.drop_duplicates(subset=['姓名'], keep='first')
    unique_count = len(df_unique)

    print(f"📊 待处理: {unique_count} 人 (已去重)")

    processed_data = []
    pbar = tqdm(total=unique_count, unit="star", desc="🚀 提取 & 归档中")

    success_count = 0
    fail_count = 0

    for index, row in df_unique.iterrows():
        name = row['姓名']

        # 路径查找
        folder_name = os.path.basename(os.path.normpath(str(row['图片文件名'])))
        target_dir = os.path.join(IMAGES_DIR, folder_name)
        if not os.path.isdir(target_dir):
            target_dir = os.path.join(IMAGES_DIR, str(name))

        best_data = None

        if os.path.isdir(target_dir):
            image_files = [f for f in os.listdir(target_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            valid_candidates = []

            for img_file in image_files:
                full_path = os.path.join(target_dir, img_file)
                res = extractor.process_image(full_path)
                if res:
                    valid_candidates.append(res)

            # 筛选最佳图片
            if valid_candidates:
                if len(valid_candidates) == 1:
                    best_data = valid_candidates[0]
                else:
                    embs = np.array([d['embedding'] for d in valid_candidates])
                    mean = np.mean(embs, axis=0)
                    dists = np.linalg.norm(embs - mean, axis=1)
                    best_data = valid_candidates[np.argmin(dists)]

        # --- 归档与保存逻辑 ---
        if best_data:
            # 1. 准备新家
            # 处理文件夹名称中可能的非法字符
            safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_', '-')]).strip()
            star_best_dir = os.path.join(BEST_IMAGES_DIR, safe_name)

            if not os.path.exists(star_best_dir):
                os.makedirs(star_best_dir)

            # 2. 复制图片
            # 源文件
            src_file = best_data['image_path']
            # 目标文件名 (保留原后缀，名字改为 best_match 以便识别)
            ext = os.path.splitext(src_file)[1]
            dst_filename = "best_match" + ext
            dst_file = os.path.join(star_best_dir, dst_filename)

            try:
                shutil.copy2(src_file, dst_file)

                # ✨ 关键：保存到数据库的路径，改成新的 Best_Images 路径！
                # 使用相对路径，这样你的项目搬到任何电脑都能运行
                relative_path = os.path.relpath(dst_file, PROJECT_ROOT)

                processed_data.append({
                    "name": name,
                    "year": row['年份'],
                    "country": row['国家/地区'],
                    "image_path": relative_path,  # 指向 Best_Images 里的图
                    "embedding": best_data['embedding'],
                    "features": best_data['geo_features']
                })
                success_count += 1
            except Exception as e:
                # print(f"复制失败: {e}")
                fail_count += 1
        else:
            fail_count += 1

        pbar.set_postfix({"✅": success_count, "❌": fail_count})
        pbar.update(1)

        # 自动存档
        if success_count > 0 and success_count % 20 == 0:
            with open(OUTPUT_FILE, 'wb') as f:
                pickle.dump(processed_data, f)

    pbar.close()

    print(f"\n📊 统计: 成功归档 {success_count} 人, 失败 {fail_count} 人")
    if processed_data:
        with open(OUTPUT_FILE, 'wb') as f:
            pickle.dump(processed_data, f)
        print(f"🎉 成功！\n1. 数据已保存至 {OUTPUT_FILE}\n2. 最佳图片已归档至 {BEST_IMAGES_DIR}")
    else:
        print("❌ 无数据生成。")


if __name__ == "__main__":
    main()