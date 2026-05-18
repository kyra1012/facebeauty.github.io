import streamlit as st
import base64

# ==============================================================================
# 1. 核心 CSS 注入 (全层级绝对锁屏 + 局部滚动防穿透)
# ==============================================================================
COLOR_UI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&family=Noto+Serif+SC:wght@500;700;900&display=swap');

/* ================= 霸道锁屏：全层级彻底禁止页面滚动 ================= */
/* 强制覆盖 Streamlit 的所有潜在滚动父级，直接锁死高度和溢出 */
html, body, .stApp, [data-testid="stAppViewContainer"], .main, [data-testid="stMain"], [data-testid="stMainBlockContainer"], .block-container { 
    overflow: hidden !important; 
    height: 100vh !important; 
    max-height: 100vh !important;
    margin: 0 !important;
}

/* 限定主容器样式 */
[data-testid="stMainBlockContainer"], .block-container { 
    max-width: 1600px !important; 
    padding: 1rem 2rem !important; 
}
header { display: none !important; }

/* 强制隐藏全局可能残留的滚动条，确保页面视觉干净 */
::-webkit-scrollbar { width: 0px !important; height: 0px !important; background: transparent !important; }

/* ================= 手风琴核心容器 ================= */
.accordion-container {
    display: flex;
    justify-content: center;
    width: 100%;
    height: 585px; 
    gap: 15px; 
    margin-top: 30px;
}

.hidden-radio { display: none; }

/* 基础卡片样式 (初始闭合状态：纤细独立书签) */
.accordion-item {
    position: relative;
    flex: 0 0 240px; 
    height: 100%;
    border-radius: 20px;
    background: #ffffff; 
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.04);
    border: 1px solid rgba(0,0,0,0.02);
    transition: all 0.6s cubic-bezier(0.25, 1, 0.3, 1);
    display: flex; 
}
.accordion-item:hover { box-shadow: 0 15px 40px rgba(0,0,0,0.08); transform: translateY(-5px); }

/* ================= 展开态接管 ================= */
#spring:checked ~ .item-spring,
#summer:checked ~ .item-summer,
#autumn:checked ~ .item-autumn,
#winter:checked ~ .item-winter {
    flex: 1 1 850px; 
    max-width: 950px;
    background: linear-gradient(145deg, #ffffff 0%, #fafafa 100%);
    box-shadow: 0 20px 50px rgba(0,0,0,0.08);
    transform: translateY(0);
}

/* ================= 极致压缩态 ================= */
#spring:checked ~ .accordion-item:not(.item-spring),
#summer:checked ~ .accordion-item:not(.item-summer),
#autumn:checked ~ .accordion-item:not(.item-autumn),
#winter:checked ~ .accordion-item:not(.item-winter) {
    flex: 0 0 140px; 
}

/* ================= 卡片封面区 (左侧封面) ================= */
.card-cover {
    width: 240px;
    min-width: 240px;
    height: 100%;
    padding: 20px 15px; 
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    z-index: 2;
    background: #ffffff;
    border-right: 1px solid transparent; 
    transform: translateX(calc((100% - 240px) / 2));
    transition: transform 0.6s cubic-bezier(0.25, 1, 0.3, 1);
}

#spring:checked ~ .item-spring .card-cover,
#summer:checked ~ .item-summer .card-cover,
#autumn:checked ~ .item-autumn .card-cover,
#winter:checked ~ .item-winter .card-cover {
    transform: translateX(0); 
    border-right: 1px dashed rgba(0,0,0,0.08); 
}

/* ================= 封面内部元素 ================= */
.kaiti-text { font-family: 'KaiTi', 'STKaiti', 'BiauKai', 'Noto Serif SC', serif !important; }

.card-cal { 
    position: absolute; 
    top: 25px; 
    left: 50%;
    transform: translateX(-50%); 
    width: 140px; 
    height: 85px; 
    object-fit: contain; 
    object-position: center bottom; 
    z-index: 10; 
    pointer-events: none; 
    transition: all 0.5s; 
}

