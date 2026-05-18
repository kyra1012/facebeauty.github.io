import cv2
import numpy as np
import pandas as pd
import os
import mediapipe as mp
import math
import requests
import json
from zhipuai import ZhipuAI

# ================= 🔧 配置区域 =================
# 输入和输出的基本路径
base_dir = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset"
csv_input_dir = os.path.join(base_dir, "csv")
image_output_dir = os.path.join(base_dir, "Yearly_AI_ID_Photos")  # 改个名，强调是证件照
summary_csv_path = os.path.join(csv_input_dir, "Yearly_Face_Summaries.csv")  # 总结报告的保存路径

# ✅ 您的 API Key
API_KEY = "5f5b84cb0bfe4c509e79b57830fbe0e7.Fg1hcRftIwFxOhc1"
# =================================================

print("⏳ 系统初始化：启动双流 AI 引擎 (绘图 + 写作)...")
if not os.path.exists(image_output_dir): os.makedirs(image_output_dir)

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

client = ZhipuAI(api_key=API_KEY)

# 用于存储最后生成表格的数据列表
final_summary_data = []

# 关键点映射
KP = {
    'chin': 152, 'forehead': 10, 'left_cheek': 234, 'right_cheek': 454,
    'left_eye_L': 33, 'left_eye_R': 133, 'left_eye_top': 159, 'left_eye_bot': 145,
    'right_eye_L': 362, 'right_eye_R': 263,
    'nose_root': 168, 'nose_tip': 1, 'nose_bot': 2, 'nose_L': 102, 'nose_R': 331,
    'mouth_L': 61, 'mouth_R': 291, 'lip_top': 0, 'lip_bot': 17,
    'brow_center': 9
}


