import streamlit as st
import base64
import os


# ================= 资源加载函数 =================
def get_card_images():
    """自动扫描 assets/landing_page1/ 下的所有图片"""
    default_colors = ["#1A1A1A", "#9E9E9E", "#FDD835", "#FFFFFF", "#F48FB1", "#66BB6A"]
    images = []

    base_dir = os.path.join("assets", "landing_page1")
    found_files = []

    if os.path.exists(base_dir):
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        files = [f for f in os.listdir(base_dir) if os.path.splitext(f)[1].lower() in valid_exts]
        files.sort()
        found_files = [os.path.join(base_dir, f) for f in files]

    for i in range(6):
        img_data = None
        if i < len(found_files):
            try:
                with open(found_files[i], "rb") as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()
                    ext = os.path.splitext(found_files[i])[1].lower()
                    mime = "image/png" if ext == ".png" else "image/jpeg"
                    img_data = f"data:{mime};base64,{encoded}"
            except Exception:
                pass

        if not img_data:
            color = default_colors[i]
            svg = f"""<svg width="300" height="400" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="{color}"/><text x="50%" y="50%" font-family="sans-serif" font-size="40" fill="#888" text-anchor="middle" dy=".3em">IMG {i + 1}</text></svg>"""
            encoded_svg = base64.b64encode(svg.encode('utf-8')).decode()
            img_data = f"data:image/svg+xml;base64,{encoded_svg}"

        images.append(img_data)
    return images


def show():
    # ================= 0. 路由逻辑 =================
    if st.query_params.get("nav") == "auth":
        st.session_state.current_page = "auth_login"
        st.query_params.clear()
        st.rerun()

        # ================= [核心修复]：动态生成绑定 UID 的跳转链接 =================
    current_uid = st.session_state.get("current_user_id", "guest")
    if current_uid != "guest":
        # 已登录：跳转时死死绑定当前 uid
        link_dashboard = f"?page=审美趋势&sub_view=dashboard&uid={current_uid}"
        link_analysis = f"?page=智能分析&uid={current_uid}"
        link_profile = f"?page=个人档案&uid={current_uid}"
    else:
        # 未登录：点击按钮统统引流去登录页
        link_dashboard = "?nav=auth"
        link_analysis = "?nav=auth"
        link_profile = "?nav=auth"

    # ================= 1. 获取图片 =================
    img_list = get_card_images()
    cards_html = ""
    for idx, img_src in enumerate(img_list):
        cards_html += f'<div class="stack-card"><img src="{img_src}" draggable="false"></div>'

    # ================= 2. 定义样式 (CSS) =================
    # 包含了米杏色背景、磨砂纹理、呼吸动画
    raw_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,600;1,400&family=Montserrat:wght@200;400;500&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Courier+New&display=swap');

