import streamlit as st
import analysis_services as services
from PIL import Image
import cv2
import numpy as np
import time

# ==============================================================================
# 首页专属 CSS (保留完整原始按钮样式 + 强化全屏加载遮罩)
# ==============================================================================
HOME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;600&family=Montserrat:wght@300;400;500;600&display=swap');
.stApp { background-color: #FDFCF9; font-family: 'Montserrat', sans-serif; }
.block-container { padding-top: 1rem; padding-bottom: 5rem; max-width: 95% !important; }

/* ------ 全屏置顶加载遮罩 ------ */
#loading-mask {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background: #FDFCF9; 
    z-index: 9999999 !important;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
}
.spinner {
    width: 60px; height: 60px;
    border: 5px solid #F3E5F5;
    border-top: 5px solid #B39DDB;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}
.loading-text {
    margin-top: 25px;
    font-family: 'Noto Serif SC', serif;
    font-size: 1.5rem; color: #453750; font-weight: 600; letter-spacing: 2px;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

/* ------ 原始按钮样式 (完整保留) ------ */
[data-testid="stFileUploader"] {
    position: relative; z-index: 999 !important; opacity: 0 !important;
    height: 85px !important; min-height: 85px !important;
    margin-bottom: -185px !important; cursor: pointer !important;
}
[data-testid="stFileUploader"] section { height: 100% !important; padding: 0 !important; }

.visual-btn-container {
    position: relative; height: 60px; display: flex; justify-content: center;
    align-items: center; z-index: 1; pointer-events: none; margin-top: -25px;
}
.scribble-button {
    text-decoration: none !important; position: relative; text-align: center;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); background-color: transparent;
    filter: url(#handDrawnNoise); display: flex; justify-content: center; align-items: center;
    user-select: none; font-family: "Courier New", monospace; font-size: 1.5rem;
    font-weight: bold; color: #ffd230 !important; text-shadow: 1px 1px 0px rgba(0,0,0,0.1);
    padding: 0.6em 1.5em; border-width: 0px; border-radius: 2rem;
    box-shadow: #33333366 4px 4px 0 1px; animation: idle 3s infinite ease-in-out; white-space: nowrap;
}
.highlight {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    fill: none; stroke: transparent; stroke-width: 17; stroke-linecap: round; stroke-linejoin: round;
    stroke-dasharray: 600; stroke-dashoffset: 600; transition: stroke-dashoffset 0.6s ease-in-out, stroke 0.3s;
    mix-blend-mode: multiply;
}
div[data-testid="stElementContainer"]:has([data-testid="stFileUploader"]:hover) + div .scribble-button {
    color: #F48FB1 !important; transform: rotate(-1.5deg) scale(1.05);
    text-shadow: 2px 2px 0px rgba(244, 143, 177, 0.2); box-shadow: #33333344 6px 6px 0 1px;
}
div[data-testid="stElementContainer"]:has([data-testid="stFileUploader"]:hover) + div .highlight {
    stroke-dashoffset: 0; stroke: rgba(244, 143, 177, 0.6);
}

/* 画廊与卡片容器基础样式 */
.gallery-container { 
    position: relative; 
    width: 100%; 
    height: 380px; 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    margin-top: -15px; 
    margin-bottom: 15px; 
    perspective: 1200px; 
}
.art-card { 
    position: absolute; 
    width: 220px; 
    height: 320px; 
    border-radius: 26px; 
    background-size: cover; 
    background-position: center; 
    box-shadow: 0 15px 40px rgba(100, 100, 111, 0.1); 
    border: 3px solid rgba(255,255,255,0.95); 
    cursor: pointer;
    /* 关键：使用 transform-origin 确保缩放从中心开始 */
    transform-origin: center center;
}

/* Bento Grid 样式优化 */
.bento-item { 
    background: rgba(255,255,255,0.5); 
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.8); 
    border-radius: 20px; 
    padding: 38px 38px; 
    text-align: left; 
    transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1); 
    height: 100%; 
    box-shadow: 0 4px 20px rgba(0,0,0,0.02);
}
.bento-item:hover { 
    background: rgba(255,255,255,0.95); 
    transform: translateY(-8px); 
    box-shadow: 0 15px 35px rgba(233, 30, 99, 0.08);
    border-color: #F8BBD0;
}
.bento-head { 
    font-family: 'Noto Serif SC', serif; 
    font-weight: 600; 
    font-size: 16px; 
    color: #5D4037; 
    margin-bottom: 15px; 
    display: flex;
    align-items: center;
    gap: 8px;
}
.bento-body { 
    font-size: 13px; 
    color: #78909C; 
    line-height: 1.7; 
    letter-spacing: 0.5px;
    text-align: justify;
}