def dist(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def get_raw_face_data(image):
    """提取纯粹几何数据"""
    h, w = image.shape[:2]
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    res = face_mesh.process(rgb)
    if not res.multi_face_landmarks: return None
    lm = res.multi_face_landmarks[0].landmark

    def p(name):
        return lm[idx_map] if isinstance(idx_map := KP[name], int) else idx_map

    face_w = dist(p('left_cheek'), p('right_cheek'))
    face_h = dist(p('forehead'), p('chin'))

    # 1. 脸型长宽比
    ratio_wh = face_h / face_w if face_w > 0 else 0

    # 2. 中下庭比例
    mid_court = dist(p('brow_center'), p('nose_bot'))
    low_court = dist(p('nose_bot'), p('chin'))
    court_ratio = mid_court / low_court if low_court > 0 else 0

    # 3. 眼睛圆度
    eye_w_val = dist(p('left_eye_L'), p('left_eye_R'))
    eye_h_val = dist(p('left_eye_top'), p('left_eye_bot'))
    eye_round = eye_h_val / eye_w_val if eye_w_val > 0 else 0

    # 4. 眼间距占比
    inter_eye = dist(p('left_eye_L'), p('right_eye_L'))
    eye_space_ratio = inter_eye / face_w if face_w > 0 else 0

    # 5. 鼻翼宽度占比 (相对于眼间距)
    nose_w_val = dist(p('nose_L'), p('nose_R'))
    nose_ratio = nose_w_val / inter_eye if inter_eye > 0 else 0

    if ratio_wh == 0 or court_ratio == 0: return None

    return {
        "face_L_W_ratio": ratio_wh,  # 长宽比：>1.35偏长，<1.25偏短圆
        "mid_lower_ratio": court_ratio,  # 中下庭比：>1.05偏成熟，<0.95偏幼态
        "eye_roundness": eye_round,  # 眼睛圆度：>0.35偏圆，<0.28偏细长
        "eye_spacing": eye_space_ratio,  # 眼间距占比：越大越分散
        "nose_width_ratio": nose_ratio  # 鼻翼/眼距比：越大鼻翼越宽
    }


# === AI 功能 1：生成标准证件照指令 (GLM-4) ===
def generate_id_photo_prompt(year, raw_data):
    data_str = json.dumps(raw_data, indent=2)

    # 系统提示词：强制定义输出格式为标准证件照
    system_prompt = """
    You are an expert biometric analyst generating instructions for a passport photo AI.

    CRITICAL OUTPUT CONSTRAINTS (Must obey):
    1. Style: Official Passport/ID Photograph.
    2. Hair: Hair must be completely tied back tightly into a bun, no loose hair framing the face. Ears must be visible.
    3. Lighting: Flat, even studio lighting. NO shadows, NO highlights, NO dramatic aspect.
    4. Angle: Dead center, full frontal view. Neutral expression.
    5. Background: Plain solid grey studio background.

    Your Task:
    Read the provided biometric data averages for a specific year. Translate these numbers into a detailed description of the facial bone structure and features (eyes, nose, face shape) that will be placed within the strict ID photo constraints above. Do NOT describe hair or lighting, only the biological features derived from data.
    """

    user_msg = f"Year Data: {year}\n{data_str}\n\nDescribe the facial features for the ID photo prompt:"

    print(f"  🧠 [AI 1-绘图指令] 正在解析 {year}年 数据并构建证件照需求...")
    try:
        response = client.chat.completions.create(
            model="glm-4", messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        )
        # 拼接最终的强制约束前缀
        full_prompt = "A professional passport photograph. " + response.choices[
            0].message.content + " Hair tightly tied back, full frontal view, flat even lighting, plain background."
        return full_prompt
    except Exception as e:
        print(f"  ❌ 指令生成失败: {e}")
        return None


# === AI 功能 2：生成中文总结报告 (GLM-4) ===
def generate_chinese_summary(year, raw_data):
    data_str = json.dumps(raw_data, indent=2)

    system_prompt = """
    你是一位资深的面部美学分析专家。你的任务是根据提供的年度平均人脸几何数据，写一段专业、精炼的中文总结段落。

    要求：
    1. 语言风格：专业、客观、符合东亚审美分析习惯（使用诸如“骨相”、“皮相”、“中庭”、“眼型”等术语）。
    2. 内容：概括该年度平均脸的最显著特征。重点分析脸型比例（偏长/偏圆）、三庭分布（成熟/幼态）、眉眼间距和鼻翼形态。
    3. 格式：直接输出一段话，不要分点，字数控制在 150字左右。

    数据参考（仅供理解，不要在报告中出现数字）：
    - face_L_W_ratio (长宽比): >1.35长脸, <1.25短脸
    - mid_lower_ratio (中下庭比): >1.05中庭长(成熟), <0.95下庭长/中庭短(幼态)
    - eye_roundness (眼睛圆度): >0.35圆眼, <0.28细长眼
    - eye_spacing (眼间距): 数值大则眼距宽(疏离感)
    """

    user_msg = f"年份：{year}\n数据：\n{data_str}\n\n请生成该年度的平均脸特征总结段落："

    print(f"  📝 [AI 2-总结报告] 正在撰写 {year}年 的中文特征分析...")
    try:
        response = client.chat.completions.create(
            model="glm-4", messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        )
        summary = response.choices[0].message.content.strip()
        print(f"     ✅ 报告生成完毕 (预览): {summary[:30]}...")
        return summary
    except Exception as e:
        print(f"  ❌ 报告生成失败: {e}")
        return "数据分析失败，无法生成报告。"


# === AI 功能 3：执行绘图 (CogView-3) ===
def call_cogview_to_draw_id_photo(year, prompt):
    print(f"  🎨 [AI 3-执行绘图] 正在生成标准证件照...")
    try:
        response = client.images.generations(model="cogview-3-plus", prompt=prompt)
        img_url = response.data[0].url
        save_path = os.path.join(image_output_dir, f"{year}_ID_Face.jpg")
        with open(save_path, 'wb') as f:
            f.write(requests.get(img_url).content)
        print(f"     🎉 证件照已保存: {save_path}")
    except Exception as e:
        print(f"  ❌ 绘图失败: {e}")


def process_year_final(year, excel_file):
    print(f"\n🚀 正在处理 {year}年 全流程...")
    try:
        df = pd.read_excel(excel_file)
    except:
        return

    all_data = []
    # 1. 数据提取 (取样分析)
    if '图片文件名' in df.columns:
        for folder in df['图片文件名'].dropna():
            if os.path.exists(str(folder)):
                files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png'))]
                # 为提高速度，每人取前3张代表作进行分析，样本足够大时结果极其接近全量
                for f in files[:3]:
                    try:
                        img = cv2.imdecode(np.fromfile(os.path.join(folder, f), np.uint8), cv2.IMREAD_COLOR)
                        if img is not None:
                            raw = get_raw_face_data(img)
                            if raw: all_data.append(list(raw.values()))
                    except:
                        pass

    if not all_data:
        print("  ❌ 无有效数据，跳过。")
        summary_text = "本年度数据不足，无法分析。"
    else:
        # 2. 计算平均值
        avg_vals = np.mean(all_data, axis=0)
        final_raw_data = {
            "face_L_W_ratio": float(avg_vals[0]),
            "mid_lower_ratio": float(avg_vals[1]),
            "eye_roundness": float(avg_vals[2]),
            "eye_spacing": float(avg_vals[3]),
            "nose_width_ratio": float(avg_vals[4])
        }
        print(f"  📊 数据指纹已生成 (基于 {len(all_data)} 个样本)")

        # --- 并行流 A：生成图像 ---
        id_prompt = generate_id_photo_prompt(year, final_raw_data)
        if id_prompt:
            call_cogview_to_draw_id_photo(year, id_prompt)

        # --- 并行流 B：生成总结报告 ---
        summary_text = generate_chinese_summary(year, final_raw_data)

    # 3. 将总结数据添加到总列表
    final_summary_data.append({"Year": year, "Summary": summary_text})


if __name__ == "__main__":
    print("=" * 60)
    print("🧬 全自动证件照平均脸生成与数据报告系统启动")
    print(f"📂 图像保存至: {image_output_dir}")
    print(f"📂 报告保存至: {summary_csv_path}")
    print("=" * 60)

    for year in range(2016, 2026):
        excel_path = os.path.join(csv_input_dir, f"{year}_Top100.xlsx")
        if os.path.exists(excel_path):
            process_year_final(year, excel_path)

    # --- 最后一步：保存汇总 CSV ---
    print("\n" + "=" * 60)
    print("正在归档年度总结报告...")
    if final_summary_data:
        summary_df = pd.DataFrame(final_summary_data)
        # 确保按年份排序
        summary_df = summary_df.sort_values(by='Year')
        summary_df.to_csv(summary_csv_path, index=False, encoding='utf-8-sig')  # sig用于解决中文乱码
        print(f"✅✅✅ 全部完成！总结表格已生成: {summary_csv_path}")
        print("请打开表格查看每年的详细特征分析。")
    else:
        print("❌ 未生成任何数据，无法保存表格。")