/* --- 基础重置 --- */
    .stApp {
        margin: 0; padding: 0;
        background-color: #F9F7F2; /* 全局米杏色背景 */
        font-family: 'Montserrat', sans-serif;
    }
    .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
    header, footer, #MainMenu { display: none !important; }

    /* --- 全屏滚动容器 --- */
    .scroll-container {
        width: 100vw;
        min-height: 100vh;
    }

    /* 📱 针对桌面端保留酷炫的吸附滚动，移动端自动放开以防 iframe 导致白屏 */
    @media (min-width: 768px) {
        .stApp { overflow: hidden !important; }
        .scroll-container {
            height: 100vh;
            overflow-y: scroll;
            scroll-snap-type: y mandatory;
            scroll-behavior: smooth;
        }
    }
    
    /* --- 通用 Section 样式 --- */
    .snap-section {
        height: 100vh; width: 100vw; scroll-snap-align: start;
        position: relative; overflow: hidden; display: flex; flex-direction: column; align-items: center;
        /* 统一添加磨砂质感纹理 */
        background-image: url("https://www.transparenttextures.com/patterns/stardust.png");
        background-color: transparent; 
    }

    .hero-section { justify-content: flex-start; padding-top: 12vh; }
    .features-section { justify-content: center; } 

    /* --- 字体排版 --- */
    .title-serif { font-family: 'Cormorant Garamond', serif; font-weight: 600; color: #633974; }
    .text-sans { font-family: 'Montserrat', sans-serif; font-weight: 300; letter-spacing: 0.05em; }
    .hero-content { text-align: center; position: relative; z-index: 10; } 

    /* --- 品牌头部 --- */
    .brand-header-container {
        display: flex; align-items: center; justify-content: center; gap: 15px;
        margin-bottom: 25px; opacity: 0.9;
    }
    .brand-line { width: 60px; height: 1px; background-color: #C5A595; }
    .brand-star { font-size: 14px; color: #C5A595; }
    .brand-text {
        font-size: 12px; text-transform: uppercase; letter-spacing: 4px; color: #861043;
        font-weight: 600;
    }

    .main-headline {
        font-size: 70px; line-height: 1.1; margin-bottom: 20px;
        background: linear-gradient(135deg, #503B5B 60%, #815A6D 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .sub-headline { font-size: 16px; color: #510424; max-width: 600px; line-height: 1.8; margin: 0 auto 30px auto; }

    /* --- 手绘风格按钮 --- */
    .scribble-button {
        text-decoration: none !important;
        position: relative;
        text-align: center;
        transition: 0.3s ease-in-out;
        cursor: pointer;
        background-color: transparent;
        filter: url(#handDrawnNoise); 
        display: flex; justify-content: center; align-items: center;
        user-select: none;
        font-family: "Courier New", monospace;
        font-size: 1.5rem; font-weight: bold;
        color: #ffd230 !important;
        padding: 0.5em 1em; margin: 0 auto; width: fit-content;
        border-width: 0px; border-radius: 2rem;
        box-shadow: #33333366 4px 4px 0 1px;
        animation: idle 2s infinite ease-in-out;
    }

    .highlight {
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        fill: none; stroke: transparent; stroke-width: 17; 
        stroke-linecap: round; stroke-linejoin: round; pointer-events: none;
        stroke-dasharray: 600; stroke-dashoffset: 600;
        transition: stroke-dashoffset 0.6s ease-in-out, stroke 0.3s;
        mix-blend-mode: multiply;
    }

    @keyframes idle {
        0% { filter: url(#handDrawnNoise); }
        50% { rotate: 1deg; filter: url(#handDrawnNoise2); }
        100% { filter: url(#handDrawnNoise); }
    }

    .scribble-button:hover { color: #F48FB1 !important; transform: rotate(-1.5deg) scale(1.05); }
    .scribble-button:active { color: #8E24AA !important; transform: scale(0.98); filter: url(#handDrawnNoiseActive); }
    .scribble-button:hover .highlight { stroke-dashoffset: 0; stroke: rgba(244, 143, 177, 0.6); }
    .scribble-button:active .highlight { stroke: rgba(142, 36, 170, 0.6); }

    /* --- 底部堆叠卡片 (含呼吸浮动) --- */
    .stack-container {
        position: absolute;
        bottom: -100px;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        height: 500px;
        display: flex;
        justify-content: center;
        align-items: flex-end;
        z-index: 5;
        perspective: 1200px;
        pointer-events: none;
    }

    /* 呼吸动画 */
    @keyframes subtle-float {
        0%, 100% { bottom: 120px; }
        50% { bottom: 135px; }
    }

    .stack-card {
        position: absolute;
        bottom: 120px; /* 初始位置 */
        width: 280px; height: 380px;
        border-radius: 15px;
        background-color: #fff;
        box-shadow: 0 5px 15px rgba(0,0,0,0.15); 
        transition: all 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
        transform-origin: bottom center;
        cursor: pointer;
        overflow: hidden;
        pointer-events: auto;
        border: none;

        /* 应用呼吸动画 */
        animation: subtle-float 6s ease-in-out infinite;
    }

    /* 动画延迟 */
    .stack-card:nth-child(1) { animation-delay: 0s; }
    .stack-card:nth-child(2) { animation-delay: 1.2s; }
    .stack-card:nth-child(3) { animation-delay: 2.4s; }
    .stack-card:nth-child(4) { animation-delay: 0.8s; }
    .stack-card:nth-child(5) { animation-delay: 2.0s; }
    .stack-card:nth-child(6) { animation-delay: 3.2s; }

    .stack-card img { width: 100%; height: 100%; object-fit: cover; pointer-events: none; }

    /* 扇形布局 */
    .stack-card:nth-child(1) { transform: translateX(-300px) translateY(80px) rotate(-20deg); z-index: 1; }
    .stack-card:nth-child(2) { transform: translateX(-180px) translateY(50px) rotate(-12deg); z-index: 2; }
    .stack-card:nth-child(3) { transform: translateX(-60px) translateY(20px) rotate(-4deg); z-index: 3; }
    .stack-card:nth-child(4) { transform: translateX(60px) translateY(20px) rotate(4deg); z-index: 4; }
    .stack-card:nth-child(5) { transform: translateX(180px) translateY(50px) rotate(12deg); z-index: 3; }
    .stack-card:nth-child(6) { transform: translateX(300px) translateY(80px) rotate(20deg); z-index: 2; }

    /* 悬停交互 */
    .stack-card:hover {
        z-index: 999 !important;
        box-shadow: 0 30px 50px rgba(0,0,0,0.4); 
        border: none;
        animation-play-state: paused;
    }

    .stack-card:nth-child(1):hover { transform: translateX(-300px)  rotate(0deg) scale(1.08); }
    .stack-card:nth-child(2):hover { transform: translateX(-180px)  rotate(0deg) scale(1.08); }
    .stack-card:nth-child(3):hover { transform: translateX(-60px)  rotate(0deg) scale(1.08); }
    .stack-card:nth-child(4):hover { transform: translateX(60px)  rotate(0deg) scale(1.08); }
    .stack-card:nth-child(5):hover { transform: translateX(180px)  rotate(0deg) scale(1.08); }
    .stack-card:nth-child(6):hover { transform: translateX(300px)  rotate(0deg) scale(1.08); }

    /* --- Page 2 Grid --- */
    /* =========================================================================
       ▼▼▼ Page 2 终极修正：4列布局 + 回归高级质感 (图标/数字/中文) ▼▼▼
       ========================================================================= */
    /* 1. 动画定义 */
    @keyframes scrollReveal {
        from { opacity: 0; transform: translateY(60px) scale(0.98); filter: blur(8px); }
        to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
    }

    .animate-on-scroll {
        opacity: 0;
        animation: scrollReveal 1s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
        animation-timeline: view();
        animation-range: entry 5% cover 30%;
    }

    /* 2. Header 容器 (整体下移，修复遮挡) */
    .header-stack-container {
        display: grid; place-items: center; width: 100%; 
        height: 320px; /* 增加高度 */
        position: relative; 
        margin-top: 60px; /* 核心修复：增加顶部外边距，整体下移 */
        margin-bottom: 20px;
    }

    .bg-text-gradient {
        grid-area: 1 / 1;
        font-family: 'Playfair Display', serif; 
        font-size: 200px; 
        font-weight: 900; 
        font-style: italic;
        line-height: 1; 
        white-space: nowrap;
        /* 渐变优化 */
        background: linear-gradient(180deg, rgba(180, 160, 210, 0.8) 0%, rgba(255, 255, 255, 0.0) 80%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        z-index: 1; pointer-events: none; user-select: none; 
        padding-bottom: 20px;
    }

    .fg-title {
        grid-area: 1 / 1; z-index: 2; 
        margin-top: 120px; /* 增加间距，让两行字错开 */
        font-family: 'Noto Serif SC', serif; font-size: 60px; font-weight: 700; letter-spacing: 12px;
        background: linear-gradient(180deg, #594B64 60%, #8E7D96 70%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 5px 15px rgba(255,255,255,0.9));
    }

    /* 3. Slogan 区域 */
    .slogan-container {
        text-align: center; max-width: 900px; margin: 0 auto 50px auto;
        position: relative; z-index: 5; padding: 0 20px;
    }
    .slogan-main {
        font-family: 'Noto Serif SC', serif; font-size: 26px; font-weight: 600; color: #510424;
        margin-bottom: 16px; line-height: 1.4;
    }
    .slogan-sub {
        font-family: 'Montserrat', sans-serif; font-size: 13px; color: #674656;
        line-height: 1.8; font-weight: 400; opacity: 0.9;
    }
    
    /* 4. 四卡片布局 (4列并排) */
    .feature-grid {
        display: grid; 
        grid-template-columns: repeat(4, 1fr); 
        gap: 20px;
        width: 92%; max-width: 1450px; /* 稍微加宽以容纳4列 */
        padding: 10px 10px;
        position: relative; z-index: 10;
    }

    /* 白瓷卡片 (找回高级质感) */
    .porcelain-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 1.0);
        border-radius: 20px;
        padding: 30px 24px;
        position: relative; overflow: hidden;
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 15px 30px -10px rgba(168, 164, 175, 0.15), inset 0 0 20px rgba(255,255,255,0.8);
        display: flex; flex-direction: column; justify-content: space-between;
        min-height: 400px; /* 增加高度以容纳图标和中文 */
    }

    .porcelain-card:hover {
        transform: translateY(-8px); background: #FFFFFF;
        box-shadow: 0 25px 50px -12px rgba(93, 64, 55, 0.15), 0 0 0 1px rgba(109, 82, 118, 0.2); /* 紫色微光描边 */
    }

    /* 装饰元素：背景大数字 (找回) */
    .bg-number {
        position: absolute; top: -15px; right: 0px;
        font-family: 'Playfair Display', serif; font-size: 100px; 
        font-style: italic; color: rgba(93, 64, 55, 0.03); 
        pointer-events: none; transition: 0.5s; z-index: 0;
    }
    .porcelain-card:hover .bg-number { color: rgba(109, 82, 118, 0.08); transform: translateX(-5px) scale(1.05); }

    /* 内容层 */
    .content-layer { position: relative; z-index: 2; }

    /* 图标盒子 (找回) */
    .icon-box {
        width: 42px; height: 42px; border-radius: 10px;
        background: #FDFCF9; border: 1px solid #FFF;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        display: flex; align-items: center; justify-content: center;
        font-size: 18px; color: #6D4C41; margin-bottom: 20px; transition: 0.4s;
    }
    .porcelain-card:hover .icon-box { background: #6D5276; color: #FFF; transform: rotate(10deg); }

    /* 标题样式 (适配中文) */
    .card-h { 
        font-family: 'Noto Serif SC', serif; /* 中文衬线体 */
        font-size: 28px; font-weight: 700; color: #4D0C2C; 
        margin-bottom: 8px; line-height: 1.4; 
    }
    
    .card-sub { 
        font-family: 'Montserrat', sans-serif; font-size: 16px; font-weight: 500; 
        color: #956F82; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; display: block;
    }

    .card-p { font-family: 'Noto Serif SC', serif; font-size: 18px; color: #674656; line-height: 1.8; text-align: justify; opacity: 0.9; }

    /* 底部链接按钮 (修复颜色逻辑) */
    .action-link {
        margin-top: 20px; padding-top: 15px;
        border-top: 1px solid rgba(0,0,0,0.05);
        display: flex; align-items: center; justify-content: space-between;
        font-family: 'Noto Serif SC', serif; font-size: 17px; font-weight: 600; 
        color: #9086A7 !important; /* 静态：与正文/Slogan呼应的深褐色 */
        text-decoration: none !important;
        transition: 0.3s; cursor: pointer;
    }
    .arrow { transition: 0.3s; opacity: 0; transform: translateX(-10px); color: #6D5276; }
    
    /* 悬停效果：变为品牌紫色，箭头浮现 */
    .porcelain-card:hover .action-link { color: #5F3F69 !important; border-color: rgba(109, 82, 118, 0.2); }
    .porcelain-card:hover .arrow { opacity: 1; transform: translateX(0); }
    </style>
    """

    # ================= 3. 定义 HTML 结构 =================
    raw_html = f"""
    <div class="scroll-container">
        <svg style="display: none;">
            <defs>
                <filter id="handDrawnNoise"><feTurbulence type="fractalNoise" baseFrequency="1.5" numOctaves="3" result="noise"/><feDisplacementMap in="SourceGraphic" in2="noise" scale="3" /></filter>
                <filter id="handDrawnNoiseActive"><feTurbulence type="fractalNoise" baseFrequency="2.5" numOctaves="4" result="noise"/><feDisplacementMap in="SourceGraphic" in2="noise" scale="2" /></filter>
            </defs>
        </svg>

        <div class="snap-section hero-section">
            <div class="hero-content">
                <div class="brand-header-container">
                    <div class="brand-line"></div>
                    <div class="brand-star">✦</div>
                    <div class="brand-text">FACE BEAUTY AESTHETIC LAB</div>
                    <div class="brand-star">✦</div>
                    <div class="brand-line"></div>
                </div>

                <h1 class="main-headline title-serif">Find Your True Beauty</h1>
                <p class="sub-headline text-sans">
                    审美实验室 · 发掘原生美学<br>
                    结合全球百大面孔数据与 AI 深度视觉分析，<br>为您定制专属的审美趋势报告与风格建议。
                </p>

                <div style="display: flex; justify-content: center; position: relative; left: -20px; margin-top: 20px;">
                    <a class="scribble-button" href="?nav=auth" target="_self">
                        EXPLORE NOW
                        <svg class="highlight" viewBox="0 -10 220 80" preserveAspectRatio="none">
                            <path d="M5,30 Q15,-5 30,30 Q42,65 55,30 Q70,0 82,30 Q95,60 110,30 Q122,-5 135,30 Q150,65 162,30 Q175,0 190,30 Q202,60 215,30" />
                        </svg>
                    </a>
                </div>
            </div>

            <div class="stack-container">
                {cards_html}
            </div>
        </div>

        <div class="snap-section features-section">
            
            <div class="header-stack-container">
                <div class="bg-text-gradient animate-on-scroll">Beauty Face</div>
                <div class="fg-title animate-on-scroll">审美实验室</div>
            </div>

            <div class="slogan-container animate-on-scroll" style="animation-delay: 0.2s;">
                <div class="slogan-main">
                    量颜定造，让我们不再凭感觉变美。<br>
                    面孔解码，发现每个人的独特亮点。
                </div>
                <div class="slogan-sub">
                    告别“我觉得我适合…”的猜测时代。FaceTrend系统将你的面容转化为可分析、可比较、可预测的数据模型，<br>
                    让每一次形象决策，都有全球审美数据库和深度学习算法作为依据。
                </div>
            </div>

            <div class="feature-grid">
                
                <div class="porcelain-card animate-on-scroll" style="animation-delay: 0.3s;">
                    <div class="bg-number">01</div>
                    <div class="content-layer">
                        <div class="icon-box">◈</div>
                        <div class="card-h">全球审美趋势情报局</div>
                        <div class="card-sub">定位你的审美坐标</div>
                        <div class="card-p">
                            收录近十年 TC Candler 全球百大最美面孔数据。通过沉浸式交互图表，洞察东西方审美文化的流动与变迁。
                        </div>
                    </div>
                    <a class="action-link" href="?nav=auth" target="_self">
                        <span>立即探索趋势</span>
                        <span class="arrow">→</span>
                    </a>
                </div>

                <div class="porcelain-card animate-on-scroll" style="animation-delay: 0.4s;">
                    <div class="bg-number">02</div>
                    <div class="content-layer">
                        <div class="icon-box">✦</div>
                        <div class="card-h">智能美学分析</div>
                        <div class="card-sub">解密你的面部密码</div>
                        <div class="card-p">
                            运用计算机视觉技术，精准量化五官比例与脸型特征。打破主观界限，用数据读懂您的原生骨相美。
                        </div>
                    </div>
                    <a class="action-link" href="?nav=auth" target="_self">
                        <span>开始面部诊断</span>
                        <span class="arrow">→</span>
                    </a>
                </div>

                <div class="porcelain-card animate-on-scroll" style="animation-delay: 0.5s;">
                    <div class="bg-number">03</div>
                    <div class="content-layer">
                        <div class="icon-box">✿</div>
                        <div class="card-h">个性化形象顾问</div>
                        <div class="card-sub">定制你的专属方案</div>
                        <div class="card-p">
                            基于你的独家面部数据，生成可执行的变美方案，获取专属于你独特面部特征的妆容与风格定制建议。
                        </div>
                    </div>
                    <a class="action-link" href="?nav=auth" target="_self">
                        <span>生成我的方案</span>
                        <span class="arrow">→</span>
                    </a>
                </div>

                <div class="porcelain-card animate-on-scroll" style="animation-delay: 0.6s;">
                    <div class="bg-number">04</div>
                    <div class="content-layer">
                        <div class="icon-box">★</div>
                        <div class="card-h">用户成长档案</div>
                        <div class="card-sub">见证你的美丽历程</div>
                        <div class="card-p">
                            建立您的专属审美数据库。每一次分析，都会被收录进您的私人美学时间轴。让你的美，成为一种可测量的成长历程。
                        </div>
                    </div>
                    <a class="action-link" href="?nav=auth" target="_self">
                        <span>查看我的档案</span>
                        <span class="arrow">→</span>
                    </a>
                </div>

            </div>

            <div class="animate-on-scroll" style="position: absolute; bottom: 30px; font-size: 10px; letter-spacing: 2px; opacity: 0.4;">
                SCROLL TO EXPLORE · DESIGNED FOR AESTHETICS
            </div>
        </div>
    </div>
    """

    # ================= 4. 关键修正：压缩字符串 =================
    # 将多行字符串合并为一行，彻底消除缩进造成的影响
    # 这样 Streamlit 接收到的是一整段没有换行的 HTML，绝对不会被当作 Markdown 代码块
    final_content = " ".join([line.strip() for line in (raw_css + raw_html).splitlines()])

    # 渲染
    st.markdown(final_content, unsafe_allow_html=True)
