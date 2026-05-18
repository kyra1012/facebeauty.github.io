import pandas as pd
import os
import shutil
import ssl
from icrawler.builtin import BingImageCrawler

# ================= 关键修改 1：强行忽略证书报错 =================
ssl._create_default_https_context = ssl._create_unverified_context
# ============================================================

# ================= 配置区域 =================
# 请确保路径正确，如果不正确请修改
excel_path = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset\csv\data.xlsx"
dataset_root = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset"
source_base = os.path.join(dataset_root, "Source_Images")

# 下载数量建议：
# 因为加了严格过滤，搜出来的图会变少但质量变高。
# 建议设为 10-15 张，确保能有 3-5 张完美正脸即可。
DOWNLOAD_NUM = 30
# =====================================================

def auto_download_images_retry():
    # 读取 Excel
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        return

    # 提取名单
    people_list = df[['姓名', '国家/地区']].drop_duplicates(subset=['姓名'])

    print(f"🚀 开始精准下载，目标每人 {DOWNLOAD_NUM} 张高清正脸照...")

    for index, row in people_list.iterrows():
        name = row['姓名']
        country = row['国家/地区']

        # 处理文件夹名
        safe_name = str(name).strip().replace('/', '_').replace('\\', '_').replace(':', '')
        person_folder = os.path.join(source_base, safe_name)

        if not os.path.exists(person_folder):
            os.makedirs(person_folder)

        # === 智能判断逻辑 ===
        existing_files = [f for f in os.listdir(person_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        current_count = len(existing_files)

        # 如果已有足够图片，跳过
        if current_count >= DOWNLOAD_NUM:
            print(f"⏭️ {name} 已有 {current_count} 张，跳过...")
            continue

        print(f"\n🔍 正在搜索: {name} (当前 {current_count} 张)...")

        # ================= 关键修改 2：关键词魔法 =================
        # 解释：
        # "frontal face": 强调正脸
        # "close up": 强调面部特写（非全身）
        # "solo": 强调单人
        # "studio": 影棚摄影（通常背景干净、光线好、五官清晰）
        keyword = f"{name} {country} frontal face close up solo studio shot high quality"

        bing_crawler = BingImageCrawler(
            downloader_threads=4,
            storage={'root_dir': person_folder},
            log_level='ERROR'
        )

        # ================= 关键修改 3：启用 Bing 过滤器 =================
        # filters={'people': 'face'} 是大杀器！
        # 它会告诉 Bing ：“我只要脸部特写”。
        # type='photo' 排除 漫画/素描/GIF。
        bing_crawler.crawl(
            keyword=keyword,
            max_num=DOWNLOAD_NUM,
            filters={'people': 'face', 'type': 'photo'}
        )

    print("\n" + "=" * 30)
    print("✅ 下载完成！请去 Source_Images 文件夹检查。")
    print("   提示：现在的图片应该是以大头照为主，清洗工作量会减少很多。")

if __name__ == "__main__":
    auto_download_images_retry()