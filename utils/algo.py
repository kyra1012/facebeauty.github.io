# 举例：真的算法代码
from deepface import DeepFace
def analyze_face(img_path):
    # 这行代码是真的能分析年龄和表情
    obj = DeepFace.analyze(img_path, actions = ['age', 'gender', 'race'])
    return obj