@keyframes idle { 0% { filter: url(#handDrawnNoise); } 50% { rotate: 1deg; filter: url(#handDrawnNoise2); } 100% { filter: url(#handDrawnNoise); } }
</style>
"""


def show():
    # 注入样式
    st.markdown(HOME_CSS, unsafe_allow_html=True)
    st.markdown(
        """<svg style="display: none;"><defs><filter id="handDrawnNoise"><feTurbulence type="fractalNoise" baseFrequency="1.5" numOctaves="3" result="noise"/><feDisplacementMap in="SourceGraphic" in2="noise" scale="3" /></filter></defs></svg>""",
        unsafe_allow_html=True)

    # 1. 引擎加载
    if 'engine' not in st.session_state:
        with st.spinner("🚀 引擎初始化中..."):
            try:
                st.session_state.engine = services.BeautyEngine()
            except Exception as e:
                st.error(f"引擎故障: {e}");
                st.stop()

    # ==========================================================================
    # 2. 状态控制 (隔离渲染模式)
    # ==========================================================================

    # 检查是否有文件正在分析
    if 'uploaded_file' in st.session_state and not st.session_state.get('analyzed', False):
        # 立即显示全屏遮罩
        st.markdown("""
            <div id="loading-mask">
                <div class="spinner"></div>
                <div class="loading-text">正在分析美学基因，请稍等...</div>
            </div>
        """, unsafe_allow_html=True)

        # 执行算法逻辑
        uploaded = st.session_state.uploaded_file
        img = Image.open(uploaded).convert('RGB')
        img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        user_res = st.session_state.engine.process_image(img_bgr)

        if user_res:
            neighbors = st.session_state.engine.find_matches(user_res['embedding'])
            st.session_state.user_res = user_res
            st.session_state.neighbors = neighbors
            st.session_state.top_star = neighbors[0]
            st.session_state.star_stats = neighbors[0].get('radar_stats', None)

            st.session_state.analyzed = True
            time.sleep(0.5)
            st.rerun()
        else:
            # 失败则清除文件状态防止死循环
            if 'uploaded_file' in st.session_state: del st.session_state.uploaded_file
            st.error("检测不到人脸")
            time.sleep(1);
            st.rerun()

        return  # 强制中断

    # ==========================================================================
    # 3. 正常首页渲染
    # ==========================================================================

    # 标题区
    st.markdown("""
    <div style="text-align:center; padding-top: -50px; margin-bottom: -30px;">
        <h1 style="font-family:'Noto Serif SC', serif; font-size:2.5rem; font-weight:700; color:#453750; margin:0; letter-spacing:-1px;">发现你的美学基因</h1>
        <p style="font-family:'Montserrat', sans-serif; font-size:1rem; color:#B39DDB; letter-spacing:4px; margin-top:10px; text-transform:uppercase;">Discover Your Aesthetic DNA</p>
    </div>""", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # 强化交互感与呼吸感的画廊 (Silky Smooth Interaction)
    # --------------------------------------------------------------------------
    gallery_imgs = services.get_local_images_base64(services.GALLERY_PATH)

    # 布局配置
    card_configs = [
        ("pos-L3", -440, 60, -15, 4, 0, "0s"),
        ("pos-L2", -310, 30, -10, 6, 1, "1.2s"),
        ("pos-L1", -160, 10, -5, 8, 2, "0.5s"),
        ("pos-center", 0, 0, 0, 10, 3, "2.5s"),
        ("pos-R1", 160, 10, 5, 8, 4, "0.8s"),
        ("pos-R2", 310, 30, 10, 6, 5, "1.5s"),
        ("pos-R3", 440, 60, 15, 4, 6, "0.2s"),
    ]

    gallery_css_dynamic = "<style>"

    # 定义更自然的呼吸动画 (使用 margin-top 而非 transform，避免冲突)
    gallery_css_dynamic += """
    @keyframes soft-breathe {
        0%, 100% { margin-top: 0px; }
        50% { margin-top: -15px; } 
    }
    """

    for cls, x, y, rot, z, img_idx, delay in card_configs:
        gallery_css_dynamic += f"""
        .{cls} {{
            z-index: {z};
            background-image: url('{gallery_imgs[img_idx]}');
            /* 1. 静态定位使用 transform */
            transform: translate({x}px, {y}px) rotate({rot}deg);
            /* 2. 动态浮动使用 margin，与 transform 解耦 */
            animation: soft-breathe 6s ease-in-out infinite {delay};
            /* 3. 丝滑过渡配置 */
            transition: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
        }}

        /* 交互态 (Hover State) */
        .{cls}:hover {{
            z-index: 100 !important;
            /* 放大 1.15 倍，覆盖原定位 */
            transform: translate({x}px, {y}px) rotate({rot}deg) scale(1.15);
            /* 添加柔光滤镜和扩散阴影 */
            filter: brightness(1.08);
            box-shadow: 0 30px 60px rgba(0,0,0,0.2), 0 0 0 2px rgba(255,255,255,0.8);
            /* 动画不停止，保持微微的浮动感，更加自然 */
        }}
        """

    gallery_css_dynamic += "</style>"

    st.markdown(gallery_css_dynamic, unsafe_allow_html=True)
    cards_html = "".join([f'<div class="art-card {item[0]}"></div>' for item in card_configs])
    st.markdown(f'<div class="gallery-container">{cards_html}</div>', unsafe_allow_html=True)

    # 按钮区
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        new_file = st.file_uploader("请上传图片", type=['jpg', 'png', 'jpeg'], key="uploader_main", label_visibility="collapsed")
        if new_file:
            st.session_state.uploaded_file = new_file
            st.rerun()

        st.markdown(
            """<div class="visual-btn-container"><div class="scribble-button">上传照片<svg class="highlight" viewBox="0 -10 220 80" preserveAspectRatio="none"><path d="M5,30 Q15,-5 30,30 Q42,65 55,30 Q70,0 82,30 Q95,60 110,30 Q122,-5 135,30 Q150,65 162,30 Q175,0 190,30 Q202,60 215,30" /></svg></div></div><div style="color:#B0BEC5; margin-top:17px; text-align:center; font-size:16px;">请上传正脸无遮挡照片</div>""",
            unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # 功能网格 (Bento) - 文案已大幅润色，更加丰满
    # --------------------------------------------------------------------------
    st.markdown('<div style="height:30px;"></div>', unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown(
            '<div class="bento-item"><div class="bento-head">📐 骨相精密测算</div><div class="bento-body">深度量化三庭五眼黄金比例，解析面部骨骼折叠度与支撑力，揭示骨相美学密码。</div></div>',
            unsafe_allow_html=True)
    with r2:
        st.markdown(
            '<div class="bento-item"><div class="bento-head">🧭 风格气质定位</div><div class="bento-body">多维判别清冷、幼态、港风、古典等八大气质类型，精准定位您的原生美学风格。</div></div>',
            unsafe_allow_html=True)
    with r3:
        st.markdown(
            '<div class="bento-item"><div class="bento-head">✨ 相似明星检索</div><div class="bento-body">依托近十年全球百美名单数据库，寻找与您骨相皮相最契合的美学缪斯。</div></div>',
            unsafe_allow_html=True)

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    r4, r5, r6 = st.columns(3)
    with r4:
        st.markdown(
            '<div class="bento-item"><div class="bento-head">📊 六维美学雷达</div><div class="bento-body">从折叠度、深邃度、留白感等核心维度，生成专属美学雷达图，直观呈现五官优劣势。</div></div>',
            unsafe_allow_html=True)
    with r5:
        st.markdown(
            '<div class="bento-item"><div class="bento-head">💡 五官高光解析</div><div class="bento-body">识别面部最具辨识度的“高光五官”，提供扬长避短的针对性妆容与造型改善建议。</div></div>',
            unsafe_allow_html=True)
    with r6:
        st.markdown(
            '<div class="bento-item"><div class="bento-head">📄 专属分析报告</div><div class="bento-body">一键生成影楼级深度美学分析报告，包含变美策略与风格指导，支持离线打印珍藏。</div></div>',
            unsafe_allow_html=True)