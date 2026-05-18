import pandas as pd
import os
import ssl
from icrawler.builtin import BingImageCrawler

# ================= 🔧 关键配置 =================
# 1. 忽略 SSL 报错 (必须加)
ssl._create_default_https_context = ssl._create_unverified_context

# 2. Excel 文件路径
excel_path = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset\csv\data.xlsx"

# 3. 根目录
dataset_root = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset"

# 4. 【新】只存放 Top 10 的文件夹
target_root_folder = os.path.join(dataset_root, "Top10_Source_Images")

# 5. 下载数量 (建议 15-20 张，方便筛选出精品)
DOWNLOAD_NUM = 10


# ==============================================

def download_top10_stars():
    # 1. 读取 Excel
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        return

    # 2. 核心筛选逻辑：只保留排名 <= 10 的行
    print("📊 正在筛选历年 Top 10 名单...")
    top10_df = df[df['排名'] <= 10]

    # 3. 提取姓名和国家，并去重 (同一个人拿了好几年 Top 10，只算一次)
    # subset=['姓名'] 表示只要名字一样就视为同一人
    unique_stars = top10_df[['姓名', '国家/地区']].drop_duplicates(subset=['姓名'])

    print(f"✅ 筛选完成！历年（2016-2025）共有 {len(unique_stars)} 位女星进入过前 10 名。")
    print(f"📂 图片将保存在: {target_root_folder}")
    print("-" * 10)

    # 4. 创建总目录
    if not os.path.exists(target_root_folder):
        os.makedirs(target_root_folder)

    # 5. 开始循环下载
    for index, row in unique_stars.iterrows():
        name = row['姓名']
        country = row['国家/地区']

        # 清洗文件名
        safe_name = str(name).strip().replace('/', '_').replace('\\', '_').replace(':', '')
        person_folder = os.path.join(target_root_folder, safe_name)

        # 创建单人文件夹
        if not os.path.exists(person_folder):
            os.makedirs(person_folder)

        # 检查是否已经下载过
        existing_files = [f for f in os.listdir(person_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        if len(existing_files) >= DOWNLOAD_NUM:
            print(f"⏭️ {name} 文件夹已满 ({len(existing_files)} 张)，跳过...")
            continue

        print(f"🔍 [Top10] 正在搜索: {name} ({country})...")

        keyword = f"{name} {country} "

        # === 启动爬虫 ===
        bing_crawler = BingImageCrawler(
            downloader_threads=4,
            storage={'root_dir': person_folder},
            log_level='ERROR'
        )

        # 启用过滤器：只找“人脸”照片
        bing_crawler.crawl(
            keyword=keyword,
            max_num=DOWNLOAD_NUM,
            filters={'people': 'face', 'type': 'photo'}
        )

    print("\n" + "=" * 30)
    print("🎉 Top 10 明星照片抓取完成！")
    print("👉 下一步建议：")
    print("1. 人工快速扫一眼 Top10_Source_Images 里的图片，删掉明显的错图。")
    print("2. 运行之前的【裁切清洗脚本】，把 source_base 路径改成 'Top10_Source_Images'。")


if __name__ == "__main__":
    download_top10_stars()