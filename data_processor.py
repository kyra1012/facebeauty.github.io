import pandas as pd
import os
import json
import base64
import glob

# ================= 配置区域 =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "dataset/csv/data.xlsx")

CHAMPION_DIR = os.path.join(BASE_DIR, "dataset", "Decade_Champions")
YEARLY_TOP10_DIR = os.path.join(BASE_DIR, "dataset", "Yearly_Top10_face")

EAST_COUNTRIES = [
    '中国', '中国大陆', '中国台湾', '台湾', '香港', '韩国', '日本', '泰国',
    '越南', '菲律宾', '马来西亚', '新加坡', '印度尼西亚', '印度', '缅甸',
    '蒙古', '老挝', '柬埔寨', '土耳其'
]

CN_TO_EN_COUNTRY = {
    '中国': 'China', '中国台湾': 'Taiwan', '台湾': 'Taiwan', '美国': 'United States',
    '韩国': 'South Korea', '日本': 'Japan', '泰国': 'Thailand', '以色列': 'Israel',
    '澳大利亚': 'Australia', '英国': 'United Kingdom', '法国': 'France', '俄罗斯': 'Russia',
    '巴西': 'Brazil', '加拿大': 'Canada', '德国': 'Germany', '意大利': 'Italy',
    '西班牙': 'Spain', '瑞典': 'Sweden', '荷兰': 'Netherlands', '土耳其': 'Turkey',
    '乌克兰': 'Ukraine', '墨西哥': 'Mexico', '菲律宾': 'Philippines', '越南': 'Vietnam',
    '印度': 'India', '印尼': 'Indonesia', '印度尼西亚': 'Indonesia', '伊朗': 'Iran',
    '古巴': 'Cuba', '索马里': 'Somalia', '肯尼亚': 'Kenya', '埃塞俄比亚': 'Ethiopia',
    '新西兰': 'New Zealand', '丹麦': 'Denmark', '挪威': 'Norway', '波兰': 'Poland'
}


