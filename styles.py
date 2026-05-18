import streamlit as st
import base64
import os
import textwrap
import data_manager  # 确保引用了 data_manager


# ==============================================================================
# 1. 资源加载辅助函数
# ==============================================================================
def get_img_as_base64(file_path):
    possible_paths = [
        file_path,
        os.path.join("assets", file_path),
        os.path.join(os.path.dirname(__file__), "assets", file_path)
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#ccc" opacity="0.3"/></svg>'''
    return base64.b64encode(svg.encode()).decode()


# ==============================================================================
# 2. 核心 CSS 加载
# ==============================================================================
def load_css():
    raw_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&display=swap');

        /* 全局背景 */
        [data-testid="stAppViewContainer"] {
            background-color: #FFFEF9; 
            background-image: 
                radial-gradient(circle at 20% 20%, rgba(243, 229, 245, 0.4) 0%, transparent 60%),
                radial-gradient(circle at 90% 90%, rgba(255, 235, 238, 0.6) 0%, transparent 50%),
                radial-gradient(circle at 20% 60%, rgba(255, 250, 225, 0.5) 0%, transparent 40%);
            background-attachment: fixed;
        }
        .stApp { background: transparent !important; }
        #MainMenu, header, footer {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}

        .block-container { padding-top: 0px !important; }

        /* 导航栏容器 */
        .top-right-nav-container {
            position: fixed !important; 
            top: 0 !important;
            right: 0 !important;
            left: auto !important;
            z-index: 999999 !important;
            display: flex !important;
            align-items: center;
            justify-content: flex-end;
            padding: 15px 40px 0 0; 
            width: 100%;
            pointer-events: none; 
            background: transparent;
            font-family: 'Plus Jakarta Sans', sans-serif;
            overflow: visible;
            transform: none !important;
            will-change: auto !important;
        }

        .top-right-nav-container > * {
            pointer-events: auto;
        }

        .nav-links-group {
            display: flex;
            gap: 12px; 
            align-items: center;
        }

        .minimal-link {
            text-decoration: none !important;
            color: #000000 !important; 
            font-size: 15px;
            font-weight: 500;
            opacity: 0.6;
            padding: 8px 12px;
            border-radius: 12px; 
            background: transparent !important;
            border: none !important;
            transition: all 0.4s ease;
            box-shadow: none !important;
        }

        .minimal-link:hover {
            opacity: 1;
            font-weight: 600;
            transform: translateY(-2px); 
            box-shadow: none !important;
            background: radial-gradient(
                ellipse 60% 18% at 50% 100%, 
                rgba(160, 190, 180, 0.6) 0%, 
                transparent 80%
            ) !important;
        }

        .minimal-link.active {
            opacity: 1;
            font-weight: 700;
            box-shadow: none !important;
            background: radial-gradient(
                ellipse 60% 18% at 50% 100%, 
                rgba(140, 120, 150, 0.5) 0%, 
                transparent 80%
            ) !important;
        }

        .minimal-link.active::after, .minimal-link::after { display: none !important; }

        /* 大标题位置 */
        .hero-header {
            position: relative; width: 100%; height: 160px;
            display: flex; align-items: center; justify-content: center;
            overflow: hidden; 
            margin-top: -20px; 
            margin-bottom: 10px;
        }
        .bg-text-gradient {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            font-family: 'Playfair Display', serif; font-size: 210px; font-weight: 900;
            font-style: italic; line-height: 1; width: 100%; text-align: center;
            background: linear-gradient(180deg, rgba(180, 160, 210, 0.5) 0%, rgba(255, 255, 255, 0.0) 80%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            z-index: 1; pointer-events: none; user-select: none; letter-spacing: -5px;
        }
        .fg-title {
            position: relative; z-index: 2; font-family: 'Noto Serif SC', serif;
            font-size: 60px; font-weight: 700; letter-spacing: 10px; margin-top: 100px; 
            background: linear-gradient(180deg, rgba(89, 75, 100, 1.0) 20%, rgba(89, 75, 100, 0.6) 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 15px rgba(255,255,255,0.9));
        }

        /* 用户头像与下拉卡片 - 高级质感优化版 */
        .user-menu-details { 
            position: relative; 
            cursor: pointer; 
            margin-left: 12px; 
            z-index: 1000002; /* 确保层级最高 */
        }

        /* 头像按钮优化 */
        .user-avatar-btn {
            list-style: none; 
            width: 36px; height: 36px; /*稍微加大尺寸*/
            border-radius: 50%;
            background: #FFFFFF;
            border: 1px solid rgba(0,0,0,0.06);
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; font-weight: 600; color: #555; 
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .user-avatar-btn:hover { 
            background: #FFFFFF; 
            box-shadow: 0 6px 16px rgba(0,0,0,0.08); 
            transform: translateY(-1px);
            color: #000;
        }
        .user-avatar-btn::-webkit-details-marker { display: none; }

        /* 下拉卡片容器 - 仿 iOS 高级模糊质感 */
        .user-dropdown-card {
            position: absolute; 
            top: 50px; right: 0; 
            width: 220px;
            background: rgba(255, 255, 255, 0.95); /* 高透明度白色 */
            backdrop-filter: blur(20px); /* 强毛玻璃效果 */
            -webkit-backdrop-filter: blur(20px);
            border-radius: 16px;
            box-shadow: 
                0 0 0 1px rgba(0,0,0,0.03), /* 极细内描边 */
                0 20px 50px -10px rgba(0,0,0,0.12), /* 扩散阴影 */
                0 10px 20px -5px rgba(0,0,0,0.04); /* 核心阴影 */
            padding: 12px; 
            display: flex; flex-direction: column; gap: 4px;
            animation: slideInMenu 0.25s cubic-bezier(0.16, 1, 0.3, 1); 
            cursor: default;
            overflow: hidden;
        }

        @keyframes slideInMenu { 
            from { opacity: 0; transform: translateY(-8px) scale(0.98); } 
            to { opacity: 1; transform: translateY(0) scale(1); } 
        }

        /* 用户信息区域 */
        .card-user-info { 
            padding: 8px 12px 16px 12px; 
            border-bottom: 1px solid rgba(0,0,0,0.04); 
            margin-bottom: 6px; 
        }
        .info-label { 
            font-size: 11px; 
            color: #999; 
            letter-spacing: 0.5px; 
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .info-name { 
            font-size: 16px; 
            font-weight: 700; 
            color: #2c2c2c; 
            letter-spacing: -0.3px;
        }

        /* 链接按钮通用样式 - 强制去除蓝色和下划线 */
        .card-action-link {
            text-decoration: none !important; /* 核心：去除下划线 */
            display: flex; align-items: center; gap: 12px;
            padding: 10px 12px; 
            border-radius: 10px; 
            color: #555 !important; /* 核心：去除蓝色，改为深灰 */
            font-size: 14px; 
            font-weight: 500;
            transition: all 0.2s ease;
            background: transparent;
            border: none;
        }

        /* 悬停效果 */
        .card-action-link:hover { 
            background: rgba(0,0,0,0.04); /* 极淡的灰色背景 */
            color: #000 !important; /* 悬停变黑 */
            transform: translateX(4px); /* 微妙的位移 */
        }

        /* 图标微调 */
        .card-action-link .icon { 
            font-size: 16px; 
            width: 20px; 
            text-align: center; 
            filter: grayscale(100%); /* 图标去色，更显高级 */
            opacity: 0.7;
            transition: all 0.2s;
        }
        .card-action-link:hover .icon {
            filter: grayscale(0%); /* 悬停恢复彩色 */
            opacity: 1;
            transform: scale(1.1);
        }

        /* 退出登录特殊样式 */
        .action-logout { 
            margin-top: 4px;
            color: #c9302c !important; /* 保持红色警示 */
            opacity: 0.8;
        }
        .action-logout:hover { 
            background: #FFF5F5; 
            color: #d9534f !important;
            opacity: 1;
        }

        .soft-card {
            background-color: rgba(255, 255, 255, 0.75); border-radius: 24px; padding: 24px; 
            border: 1px solid rgba(255, 255, 255, 0.9);
            box-shadow: 0 10px 40px -10px rgba(235, 220, 230, 0.5); backdrop-filter: blur(25px); 
            margin-bottom: 24px;
        }
        .section-header { font-size: 18px; font-weight: 700; color: #5D4037; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
        .fancy-divider { height: 1px; margin: 30px auto; width: 90%; background: linear-gradient(90deg, transparent, rgba(236, 64, 122, 0.2), transparent); position: relative; }
        .tag-pill { border: 1px solid rgba(255,255,255,0.8); padding: 6px 16px; margin-right: 8px; border-radius: 20px; font-size: 13px; font-weight: 600; }
        .tag-purple { background: #F3E5F5; color: #8E24AA; }
    </style>
    """

    st.markdown(textwrap.dedent(raw_css), unsafe_allow_html=True)

    st.markdown("""
    <script>
    (function() {
        function fixNavbar() {
            const navContainer = document.querySelector('.top-right-nav-container');
            if (navContainer) {
                navContainer.style.position = 'fixed';
                navContainer.style.top = '0';
                navContainer.style.right = '0';
                navContainer.style.zIndex = '999999';
            }
        }
        fixNavbar();
        const observer = new MutationObserver(fixNavbar);
        observer.observe(document.body, { childList: true, subtree: true });
        window.addEventListener('scroll', function() { fixNavbar(); }, { passive: true });
    })();
    </script>
    """, unsafe_allow_html=True)

    st.markdown("""
    <script>
    setTimeout(function() {
        if (window.parent.document.getElementById('scroll-to-top-btn')) return;
        const btn = document.createElement('div');
        btn.id = 'scroll-to-top-btn';
        btn.innerHTML = '⬆';
        Object.assign(btn.style, {
            position: 'fixed', bottom: '40px', right: '40px', width: '45px', height: '45px', borderRadius: '50%',
            background: 'linear-gradient(135deg, #FFF 0%, #F3E5F5 100%)', 
            display: 'flex', justifyContent: 'center', alignItems: 'center', cursor: 'pointer',
            boxShadow: '0 6px 16px rgba(142, 36, 170, 0.15)', zIndex: '9999', color: '#AB47BC',
            fontSize: '20px', border: '1px solid #F8BBD0'
        });
        btn.onclick = () => window.parent.scrollTo({top:0, behavior:'smooth'});
        window.parent.document.body.appendChild(btn);
    }, 1000);
    </script>
    """, unsafe_allow_html=True)


# ==============================================================================
# 3. 核心修复：绘制极简贴边导航栏 + 头像卡片
# ==============================================================================
def draw_navbar():
    # 1. 优先获取 URL 参数
    params = st.query_params
    current_page = params.get("page", "landing")
    sub_view = params.get("sub_view", "")

    # 2. 获取正确的用户 Session
    user_id = st.session_state.get("current_user_id", "guest")

    # 3. 初始化默认值
    display_name = "Guest"
    initial = "G"

    # --- 核心修改：构建 URL 参数后缀，确保点击链接后 ID 不丢失 ---
    uid_suffix = f"&uid={user_id}" if user_id != "guest" else ""

    # 4. 如果不是访客，尝试获取真实数据
    if user_id != "guest":
        try:
            info = data_manager.get_user_info(user_id)
            if info:
                display_name = info.get("name", user_id)
            else:
                display_name = user_id
        except Exception:
            display_name = user_id  # 出错时兜底显示账号

    # 5. 计算首字母（确保不为空）
    if display_name:
        initial = display_name[0].upper()
    else:
        initial = "U"

    # 6. 定义内部函数 get_cls (必须在 draw_navbar 内部以访问 current_page)
    def get_cls(target_page, target_sub=""):
        # 核心修复：如果 URL 中没有明确的 sub_view，直接读取 session_state 中真实的默认状态
        actual_sub_view = sub_view if sub_view else st.session_state.get("nav_radio", "cockpit")

        if target_page == "审美趋势":
            # 只要目标子页面与实际加载的子页面一致，就加上 active 高亮
            if target_sub == actual_sub_view and current_page == "审美趋势":
                return "active"
        elif current_page == target_page and target_sub == "":
            return "active"
        return ""

    # 7. 生成 HTML (注意：所有链接都追加了 {uid_suffix})
    raw_html = f"""
    <div class="top-right-nav-container">

        <div class="nav-links-group">
            <a href="/?page=审美趋势&sub_view=cockpit{uid_suffix}" target="_self" class="minimal-link {get_cls('审美趋势', 'cockpit')}">大屏导览</a>
            <a href="/?page=审美趋势&sub_view=dashboard{uid_suffix}" target="_self" class="minimal-link {get_cls('审美趋势', 'dashboard')}">审美概述</a>
            <a href="/?page=智能分析{uid_suffix}" target="_self" class="minimal-link {get_cls('智能分析')}">智能分析</a>
            <a href="/?page=四季色彩{uid_suffix}" target="_self" class="minimal-link {get_cls('四季色彩')}">四季色彩</a>
            <a href="/?page=美学计划{uid_suffix}" target="_self" class="minimal-link {get_cls('美学计划')}">美学计划</a>
            <a href="/?page=个人档案{uid_suffix}" target="_self" class="minimal-link {get_cls('个人档案')}">个人档案</a>
        </div>

        <details class="user-menu-details">
            <summary class="user-avatar-btn" title="个人中心">
                {initial}
            </summary>

            <div class="user-dropdown-card">
                <div class="card-user-info">
                    <div class="info-label">当前登录账号</div>
                    <div class="info-name">{display_name}</div>
                </div>

                <a href="/?page=个人档案{uid_suffix}" target="_self" class="card-action-link">
                    <span class="icon">✏️</span> 编辑资料
                </a>
                <a href="/?page=个人档案{uid_suffix}" target="_self" class="card-action-link">
                    <span class="icon">🔒</span> 修改密码
                </a>
                <a href="/?action=logout" target="_self" class="card-action-link action-logout">
                    <span class="icon">🚪</span> 退出登录
                </a>
            </div>
        </details>

    </div>
    """
    final_html = " ".join([line.strip() for line in raw_html.splitlines()])
    st.markdown(final_html, unsafe_allow_html=True)


# ==============================================================================
# 4. 标题绘制 (大渐变字)
# ==============================================================================
def draw_header():
    raw_html = """
    <div class="hero-header">
        <div class="bg-text-gradient">Beauty Face</div>
        <div class="fg-title">审美实验室</div>
    </div>
    """
    final_html = " ".join([line.strip() for line in raw_html.splitlines()])
    st.markdown(final_html, unsafe_allow_html=True)


def draw_divider():
    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)