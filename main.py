import streamlit as st
import sqlite3
import os
import urllib.request  # 用于云端自动下载巨型模型文件

# ================= 1. 核心配置 (必须是第一行执行的代码) =================
st.set_page_config(
    page_title="Beauty Face | 审美实验室",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= [终极优化] 1.5 浏览器伪装+分块流式下载引擎 =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICTOR_PATH = os.path.join(BASE_DIR, "preprocess", "shape_predictor_68_face_landmarks.dat")
RECOGNITION_PATH = os.path.join(BASE_DIR, "preprocess", "dlib_face_recognition_resnet_model_v1.dat")

def download_model_if_missing(local_path, url, model_name):
    if not os.path.exists(local_path):
        # 自动创建 preprocess 文件夹目录
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with st.spinner(f"📥 首次部署启动，正在下载 {model_name} (约100MB)... 请静候1-2分钟。"):
            try:
                # 🔥 核心修复 1：加入浏览器伪装 Headers，彻底击碎 401 Unauthorized 权限屏蔽！
                req = urllib.request.Request(
                    url, 
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                )
                # 🔥 核心修复 2：采用 1MB 分块流式下载，绝不一次性吃满内存，完美防爆！
                with urllib.request.urlopen(req) as response, open(local_path, 'wb') as out_file:
                    while True:
                        chunk = response.read(1024 * 1024)  # 每次仅加载 1MB 进内存
                        if not chunk:
                            break
                        out_file.write(chunk)
            except Exception as e:
                st.error(f"❌ {model_name} 下载失败，请重新部署或刷新。报错原因: {e}")
                st.stop()

# 🔥 核心修复 3：更换为完全公开、无任何权限限制的 GitHub 官方开源大模型直链
LANDMARKS_URL = "https://raw.githubusercontent.com/ageitgey/face_recognition_models/master/face_recognition_models/models/shape_predictor_68_face_landmarks.dat"
RECOGNITION_URL = "https://raw.githubusercontent.com/ageitgey/face_recognition_models/master/face_recognition_models/models/dlib_face_recognition_resnet_model_v1.dat"

# 执行静默检查与下载
download_model_if_missing(PREDICTOR_PATH, LANDMARKS_URL, "人脸68点定位模型")
download_model_if_missing(RECOGNITION_PATH, RECOGNITION_URL, "人脸识别特征模型")

# 引入新模块
import landing_page
import auth_login

# 引入原有模块
import admin_system
import views_analysis
import views_dashboard
import styles
import Control_module
import Map_detail
import List_detail
import Trend_detail
import Top10_detail
import Gallery_detail
import Champions_detail
import views_profile
import views_color
import views_todo

# ================= 2. 状态初始化与自动恢复 =================

# A. 优先处理退出登录指令 (防止自动登录逻辑覆盖退出操作)
if st.query_params.get("action") == "logout":
    st.session_state.current_user_id = 'guest'
    st.session_state.is_logged_in = False
    st.session_state.current_page = "landing"
    st.query_params.clear()  # 清空URL，包括uid
    st.rerun()

# B. 自动恢复登录状态：如果 Session 是空的，但 URL 里有 uid，就自动登回去
if 'current_user_id' not in st.session_state or st.session_state.current_user_id == 'guest':
    url_uid = st.query_params.get("uid")
    if url_uid:
        st.session_state.current_user_id = url_uid
        st.session_state.is_logged_in = True
    else:
        st.session_state.current_user_id = 'guest'
        st.session_state.is_logged_in = False

# ---> [核心修复] C. 强制状态同步：防刷新丢失机制 <---
# 只要当前 Session 里判定为已登录，就强制将 uid 写进 URL 地址栏中。
if st.session_state.get('current_user_id', 'guest') != 'guest':
    st.query_params["uid"] = st.session_state.current_user_id
elif "uid" in st.query_params:
    # 如果当前是 guest 但 URL 里却有残留的 uid，清理掉它
    del st.query_params["uid"]

# D. 初始化其他状态
if 'current_page' not in st.session_state:
    st.session_state.current_page = "landing"

if "nav_radio" not in st.session_state:
    st.session_state.nav_radio = "cockpit"

# ================= 4. 定义导航映射 =================
NAV_MAP = {
    "cockpit": "沉浸指挥舱",
    "dashboard": "首页概览",
    "map": "地图分布",
    "top10_country": "Top10 国家",
    "top10": "Top10 人物",
    "trend": "趋势分析",
    "gallery": "历年图鉴",
    "champions": "冠军殿堂"
}
NAV_KEYS = list(NAV_MAP.keys())


# 辅助：同步 Sidebar 状态到 URL
def sync_sidebar_state():
    if st.session_state.current_page == "审美趋势":
        if st.session_state.nav_radio != st.query_params.get("sub_view"):
            st.query_params["sub_view"] = st.session_state.nav_radio
            st.query_params["page"] = "审美趋势"
            # 保持 uid
            if st.session_state.current_user_id != 'guest':
                st.query_params["uid"] = st.session_state.current_user_id


# ================= 5. 路由参数监听与处理 =================
try:
    query_params = st.query_params
    nav_mode = query_params.get("nav", None)
    nav_target = query_params.get("nav_target", None)

    # page 处理逻辑
    if "page" in query_params:
        target_page = query_params["page"]

        # 仅当 URL 页面与当前 Session 页面不一致时才更新
        if st.session_state.current_page != target_page:
            # 允许的页面白名单
            if target_page in ["审美趋势", "智能分析", "四季色彩", "美学计划", "个人档案", "后台管理", "landing", "auth_login"]:
                st.session_state.current_page = target_page

                # 同步子视图参数
                if target_page == "审美趋势" and "sub_view" in query_params:
                    url_view = query_params["sub_view"]
                    if url_view in NAV_KEYS:
                        st.session_state.nav_radio = url_view

                # ---> [核心修复] 跳转重载前，必须把 uid 绑定在 URL 上 <---
                if st.session_state.get("current_user_id", "guest") != "guest":
                    st.query_params["uid"] = st.session_state.current_user_id

                st.rerun()

    # 外部跳转逻辑
    elif nav_mode == "landing":
        st.session_state.current_page = "landing"
        st.session_state.auth_mode = "login"
        st.query_params.clear()  # 清除参数，防死循环
        st.rerun()

    elif nav_target == "dashboard":
        st.session_state.current_page = "审美趋势"
        st.session_state.nav_radio = "dashboard"

        st.query_params.clear()  # 【关键修复】：彻底清空 nav_target 避免与后续参数冲突

        # 重新赋上目标页面的参数
        st.query_params["page"] = "审美趋势"
        st.query_params["sub_view"] = "dashboard"
        if st.session_state.get("current_user_id", "guest") != 'guest':
            st.query_params["uid"] = st.session_state.current_user_id

        st.rerun()

except Exception as e:
    pass

# ================= 6. 页面渲染分发 =================
# --- 场景 A: 着陆页 ---
if st.session_state.current_page == "landing":
    landing_page.show()

# --- 场景 B: 注册/登录页 ---
elif st.session_state.current_page == "auth_login":
    auth_login.show()

# --- 场景 C: 后台管理页 ---
elif st.session_state.current_page == "后台管理":
    current_uid = st.session_state.get("current_user_id", "guest")
    is_admin = False

    # 1. 安全拦截：动态查询数据库校验真实权限
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, "user_data.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE username=?", (current_uid,))
            row = c.fetchone()
            conn.close()
            # 只要数据库中用户的 role 字段包含 "Admin"，即视为管理员
            if row and "Admin" in row[0]:
                is_admin = True
    except Exception:
        pass

    # 兜底保护：系统级特权账号强制放行
    if current_uid in ["admin27", "admin"]:
        is_admin = True

    if not is_admin:
        st.error(f"⛔ 权限校验失败：账号 [{current_uid}] 并非管理员，无权访问后台系统。")
        st.stop()


    # 3. 渲染后台业务模块 (样式和具体功能全都在 admin_system 里)
    with st.container():
        admin_system.show()