class DataService:
    def __init__(self):
        self.df = self._load_data()
        self.years = sorted(self.df['年份'].unique()) if not self.df.empty else list(range(2016, 2026))

    def _load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                return pd.read_excel(DATA_FILE)
            except:
                pass
        csv_fallback = os.path.join(BASE_DIR, "data.xlsx - Sheet1.csv")
        if os.path.exists(csv_fallback):
            return pd.read_csv(csv_fallback)
        print(f"⚠️ 警告：未找到数据文件: {DATA_FILE}")
        return pd.DataFrame()

    def _normalize_country(self, country_name):
        c = str(country_name).strip()
        if c in ['中国台湾', '台湾', '中国香港', '香港', '中国澳门', '澳门']:
            return '中国'
        return c

    def _get_region(self, country):
        if any(c in str(country) for c in EAST_COUNTRIES): return 'Oriental'
        return 'Western'

    def _find_image_recursive(self, base_folder, name_keyword):
        if not os.path.exists(base_folder): return None
        extensions = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.bmp')
        for ext in extensions:
            pattern = os.path.join(base_folder, f"*{name_keyword}*{ext[1:]}")
            files = glob.glob(pattern)
            if files: return files[0]
        for root, dirs, files in os.walk(base_folder):
            for file in files:
                if name_keyword.lower() in file.lower() and file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    return os.path.join(root, file)
        return "https://via.placeholder.com/300x400?text=No+Image"

    def get_image_base64(self, path):
        if not path or path.startswith("http"): return path
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    data = f.read()
                ext = path.split('.')[-1].lower()
                mime = 'webp' if ext == 'webp' else 'jpeg'
                return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"
            except:
                pass
        return "https://via.placeholder.com/300x400?text=Error"

    def get_country_stats(self):
        if self.df.empty: return pd.DataFrame()
        df_temp = self.df.copy()
        df_temp['国家/地区'] = df_temp['国家/地区'].apply(self._normalize_country)
        stats = df_temp['国家/地区'].value_counts().reset_index()
        stats.columns = ['Country_CN', 'Faces']
        stats['Country_EN'] = stats['Country_CN'].map(CN_TO_EN_COUNTRY).fillna(stats['Country_CN'])
        stats['Rank'] = stats['Faces'].rank(ascending=False, method='min')
        return stats

    def get_top_stars(self):
        """
        【重要更新】明星排行逻辑 v2.0
        排序规则：
        1. Mentions (降序): 上榜次数越多越好
        2. Best_Rank (升序): 最高名次越小越好 (1 > 10)
        3. Avg_Rank (升序): 平均名次越小越好 (发挥越稳定)
        """
        if self.df.empty: return pd.DataFrame()

        # 聚合计算：次数、最高排名、平均排名
        stats = self.df.groupby('姓名').agg(
            Mentions=('年份', 'count'),
            Best_Rank=('排名', 'min'),
            Avg_Rank=('排名', 'mean')
        ).reset_index()

        # 多级排序
        stats = stats.sort_values(
            by=['Mentions', 'Best_Rank', 'Avg_Rank'],
            ascending=[False, True, True]
        ).head(10)

        # 格式化平均排名 (保留1位小数)
        stats['Avg_Rank'] = stats['Avg_Rank'].round(1)

        # 添加一个 Ranking_Index (1-10)，用于前端控制颜色深浅 (1最深, 10最浅)
        stats = stats.reset_index(drop=True)
        stats['Ranking_Index'] = stats.index + 1

        stats = stats.rename(columns={'姓名': 'Star'})
        return stats

    def get_region_ratio(self):
        if self.df.empty: return [0, 0]
        regions = self.df['国家/地区'].apply(self._get_region)
        counts = regions.value_counts()
        return [counts.get('Oriental', 0), counts.get('Western', 0)]

    def get_yearly_trend(self):
        trend_data = {'years': [], 'east': [], 'west': []}
        if self.df.empty: return trend_data
        groups = self.df.groupby('年份')
        for year in self.years:
            if year in groups.groups:
                grp = groups.get_group(year)
                regions = grp['国家/地区'].apply(self._get_region)
                total = len(grp)
                e = len(regions[regions == 'Oriental'])
                trend_data['years'].append(int(year))
                trend_data['east'].append(round(e / total * 100, 1) if total > 0 else 0)
                trend_data['west'].append(round((total - e) / total * 100, 1) if total > 0 else 0)
        return trend_data

    def get_timeline_data(self):
        timeline_db = {}
        if self.df.empty: return "{}"
        for year in self.years:
            top10 = self.df[(self.df['年份'] == year) & (self.df['排名'] <= 10)].sort_values('排名')
            year_folder = os.path.join(YEARLY_TOP10_DIR, f"{year}Top10")
            year_list = []
            for _, row in top10.iterrows():
                img_path = self._find_image_recursive(year_folder, row['姓名'])
                img_b64 = self.get_image_base64(img_path)
                year_list.append({
                    "rank": int(row['排名']),
                    "name": row['姓名'],
                    "country": row['国家/地区'],
                    "img": img_b64
                })
            timeline_db[int(year)] = year_list
        return json.dumps(timeline_db)

    def get_champion_gallery(self):
        slides = []
        for year in sorted(self.years, reverse=True):
            img_path = self._find_image_recursive(CHAMPION_DIR, str(year))
            if not img_path or "placeholder" in img_path:
                champ_row = self.df[(self.df['年份'] == year) & (self.df['排名'] == 1)]
                if not champ_row.empty:
                    champ_name = champ_row.iloc[0]['姓名']
                    img_path = self._find_image_recursive(CHAMPION_DIR, champ_name)
            desc = f"{year} 冠军"
            champ_row = self.df[(self.df['年份'] == year) & (self.df['排名'] == 1)]
            if not champ_row.empty:
                row = champ_row.iloc[0]
                desc = f"{year} 冠军: {row['姓名']} ({row['国家/地区']})"
            if img_path and "placeholder" not in img_path:
                slides.append({"year": year, "img_path": img_path, "desc": desc})
        return slides


data_service = DataService()
