import os
import cv2
import dlib
import numpy as np
import pickle
from imutils import face_utils
from tqdm import tqdm

# ================= 路径自动修正 =================
# 1. 获取当前脚本所在的目录 (即 .../FaceBeautyProject/preprocess)
CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 获取项目根目录 (往上跳一级，即 .../FaceBeautyProject)
PROJECT_ROOT = os.path.dirname(CURRENT_SCRIPT_DIR)

print(f"📂 脚本位置: {CURRENT_SCRIPT_DIR}")
print(f"📂 项目根目录: {PROJECT_ROOT}")

# 3. 配置模型路径 (模型就在脚本旁边，所以直接用 CURRENT_SCRIPT_DIR)
PREDICTOR_PATH = os.path.join(CURRENT_SCRIPT_DIR, "shape_predictor_68_face_landmarks.dat")

# 4. 配置数据文件路径 (在根目录)
DATA_PKL_PATH = os.path.join(PROJECT_ROOT, "star_features.pkl")


# ================= 核心修复逻辑 =================
class DatabaseRepairman:
    def __init__(self):
        print("🔧 启动修复程序...")
        if not os.path.exists(PREDICTOR_PATH):
            raise FileNotFoundError(f"❌ 找不到模型: {PREDICTOR_PATH}")

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(PREDICTOR_PATH)
        print("✅ 模型加载成功！")

    def compute_full_features(self, shape):
        """完整的五官计算逻辑"""
        feats = {}
        eps = 1e-6
        # 1. 眼睛
        l_w = np.linalg.norm(shape[36] - shape[39])
        l_h = (np.linalg.norm(shape[37] - shape[41]) + np.linalg.norm(shape[38] - shape[40])) / 2
        l_ratio = l_w / (l_h + eps)
        l_tilt = shape[36][1] - shape[39][1]
        r_w = np.linalg.norm(shape[42] - shape[45])
        r_h = (np.linalg.norm(shape[43] - shape[47]) + np.linalg.norm(shape[44] - shape[46])) / 2
        r_ratio = r_w / (r_h + eps)
        r_tilt = shape[42][1] - shape[45][1]
        feats['eyes_vector'] = np.array([(l_ratio + r_ratio) / 2, (l_tilt + r_tilt) / 2])

        # 2. 鼻子
        nose_w = np.linalg.norm(shape[31] - shape[35])
        nose_h = np.linalg.norm(shape[27] - shape[33])
        feats['nose_vector'] = np.array([nose_w / (nose_h + eps)])

        # 3. 嘴巴
        lip_fullness = np.linalg.norm(shape[51] - shape[62]) + np.linalg.norm(shape[66] - shape[57])
        lip_width = np.linalg.norm(shape[48] - shape[54])
        face_width = np.linalg.norm(shape[3] - shape[13])
        feats['mouth_vector'] = np.array([lip_fullness / (lip_width + eps), lip_width / (face_width + eps)])

        # 4. 脸型
        jaw_w = np.linalg.norm(shape[4] - shape[12])
        cheek_w = np.linalg.norm(shape[2] - shape[14])
        face_h = np.linalg.norm(shape[8] - shape[27]) * 1.6
        feats['face_vector'] = np.array([jaw_w / (cheek_w + eps), face_h / (cheek_w + eps)])

        return feats

    def fix(self):
        if not os.path.exists(DATA_PKL_PATH):
            print(f"❌ 找不到特征库: {DATA_PKL_PATH}")
            return

        with open(DATA_PKL_PATH, "rb") as f:
            data = pickle.load(f)

        print(f"📊 正在扫描 {len(data)} 条数据...")
        fixed_count = 0

        for item in tqdm(data):
            features = item['features']
            # 检查是否缺失 'nose_vector'
            if 'nose_vector' not in features:
                # 1. 拼接图片绝对路径 (基于 PROJECT_ROOT)
                # 因为 item['image_path'] 存的是 "dataset/Best_Images/..." 这样的相对路径
                img_path = os.path.join(PROJECT_ROOT, item['image_path'])

                # 2. 重新计算
                if os.path.exists(img_path):
                    try:
                        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), -1)
                        if img is not None:
                            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            rects = self.detector(gray, 1)
                            if len(rects) > 0:
                                rect = max(rects, key=lambda r: r.width() * r.height())
                                shape = self.predictor(gray, rect)
                                shape_np = face_utils.shape_to_np(shape)

                                # 覆盖旧特征
                                item['features'] = self.compute_full_features(shape_np)
                                fixed_count += 1
                    except Exception as e:
                        print(f"修复失败 {item['name']}: {e}")
                else:
                    print(f"⚠️ 图片文件丢失: {img_path}")

        if fixed_count > 0:
            with open(DATA_PKL_PATH, "wb") as f:
                pickle.dump(data, f)
            print(f"\n✅ 成功修复了 {fixed_count} 条数据！")
            print("🚀 现在可以去运行 app.py 了！")
        else:
            print("\n🎉 数据很完美，没有发现缺失项。")


if __name__ == "__main__":
    try:
        repairman = DatabaseRepairman()
        repairman.fix()
    except Exception as e:
        print(f"运行出错: {e}")