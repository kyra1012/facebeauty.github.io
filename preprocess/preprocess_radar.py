import os
import cv2
import dlib
import numpy as np
import pickle
from imutils import face_utils
from tqdm import tqdm

# ================= 1. 路径自动修正系统 =================
# 获取当前脚本所在的目录 (即 .../FaceBeautyProject/preprocess)
CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 获取项目根目录 (往上跳一级，即 .../FaceBeautyProject)
PROJECT_ROOT = os.path.dirname(CURRENT_SCRIPT_DIR)

print(f"📂 脚本位置: {CURRENT_SCRIPT_DIR}")
print(f"📂 项目根目录: {PROJECT_ROOT}")

# 模型路径 (模型在 preprocess 文件夹里)
PREDICTOR_PATH = os.path.join(CURRENT_SCRIPT_DIR, "shape_predictor_68_face_landmarks.dat")

# 读取旧数据库 (在根目录)
INPUT_PKL = os.path.join(PROJECT_ROOT, "star_features.pkl")

# 输出新数据库 (保存到根目录)
OUTPUT_PKL = os.path.join(PROJECT_ROOT, "star_features_radar.pkl")


# ================= 2. 核心算法：六维特征计算器 =================
class RadarFeatureCalculator:
    def __init__(self):
        print("⏳ 正在加载 Dlib 模型...")
        if not os.path.exists(PREDICTOR_PATH):
            raise FileNotFoundError(f"❌ 模型文件未找到: {PREDICTOR_PATH}")
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(PREDICTOR_PATH)

    def calculate_metrics(self, image_path):
        """计算单张图片的 6 大维度"""
        # 路径修正：数据库里的 image_path 是 "dataset/Best_Images/..." (相对路径)
        # 我们需要把它拼接成绝对路径
        full_path = os.path.join(PROJECT_ROOT, image_path)

        if not os.path.exists(full_path):
            # print(f"⚠️ 图片丢失: {full_path}")
            return None

        try:
            img = cv2.imdecode(np.fromfile(full_path, dtype=np.uint8), -1)
            if img is None: return None

            # 检测人脸
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            rects = self.detector(gray, 1)
            if len(rects) == 0: return None

            # 取最大的人脸
            rect = max(rects, key=lambda r: r.width() * r.height())
            shape = self.predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)

            # ================= 维度计算 (严格按照需求) =================

            # 1. 眼间距 (Eye Distance)
            # 内眼角间距 (39-42) / 外眼角间距 (36-45)
            inner_dist = np.linalg.norm(shape[39] - shape[42])
            outer_dist = np.linalg.norm(shape[36] - shape[45])
            eye_dist = inner_dist / (outer_dist + 1e-6)

            # 2. 眉眼距 (Brow-Eye Distance)
            # 眉毛下缘(19,24) 到 眼睛上缘(37,44) 的平均距离 / 脸长
            brow_y = (shape[19][1] + shape[24][1]) / 2
            eye_y = (shape[37][1] + shape[44][1]) / 2
            face_len = np.linalg.norm(shape[27] - shape[8]) * 1.6
            brow_eye = abs(eye_y - brow_y) / (face_len + 1e-6)

            # 3. 三庭比例 (Thirds Ratio)
            # 中庭(眉心-鼻底) / 下庭(鼻底-下巴)
            brow_center_y = (shape[21][1] + shape[22][1]) / 2
            nose_base_y = shape[33][1]
            chin_y = shape[8][1]
            middle_len = nose_base_y - brow_center_y
            lower_len = chin_y - nose_base_y
            thirds_ratio = middle_len / (lower_len + 1e-6)

            # 4. 面部折叠度 (Face Fold / Jaw Impact)
            # 下颚角宽度 (4-12) / 颧骨宽度 (1-15)
            jaw_w = np.linalg.norm(shape[4] - shape[12])
            cheek_w = np.linalg.norm(shape[1] - shape[15])
            fold_ratio = jaw_w / (cheek_w + 1e-6)

            # 5. 五官聚集度 (Feature Compactness)
            # 五官矩形面积 / 全脸矩形面积
            feat_top = min(shape[19][1], shape[24][1])
            feat_bot = shape[57][1]
            feat_h = feat_bot - feat_top
            feat_area = feat_h * outer_dist
            face_area = face_len * cheek_w
            compact_ratio = feat_area / (face_area + 1e-6)

            # 6. 鼻型精致度 (Nose Shape)
            # 鼻翼宽 / 鼻梁长
            nose_w = np.linalg.norm(shape[31] - shape[35])
            nose_h = np.linalg.norm(shape[27] - shape[33])
            nose_ratio = nose_w / (nose_h + 1e-6)

            return {
                'eye_dist': eye_dist,
                'brow_eye': brow_eye,
                'thirds': thirds_ratio,
                'fold': fold_ratio,
                'compact': compact_ratio,
                'nose': nose_ratio
            }
        except Exception:
            return None


# ================= 3. 主程序 =================
def main():
    print(f"📄 读取旧数据库: {INPUT_PKL}")
    if not os.path.exists(INPUT_PKL):
        print(f"❌ 依然找不到文件！请确认文件是否在: {INPUT_PKL}")
        return

    with open(INPUT_PKL, "rb") as f:
        data = pickle.load(f)

    calculator = RadarFeatureCalculator()
    success_count = 0

    print("\n🚀 开始重新计算明星的六维雷达数据...")
    # 使用 tqdm 显示进度
    for star in tqdm(data):
        img_path = star['image_path']  # 这是相对路径 "dataset/Best_Images/..."

        # 计算新特征
        radar_stats = calculator.calculate_metrics(img_path)

        # 无论成功失败，都必须要有这个字段，否则前端会报错
        if radar_stats:
            star['radar_stats'] = radar_stats
            success_count += 1
        else:
            # 失败兜底数据 (使用美学常模)
            star['radar_stats'] = {
                'eye_dist': 0.35, 'brow_eye': 0.06, 'thirds': 1.0,
                'fold': 0.75, 'compact': 0.35, 'nose': 0.7
            }

    print(f"\n✅ 处理完成！成功更新 {success_count} / {len(data)} 位明星。")

    # 保存新文件
    with open(OUTPUT_PKL, "wb") as f:
        pickle.dump(data, f)
    print(f"💾 新数据库已保存至: {OUTPUT_PKL}")

if __name__ == "__main__":
    main()