.item-spring .card-cal {
    transform: translateX(-50%) scale(1.2) !important;
    top: 28px !important;
}

.item-autumn .card-cal {
    transform: translateX(-50%) scale(1.1) !important;
    top: 23px !important;
    left: 52%;
}

.card-arch { 
    width: 160px; 
    height: 280px; 
    margin-top: 66px; 
    border-radius: 100px 100px 0 0; 
    overflow: hidden; 
    background: var(--theme-color); 
    position: relative; 
}
.card-bg { width: 100%; height: 100%; object-fit: cover; transition: transform 0.8s ease; }
.accordion-item:hover .card-bg { transform: scale(1.08); }

.card-text { margin-top: auto; text-align: center; padding-bottom: 5px; display: flex; flex-direction: column; align-items: center; z-index: 10; }
.card-title { font-size: 18px; font-weight: 600; line-height: 1.4; color: #2c2c2c; letter-spacing: 3px; }
.card-stamp { width: 22px; height: 22px; background: #bd3124; color: rgba(255,255,255,0.9); font-size: 12px; display: inline-flex; align-items: center; justify-content: center; margin: 8px 0; border-radius: 4px; opacity: 0.9;}
.card-sub { font-size: 11px; color: #777; line-height: 1.6; width: 85%; }

.card-click-overlay { position: absolute; inset: 0; z-index: 5; cursor: pointer; display: block; }

/* ================= 交互按钮 ================= */
.btn {
    margin-top: 10px; font-size: 12px; font-weight: 700;
    color: var(--theme-color); border: 1px solid var(--theme-color);
    padding: 6px 20px; border-radius: 20px; letter-spacing: 2px;
    transition: all 0.3s; background: #fff; cursor: pointer;
    position: relative; z-index: 10;
}
.accordion-item:hover .btn { background: var(--theme-color); color: #fff; }

.close-btn { display: none; } 
.expand-btn { display: inline-block; }

#spring:checked ~ .item-spring .card-click-overlay,
#summer:checked ~ .item-summer .card-click-overlay,
#autumn:checked ~ .item-autumn .card-click-overlay,
#winter:checked ~ .item-winter .card-click-overlay { display: none; }

#spring:checked ~ .item-spring .expand-btn,
#summer:checked ~ .item-summer .expand-btn,
#autumn:checked ~ .item-autumn .expand-btn,
#winter:checked ~ .item-winter .expand-btn { display: none; }

#spring:checked ~ .item-spring .close-btn,
#summer:checked ~ .item-summer .close-btn,
#autumn:checked ~ .item-autumn .close-btn,
#winter:checked ~ .item-winter .close-btn { display: inline-block; }

/* ================= 详细内容区 (只保留此处滚动，且启用防穿透) ================= */
.card-content {
    flex: 1; min-width: 440px; 
    height: 100%; padding: 25px 35px;
    opacity: 0; 
    overflow-y: auto !important; 
    overflow-x: hidden !important;
    overscroll-behavior: contain !important; /* 终极防穿透：文字划到底绝不牵连页面 */
    transform: translateX(30px); transition: all 0.5s cubic-bezier(0.25, 1, 0.3, 1);
    pointer-events: none;
    box-sizing: border-box;
}

#spring:checked ~ .item-spring .card-content,
#summer:checked ~ .item-summer .card-content,
#autumn:checked ~ .item-autumn .card-content,
#winter:checked ~ .item-winter .card-content {
    opacity: 1; transform: translateX(0); pointer-events: auto; transition-delay: 0.2s;
}

.season-top { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid var(--theme-color); padding-bottom: 15px; margin-bottom: 20px; opacity: 0.8;}
.season-name-box h2 { font-size: 30px; font-weight: 800; color: #0f172a; margin: 0 0 10px 0; font-family: 'Noto Serif SC', serif; }
.season-tags { display: flex; gap: 10px; flex-wrap: wrap;}
.tag { background: color-mix(in srgb, var(--theme-color) 12%, white); color: var(--theme-color); font-size: 12px; font-weight: 800; padding: 5px 12px; border-radius: 20px; border: 1px solid color-mix(in srgb, var(--theme-color) 30%, white);}

.stats-container { width: 240px; display: flex; flex-direction: column; gap: 8px; }
.stat-row { display: flex; align-items: center; justify-content: space-between; font-size: 11px; font-weight: 600; color: #475569; }
.stat-bar-bg { width: 65%; height: 6px; background: #e2e8f0; border-radius: 10px; overflow: hidden; position: relative; }
.stat-bar-fill { height: 100%; border-radius: 10px; position: absolute; left: 0; top: 0; background: var(--theme-color); }
.stat-bar-fill.temp-bar { background: linear-gradient(90deg, #e2e8f0, var(--theme-color)); }

.season-desc { font-size: 14px; color: #475569; line-height: 1.7; font-weight: 500; margin-bottom: 20px; text-align: justify; }

.magazine-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px; }
.grid-item { background: #ffffff; padding: 15px 18px; border-radius: 16px; border: 1px solid rgba(0,0,0,0.04); border-top: 4px solid var(--theme-color); box-shadow: 0 4px 15px rgba(0,0,0,0.02); }
.grid-title { font-size: 14px; font-weight: 800; color: #1e293b; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; padding-bottom: 8px; border-bottom: 1px dashed rgba(0,0,0,0.06); }
.grid-content { font-size: 12.5px; color: #475569; line-height: 1.6; }
.grid-content b { color: #0f172a; }

.palette-section { margin-top: 10px; padding-bottom: 30px;}
.palette-title { font-size: 12px; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 1px; border-left: 3px solid var(--theme-color); padding-left: 8px;}
.swatch-group { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 15px; }
.swatch-card { background: #fff; padding: 8px; border-radius: 14px; width: 95px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.03); transition: all 0.3s; border: 1px solid rgba(0,0,0,0.02); }
.swatch-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); border-color: var(--theme-color); }
.swatch-circle { width: 100%; aspect-ratio: 1/1; border-radius: 10px; margin-bottom: 8px; }
.swatch-name { font-size: 11px; font-weight: 800; color: #1e293b; margin-bottom: 2px; }
.swatch-hex { font-family: monospace; font-size: 9px; color: #94a3b8; }
.avoid-card .swatch-circle { position: relative; opacity: 0.6; filter: grayscale(50%); }
.avoid-card .swatch-circle::after { content: "✕"; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 24px; color: rgba(255,255,255,0.9); font-weight: 900; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }

/* 为内部内容框独立开启并美化滚动条 */
.card-content::-webkit-scrollbar { display: block !important; width: 5px !important; height: 5px !important; }
.card-content::-webkit-scrollbar-track { background: transparent !important; }
.card-content::-webkit-scrollbar-thumb { background: #cbd5e1 !important; border-radius: 10px !important; }
.card-content::-webkit-scrollbar-thumb:hover { background: #94a3b8 !important; }
</style>
"""

# ==============================================================================
# 2. 丰富维度的美学数据库
# ==============================================================================
COLOR_DATA = {
    "Spring": {
        "icon": "🌸", "name": "春季型 (Light Spring)", "keywords": ["明媚", "轻盈", "人间水蜜桃"],
        "stats": {"lightness": "85%", "saturation": "65%", "temp": "暖调 (Warm)"},
        "desc": "春季型人宛如初春的阳光，给人明媚、活泼、轻盈的印象。你的肤色通常带有温暖的象牙色调，眼神明亮。最适合你的颜色是低饱和、高明度的暖色调，宛如甜美可口的马卡龙，能极大提升你的元气感。",
        "celebs": "允儿 (Yoona)、IU、赵露思", "jewelry": "玫瑰金、香槟金、浅色贝母、彩色细珠串",
        "outfit": "轻盈飘逸的材质（如雪纺、细针织、欧根纱）。多穿明亮温暖的浅色系，如同将春天穿在身上。绝佳搭配是同色系的深浅叠穿。",
        "makeup": "追求清透、有呼吸感的光泽水光肌。眼妆适合香槟色、杏橘色打底；腮红大面积扫打蜜桃粉；口红首选水光质地的珊瑚橘、西柚色。棕色眼线比纯黑更灵动。",
        "scent": "清新灵动的<b>花果香调</b>与<b>绿意柑橘调</b>。如同清晨带露水的草坪。<br><br><b>💡 代表意境：</b>祖玛珑蓝风铃、欧珑赤霞橘光、蒂普提克清晨百合。",
        "colors": [
            {"name": "初恋蜜桃", "hex": "#FFD1DC"}, {"name": "半熟奶黄", "hex": "#FFF0D1"},
            {"name": "薄荷海盐", "hex": "#C1E1C1"}, {"name": "婴儿晴蓝", "hex": "#C1D3FE"},
            {"name": "暖柔燕麦", "hex": "#F5E6CC"}, {"name": "浅杏橘黄", "hex": "#FFD8B1"},
            {"name": "樱花柔粉", "hex": "#FFB7B2"}
        ],
        "avoids": [
            {"name": "暗黑灰", "hex": "#2d3748"}, {"name": "荧光紫", "hex": "#d946ef"},
            {"name": "藏青蓝", "hex": "#1a237e"}, {"name": "浑浊土棕", "hex": "#8d6e63"}
        ],
        "formula": "<b>🎨 穿搭灵感：</b>同色系渐变（浅杏+蜜桃粉） / 撞色点缀（薄荷绿+奶黄）"
    },
    "Summer": {
        "icon": "🍉", "name": "夏季型 (Soft Summer)", "keywords": ["清冷", "知性", "清冷白月光"],
        "stats": {"lightness": "70%", "saturation": "35%", "temp": "冷调 (Cool)"},
        "desc": "夏季型人带有一种清冷、柔和、知性的疏离感。你的肤色底色偏冷（偏粉或青），眼神温柔。最适合你的颜色是低饱和、低对比度的冷色调，就像蒙上了一层灰色的高级莫兰迪滤镜。",
        "celebs": "孙艺珍、金泰梨、刘亦菲", "jewelry": "银饰、白金、大小圆润的珍珠、透明水晶",
        "outfit": "垂坠感极佳的面料（如真丝、天丝、亚麻混纺）。莫兰迪色系是你的绝对主场，灰粉、雾霾蓝、薄荷绿能将你的温柔清冷气质发挥到极致。",
        "makeup": "干净的半哑光或微雾面底妆。眼妆采用藕粉色、灰棕色消肿；腮红使用牛奶粉、膨胀紫；口红绝配是玫瑰豆沙色、浆果梅子色。面部C区使用冷调高光。",
        "scent": "自带疏离感的<b>水生调</b>、<b>茶香</b>与<b>清冷木质香</b>。宛如雨后初霁的微风。<br><br><b>💡 代表意境：</b>宝格丽大吉岭茶、爱马仕尼罗河花园、芦丹氏冷水。",
        "colors": [
            {"name": "灰粉玫瑰", "hex": "#E2C2C6"}, {"name": "莫兰迪蓝", "hex": "#BBD0FF"},
            {"name": "烟紫丁香", "hex": "#E8DFF5"}, {"name": "鼠尾草绿", "hex": "#D3E8E1"},
            {"name": "气质浅灰", "hex": "#D1D1D1"}, {"name": "柔灰紫", "hex": "#C8B6E2"},
            {"name": "雾霾冷绿", "hex": "#A7E8BD"}
        ],
        "avoids": [
            {"name": "正橘色", "hex": "#ea580c"}, {"name": "深咖啡", "hex": "#451a03"},
            {"name": "亮明黄", "hex": "#ffb300"}, {"name": "荧光绿", "hex": "#39ff14"}
        ],
        "formula": "<b>🎨 搭配灵感：</b>清冷极简（灰紫+珍珠白） / 高级莫兰迪（雾霾蓝+灰粉）"
    },
    "Autumn": {
        "icon": "🍁", "name": "秋季型 (Deep Autumn)", "keywords": ["浓郁", "醇厚", "复古老钱风"],
        "stats": {"lightness": "40%", "saturation": "75%", "temp": "暖调 (Warm)"},
        "desc": "秋季型人散发着成熟、浓郁、华丽的古典气息。你的肤色通常为温暖的暗黄、小麦色或象牙白，眼神深邃。最适合你的颜色是中低明度、带有醇厚感的暖调大地色，极具复古电影感。",
        "celebs": "Jennie、韩素希、舒淇", "jewelry": "复古做旧金、黄铜、琥珀、玳瑁、木质配饰",
        "outfit": "肌理感强、有重量感的面料（如灯芯绒、粗织毛衣、皮革、丝绒）。军绿、砖红、驼色、芥末黄。极其适合大面积的美式复古（Vintage）撞色搭配。",
        "makeup": "高级无瑕的全哑光丝绒肌，强调面部骨骼感。眼影是大地色、枫叶红棕的天下；使用带修容效果的橘棕色腮红；口红天选之子是砖红色、土橘色、牛血色。",
        "scent": "醇厚微醺的<b>东方木质调</b>与<b>辛辣琥珀调</b>。散发着神秘且沉稳的温暖气息。<br><br><b>💡 代表意境：</b>芦丹氏孤儿怨、爱马仕大地、汤姆福特乌木沉香。",
        "colors": [
            {"name": "焦糖陶土", "hex": "#D4A373"}, {"name": "复古芥黄", "hex": "#E9EDC9"},
            {"name": "橄榄枯叶", "hex": "#CCD5AE"}, {"name": "榛果深棕", "hex": "#B2967D"},
            {"name": "拿铁奶咖", "hex": "#E3D5CA"}, {"name": "枫叶砖红", "hex": "#A0522D"},
            {"name": "浓郁墨绿", "hex": "#4A5D23"}
        ],
        "avoids": [
            {"name": "浅粉蓝", "hex": "#bae6fd"}, {"name": "荧光绿", "hex": "#4ade80"},
            {"name": "芭比粉", "hex": "#ff66cc"}, {"name": "亮橘橙", "hex": "#ff7f50"}
        ],
        "formula": "<b>🎨 搭配灵感：</b>老钱大地色（焦糖+榛果棕） / 浓郁复古（砖红+浓墨绿）"
    },
    "Winter": {
        "icon": "❄️", "name": "冬季型 (Clear Winter)", "keywords": ["冷艳", "锐利", "明艳大女主"],
        "stats": {"lightness": "20%", "saturation": "85%", "temp": "极冷 (Ice Cool)"},
        "desc": "冬季型人拥有冷艳、分明、极具锐度的摩登感，自带“大女主”气场。发色与肤色对比度极高，黑发雪肤。你是唯一能把纯黑纯白以及高饱和纯色穿得极具压倒性美感的季型。",
        "celebs": "Jisoo (智秀)、郑秀晶、倪妮", "jewelry": "高反光银饰、璀璨钻石、铂金、黑曜石",
        "outfit": "硬挺、有光泽、剪裁利落的面料（如高级西装、缎面、漆皮）。极简的黑白灰是你的统治区。偶尔用高饱和宝石色（如宝蓝、正红）点缀，极具都市丽人感。",
        "makeup": "极致白净、对比强烈的高遮瑕净面底妆。眼妆做减法，用冷灰色简单勾勒；重点在于唇妆，正红色、复古红唇、蓝调红完美驾驭。强调野生浓眉与清晰眼线。",
        "scent": "具有穿透力的<b>冷冽醛香</b>与<b>浓郁花香调</b>。气场全开，不可忽视的存在感。<br><br><b>💡 代表意境：</b>香奈儿5号、百瑞德超级雪松、伊夫圣罗兰黑鸦片。",
        "colors": [
            {"name": "勃艮第红", "hex": "#9D0208"}, {"name": "克莱因蓝", "hex": "#03045E"},
            {"name": "祖母绿", "hex": "#2B9348"}, {"name": "黑曜石", "hex": "#212529"},
            {"name": "极地雪白", "hex": "#F8F9FA"}, {"name": "浆果深紫", "hex": "#4A148C"},
            {"name": "冰川冷灰", "hex": "#CFD8DC"}
        ],
        "avoids": [
            {"name": "浑浊土黄", "hex": "#ca8a04"}, {"name": "浅卡其", "hex": "#d6d3d1"},
            {"name": "暖珊瑚色", "hex": "#ff7f50"}, {"name": "荧光橘", "hex": "#ff9900"}
        ],
        "formula": "<b>🎨 搭配灵感：</b>高智感极简（黑曜石+极地白） / 宝石感撞色（克莱因蓝+勃艮第红）"
    }
}


# ==============================================================================
# 3. 卷轴引擎核心逻辑
# ==============================================================================

def get_image_base64(relative_path):
    try:
        with open(relative_path, "rb") as f:
            ext = relative_path.split('.')[-1].lower()
            mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"
            return f"data:{mime_type};base64,{base64.b64encode(f.read()).decode('utf-8')}"
    except Exception:
        return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"


def build_card_content(season_key):
    data = COLOR_DATA[season_key]
    tags_html = "".join([f"<span class='tag'>{t}</span>" for t in data["keywords"]])
    swatches_html = "".join([
        f"<div class='swatch-card'><div class='swatch-circle' style='background-color: {color['hex']};'></div><div class='swatch-name'>{color['name']}</div><div class='swatch-hex'>{color['hex']}</div></div>"
        for color in data["colors"]])
    avoids_html = "".join([
        f"<div class='swatch-card avoid-card'><div class='swatch-circle' style='background-color: {color['hex']};'></div><div class='swatch-name'>{color['name']}</div><div class='swatch-hex'>避雷</div></div>"
        for color in data["avoids"]])

    return f"""
    <div class="season-top">
        <div class="season-name-box">
            <h2>{data['name']}</h2>
            <div class="season-tags">{tags_html}</div>
        </div>
        <div class="stats-container">
            <div class="stat-row"><span>推荐明度 (Lightness)</span><span>{data['stats']['lightness']}</span></div>
            <div class="stat-bar-bg"><div class="stat-bar-fill" style="width: {data['stats']['lightness']};"></div></div>
            <div class="stat-row"><span>色彩饱和 (Saturation)</span><span>{data['stats']['saturation']}</span></div>
            <div class="stat-bar-bg"><div class="stat-bar-fill" style="width: {data['stats']['saturation']};"></div></div>
            <div class="stat-row"><span>色彩冷暖 (Temperature)</span><span>{data['stats']['temp']}</span></div>
            <div class="stat-bar-bg"><div class="stat-bar-fill temp-bar" style="width: 100%;"></div></div>
        </div>
    </div>
    <div class="season-desc">{data['desc']}</div>

    <div class="magazine-grid">
        <div class="grid-item">
            <div class="grid-title">👗 OOTD 穿搭法则</div>
            <div class="grid-content">{data['outfit']}</div>
        </div>
        <div class="grid-item">
            <div class="grid-title">💄 MAKEUP 妆容解析</div>
            <div class="grid-content">{data['makeup']}</div>
        </div>
        <div class="grid-item">
            <div class="grid-title">🌸 SCENT 香氛意境</div>
            <div class="grid-content">{data['scent']}</div>
        </div>
        <div class="grid-item">
            <div class="grid-title">✨ DETAILS 灵感细节</div>
            <div class="grid-content"><b>💍 首饰材质：</b><br>{data['jewelry']}<br><br><b>🌟 代表明星：</b><br>{data['celebs']}</div>
        </div>
    </div>

    <div class="palette-section">
        <div class="palette-title">👍 核心命定色彩 (Best Matches)</div>
        <div class="swatch-group">{swatches_html}</div>

        <div style="background: rgba(255,255,255,0.8); border: 1px dashed var(--theme-color); padding: 12px 18px; border-radius: 12px; font-size: 13px; color: #475569; margin-bottom: 25px; display: inline-block;">
            {data.get('formula', '')}
        </div>

        <div class="palette-title" style="color: #ef4444; border-left-color: #ef4444;">⛔ 绝对避雷色彩 (Colors to Avoid)</div>
        <div class="swatch-group">{avoids_html}</div>
    </div>
    """

def show():
    st.markdown("".join([line.strip() for line in COLOR_UI_CSS.splitlines()]), unsafe_allow_html=True)

    SEASONS_META = {
        "Spring": {"id": "spring", "bg": "assets/views_color/pic/春.jpg", "cal": "assets/views_color/四季书法/春.png",
                   "title": "春風和煦<br>萬物復甦", "subtitle": "春风拂面，不寒不燥。惊蛰时分大地苏醒",
                   "theme": "#e892a3"},
        "Summer": {"id": "summer", "bg": "assets/views_color/pic/夏.jpg", "cal": "assets/views_color/四季书法/夏.png",
                   "title": "夏日炎炎<br>荷香滿池", "subtitle": "夏日烈烈，阳光在绿叶间洒下斑驳光影",
                   "theme": "#3e9680"},
        "Autumn": {"id": "autumn", "bg": "assets/views_color/pic/秋.jpg", "cal": "assets/views_color/四季书法/秋.png",
                   "title": "秋高氣爽<br>碩果累累", "subtitle": "银杏叶铺满了小径，金黄闪烁", "theme": "#cf8d32"},
        "Winter": {"id": "winter", "bg": "assets/views_color/pic/冬.jpg", "cal": "assets/views_color/四季书法/冬.png",
                   "title": "銀裝素裹<br>瑞雪豐年", "subtitle": "漫步在银装素裹的小径，高级感拉满", "theme": "#406a96"}
    }

    radios_html = """
        <input type="radio" name="season_gallery" id="reset_all" class="hidden-radio" checked>
        <input type="radio" name="season_gallery" id="spring" class="hidden-radio">
        <input type="radio" name="season_gallery" id="summer" class="hidden-radio">
        <input type="radio" name="season_gallery" id="autumn" class="hidden-radio">
        <input type="radio" name="season_gallery" id="winter" class="hidden-radio">
    """

    items_html = ""
    for key, meta in SEASONS_META.items():
        bg_b64 = get_image_base64(meta['bg'])
        cal_b64 = get_image_base64(meta['cal'])

        items_html += f"""
        <div class="accordion-item item-{meta['id']}" style="--theme-color: {meta['theme']}">
            <div class="card-cover">
                <label for="{meta['id']}" class="card-click-overlay"></label>

                <img class="card-cal" src="{cal_b64}" alt="Calligraphy">
                <div class="card-arch">
                    <img class="card-bg" src="{bg_b64}" alt="Background">
                </div>
                <div class="card-text">
                    <div class="card-title kaiti-text">{meta['title']}</div>
                    <div class="card-stamp kaiti-text">印</div>
                    <div class="card-sub kaiti-text">{meta['subtitle']}</div>

                    <label for="{meta['id']}" class="btn expand-btn kaiti-text">展开 ➔</label>
                    <label for="reset_all" class="btn close-btn kaiti-text">合上 ➔</label>
                </div>
            </div>
            <div class="card-content">
                {build_card_content(key)}
            </div>
        </div>
        """

    accordion_html = f"<div class='accordion-container'>{radios_html}{items_html}</div>"
    clean_accordion_html = "".join([line.strip() for line in accordion_html.splitlines()])
    st.markdown(clean_accordion_html, unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    show()