# --- 场景 D: 主系统功能页 ---
else:
    styles.load_css()

    # 渲染导航栏
    styles.draw_navbar()
    styles.draw_header()

    # 具体子页面渲染
    if st.session_state.current_page == "审美趋势":
        with st.sidebar:
            st.markdown("### 📊 视图切换")
            if st.session_state.nav_radio not in NAV_KEYS:
                st.session_state.nav_radio = "cockpit"

            st.radio(
                "选择分析维度:",
                options=NAV_KEYS,
                format_func=lambda x: NAV_MAP[x],
                key="nav_radio",
                on_change=sync_sidebar_state
            )

        sub_view = st.session_state.nav_radio

        if sub_view == "cockpit":
            Control_module.show()
        elif sub_view == "dashboard":
            views_dashboard.show()
        elif sub_view == "map":
            Map_detail.show()
        elif sub_view == "top10_country":
            Top10_detail.show()
        elif sub_view == "top10":
            List_detail.show()
        elif sub_view == "trend":
            Trend_detail.show()
        elif sub_view == "gallery":
            Gallery_detail.show()
        elif sub_view == "champions":
            Champions_detail.show()

    elif st.session_state.current_page == "智能分析":
        views_analysis.show()

    elif st.session_state.current_page == "四季色彩":
        views_color.show()

    elif st.session_state.current_page == "美学计划":
        views_todo.show()

    elif st.session_state.current_page == "个人档案":
        views_profile.show()
