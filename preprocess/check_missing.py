import pandas as pd
import pickle
import os

# ================= 配置 =================
CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_SCRIPT_DIR)  # 假设脚本在 preprocess 文件夹
# PROJECT_ROOT = CURRENT_SCRIPT_DIR # 如果你在根目录运行，用这行

CSV_PATH = os.path.join(PROJECT_ROOT, "dataset", "csv", "data.xlsx")
PKL_PATH = os.path.join(PROJECT_ROOT, "star_features.pkl")


# ================= 检查逻辑 =================
def check():
    # 1. 读取 Excel 中的所有人名
    if CSV_PATH.endswith('.csv'):
        df = pd.read_csv(CSV_PATH)
    else:
        df = pd.read_excel(CSV_PATH)
    all_names = set(df['姓名'].unique())

    # 2. 读取已生成的 PKL 中的人名
    if not os.path.exists(PKL_PATH):
        print("❌ 特征文件不存在！")
        return

    with open(PKL_PATH, 'rb') as f:
        data = pickle.load(f)

    existing_names = set([item['name'] for item in data])

    # 3. 找出差集
    missing_names = all_names - existing_names

    print(f"\n📊 检查报告：")
    print(f"应有人数: {len(all_names)}")
    print(f"实际人数: {len(existing_names)}")
    print(f"缺失人数: {len(missing_names)}")

    if missing_names:
        print("\n⚠️ 以下明星处理失败：")
        for name in missing_names:
            print(f"  - {name}")
        print(
            "\n💡 建议：请去 dataset/Source_Images 文件夹下找到这几个人，\n手动替换几张清晰的正脸大头照，然后运行补救脚本。")
    else:
        print("🎉 恭喜！数据完整，没有缺失。")


if __name__ == "__main__":
    check()