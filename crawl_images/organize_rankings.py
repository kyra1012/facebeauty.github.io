import pandas as pd
import os
import shutil

# ================= 🔧 配置区域 =================
# 1. Excel 文件路径
excel_path = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset\csv\data.xlsx"

# 2. 数据集根目录
dataset_root = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset"

# 3. 图片源目录 (之前的 Top 10 明星素材库)
source_base = os.path.join(dataset_root, "Top10_Source_Images")

# 4. 历年 Top10 文件夹的存放位置 (我会把它们统一放在一个 "Yearly_Rankings" 总目录下，保持整洁)
yearly_output_root = os.path.join(dataset_root, "Yearly_Top10_face")

# 5. 十年 Top1 冠军文件夹存放位置
top1_output_folder = os.path.join(dataset_root, "Decade_Champions")


# ==============================================

def organize_rankings():
    # 1. 读取数据
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        return

    # 2. 筛选前 10 名的数据
    top10_df = df[df['排名'] <= 10]

    # 计数器
    count_yearly = 0
    count_champions = 0
    missing_list = []

    print("🚀 开始整理归档照片...")

    for index, row in top10_df.iterrows():
        year = row['年份']
        rank = row['排名']
        name = row['姓名']
        country = row['国家/地区']

        # 清洗文件名，找到源文件夹
        safe_name = str(name).strip().replace('/', '_').replace('\\', '_').replace(':', '')
        safe_country = str(country).strip().replace('/', '_').replace('\\', '_')

        person_source_dir = os.path.join(source_base, safe_name)

        # 检查源文件夹是否存在
        if not os.path.exists(person_source_dir):
            missing_list.append(f"{year}年第{rank}名: {name} (文件夹缺失)")
            continue

        # 获取源文件夹里的第一张图 (通常是最好的)
        valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
        images = [f for f in os.listdir(person_source_dir) if f.lower().endswith(valid_exts)]

        if not images:
            missing_list.append(f"{year}年第{rank}名: {name} (文件夹为空)")
            continue

        # 这里的 images[0] 就是我们要取的那张照片
        # 如果您在这个文件夹里存了多张，这里默认只拿第一张去做展示
        src_img_name = images[0]
        src_img_path = os.path.join(person_source_dir, src_img_name)
        ext = os.path.splitext(src_img_name)[1]

        # ================= 任务 A: 分发到 20xxTop10 文件夹 =================
        # 目标文件夹名: 2016Top10, 2017Top10 ...
        year_folder_name = f"{year}Top10"
        year_folder_path = os.path.join(yearly_output_root, year_folder_name)

        if not os.path.exists(year_folder_path):
            os.makedirs(year_folder_path)

        # 命名格式: 排名_姓名_国家.jpg
        dest_filename_a = f"{rank}_{safe_name}_{safe_country}{ext}"
        dest_path_a = os.path.join(year_folder_path, dest_filename_a)

        shutil.copy2(src_img_path, dest_path_a)
        count_yearly += 1

        # ================= 任务 B: 分发到 Decade_Champions (Top 1) =================
        if rank == 1:
            if not os.path.exists(top1_output_folder):
                os.makedirs(top1_output_folder)

            # 命名格式: 年份_姓名_国家.jpg
            dest_filename_b = f"{year}_{safe_name}_{safe_country}{ext}"
            dest_path_b = os.path.join(top1_output_folder, dest_filename_b)

            shutil.copy2(src_img_path, dest_path_b)
            count_champions += 1

    print("-" * 30)
    print("✅ 归档完成！")
    print(f"📂 历年 Top10 文件夹已生成在: {yearly_output_root}")
    print(f"   (共分发 {count_yearly} 张照片)")
    print(f"🏆 十年冠军合集已生成在: {top1_output_folder}")
    print(f"   (共分发 {count_champions} 张照片)")

    if missing_list:
        print(f"\n⚠️ 有 {len(missing_list)} 个条目缺失照片:")
        for item in missing_list[:10]:
            print(item)
        print("...请检查 Top10_Source_Images 中是否缺少对应明星的文件夹。")


if __name__ == "__main__":
    organize_rankings()