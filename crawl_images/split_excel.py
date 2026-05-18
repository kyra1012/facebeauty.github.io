import pandas as pd
import os

# ================= 🔧 配置区域 =================
# 1. 您的原始 Excel 文件路径
excel_path = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset\csv\data.xlsx"

# 2. 图片源目录 (脚本去这里找人名对应的文件夹)
source_images_dir = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset\Source_Images"

# 3. 拆分后的表格保存目录
output_dir = os.path.dirname(excel_path)


# ==============================================

def update_folder_path_and_split():
    # 1. 读取源表格
    if not os.path.exists(excel_path):
        print(f"❌ 找不到文件: {excel_path}")
        return

    try:
        print(f"📖 正在读取原始数据: {excel_path} ...")
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return

    # 2. 遍历每一行，只填充【文件夹路径】
    print("🔍 正在关联文件夹路径...")

    # 确保有一个列用来存路径
    if '图片文件名' not in df.columns:
        df['图片文件名'] = None

    found_count = 0

    for index, row in df.iterrows():
        name = row['姓名']

        # 清洗名字以匹配文件夹 (跟之前创建文件夹的逻辑保持一致)
        safe_name = str(name).strip().replace('/', '_').replace('\\', '_').replace(':', '')

        # 拼凑出这个人的【文件夹路径】
        person_folder = os.path.join(source_images_dir, safe_name)

        # 检查文件夹是否存在
        if os.path.exists(person_folder):
            # 这里的修改关键点：直接把文件夹路径填进去，而不是具体图片
            df.at[index, '图片文件名'] = person_folder
            found_count += 1
        else:
            # 文件夹不存在
            df.at[index, '图片文件名'] = "未找到文件夹"

    print(f"✅ 路径关联完毕！共关联了 {found_count} 个文件夹。")

    # 3. 按年份拆分并保存
    print("🚀 开始按年份拆分表格...")

    split_count = 0
    # 确保按年份处理 2016-2025
    for year in range(2016, 2026):
        # 筛选年份
        year_df = df[df['年份'] == year].copy()

        if year_df.empty:
            print(f"⚠️ {year} 年没有数据，跳过。")
            continue

        # 按排名排序
        if '排名' in year_df.columns:
            year_df = year_df.sort_values(by='排名')

        # 构建文件名
        filename = f"{year}_Top100.xlsx"
        save_path = os.path.join(output_dir, filename)

        try:
            year_df.to_excel(save_path, index=False)
            print(f"  📄 已生成: {filename} (包含 {len(year_df)} 条数据)")
            split_count += 1
        except Exception as e:
            print(f"  ❌ 保存 {filename} 失败: {e}")

    print("-" * 30)
    print(f"🎉 全部完成！")
    print(f"📂 文件保存在: {output_dir}")
    print("   (现在的表格里，【图片文件名】一列填的都是文件夹的绝对路径了)")


if __name__ == "__main__":
    update_folder_path_and_split()