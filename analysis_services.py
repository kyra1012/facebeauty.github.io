import os
import cv2
import dlib
import numpy as np
import pickle
import base64
import torch
import yaml  # Added yaml support
from torchvision import transforms
from PIL import Image
from sklearn.decomposition import PCA
from imutils import face_utils
import torch.nn as nn
from torchvision import models

print("🔥 Loaded Beauty Engine V12.0 - Full Integrity Mode")

# ==============================================================================
# 0. 全局配置与路径
# ==============================================================================
# Robust path determination
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# If script is in root (FaceBeautyProject/), assets is in ./assets
# If script is in pages/, assets is in ../assets
PROJECT_ROOT = os.path.dirname(CURRENT_DIR) if os.path.basename(CURRENT_DIR) == "pages" else CURRENT_DIR

PREDICTOR_PATH = os.path.join(PROJECT_ROOT, "preprocess", "shape_predictor_68_face_landmarks.dat")
RECOGNITION_PATH = os.path.join(PROJECT_ROOT, "preprocess", "dlib_face_recognition_resnet_model_v1.dat")
DATA_PKL_PATH = os.path.join(PROJECT_ROOT, "preprocess", "result", "star_features_radar.pkl")
MODEL_DIR = os.path.join(PROJECT_ROOT, "deep_learning", "models")
IMAGES_ROOT = PROJECT_ROOT
GALLERY_PATH = os.path.join(PROJECT_ROOT, "assets", "views_analysis")

# Content YAML Path
P1_YAML_PATH = os.path.join(PROJECT_ROOT, "assets", "content", "p1_face_analysis.yaml")

# Load P1 YAML Data Globally
try:
    if os.path.exists(P1_YAML_PATH):
        with open(P1_YAML_PATH, 'r', encoding='utf-8') as f:
            FACE_ANALYSIS_DB = yaml.safe_load(f)
    else:
        print(f"Warning: P1 YAML not found at {P1_YAML_PATH}")
        FACE_ANALYSIS_DB = {}
except Exception as e:
    print(f"Error loading P1 YAML: {e}")
    FACE_ANALYSIS_DB = {}

# ==============================================================================
# 1. 深度学习配置
# ==============================================================================
CLASS_MAPPINGS = {
    'face': ['round', 'square', 'long', 'oval', 'diamond', 'heart'],
    'eyes': ['peach', 'almond', 'phoenix', 'round_eye', 'slender', 'downturned', 'triangular'],
    'brow': ['willow', 'crescent', 'european_arch', 'flat', 'sword', 'eight'],
    'nose': ['standard', 'fleshy', 'greek', 'hawk', 'snub'],
    'lip': ['standard_lip', 'm_lip', 'thick', 'thin', 'downturned_lip']
}

MODEL_FILES = {
    'face': 'face_shape.pth',
    'eyes': 'eye_shape.pth',
    'brow': 'eyebrow_shape.pth',
    'nose': 'nose_shape.pth',
    'lip': 'lip_shape.pth'
}


# Helper to fetch text safely
def get_text(category, key, default_key=None):
    if not FACE_ANALYSIS_DB or category not in FACE_ANALYSIS_DB:
        return (key, "AI分析特征")

    # Try direct key match
    if key in FACE_ANALYSIS_DB[category]:
        data = FACE_ANALYSIS_DB[category][key]
        return (data.get('name', key), data.get('desc', ""))

    # Try mapping keys (for mismatched internal names vs yaml keys)
    # This ensures backward compatibility if internal keys don't perfectly match yaml keys
    # For now, we assume simple mapping or return key
    return (key, "AI分析特征")


