import os
import cv2
import dlib
import logging
from icrawler.builtin import BaiduImageCrawler
from icrawler.downloader import ImageDownloader

# ================= 配置区 =================
BASE_DIR = "deep_learning"
RAW_DIR = os.path.join(BASE_DIR, "raw_images")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_dataset")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# 目标：每个分类收集多少张【有效正脸】
TARGET_VALID_NUM = 50

# 初始化 dlib 正脸检测器
detector = dlib.get_frontal_face_detector()


# ================= 核心组件：带人脸检测的下载器 =================
class FaceValidationDownloader(ImageDownloader):
    """
    自定义下载器：下载后立即检查是否包含正脸，不合格则直接删除。
    """

    def get_filename(self, task, default_ext):
        return super().get_filename(task, default_ext)

    def process(self, task, **kwargs):
        super().process(task, **kwargs)
        file_path = os.path.join(self.storage['root_dir'], self.get_filename(task, self.file_urls[task['file_url']]))

        if os.path.exists(file_path):
            self.validate_image(file_path, task['file_url'])

    def validate_image(self, file_path, url):
        try:
            img = cv2.imread(file_path)
            if img is None: raise Exception("无法读取")

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            rects = detector(gray, 1)  # 1次上采样，检测小脸

            if len(rects) == 0:
                os.remove(file_path)
                print(f"❌ [无脸丢弃] {file_path.split(os.sep)[-1]}")
            elif len(rects) > 1:
                os.remove(file_path)
                print(f"❌ [多脸丢弃] {file_path.split(os.sep)[-1]}")
            else:
                # 检查脸部占比，太小的不要
                face_h = rects[0].bottom() - rects[0].top()
                if face_h < img.shape[0] * 0.15:
                    os.remove(file_path)
                    print(f"❌ [脸太小] {file_path.split(os.sep)[-1]}")
                else:
                    print(f"✅ [有效保留] {file_path.split(os.sep)[-1]}")

        except Exception as e:
            if os.path.exists(file_path): os.remove(file_path)


# ================= 关键词后缀 (强制女性+正脸) =================
GENDER_SUFFIX = " 女生 正脸 高清"

# ================= 🌟 您指定的定制分类表 (TAXONOMY) =================
TAXONOMY = {
    # 1. 脸型 (Face Shape)
    "face_shape": {
        "oval": ["鹅蛋脸", "标准鹅蛋脸"],
        "round": ["圆脸", "娃娃脸女生"],
        "square": ["方脸", "方脸女生"],
        "square_round": ["方圆脸", "大气方圆脸"],
        "diamond": ["棱形脸", "菱形脸", "钻石脸"]
    },

    # 2. 眼型 (Eye Shape)
    "eye_shape": {
        "almond": ["杏眼", "标准杏眼"],
        "peach": ["桃花眼", "眼神迷离"],
        "phoenix": ["丹凤眼", "古典丹凤眼"],
        "downturned": ["下垂眼", "无辜狗狗眼"],
        "round": ["圆眼", "大圆眼"],
        "slender": ["细长眼", "长眼型"],
        "triangular": ["三角眼", "眼皮松弛三角眼"]
    },

    # 3. 眉型 (Eyebrow Shape)
    "eyebrow_shape": {
        "willow": ["柳叶眉", "古典柳叶眉"],
        "flat": ["一字眉", "韩式平眉"],
        "sword": ["剑眉", "英气剑眉"],
        "standard": ["标准眉", "自然眉"],
        "crescent": ["弯月眉", "月牙眉"],
        "european_arch": ["欧式挑眉", "欧美高挑眉"],
        "eight": ["八字眉", "眉头高眉尾低"]
    },

    # 4. 鼻型 (Nose Shape)
    "nose_shape": {
        "snub": ["小翘鼻", "韩式翘鼻"],
        "bulbous": ["蒜头鼻", "圆鼻头"],
        "hawk": ["鹰钩鼻", "鼻尖下勾"],
        "greek": ["希腊鼻", "直鼻"],
        "upturned_pig": ["朝天鼻", "鼻孔外露"]
    },

    # 5. 唇型 (Lip Shape)
    "lip_shape": {
        "smile": ["微笑唇", "嘴角上扬"],
        "m_shaped": ["M唇", "海鸥唇"],
        "petal": ["花瓣唇", "唇珠明显"],
        "thin": ["薄唇", "小嘴"],
        "thick": ["厚唇", "欧美厚唇"]
    }
}


def create_folders():
    """初始化目录结构"""
    for d in [RAW_DIR, PROCESSED_DIR, MODELS_DIR]:
        os.makedirs(d, exist_ok=True)

    for main_cat, sub_cats in TAXONOMY.items():
        for sub_cat in sub_cats.keys():
            os.makedirs(os.path.join(RAW_DIR, main_cat, sub_cat), exist_ok=True)
            os.makedirs(os.path.join(PROCESSED_DIR, main_cat, sub_cat), exist_ok=True)


def auto_download_smart():
    """执行智能下载"""
    # 压制 icrawler 的繁琐日志
    logger = logging.getLogger("icrawler")
    logger.setLevel(logging.ERROR)

    print(f"\n🧠 启动定制采集 | 目标: 每类 {TARGET_VALID_NUM} 张有效正脸")
    print("--------------------------------------------------")

    for main_cat, sub_cats in TAXONOMY.items():
        print(f"\n📂 [{main_cat}] 分类处理中...")
        for sub_cat, keywords in sub_cats.items():
            save_path = os.path.join(RAW_DIR, main_cat, sub_cat)

            # 检查是否已达标
            valid_count = len([f for f in os.listdir(save_path) if f.endswith(('.jpg', '.png', '.jpeg'))])
            if valid_count >= TARGET_VALID_NUM:
                print(f"  ⏭️  [{sub_cat}] 已有 {valid_count} 张，跳过")
                continue

            # 组合搜索词
            search_word = keywords[0] + GENDER_SUFFIX
            print(f"  🔍 正在爬取: {sub_cat} (关键词: {search_word})")

            try:
                crawler = BaiduImageCrawler(
                    downloader_cls=FaceValidationDownloader,  # 注入智能过滤器
                    storage={'root_dir': save_path},
                    downloader_threads=2
                )
                # 爬取数量放宽到 2 倍，因为会删掉很多废片
                crawler.crawl(keyword=search_word, max_num=TARGET_VALID_NUM * 2)
            except Exception as e:
                print(f"  ⚠️ 爬取中断: {e}")


if __name__ == "__main__":
    create_folders()
    print(f"✅ 目录结构已按您的定制列表刷新！")
    print(f"📋 共计 {sum(len(v) for v in TAXONOMY.values())} 个细分分类。")

    user_input = input("\n🚀 是否开始自动爬取数据? (y/n): ")
    if user_input.lower() == 'y':
        auto_download_smart()
        print("\n🎉 所有数据采集完成！请前往 deep_learning/raw_images 验收。")