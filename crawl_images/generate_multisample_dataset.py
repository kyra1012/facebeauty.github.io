import pandas as pd
import os
import shutil

# ================= 配置路径 =================
excel_path = r"/dataset/csv/data.xlsx"
dataset_root = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset"

# 源图片目录
source_base = os.path.join(dataset_root, "Source_Images")
# 最终输出目录
output_base = os.path.join(dataset_root, "Final_dataset_MultiSample")


# ===========================================

def generate_multisample_dataset():
    # 1. 创建输出目录 (如果不存在)
    if not os.path.exists(output_base):
        os.makedirs(output_base)
        print(f"已创建输出目录: {output_base}")

    # 2. 读取 Excel
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"读取Excel失败: {e}")
        return

    total_images_generated = 0
    missing_people = []

    print("🚀 开始执行多样本裂变生成...")

    # 3. 遍历每一行排名数据
    for index, row in df.iterrows():
        year = row['年份']
        rank = row['排名']
        name = row['姓名']
        country = row['国家/地区']

        # 清洗名字以匹配文件夹
        safe_name = str(name).strip().replace('/', '_').replace('\\', '_').replace(':', '')
        safe_country = str(country).strip().replace('/', '_').replace('\\', '_')

        # 找到该人的源文件夹
        person_folder = os.path.join(source_base, safe_name)

        if os.path.exists(person_folder):
            # 获取该文件夹下所有有效的图片文件
            valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
            images = [f for f in os.listdir(person_folder) if f.lower().endswith(valid_extensions)]

            # 如果文件夹里有图
            if images:
                # 遍历文件夹里的每一张图，生成对应的编号文件
                # enumerate(images, 1) 表示从 1 开始计数
                for i, img_name in enumerate(images, 1):
                    src_path = os.path.join(person_folder, img_name)
                    ext = os.path.splitext(img_name)[1]  # 获取后缀，如 .jpg

                    # === 命名格式: 年份_排名_姓名_国家_编号.jpg ===
                    # i:02d 表示补零，例如 1 变成 01, 10 还是 10
                    new_filename = f"{year}_{rank}_{safe_name}_{safe_country}_{i:02d}{ext}"

                    dst_path = os.path.join(output_base, new_filename)

                    # 复制文件
                    shutil.copy2(src_path, dst_path)
                    total_images_generated += 1
            else:
                # 文件夹存在但为空
                missing_people.append(name)
        else:
            # 文件夹不存在
            missing_people.append(name)

    print("-" * 30)
    print(f"✅ 全部完成！")
    print(f"总共生成了 {total_images_generated} 张训练数据图片。")
    print(f"文件保存在: {output_base}")

    if missing_people:
        unique_missing = list(set(missing_people))
        print(f"⚠️  以下 {len(unique_missing)} 个人没有图片数据:")
        print(unique_missing[:10])


if __name__ == "__main__":
    generate_multisample_dataset()