class DeepFeatureAnalyzer:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.models = {}
        self.model_classes = {}  # 🚨 新增：专门用来存储模型训练时的真实标签顺序！
        self.transforms = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        self._load_models()

    def _load_models(self):
        print(f"👉 正在组装深度学习引擎，目标文件夹: {MODEL_DIR}")
        if not os.path.exists(MODEL_DIR):
            return

        for key, filename in MODEL_FILES.items():
            path = os.path.join(MODEL_DIR, filename)
            if os.path.exists(path):
                try:
                    checkpoint = torch.load(path, map_location=self.device)

                    # 🚨 提取训练时真实的类别顺序
                    class_names = checkpoint.get('classes', [])
                    num_classes = len(class_names)
                    arch = checkpoint.get('arch', 'resnet18')

                    if num_classes == 0:
                        class_names = CLASS_MAPPINGS.get(key, [])
                        num_classes = len(class_names)

                    # 🚨 重点：把真实的顺序存起来
                    self.model_classes[key] = class_names

                    if arch == "resnet34":
                        model = models.resnet34(weights=None)
                    else:
                        model = models.resnet18(weights=None)

                    model.fc = nn.Sequential(
                        nn.Dropout(p=0.5),
                        nn.Linear(model.fc.in_features, num_classes)
                    )

                    model.load_state_dict(checkpoint['model_state_dict'])
                    model = model.to(self.device)
                    model.eval()

                    self.models[key] = model
                    print(f"✅ 成功组装并加载 {key} 模型: {filename} (标签库已校准)")

                except Exception as e:
                    print(f"❌ 找到了 {filename}，但组装崩溃了！真实原因: {str(e)}")

    def predict(self, feature_type, image_crop):
        if feature_type not in self.models or image_crop is None or image_crop.size == 0:
            return None

        try:
            img_pil = Image.fromarray(cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB))
            input_tensor = self.transforms(img_pil).unsqueeze(0).to(self.device)
            with torch.no_grad():
                outputs = self.models[feature_type](input_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                score, preds = torch.max(probs, 1)

            # 🚨 核心修复：使用模型自带的真实标签表，而不是全局写死的字典！
            real_classes = self.model_classes.get(feature_type, CLASS_MAPPINGS[feature_type])
            label_key = real_classes[preds.item()]

            yaml_key_map = {
                'face': {
                    'diamond': '菱形脸', 'oval': '鹅蛋脸', 'round': '圆脸', 'square': '方脸', 'square_round': '方圆脸'
                },
                'eyes': {
                    'almond': '杏眼', 'downturned': '下垂眼', 'peach': '桃花眼', 'phoenix': '丹凤眼', 'round': '圆眼',
                    'slender': '细长眼', 'triangular': '三角眼'
                },
                'brow': {
                    'crescent': '弯月眉', 'eight': '八字眉', 'european_arch': '欧式挑眉', 'flat': '一字平眉',
                    'sword': '剑眉', 'willow': '柳叶眉'
                },
                'nose': {
                    'bulbous': '肉肉鼻', 'greek': '希腊鼻', 'hawk': '鹰钩鼻', 'snub': '小翘鼻', 'upturned_pig': '朝天鼻'
                },
                'lip': {
                    'm_shaped': 'M字唇', 'petal': '标准花瓣唇', 'smile': '微笑唇', 'thick': '丰满唇', 'thin': '薄唇'
                }
            }

            lookup_key = yaml_key_map.get(feature_type, {}).get(label_key, label_key)
            name, desc = get_text(feature_type, lookup_key)

            return (name, desc, True, label_key)
        except Exception as e:
            print(f"❌ AI预测 {feature_type} 时崩溃: {str(e)}")
            return None
# ==============================================================================
# 2. 几何算法与六维计算
# ==============================================================================
class AdvancedFeatureCalculator:
    @staticmethod
    def calc_raw_metrics(shape):
        """计算原始几何比率"""
        try:
            inner_dist = np.linalg.norm(shape[39] - shape[42])
            outer_dist = np.linalg.norm(shape[36] - shape[45])
            eye_dist = inner_dist / (outer_dist + 1e-6)

            brow_y = (shape[19][1] + shape[24][1]) / 2
            eye_y = (shape[37][1] + shape[44][1]) / 2
            face_len = np.linalg.norm(shape[27] - shape[8]) * 1.6
            brow_eye = abs(eye_y - brow_y) / (face_len + 1e-6)

            brow_center_y = (shape[21][1] + shape[22][1]) / 2
            nose_base_y = shape[33][1]
            chin_y = shape[8][1]
            middle_len = nose_base_y - brow_center_y
            lower_len = chin_y - nose_base_y
            thirds_ratio = middle_len / (lower_len + 1e-6)

            jaw_w = np.linalg.norm(shape[4] - shape[12])
            cheek_w = np.linalg.norm(shape[1] - shape[15])
            fold_ratio = jaw_w / (cheek_w + 1e-6)

            feat_top = min(shape[19][1], shape[24][1])
            feat_bot = shape[57][1]
            feat_h = feat_bot - feat_top
            feat_area = feat_h * outer_dist
            face_area = face_len * cheek_w
            compact_ratio = feat_area / (face_area + 1e-6)

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
        except Exception as e:
            return None

    @staticmethod
    def normalize_for_radar(raw_stats):
        if not raw_stats: return [50, 50, 50, 50, 50, 50]
        mapping = [
            ('eye_dist', 0.36, 400),
            ('brow_eye', 0.08, 800),
            ('thirds', 1.0, 150),
            ('fold', 0.78, 250),
            ('compact', 0.35, 500),
            ('nose', 0.70, 200)
        ]
        scores = []
        for key, ideal, scale in mapping:
            val = raw_stats.get(key, ideal)
            diff = abs(val - ideal)
            score = 100 - (diff * scale)
            score = max(30, min(98, score))
            scores.append(int(score))
        return scores


# ==============================================================================
# 3. 几何分类器 (Refactored to use YAML text)
# ==============================================================================
class FaceClassifier:
    @staticmethod
    def _dist(lm, i, j):
        return np.linalg.norm(lm[i] - lm[j])

    @staticmethod
    def _angle(lm, p1, p2, p3):
        v1 = lm[p1] - lm[p2];
        v2 = lm[p3] - lm[p2]
        cosine = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

    @staticmethod
    def _calculate_angle(a, b, c):
        ba = a - b;
        bc = c - b
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

    # --- 辅助Getter ---
    @staticmethod
    def get_face_ratios(shape):
        cheek_w = FaceClassifier._dist(shape, 1, 15)
        jaw_w = FaceClassifier._dist(shape, 4, 12)
        ratio = jaw_w / (cheek_w + 1e-6)
        return f"骨量系数 {ratio:.2f}"

    @staticmethod
    def get_eye_ratios(shape):
        h_l = FaceClassifier._dist(shape, 37, 41);
        w_l = FaceClassifier._dist(shape, 36, 39)
        ear = h_l / (w_l + 1e-6)
        return f"纵横比 {ear:.2f}"

    @staticmethod
    def get_nose_ratios(shape):
        ratio = FaceClassifier._dist(shape, 31, 35) / (FaceClassifier._dist(shape, 39, 42) + 1e-6)
        return f"鼻宽比 {ratio:.2f}"

    @staticmethod
    def get_lip_ratios(shape):
        mouth_w = FaceClassifier._dist(shape, 48, 54)
        total_thick = shape[57][1] - shape[51][1]
        fullness = total_thick / (mouth_w + 1e-6)
        return f"厚度 {fullness:.2f}"

    # --- 几何分类逻辑 (Lookups from YAML) ---
    @staticmethod
    def classify_face_geom(shape):
        cheek_w = FaceClassifier._dist(shape, 1, 15);
        jaw_w = FaceClassifier._dist(shape, 4, 12)
        face_len = (shape[8][1] - (shape[21][1] + shape[22][1]) / 2) * 1.55
        hw_ratio = face_len / (cheek_w + 1e-6);
        jaw_cheek_ratio = jaw_w / (cheek_w + 1e-6)
        chin_angle = FaceClassifier._angle(shape, 6, 8, 10)
        left_angle = FaceClassifier._calculate_angle(shape[3], shape[4], shape[5])
        right_angle = FaceClassifier._calculate_angle(shape[11], shape[12], shape[13])
        avg_jaw_angle = (left_angle + right_angle) / 2
        detail = f"折角{int(avg_jaw_angle)}°"

        k = "鹅蛋脸"  # Default
        if jaw_cheek_ratio > 0.82:
            if avg_jaw_angle < 148:
                if chin_angle < 128:
                    k = "方圆脸"
                else:
                    k = "方脸"
        elif jaw_cheek_ratio < 0.76 and chin_angle < 120:
            k = "菱形脸"
        elif hw_ratio < 1.38:
            if avg_jaw_angle > 148:
                k = "短圆脸"
            else:
                k = "短方脸"
        elif hw_ratio > 1.55:
            k = "长形脸"

        name, desc = get_text('face', k)
        return (name, desc, detail)

    @staticmethod
    def classify_eyes_geom(shape):
        h_l = FaceClassifier._dist(shape, 37, 41);
        w_l = FaceClassifier._dist(shape, 36, 39)
        ear = h_l / (w_l + 1e-6)
        dy = shape[39][1] - shape[36][1];
        dx = shape[39][0] - shape[36][0]
        angle = np.degrees(np.arctan2(dy, dx))
        detail = f"上扬{angle:.1f}°"

        k = "杏眼"
        if angle < -2.0:
            k = "下垂眼"
        elif ear > 0.33:
            k = "圆眼"
        elif angle > 15.0:
            k = "吊梢眼"  # Mapped to specific logic if needed
        elif angle > 6.0 and ear < 0.30:
            k = "丹凤眼"
        elif ear < 0.25:
            k = "细长眼"

        name, desc = get_text('eyes', k)
        return name, desc, detail

    @staticmethod
    def classify_brow_geom(shape):
        # 提取左眉毛的三个核心关键点：17(眉尾), 19(眉峰), 21(眉头)
        brow_w = FaceClassifier._dist(shape, 17, 21)
        tilt = (shape[17][1] - shape[21][1]) / (brow_w + 1e-6)
        base_y = (shape[17][1] + shape[21][1]) / 2.0
        lift = (base_y - shape[19][1]) / (brow_w + 1e-6)

        k = "柳叶眉"  # 默认基础眉型

        if tilt > 0.15:
            k = "八字眉"
        elif tilt < -0.15 and lift < 0.08:
            k = "剑眉"
        elif lift > 0.19:  # 提高挑眉阈值，防止微小起伏被误判
            k = "欧式挑眉"
        elif lift > 0.11:
            k = "弯月眉"
        elif lift <= 0.08:  # 放宽平眉的判定范围，现实中的平眉也有微小弧度
            k = "一字平眉"

        name, desc = get_text('brow', k)
        return name, desc, ""

    @staticmethod
    def classify_nose_geom(shape):
        ratio = FaceClassifier._dist(shape, 31, 35) / (FaceClassifier._dist(shape, 39, 42) + 1e-6)
        k = "标准直鼻"
        if ratio > 1.15:
            k = "肉肉鼻"
        elif ratio < 0.80:
            k = "希腊鼻"

        name, desc = get_text('nose', k)
        return name, desc, ""

    @staticmethod
    def classify_lip_geom(shape):
        mouth_w = FaceClassifier._dist(shape, 48, 54)
        total_thick = shape[57][1] - shape[51][1]
        fullness = total_thick / (mouth_w + 1e-6)
        corner_y = (shape[48][1] + shape[54][1]) / 2;
        center_y = shape[62][1]

        # Determine primary characteristic
        k = "标准花瓣唇"
        if fullness > 0.35:
            k = "丰满唇"
        elif fullness < 0.15:
            k = "薄唇"

        # Check secondary (override or combine)
        if corner_y < center_y - 2:
            k = "微笑唇"
        elif corner_y > center_y + 3:
            k = "覆舟唇"

        cupid = (shape[50][1] + shape[52][1]) / 2 - shape[51][1]
        if cupid > 2.0: k = "M字唇"

        name, desc = get_text('lip', k)
        return name, desc, ""


# ==============================================================================
# 4. 核心引擎
# ==============================================================================
class BeautyEngine:
    def __init__(self):
        if not os.path.exists(PREDICTOR_PATH) or not os.path.exists(DATA_PKL_PATH): raise FileNotFoundError(
            "❌ 关键文件丢失")
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(PREDICTOR_PATH)
        self.facerec = dlib.face_recognition_model_v1(RECOGNITION_PATH)
        self.dl_analyzer = DeepFeatureAnalyzer()
        with open(DATA_PKL_PATH, "rb") as f: self.db = pickle.load(f)
        self.embeddings = np.array([x['embedding'] for x in self.db])
        self.pca = PCA(n_components=3)
        self.pca_result = self.pca.fit_transform(self.embeddings)

    def process_image(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 1)
        if len(rects) == 0: return None
        rect = max(rects, key=lambda r: r.width() * r.height())
        shape = self.predictor(gray, rect)
        shape_np = face_utils.shape_to_np(shape)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        embedding = np.array(self.facerec.compute_face_descriptor(rgb, shape))

        raw_radar_stats = AdvancedFeatureCalculator.calc_raw_metrics(shape_np)

        analysis = {}

        def analyze(feat, indices, pad, geo_func, geo_getter):
            roi = self._crop_roi(image, shape_np, indices, pad)
            ai_res = self.dl_analyzer.predict(feat, roi)
            geo_data = geo_getter(shape_np)
            if ai_res: return (ai_res[0], ai_res[1], geo_data)
            return geo_func(shape_np)

        def analyze_face():
            geo_res = FaceClassifier.classify_face_geom(shape_np)
            roi = self._crop_roi(image, shape_np, list(range(0, 17)) + list(range(17, 27)), 0.2)
            ai_res = self.dl_analyzer.predict('face', roi)
            if ai_res and '方' in ai_res[0] and '方' in geo_res[0]:
                # Hybrid adjustment logic
                return ("方圆脸 【AI修正】", geo_res[1], geo_res[2])  # Use geo desc as base
            if ai_res: return (ai_res[0], ai_res[1], geo_res[2])
            return geo_res

        def analyze_brow():
            # 1. 绝对的数学几何测算 (基于上一步放宽后的标准)
            geo_res = FaceClassifier.classify_brow_geom(shape_np)

            # 2. 截取双侧完整眉毛送给 AI (修复了你代码里写反的 range(27, 22) Bug！)
            # 17到27涵盖了完整的左右双眉，padding 设为 0.3 避免切到眼睛
            roi = self._crop_roi(image, shape_np, list(range(17, 27)), 0.3)
            ai_res = self.dl_analyzer.predict('brow', roi)

            if ai_res:
                ai_name = ai_res[0]
                geo_name = geo_res[0]

                # 🚨 终极裁决：数学几何一票否决权！
                # 场景A：数学事实是平的/微弯，AI却瞎说是弯月/挑眉 -> 强制纠正！
                if ('平' in geo_name or '柳' in geo_name) and ('月' in ai_name or '挑' in ai_name):
                    return (f"{geo_name} 【算法校准】", geo_res[1], "")

                # 场景B：数学事实有明显起伏，AI却非说是平的 -> 强制纠正！
                if ('月' in geo_name or '挑' in geo_name) and '平' in ai_name:
                    return (f"{geo_name} ", geo_res[1], "")

                # 场景C：如果不冲突，采信AI结果
                return (ai_name, ai_res[1], "")

            return geo_res

        analysis['face'] = analyze_face()
        analysis['eyes'] = analyze('eyes', list(range(36, 42)), 0.6, FaceClassifier.classify_eyes_geom,
                                   FaceClassifier.get_eye_ratios)
        analysis['nose'] = analyze('nose', list(range(27, 36)), 0.3, FaceClassifier.classify_nose_geom,
                                   FaceClassifier.get_nose_ratios)
        analysis['lip'] = analyze('lip', list(range(48, 68)), 0.3, FaceClassifier.classify_lip_geom,
                                  FaceClassifier.get_lip_ratios)
        analysis['brow'] = analyze_brow()
        analysis['skin'] = self._analyze_skin_tone(image, shape_np)
        analysis['prop'] = self._analyze_proportions(shape_np, rect)

        return {
            "rect": rect,
            "shape": shape_np,
            "embedding": embedding,
            "analysis": analysis,
            "stats": raw_radar_stats,
            "raw_img": image
        }

    def _crop_roi(self, image, shape, point_indices, padding=0.2):
        pts = shape[point_indices]
        x, y, w, h = cv2.boundingRect(pts)

        # 🚨 核心修复：防止形变失真！
        # 找到五官的中心点
        center_x = x + w // 2
        center_y = y + h // 2

        # 找出宽和高中较大的那个，作为正方形的基准边长
        side_length = max(w, h)

        # 加上 Padding，确保五官周围有足够的呼吸空间
        padded_side = int(side_length * (1 + padding * 2))

        h_img, w_img = image.shape[:2]

        # 计算真正的正方形裁剪边界（并防止超出图片边缘）
        x1 = max(0, center_x - padded_side // 2)
        y1 = max(0, center_y - padded_side // 2)
        x2 = min(w_img, center_x + padded_side // 2)
        y2 = min(h_img, center_y + padded_side // 2)

        return image[y1:y2, x1:x2]

    def find_matches(self, user_emb):
        dists = np.linalg.norm(self.embeddings - user_emb, axis=1)
        indices = np.argsort(dists)[:3]
        neighbors = []
        for idx in indices:
            star = self.db[idx].copy();
            star['dist'] = dists[idx];
            star['pca'] = self.pca_result[idx]
            star['sim_score'] = max(0, (1.2 - dists[idx]) / 1.2 * 100)
            neighbors.append(star)
        return neighbors

    def find_best_feature_match(self, user_shape, star_stats):
        # Simplified placeholder as per original
        return "eye", 92.0

    def _analyze_skin_tone(self, image, shape):
        # 1. 创建面部取样遮罩 (保持原有多边形，但后续算法会剔除边缘阴影)
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        pts = np.array([shape[2], shape[4], shape[48], shape[31]])
        cv2.fillPoly(mask, [pts], 255)

        # 提取遮罩内的所有像素
        skin_pixels = image[mask == 255]
        if len(skin_pixels) == 0:
            return {"tone": "中性", "level": "二白", "desc": "自然色", "full_desc": "无法识别", "hex": "#e0ac69"}

        # 转换为 LAB 颜色空间 (OpenCV 中形变技巧)
        lab_pixels = cv2.cvtColor(np.uint8([skin_pixels]), cv2.COLOR_BGR2LAB)[0]
        L_channel = lab_pixels[:, 0]
        a_channel = lab_pixels[:, 1]
        b_channel = lab_pixels[:, 2]

        # 🚨 核心黑科技：高光提纯！
        # 拒绝被阴影平均，只取该区域亮度排名前 40% 的像素代表真实肤色
        threshold_L = np.percentile(L_channel, 60)
        bright_mask = L_channel >= threshold_L

        # 防错机制
        if not np.any(bright_mask):
            bright_mask = np.ones_like(L_channel, dtype=bool)

        # 获取提纯后的 LAB 均值
        L = np.mean(L_channel[bright_mask])
        a = np.mean(a_channel[bright_mask])
        b_val = np.mean(b_channel[bright_mask])

        # 获取用于前端展示的提纯 RGB 颜色
        b_rgb, g_rgb, r_rgb = np.mean(skin_pixels[bright_mask], axis=0)

        # 2. 修正反人类的摄影机亮度阈值
        if L > 170:
            level = "一白"
        elif L > 150:
            level = "二白"
        elif L > 130:
            level = "三白"
        else:
            level = "小麦色"

        # 3. 色调判断灵敏度微调
        if b_val > 142:
            tone = "暖黄"
        elif b_val < 135 or a > 138:
            tone = "冷粉"
        else:
            tone = "中性"

        full_key = f"{tone}{level}"
        color_hex = '#%02x%02x%02x' % (int(r_rgb), int(g_rgb), int(b_rgb))

        name, desc = get_text('skin', full_key)

        return {"tone": tone, "level": level, "desc": name, "full_desc": desc, "hex": color_hex}

    def _analyze_proportions(self, shape, rect):
        brow_y = (shape[21][1] + shape[22][1]) / 2;
        nose_y = shape[33][1];
        chin_y = shape[8][1]
        mid_len = nose_y - brow_y;
        hairline_y = max(0, brow_y - mid_len)
        if rect.top() < hairline_y: hairline_y = int((hairline_y + rect.top()) / 2)
        upper = abs(brow_y - hairline_y);
        middle = abs(nose_y - brow_y);
        lower = abs(chin_y - nose_y)
        total = upper + middle + lower + 1e-6
        ratios = [upper / total, middle / total, lower / total]

        key = "三庭比例均衡"
        if ratios[0] > 0.36:
            key = "上庭偏长"
        elif ratios[0] < 0.30:
            key = "上庭偏短"
        elif ratios[1] > 0.36:
            key = "中庭偏长"
        elif ratios[1] < 0.30:
            key = "中庭偏短"
        elif ratios[2] < 0.30:
            key = "下庭偏短"
        elif ratios[2] > 0.36:
            key = "下庭偏长"

        name, desc = get_text('prop', key)
        return {"ratios": ratios, "comments": name, "desc": desc}


def get_local_images_base64(folder_path):
    images = []
    defaults = [f"https://picsum.photos/300/400?random={i}" for i in range(10)]
    if os.path.exists(folder_path):
        files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        for f in files:
            try:
                with open(os.path.join(folder_path, f), "rb") as img_file:
                    images.append(f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode()}")
            except:
                pass
    return (images + defaults)[:7]