import pandas as pd
import os

# ================= 配置路径 =================
file_path = r"/dataset/csv/data.xlsx"
output_root_dir = r"/dataset"


# ===========================================

def create_folders():
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"读取Excel失败: {e}")
        return

    # 提取唯一姓名
    unique_names = df['姓名'].unique()

    # 创建 Source_Images 目录
    base_folder = os.path.join(output_root_dir, "Source_Images")
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)

    count = 0
    for name in unique_names:
        # 清洗文件名
        safe_name = str(name).strip().replace('/', '_').replace('\\', '_').replace(':', '')
        folder_path = os.path.join(base_folder, safe_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            count += 1

    print(f"✅ 文件夹结构就绪！位置: {base_folder}")
    print(f"👉 请往每个文件夹里放入 3-5 张不同角度/光线的正脸图片。")


if __name__ == "__main__":
    create_folders()