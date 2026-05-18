import streamlit as st
import sqlite3
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import random
import time
import hashlib
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# ================= 1. 系统核心路径挂载 =================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)


def find_valid_path(rel_paths):
    for p in rel_paths:
        if os.path.exists(p):
            return p
    return None


DB_PATH = find_valid_path([
    os.path.join(CURRENT_DIR, "user_data.db"),
    os.path.join(PARENT_DIR, "user_data.db")
])

STAR_IMAGES_DIR = find_valid_path([
    os.path.join(CURRENT_DIR, "dataset", "Source_Images"),
    os.path.join(PARENT_DIR, "dataset", "Source_Images")
])

HISTORY_DIR = find_valid_path([
    os.path.join(CURRENT_DIR, "assets", "history_imgs"),
    os.path.join(PARENT_DIR, "assets", "history_imgs"),
    os.path.join(PARENT_DIR, "face", "assets", "history_imgs")
])

HISTORY_JSON_PATH = find_valid_path([
    os.path.join(CURRENT_DIR, "assets", "data", "history.json"),
    os.path.join(PARENT_DIR, "assets", "data", "history.json"),
    os.path.join(PARENT_DIR, "face", "assets", "data", "history.json")
])

USERS_PROFILE_JSON_PATH = find_valid_path([
    os.path.join(CURRENT_DIR, "assets", "data", "users_profile.json"),
    os.path.join(PARENT_DIR, "assets", "data", "users_profile.json"),
    os.path.join(PARENT_DIR, "face", "assets", "data", "users_profile.json")
])

AVATARS_DIR = find_valid_path([
    os.path.join(CURRENT_DIR, "assets", "avatars"),
    os.path.join(PARENT_DIR, "assets", "avatars"),
    os.path.join(PARENT_DIR, "face", "assets", "avatars")
])


# ================= 2. 真实数据库架构补全与万能容错机制 =================
def ensure_db_schema():
    if not DB_PATH: return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in c.fetchall()]

        if 'role' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT '👤 User'")
        if 'status' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT '🟢 正常 (Active)'")
        if 'plain_password' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN plain_password TEXT DEFAULT '******'")

        c.execute("SELECT * FROM users WHERE username='admin27'")
        if not c.fetchone():
            admin_pwd = "Aadmin041012"
            admin_hash = hashlib.sha256(admin_pwd.encode()).hexdigest()
            create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                c.execute(
                    "INSERT INTO users (username, password_hash, email, created_at, role, status, plain_password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    ('admin27', admin_hash, 'admin@beauty.com', create_time, '👑 Super Admin', '🟢 正常 (Active)',
                     admin_pwd))
            except Exception:
                pass

        conn.commit()
        conn.close()
    except Exception:
        pass


def update_user_field(username, field, value):
    if not DB_PATH: return False
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"UPDATE users SET {field} = ? WHERE username = ?", (value, username))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ================= 3. 审计日志读写模块 =================
AUDIT_LOG_PATH = find_valid_path([
    os.path.join(CURRENT_DIR, "assets", "data", "audit_logs.json"),
    os.path.join(PARENT_DIR, "assets", "data", "audit_logs.json"),
    os.path.join(PARENT_DIR, "face", "assets", "data", "audit_logs.json")
])

if not AUDIT_LOG_PATH:
    AUDIT_LOG_PATH = os.path.join(CURRENT_DIR, "assets", "data", "audit_logs.json")
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)


def load_audit_logs():
    if os.path.exists(AUDIT_LOG_PATH):
        try:
            with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
                logs = json.load(f)
                return logs if isinstance(logs, list) else []
        except Exception:
            return []
    return []


def add_audit_log(operator, action, status):
    logs = load_audit_logs()
    new_log = {
        "时间戳 (Timestamp)": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "操作实体 (Operator)": operator,
        "行为事件 (Event Action)": action,
        "执行结果 (Status)": status
    }
    logs.insert(0, new_log)
    logs = logs[:100]
    try:
        with open(AUDIT_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


# ================= 4. 冗余数据回收策略 =================
def perform_smart_cleanup():
    deleted_history_imgs = 0
    deleted_avatars = 0

    if HISTORY_JSON_PATH and HISTORY_DIR:
        try:
            with open(HISTORY_JSON_PATH, 'r', encoding='utf-8') as f:
                history_data = json.load(f)

            from collections import defaultdict
            user_records = defaultdict(list)
            for r in history_data:
                user_records[r.get("user_id", "unknown")].append(r)

            protected_img_filenames = set()
            for uid, records in user_records.items():
                records.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
                for r in records[:30]:
                    if r.get("img_path"):
                        protected_img_filenames.add(os.path.basename(r["img_path"]))

            for root, dirs, files in os.walk(HISTORY_DIR):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        if file not in protected_img_filenames:
                            file_path = os.path.join(root, file)
                            try:
                                os.remove(file_path)
                                deleted_history_imgs += 1
                            except Exception:
                                pass
        except Exception:
            pass

    if USERS_PROFILE_JSON_PATH and AVATARS_DIR:
        try:
            with open(USERS_PROFILE_JSON_PATH, 'r', encoding='utf-8') as f:
                users_profile = json.load(f)

            protected_avatar_filenames = set()
            for uid, profile in users_profile.items():
                if profile.get("avatar"):
                    protected_avatar_filenames.add(os.path.basename(profile["avatar"]))

            for root, dirs, files in os.walk(AVATARS_DIR):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        if file not in protected_avatar_filenames:
                            file_path = os.path.join(root, file)
                            try:
                                os.remove(file_path)
                                deleted_avatars += 1
                            except Exception:
                                pass
        except Exception:
            pass

    return deleted_history_imgs, deleted_avatars


# ================= 5. 核心业务指标拉取 =================
def get_real_metrics():
    user_count = 0
    vector_count = 0
    star_photo_count = 0
    history_call_count = 0

    if DB_PATH:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            user_count = c.fetchone()[0]
            conn.close()
        except Exception:
            pass

    if STAR_IMAGES_DIR:
        try:
            for item in os.listdir(STAR_IMAGES_DIR):
                if os.path.isdir(os.path.join(STAR_IMAGES_DIR, item)):
                    vector_count += 1
            for root, dirs, files in os.walk(STAR_IMAGES_DIR):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        star_photo_count += 1
        except Exception:
            pass

    if HISTORY_JSON_PATH:
        try:
            with open(HISTORY_JSON_PATH, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                history_call_count = len(history_data)
        except Exception:
            pass

    return user_count, vector_count, star_photo_count, history_call_count


def get_users_df():
    ensure_db_schema()
    if DB_PATH:
        try:
            conn = sqlite3.connect(DB_PATH)
            df_raw = pd.read_sql_query("SELECT * FROM users", conn)
            conn.close()

            if df_raw.empty:
                return pd.DataFrame()

            df = pd.DataFrame()
            df['Username'] = df_raw['username'] if 'username' in df_raw.columns else 'Unknown'
            df['Email'] = df_raw['email'] if 'email' in df_raw.columns else '未绑定邮箱'

            df['Status'] = df_raw['status'] if 'status' in df_raw.columns else '🟢 正常 (Active)'
            df['Role'] = df_raw['role'] if 'role' in df_raw.columns else '👤 User'
            df['RegisterDate'] = df_raw['created_at'] if 'created_at' in df_raw.columns else '未知时间'

            df['Status'] = df['Status'].fillna('🟢 正常 (Active)')
            df['Role'] = df['Role'].fillna('👤 User')

            for i in range(len(df)):
                uname = str(df.loc[i, 'Username']).lower()
                if uname == 'admin' or uname == 'admin27':
                    if df.loc[i, 'Role'] == '👤 User':
                        df.loc[i, 'Role'] = '👑 Super Admin'
                        update_user_field(df.loc[i, 'Username'], 'role', '👑 Super Admin')

            return df
        except Exception as e:
            return pd.DataFrame()
    return pd.DataFrame()


# ================= 6. 管理控制台视图渲染 =================
# ================= 6. 管理控制台视图渲染 =================
def show():
    # 动态抓取当前操作者的真实账号 (优先从 URL 的 uid 获取，如果没有则尝试读取 session_state，兜底显示 Unknown_Admin)
    current_admin = st.query_params.get("uid", st.session_state.get("username", "Unknown_Admin"))

    if 'has_logged_view' not in st.session_state:
        # 将原先写死的 "System_Admin" 替换为 current_admin 变量
        add_audit_log(current_admin, "访问后台系统：系统主看板数据加载", "✅ 挂载成功")
        st.session_state.has_logged_view = True

    user_count, vector_count, star_photo_count, history_call_count = get_real_metrics()

    import base64
    bg_path = os.path.join(CURRENT_DIR, "assets", "admin_system", "1.jpg")
    if os.path.exists(bg_path):
        with open(bg_path, "rb") as f:
            bg_base64 = base64.b64encode(f.read()).decode()

        bg_css = f"""
        <style>
            .stApp {{ background: url("data:image/jpeg;base64,{bg_base64}") no-repeat center center fixed !important; background-size: cover !important; }}
            header[data-testid="stHeader"] {{ background-color: transparent !important; }}
            .block-container {{ background: transparent !important; }}
        </style>
        """.replace('\n', ' ')
        st.markdown(bg_css, unsafe_allow_html=True)

        # ================= 核心 CSS 样式注入 (回归纯净布局，彻底解决回弹与留白) =================
        core_css = """
                        <style>
                            /* 1. 彻底抹杀原生侧边栏和顶部导航 */
                            [data-testid="stSidebar"], [data-testid="collapsedControl"], header[data-testid="stHeader"] { 
                                display: none !important; opacity: 0 !important; visibility: hidden !important; height: 0 !important; 
                            }
                            div[data-testid="stHeadingWithActionElements"], div[data-testid="stHeading"] h1, hr { 
                                display: none !important; 
                            }
                            ::-webkit-scrollbar { display: none !important; }
                            * { scrollbar-width: none !important; }

                            /* 2. 核心重构：修复 Streamlit 层级断裂，将滚动权交给真正的直接父级 block-container */
                            .stApp { overflow: hidden !important; background: transparent !important; }
                            section[data-testid="stMain"] {
                                height: 100vh !important;
                                overflow: hidden !important; /* 禁用外层滚动，防止双滚动条打架 */
                                padding: 0 !important; margin: 0 !important;
                            }
                            .block-container { 
                                height: 100vh !important;
                                overflow-y: scroll !important;
                                scroll-snap-type: y proximity !important; /* 关键：从mandatory改为proximity，减少强制回弹 */
                                scroll-behavior: smooth !important;
                                padding: 0 !important; margin: 0 !important; max-width: 100% !important; background: transparent !important;
                                position: relative !important; /* 新增：避免滚动偏移 */
                            }

                            /* 3. 精准设定 PPT 切换吸附点 */
                            div.element-container:has(div[data-testid="stTabs"]) {
                                scroll-snap-align: start !important;
                                scroll-snap-stop: always !important;
                                height: 100vh !important; 
                                max-height: 100vh !important;
                                overflow: hidden !important; 
                                width: 100vw !important;
                                margin: 0 !important; /* 新增：暴力干掉 Streamlit 幽灵组件间隙 */
                                padding: 0 !important;
                            }

                            div.element-container:has(div[data-testid="stTabs"]) {
                                scroll-snap-align: start !important;
                                scroll-snap-stop: always !important;
                                min-height: 100vh !important;
                                width: 100vw !important;
                            }

                            /* ================= 视觉美化样式 ================= */
                            .hero-fullscreen { 
                                height: 100vh !important; width: 100vw !important; 
                                display: flex; flex-direction: column; justify-content: center; align-items: center; 
                                position: relative; overflow: hidden; 
                            }

                            .logout-btn-custom {
                                position: absolute; top: 20px; right: 80px; 
                                padding: 12px 24px; background: rgba(255, 255, 255, 0.2); 
                                backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.5);
                                border-radius: 20px; color: #355070; text-decoration: none !important;
                                font-weight: 700; transition: all 0.3s ease; z-index: 100;
                                box-shadow: 0 4px 15px rgba(53, 80, 112, 0.1);
                            }
                            .logout-btn-custom:hover { background: rgba(255, 255, 255, 0.6); transform: translateY(-3px) scale(1.02); box-shadow: 0 8px 25px rgba(53, 80, 112, 0.2); }

                            .hero-content-wrapper { transform: translateY(-13vh); display: flex; flex-direction: column; align-items: center; width: 100%; }
                            .hero-title { font-family: 'Noto Serif SC', 'Plus Jakarta Sans', serif; font-size: 64px; font-weight: 900; letter-spacing: 12px; color: #355070; margin-bottom: 80px; text-shadow: 0 10px 30px rgba(255, 255, 255, 0.6); z-index: 10; text-align: center; }
                            .bubbles-container { display: flex; gap: 50px; justify-content: center; align-items: center; flex-wrap: wrap; width: 100%; max-width: 1400px; z-index: 10; padding: 0 20px; }
                            .glass-bubble { width: 250px; height: 250px; border-radius: 50%; background: radial-gradient(135deg, rgba(255, 255, 255, 0.65) 0%, rgba(255, 255, 255, 0.1) 100%); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.8); box-shadow: inset 0 0 30px rgba(255,255,255,0.9), inset 10px 0 40px rgba(229, 152, 155, 0.2), 0 20px 40px rgba(53, 80, 112, 0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; transition: all 0.6s cubic-bezier(0.2, 0.8, 0.2, 1); position: relative; animation: bubble-float 6s ease-in-out infinite; cursor: default; }
                            .glass-bubble::before { content: ''; position: absolute; top: 15%; left: 20%; width: 30%; height: 30%; border-radius: 50%; background: radial-gradient(circle, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0) 70%); filter: blur(5px); transform: rotate(-45deg); pointer-events: none; }
                            .glass-bubble:hover { transform: translateY(-20px) scale(1.08); box-shadow: inset 0 0 40px rgba(255,255,255,1), inset 15px 0 50px rgba(229, 152, 155, 0.4), 0 30px 60px rgba(53, 80, 112, 0.25); border-color: #ffffff; animation-play-state: paused; }
                            .glass-bubble:nth-child(1) { animation-delay: 0s; } .glass-bubble:nth-child(2) { animation-delay: 1.2s; } .glass-bubble:nth-child(3) { animation-delay: 0.6s; } .glass-bubble:nth-child(4) { animation-delay: 1.8s; }
                            @keyframes bubble-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
                            .bubble-icon { font-size: 38px; margin-bottom: 5px; opacity: 0.85; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1)); }
                            .bubble-value { font-size: 48px; font-weight: 900; font-family: 'Plus Jakarta Sans', sans-serif; background: linear-gradient(135deg, #453750, #B5838D); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1; margin-bottom: 5px; }
                            .bubble-label { font-size: 15px; font-weight: 700; color: #6D597A; letter-spacing: 1px; }

                            /* 修复点：激活指示器的点击和悬停属性 */
                            .scroll-indicator { position: absolute; bottom: 15vh; left: 50%; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; opacity: 0.6; animation: bounce 2s infinite; color: #355070; cursor: pointer; z-index: 100; transition: opacity 0.3s; }
                            .scroll-indicator:hover { opacity: 1; }
                            .scroll-indicator span { font-size: 12px; letter-spacing: 3px; font-weight: 700; margin-bottom: 5px; }
                            @keyframes bounce { 0%, 100% { transform: translate(-50%, 0); } 50% { transform: translate(-50%, 12px); } }

                            /* Tabs 面板 (恢复正常间距) */
                            div[data-testid="stTabs"] { 
                                height: 100vh !important; 
                                max-height: 100vh !important;
                                padding: 1px 5% 10px 5% !important; /* 关键修改：将顶部 padding 从 40px 缩减为 15px，让 Tab 栏贴顶 */
                                background: rgba(255, 255, 255, 0.2); 
                                backdrop-filter: blur(8px); 
                                overflow: hidden !important; 
                                display: flex !important;
                                flex-direction: column !important; 
                            }

                            /* 关键3：让 Tab 内部的数据面板自己滚动，保护顶部的导航栏永远吸顶固定 */
                            div[data-testid="stTabs"] > div[role="tabpanel"] {
                                overflow-y: auto !important;
                                flex-grow: 1 !important;
                                padding-bottom: 60px !important;
                            }
                            /* 隐藏内部面板滚动条保持UI纯净 */
                            div[data-testid="stTabs"] > div[role="tabpanel"]::-webkit-scrollbar {
                                display: none !important; 
                            }
                            
                            [data-baseweb="tab-list"] { background: rgba(255, 255, 255, 0.6) !important; backdrop-filter: blur(15px) !important; border-radius: 20px !important; padding: 8px !important; box-shadow: 0 10px 30px rgba(53, 80, 112, 0.08), inset 0 2px 6px rgba(255,255,255,0.8) !important; gap: 10px !important; margin: -8px auto 20px auto !important; border: 1px solid rgba(255, 255, 255, 0.9); width: fit-content; }
                            [data-baseweb="tab"] { border-radius: 14px !important; padding: 12px 30px !important; background-color: transparent !important; transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important; border: none !important; color: #8D99AE !important; font-weight: 600 !important; }
                            [aria-selected="true"] { background: linear-gradient(135deg, #ffffff, #fdfbfd) !important; box-shadow: 0 8px 20px rgba(225, 190, 231, 0.3) !important; color: #E5989B !important; font-weight: 800 !important; transform: scale(1.02); }

                            div.stButton > button { background: linear-gradient(135deg, #E5989B, #B56576) !important; color: white !important; border-radius: 14px !important; border: none !important; font-weight: 700 !important; font-size: 16px !important; padding: 12px 24px !important; box-shadow: 0 6px 15px rgba(181, 101, 118, 0.25), inset 0 2px 0 rgba(255,255,255,0.2), inset 0 -4px 0 rgba(0,0,0,0.15) !important; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important; position: relative; overflow: hidden; }
                            div.stButton > button:hover { transform: translateY(-4px) scale(1.02) !important; box-shadow: 0 12px 25px rgba(181, 101, 118, 0.4), inset 0 2px 0 rgba(255,255,255,0.3), inset 0 -4px 0 rgba(0,0,0,0.2) !important; background: linear-gradient(135deg, #D6878A, #A65767) !important; }
                            div.stButton > button:active { transform: translateY(2px) !important; box-shadow: 0 2px 10px rgba(181, 101, 118, 0.3), inset 0 3px 6px rgba(0,0,0,0.2) !important; }
                            div.stButton > button[kind="secondary"] { background: linear-gradient(135deg, #ffffff, #f4f4f8) !important; color: #6D597A !important; box-shadow: 0 6px 15px rgba(53, 80, 112, 0.1), inset 0 2px 0 rgba(255,255,255,1), inset 0 -4px 0 rgba(0,0,0,0.08) !important; }
                            div.stButton > button[kind="secondary"]:hover { color: #E5989B !important; box-shadow: 0 12px 25px rgba(53, 80, 112, 0.15), inset 0 2px 0 rgba(255,255,255,1), inset 0 -4px 0 rgba(0,0,0,0.1) !important; }
                            .ops-card-premium { background: rgba(255, 255, 255, 0.65) !important; backdrop-filter: blur(24px) !important; border: 1px solid rgba(255, 255, 255, 1) !important; border-radius: 24px !important; padding: 35px !important; box-shadow: 0 15px 35px rgba(53, 80, 112, 0.05), inset 0 0 0 1px rgba(255,255,255,0.5) !important; transition: all 0.4s; display: flex; flex-direction: column; justify-content: flex-start; height: 280px; margin-bottom: 25px; }
                            .ops-card-premium:hover { transform: translateY(-8px) !important; box-shadow: 0 25px 50px rgba(53, 80, 112, 0.12), inset 0 0 0 1px rgba(255,255,255,0.8) !important; background: rgba(255, 255, 255, 0.85) !important; }
                            .ops-header { display: flex; align-items: center; gap: 18px; margin-bottom: 20px; }
                            .ops-icon { width: 56px; height: 56px; border-radius: 18px; background: linear-gradient(135deg, #fff, #f0f0f5); box-shadow: 0 8px 16px rgba(0,0,0,0.06); display: flex; align-items: center; justify-content: center; font-size: 26px; }
                            .ops-title { font-size: 24px; font-weight: 800; color: #355070; letter-spacing: 1px; }
                            .ops-desc { font-size: 15px; color: #6D597A; line-height: 1.8; flex-grow: 1; opacity: 0.9; }
                            .ops-stats-pill { align-self: flex-start; padding: 10px 20px; background: rgba(229, 152, 155, 0.12); color: #B56576; border-radius: 12px; font-size: 13px; font-weight: 800; border: 1px solid rgba(229, 152, 155, 0.3); }
                            .chart-title { font-size: 24px; font-weight: 800; color: #355070; margin-bottom: 20px; margin-top: 10px; font-family: 'Plus Jakarta Sans', sans-serif; display: flex; align-items: center; justify-content: center; gap: 10px; text-shadow: 0 2px 10px rgba(255,255,255,0.8); }
                        </style>
                        """
        st.markdown(core_css.replace('\n', ' '), unsafe_allow_html=True)

        # ================= 暴力灭杀原生红色按钮 + 状态保持与全屏PPT式滚动黑科技 =================
        components.html("""
                                    <script>
                                    // 1. 灭杀退出按钮
                                    function exterminateRedButton() {
                                        const doc = window.parent.document;
                                        const buttons = doc.querySelectorAll('.stButton button');
                                        buttons.forEach(btn => {
                                            if (btn.innerText.includes('退出')) {
                                                const wrapper = btn.closest('.element-container');
                                                if (wrapper) wrapper.remove();
                                            }
                                        });
                                    }
                                    setInterval(exterminateRedButton, 100);

                                    // 2. 状态保持与防抖回弹
                                    const doc = window.parent.document;
                                    const container = doc.querySelector('.block-container');
                                    if (container) {
                                        const saveScroll = () => sessionStorage.setItem('adminSystemScrollPos', container.scrollTop);
                                        container.addEventListener('scroll', saveScroll);

                                        const savedPos = sessionStorage.getItem('adminSystemScrollPos');
                                        if (savedPos && parseInt(savedPos) > 10) {
                                            setTimeout(() => { container.scrollTop = parseInt(savedPos); }, 50);
                                            setTimeout(() => { container.scrollTop = parseInt(savedPos); }, 300);
                                        }
                                    }

                                    // 3. 核心：绑定鼠标滚轮 PPT 式丝滑翻页 & 修复向下按钮
                                    // 3. 核心：绑定鼠标滚轮 PPT 式丝滑翻页 & 修复向下按钮
                                    function bindScrollAndWheel() {
                                        const parentDoc = window.parent.document;
                                        const scrollBtn = parentDoc.querySelector('.scroll-indicator');
                                        const scrollContainer = parentDoc.querySelector('.block-container');

                                        // 确保容器存在，且防止被重复绑定多次事件
                                        if (scrollContainer && !scrollContainer.dataset.wheelBound) {
                                            scrollContainer.dataset.wheelBound = "true";
                                            let isAnimating = false; // 动画锁

                                            const getPage2Top = () => {
                                                return window.parent.innerHeight;
                                            };

                                            // 监听全局鼠标滚轮事件
                                            scrollContainer.addEventListener('wheel', (e) => {
                                                
                                                // === 第一层精准保护：数据表格 (st.dataframe) ===
                                                // 只要鼠标悬停在系统审计日志等 Streamlit 渲染的表格组件上，直接放行不触发全屏
                                                const isDataFrame = e.target.closest('[data-testid="stDataFrame"]') || e.target.closest('iframe[title="streamlit_dataframe"]');
                                                if (isDataFrame) {
                                                    return; 
                                                }

                                                // === 第二层精准保护：自定义定高容器 (st.container) ===
                                                // 针对账户管理面板中 with st.container(height=450): 渲染出来的容器
                                                const fixedContainer = e.target.closest('div[data-testid="stVerticalBlockBorderWrapper"]') || e.target.closest('div[data-testid="stVerticalBlock"]');
                                                if (fixedContainer) {
                                                    const style = window.getComputedStyle(fixedContainer);
                                                    if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && fixedContainer.scrollHeight > fixedContainer.clientHeight) {
                                                        const isAtTop = fixedContainer.scrollTop <= 0;
                                                        const isAtBottom = Math.ceil(fixedContainer.scrollTop + fixedContainer.clientHeight) >= fixedContainer.scrollHeight - 2;
                                                        // 如果在容器内还没滚到底或顶，允许内部滚动，不触发全屏
                                                        if (!((e.deltaY < 0 && isAtTop) || (e.deltaY > 0 && isAtBottom))) {
                                                            return;
                                                        }
                                                    }
                                                }

                                                // === 第三层保护：普通 Tab 面板内容溢出 ===
                                                const tabPanel = e.target.closest('div[role="tabpanel"]');
                                                if (tabPanel) {
                                                    const isAtTop = tabPanel.scrollTop <= 0;
                                                    const isAtBottom = Math.ceil(tabPanel.scrollTop + tabPanel.clientHeight) >= tabPanel.scrollHeight - 2;
                                                    if (!((e.deltaY < 0 && isAtTop) || (e.deltaY > 0 && isAtBottom))) {
                                                        return;
                                                    }
                                                }

                                                // === 以上条件都不满足时：拦截原生滚动，执行全屏 PPT 翻页 ===
                                                e.preventDefault();

                                                if (isAnimating) return;
                                                isAnimating = true;

                                                if (e.deltaY > 0) {
                                                    // 滚轮向下 -> 滑到第二页的看板
                                                    scrollContainer.scrollTo({ top: getPage2Top(), behavior: 'smooth' });
                                                } else {
                                                    // 滚轮向上 -> 滑回第一页的首页大屏
                                                    scrollContainer.scrollTo({ top: 0, behavior: 'smooth' });
                                                }

                                                // 强制锁死 800 毫秒（等待平滑滚动抵达终点）
                                                setTimeout(() => { isAnimating = false; }, 800);
                                            }, { passive: false });

                                            // 同步更新向下指示箭头的点击事件
                                            if (scrollBtn && !scrollBtn.dataset.clickBound) {
                                                scrollBtn.dataset.clickBound = "true";
                                                scrollBtn.style.cursor = "pointer";
                                                scrollBtn.addEventListener('click', () => {
                                                    if (isAnimating) return;
                                                    isAnimating = true;
                                                    scrollContainer.scrollTo({ top: getPage2Top(), behavior: 'smooth' });
                                                    setTimeout(() => { isAnimating = false; }, 800);
                                                });
                                            }
                                        }
                                    }
                                    // 每 200ms 探测一次页面元素是否就绪，挂载全屏翻页驱动
                                    setInterval(bindScrollAndWheel, 200);
                                    </script>
                                """, height=0, width=0)
        # ================= 第一屏：全屏气泡大屏 =================
        # 去除了导致 React 报错的 onclick 属性，将其交由上方的底层 JS 监听控制
        hero_html = (
            '<div class="hero-fullscreen">'
            '<a href="/?nav=auth" class="logout-btn-custom" target="_self">🚪 退出登录</a>'
            '<div class="hero-content-wrapper">'
            '<div class="hero-title">系统管理控制台</div>'
            '<div class="bubbles-container">'
            f'<div class="glass-bubble"><div class="bubble-icon">👤</div><div class="bubble-value">{user_count:,}</div><div class="bubble-label">平台注册账户数</div></div>'
            f'<div class="glass-bubble"><div class="bubble-icon">🎯</div><div class="bubble-value">{vector_count:,}</div><div class="bubble-label">收录基准面孔数</div></div>'
            f'<div class="glass-bubble"><div class="bubble-icon">🖼️</div><div class="bubble-value">{star_photo_count:,}</div><div class="bubble-label">源图图库容量</div></div>'
            f'<div class="glass-bubble"><div class="bubble-icon">⚡</div><div class="bubble-value">{history_call_count:,}</div><div class="bubble-label">累计测算调用量</div></div>'
            '</div>'
            '</div>'
            '<div class="scroll-indicator"><span>SCROLL DOWN</span><div>↓</div></div>'
            '</div>'
        )
        st.markdown(hero_html, unsafe_allow_html=True)

        # ================= 第二屏：大屏看板容器 (Tabs) =================
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 数据分析与看板",
            "👥 账户与风控中心",
            "🧹 系统运维与清理",
            "📝 系统审计日志"
        ])

    # ------------------ Tab 1: 可视化图表 ------------------
    with tab1:
        sel_left, sel_right = st.columns([1.8, 3])
        with sel_left:
            chart_selection = st.selectbox(
                "请选择要查看的可视化图表：",
                options=[
                    "🎭 历史测算脸型分布 (环形饼图)",
                    "📈 近期系统调用并发趋势 (折线图)",
                    "👥 平台用户增长趋势 (面积折线图)",
                    "🛡️ 账号权限与健康状态分布 (嵌套旭日图)",
                    "🕒 测算请求高频时段分析 (极坐标雷达图)",
                    "📝 后台安全审计行为分类 (水平条形图)"
                ],
                label_visibility="collapsed"
            )

            use_mock_data = st.toggle("🧪 演示模式", value=False,
                                      help="开启后将展示符合业务规律的活跃数据，关闭则严格读取系统真实数据")

        def render_echarts(option_dict, height=550):
            option_json = json.dumps(option_dict, ensure_ascii=False)
            html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <script src="https://registry.npmmirror.com/echarts/5.4.3/files/dist/echarts.min.js"></script>
                    </head>
                    <body style="margin:0; padding:0; background:transparent;">
                        <div id="chart" style="width: 100%; height: {height}px;"></div>
                        <script>
                            if (typeof echarts === 'undefined') {{
                                document.getElementById('chart').innerHTML = '<div style="color:#E5989B; padding:20px; text-align:center; font-weight:bold; margin-top:50px;">⚠️ 核心图表引擎加载失败，请检查您的网络连接或关闭代理。</div>';
                            }} else {{
                                try {{
                                    var chart = echarts.init(document.getElementById('chart'));
                                    var option = {option_json};
                                    if (option.tooltip && option.tooltip.formatter_js) {{
                                        option.tooltip.formatter = new Function('return ' + option.tooltip.formatter_js)();
                                    }}
                                    chart.setOption(option);
                                    window.addEventListener('resize', function() {{ chart.resize(); }});
                                }} catch (e) {{
                                    document.getElementById('chart').innerHTML = '<div style="color:red; padding:20px;">图表渲染发生错误: ' + e.message + '</div>';
                                }}
                            }}
                        </script>
                    </body>
                    </html>
                    """
            components.html(html_content, height=height + 20)

        premium_colors = ['#FBE4E9', '#EBE4F4', '#EAF2E6', '#FDF0E0', '#E4F0F5', '#F5E1E1', '#E6E9F5']
        chart_left, chart_center, chart_right = st.columns([0.2, 5, 0.2])

        with chart_center:
            def safe_parse_date(ts):
                try:
                    ts_float = float(ts)
                    if ts_float > 2e9:
                        return pd.to_datetime(str(int(ts_float))[:8], format='%Y%m%d')
                    else:
                        return pd.to_datetime(ts_float, unit='s') + pd.Timedelta(hours=8)
                except:
                    return pd.NaT

            if chart_selection == "🎭 历史测算脸型分布 (环形饼图)":
                title_html = '<div class="chart-title">🎭 历史测算脸型分布</div>'
                st.markdown(title_html.replace('\n', ' '), unsafe_allow_html=True)
                if use_mock_data:
                    shape_counts = {'鹅蛋脸': 1452, '长形脸': 856, '圆脸/娃娃脸': 430, '方圆脸': 210, '其他': 85}
                else:
                    shape_counts = {}
                    reports_dir = find_valid_path([os.path.join(CURRENT_DIR, "assets", "history_reports"),
                                                   os.path.join(os.path.dirname(CURRENT_DIR), "assets",
                                                                "history_reports")])
                    if reports_dir and os.path.exists(reports_dir):
                        for root, dirs, files in os.walk(reports_dir):
                            for file in files:
                                if file.endswith('.json'):
                                    try:
                                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                            data = json.load(f)
                                            shape = "未识别"
                                            if isinstance(data, dict):
                                                if "analysis" in data and "face" in data["analysis"] and len(
                                                        data["analysis"]["face"]) > 0:
                                                    raw_shape = data["analysis"]["face"][0]
                                                    shape = raw_shape.split(" ")[0] if " " in raw_shape else raw_shape
                                                elif "face_shape" in data:
                                                    shape = data["face_shape"]
                                                elif "base_info" in data and "face_shape" in data["base_info"]:
                                                    shape = data["base_info"]["face_shape"]
                                            shape_counts[shape] = shape_counts.get(shape, 0) + 1
                                    except:
                                        pass
                    if not shape_counts: shape_counts = {'暂无测算数据': 1}

                option = {
                    "tooltip": {"trigger": "item", "formatter": "{b}: {c} 人次 ({d}%)"},
                    "legend": {"bottom": "0%", "icon": "circle", "textStyle": {"color": "#7A7085"}},
                    "series": [{
                        "type": "pie",
                        "radius": ["40%", "75%"],
                        "avoidLabelOverlap": True,
                        "itemStyle": {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 4},
                        "label": {"show": True, "color": "#7A7085", "fontSize": 14, "fontWeight": "bold"},
                        "emphasis": {
                            "itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0, 0, 0, 0.1)"}},
                        "data": [{"name": k, "value": v} for k, v in shape_counts.items()],
                        "color": premium_colors
                    }]
                }
                render_echarts(option)

            elif chart_selection == "📈 近期系统调用并发趋势 (折线图)":
                title_html = '<div class="chart-title">📈 系统测算调用并发趋势</div>'
                st.markdown(title_html.replace('\n', ' '), unsafe_allow_html=True)
                if use_mock_data:
                    dates = pd.date_range(end=pd.Timestamp.now(), periods=30).strftime('%Y-%m-%d').tolist()
                    vals = [random.randint(50, 150) + (i * 5) for i in range(30)]
                else:
                    history_data = []
                    if HISTORY_JSON_PATH and os.path.exists(HISTORY_JSON_PATH):
                        try:
                            with open(HISTORY_JSON_PATH, 'r', encoding='utf-8') as f:
                                history_data = json.load(f)
                        except:
                            pass
                    if history_data:
                        df_hist = pd.DataFrame(history_data)
                        if 'timestamp' in df_hist.columns:
                            df_hist['ParsedDate'] = df_hist['timestamp'].apply(safe_parse_date)
                            df_hist = df_hist.dropna(subset=['ParsedDate'])
                            df_hist['Date'] = df_hist['ParsedDate'].dt.strftime('%Y-%m-%d')
                            counts = df_hist.groupby('Date').size().reset_index(name='Count').sort_values('Date').tail(
                                30)
                            dates = counts['Date'].tolist()
                            vals = counts['Count'].tolist()
                        else:
                            dates, vals = [pd.Timestamp.now().strftime('%Y-%m-%d')], [0]
                    else:
                        dates, vals = [pd.Timestamp.now().strftime('%Y-%m-%d')], [0]

                option = {
                    "tooltip": {"trigger": "axis",
                                "axisPointer": {"type": "cross", "label": {"backgroundColor": "#DCA7CA"}}},
                    "xAxis": {"type": "category", "data": dates, "boundaryGap": False, "axisLine": {"show": False},
                              "axisTick": {"show": False}, "axisLabel": {"color": "#A098AE"}},
                    "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "rgba(240, 240, 245, 0.8)"}},
                              "axisLabel": {"color": "#A098AE"}},
                    "series": [{
                        "data": vals, "type": "line", "smooth": True, "symbolSize": 8,
                        "areaStyle": {"color": {"type": 'linear', "x": 0, "y": 0, "x2": 0, "y2": 1,
                                                "colorStops": [{"offset": 0, "color": "rgba(220, 167, 202, 0.4)"},
                                                               {"offset": 1, "color": "rgba(220, 167, 202, 0.05)"}]}},
                        "lineStyle": {"color": "#DCA7CA", "width": 4},
                        "itemStyle": {"color": "#DCA7CA", "borderColor": "#fff", "borderWidth": 2}
                    }]
                }
                render_echarts(option)

            elif chart_selection == "👥 平台用户增长趋势 (面积折线图)":
                title_html = '<div class="chart-title">👥 平台注册用户拉新趋势</div>'
                st.markdown(title_html.replace('\n', ' '), unsafe_allow_html=True)
                if use_mock_data:
                    dates = pd.date_range(end=pd.Timestamp.now(), periods=30).strftime('%Y-%m-%d').tolist()
                    vals = [random.randint(5, 40) + int(i * 1.5) for i in range(30)]
                else:
                    df_users = get_users_df()
                    if not df_users.empty and 'RegisterDate' in df_users.columns:
                        valid_dates = pd.to_datetime(df_users['RegisterDate'], errors='coerce')
                        df_users['Date'] = valid_dates.dt.strftime('%Y-%m-%d')
                        df_users = df_users.dropna(subset=['Date'])
                        counts = df_users.groupby('Date').size().reset_index(name='Count').sort_values('Date').tail(30)
                        dates = counts['Date'].tolist()
                        vals = counts['Count'].tolist()
                    else:
                        dates, vals = [pd.Timestamp.now().strftime('%Y-%m-%d')], [0]

                option = {
                    "tooltip": {"trigger": "axis",
                                "axisPointer": {"type": "cross", "label": {"backgroundColor": "#C8B6E2"}}},
                    "xAxis": {"type": "category", "data": dates, "boundaryGap": False, "axisLine": {"show": False},
                              "axisTick": {"show": False}, "axisLabel": {"color": "#A098AE"}},
                    "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "rgba(240, 240, 245, 0.8)"}},
                              "axisLabel": {"color": "#A098AE"}},
                    "series": [{
                        "data": vals, "type": "line", "smooth": True, "symbolSize": 8,
                        "areaStyle": {"color": {"type": 'linear', "x": 0, "y": 0, "x2": 0, "y2": 1,
                                                "colorStops": [{"offset": 0, "color": "rgba(200, 182, 226, 0.4)"},
                                                               {"offset": 1, "color": "rgba(200, 182, 226, 0.05)"}]}},
                        "lineStyle": {"color": "#C8B6E2", "width": 4},
                        "itemStyle": {"color": "#C8B6E2", "borderColor": "#fff", "borderWidth": 2}
                    }]
                }
                render_echarts(option)

            elif chart_selection == "🛡️ 账号权限与健康状态分布 (嵌套旭日图)":
                title_html = '<div class="chart-title">🛡️ 账号权限与健康状态分布</div>'
                st.markdown(title_html.replace('\n', ' '), unsafe_allow_html=True)
                if use_mock_data:
                    sunburst_df = pd.DataFrame([
                        {'Role': '👤 普通用户', 'Status': '正常活跃', 'Count': 4500},
                        {'Role': '👤 普通用户', 'Status': '风控冻结', 'Count': 1200},
                        {'Role': '🛡️ 管理员', 'Status': '正常活跃', 'Count': 800},
                        {'Role': '🛡️ 管理员', 'Status': '风控冻结', 'Count': 150},
                        {'Role': '👑 超级管理', 'Status': '正常活跃', 'Count': 350}
                    ])
                else:
                    df_users = get_users_df()
                    if df_users.empty:
                        sunburst_df = pd.DataFrame()
                    else:
                        sunburst_df = df_users.groupby(['Role', 'Status']).size().reset_index(name='Count')

                        def clean_role(r):
                            r = str(r)
                            if 'Super' in r: return '👑 超级管理'
                            if 'Admin' in r: return '🛡️ 管理员'
                            return '👤 普通用户'

                        def clean_status(s):
                            s = str(s)
                            if '正常' in s or 'Active' in s: return '正常活跃'
                            return '风控冻结'

                        sunburst_df['Role'] = sunburst_df['Role'].apply(clean_role)
                        sunburst_df['Status'] = sunburst_df['Status'].apply(clean_status)

                echarts_sunburst_data = []
                if not sunburst_df.empty:
                    for role in sunburst_df['Role'].unique():
                        role_df = sunburst_df[sunburst_df['Role'] == role]
                        children = [{"name": row['Status'], "value": int(row['Count'])} for _, row in
                                    role_df.iterrows()]
                        echarts_sunburst_data.append({"name": role, "children": children})
                else:
                    echarts_sunburst_data = [{"name": "暂无数据", "value": 1}]

                option = {
                    "series": {
                        "type": "sunburst",
                        "data": echarts_sunburst_data,
                        "radius": [0, '90%'],
                        "itemStyle": {"borderRadius": 7, "borderWidth": 2, "borderColor": '#fff'},
                        "label": {"show": True, "formatter": "{b}\n{c}", "color": "#605A68", "fontWeight": "bold"},
                        "color": premium_colors
                    }
                }
                render_echarts(option)

            elif chart_selection == "🕒 测算请求高频时段分析 (极坐标雷达图)":
                title_html = '<div class="chart-title">🕒 测算API高频调用生物钟分析</div>'
                st.markdown(title_html.replace('\n', ' '), unsafe_allow_html=True)
                hours_dist = {f"{i:02}:00": 0 for i in range(24)}
                if use_mock_data:
                    mock_vals = [5, 2, 0, 0, 0, 2, 8, 15, 30, 45, 60, 90, 220, 280, 310, 340, 380, 350, 310, 240, 150,
                                 80, 40, 15]
                    hours_dist = {f"{i:02}:00": mock_vals[i] for i in range(24)}
                else:
                    if HISTORY_JSON_PATH and os.path.exists(HISTORY_JSON_PATH):
                        try:
                            with open(HISTORY_JSON_PATH, 'r', encoding='utf-8') as f:
                                for item in json.load(f):
                                    ts = item.get('timestamp')
                                    if ts:
                                        h = safe_parse_date(ts)
                                        if pd.notnull(h): hours_dist[f"{h.hour:02}:00"] += 1
                        except:
                            pass

                time_keys = list(hours_dist.keys())

                formatter_js_str = f"function(params) {{ var vals = params.value; var keys = {time_keys}; var col1 = '<div style=\"flex:1; padding-right:20px; border-right:1px solid rgba(235, 228, 244, 0.6); margin-right:20px;\">'; for(var i=0; i<12; i++){{ col1 += '<div><span style=\"color:#8D99AE\">' + keys[i] + '</span> <span style=\"float:right; font-weight:bold; color:#4A405A\">' + vals[i] + '</span></div>'; }} col1 += '</div>'; var col2 = '<div style=\"flex:1;\">'; for(var i=12; i<24; i++){{ col2 += '<div><span style=\"color:#8D99AE\">' + keys[i] + '</span> <span style=\"float:right; font-weight:bold; color:#4A405A\">' + vals[i] + '</span></div>'; }} col2 += '</div>'; return '<div style=\"font-size:13px; margin-bottom:10px; border-bottom:1px solid rgba(235, 228, 244, 0.8); padding-bottom:8px; color:#605A68; font-weight:bold;\">🕒 24小时并发量详细分布</div><div style=\"display:flex; font-size:12px; line-height:1.9;\">' + col1 + col2 + '</div>'; }}"

                option = {
                    "tooltip": {
                        "trigger": "item", "confine": True,
                        "formatter_js": formatter_js_str
                    },
                    "radar": {
                        "indicator": [
                            {"name": k, "max": max(hours_dist.values()) * 1.2 if max(hours_dist.values()) > 0 else 10}
                            for k in hours_dist.keys()],
                        "splitArea": {"show": False},
                        "axisLine": {"lineStyle": {"color": "rgba(240, 240, 245, 0.8)"}},
                        "splitLine": {"lineStyle": {"color": "rgba(240, 240, 245, 0.8)"}},
                        "axisName": {"color": "#A098AE", "fontSize": 11}
                    },
                    "series": [{
                        "type": "radar", "data": [{"value": list(hours_dist.values()), "name": "并发请求量"}],
                        "symbol": "circle", "symbolSize": 8,
                        "itemStyle": {"color": "#F5B7B1", "borderColor": "#fff", "borderWidth": 2},
                        "areaStyle": {"color": "rgba(251, 228, 233, 0.65)"},
                        "lineStyle": {"color": "#F5B7B1", "width": 3}
                    }]
                }
                render_echarts(option)

            elif chart_selection == "📝 后台安全审计行为分类 (水平条形图)":
                title_html = '<div class="chart-title">📝 后台底层安全审计作业监测</div>'
                st.markdown(title_html.replace('\n', ' '), unsafe_allow_html=True)
                if use_mock_data:
                    action_names = ['权限变更', '账户管理', '风控干预操作', '底层磁盘运维', '底层内存运维',
                                    '执行存储碎片清理', '物理磁盘动态调度', '执行并发内存调度', '系统冗余智能清理',
                                    '访问后台管理系统', '访问[核心系统看板]视图']
                    action_counts = [42, 145, 258, 324, 465, 840, 1250, 2480, 3620, 8560, 14250]
                else:
                    real_logs = load_audit_logs()
                    if real_logs:
                        df_logs = pd.DataFrame(real_logs)
                        if '行为事件 (Event Action)' in df_logs.columns:
                            counts = df_logs['行为事件 (Event Action)'].apply(
                                lambda x: x.split('：')[0] if '：' in x else (
                                    x.split(':')[0] if ':' in x else x)).value_counts()
                            action_names = counts.index.tolist()[::-1]
                            action_counts = counts.values.tolist()[::-1]
                        else:
                            action_names, action_counts = [], []
                    else:
                        action_names, action_counts = [], []

                if action_counts:
                    option = {
                        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
                        "xAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "rgba(240, 240, 245, 0.8)"}},
                                  "axisLabel": {"color": "#A098AE"}},
                        "yAxis": {"type": "category", "data": action_names, "axisLine": {"show": False},
                                  "axisTick": {"show": False}, "axisLabel": {"color": "#605A68", "fontWeight": "bold"}},
                        "series": [{
                            "type": "bar", "data": action_counts, "barWidth": "45%",
                            "itemStyle": {
                                "borderRadius": [0, 8, 8, 0],
                                "color": {"type": 'linear', "x": 0, "y": 0, "x2": 1, "y2": 0,
                                          "colorStops": [{"offset": 0, "color": "#EBE4F4"},
                                                         {"offset": 1, "color": "#FBE4E9"}]}
                            }
                        }]
                    }
                    render_echarts(option)
                else:
                    st.info("系统提示：当前暂无任何真实后台操作审计日志，请先在下方控制台执行操作。")

    # ------------------ Tab 2: 账号风控管理 ------------------
    with tab2:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        df_users = get_users_df()

        if df_users.empty:
            st.info("系统提示：当前数据库中未检索到任何用户归档信息。")
        else:
            table_header = (
                '<div style="display: flex; background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(10px); padding: 15px 20px; border-radius: 12px; font-size: 14px; font-weight: 700; color: #355070; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); border: 1px solid rgba(255,255,255,0.8);">'
                '<div style="flex: 1.5;">账户标识</div>'
                '<div style="flex: 2.5;">联络邮箱</div>'
                '<div style="flex: 1.5;">账户状态</div>'
                '<div style="flex: 1.5;">系统权限</div>'
                '<div style="flex: 1.2; text-align: center;">操作管控</div>'
                '</div>'
            )
            st.markdown(table_header, unsafe_allow_html=True)

            with st.container(height=450, border=False):
                for index, row in df_users.iterrows():
                    user_name = row.get('Username', 'Unknown')
                    email = row.get('Email', '')
                    status = row.get('Status', '🟢 正常 (Active)')
                    role = row.get('Role', '👤 User')

                    cols = st.columns([1.5, 2.5, 1.5, 1.5, 1.2], vertical_alignment="center")

                    col0_html = f"<div style='font-size:15px; font-weight:700; color:#355070; margin-left:10px;'>{user_name}</div>"
                    cols[0].markdown(col0_html.replace('\n', ' '), unsafe_allow_html=True)

                    col1_html = f"<div style='font-size:14px; color:#8D99AE;'>{email}</div>"
                    cols[1].markdown(col1_html.replace('\n', ' '), unsafe_allow_html=True)

                    status_color = "#E5989B" if "Frozen" in status or "冻结" in status else "#6D597A"
                    col2_html = f"<div style='font-size:14px; font-weight:700; color:{status_color};'>{status}</div>"
                    cols[2].markdown(col2_html.replace('\n', ' '), unsafe_allow_html=True)

                    role_color = "#E5989B" if "Admin" in role else "#8D99AE"
                    col3_html = f"<div style='font-size:14px; font-weight:700; color:{role_color};'>{role}</div>"
                    cols[3].markdown(col3_html.replace('\n', ' '), unsafe_allow_html=True)

                    with cols[4]:
                        with st.popover("⚙️ 管控", help="展开动态操作面板"):
                            pop_title = f"<div style='font-size:15px; font-weight:800; color:#355070; margin-bottom:15px;'>🎯 目标: {user_name}</div>"
                            st.markdown(pop_title.replace('\n', ' '), unsafe_allow_html=True)

                            if "Frozen" not in status and "冻结" not in status:
                                if st.button("❄️ 冻结账号", key=f"f_{user_name}_{index}", use_container_width=True,
                                             type="secondary"):
                                    if update_user_field(user_name, 'status', '🔴 冻结 (Frozen)'):
                                        add_audit_log(current_admin, f"风控操作：冻结账户 [{user_name}]", "✅ 执行成功")
                                        st.rerun()
                            else:
                                if st.button("☀️ 解冻账号", key=f"u_{user_name}_{index}", use_container_width=True,
                                             type="primary"):
                                    if update_user_field(user_name, 'status', '🟢 正常 (Active)'):
                                        add_audit_log(current_admin, f"风控操作：解除账户 [{user_name}] 冻结",
                                                      "✅ 执行成功")
                                        st.rerun()

                            if st.button("🔄 重置密码为 123456", key=f"r_{user_name}_{index}", use_container_width=True,
                                         type="secondary"):
                                new_pwd_hash = hashlib.sha256('123456'.encode()).hexdigest()
                                if update_user_field(user_name, 'password_hash', new_pwd_hash):
                                    add_audit_log(current_admin, f"账户管理：重置 [{user_name}] 鉴权口令", "✅ 执行成功")
                                    st.toast("✅ 密码已重置为 123456，用户可立即使用新密码登录。")
                                    time.sleep(1)
                                    st.rerun()

                            if "Admin" in role:
                                if st.button("⬇️ 降级为普通用户", key=f"d_{user_name}_{index}",
                                             use_container_width=True, type="secondary"):
                                    admin_count = df_users['Role'].apply(lambda x: 'Admin' in str(x)).sum()
                                    if "Super Admin" in role or str(user_name).lower() in ["admin", "admin27"]:
                                        st.error("内置超管账号享有底层保护，不可降级！")
                                    elif admin_count <= 1:
                                        st.error("⚠️ 操作失败：系统必须至少保留一位管理员！")
                                    else:
                                        if update_user_field(user_name, 'role', '👤 User'):
                                            add_audit_log(current_admin, f"权限变更：将账户 [{user_name}] 降权为 User",
                                                          "✅ 降权成功")
                                            st.toast(f"✅ [{user_name}] 已降级为普通用户。")
                                            time.sleep(1)
                                            st.rerun()
                            else:
                                if st.button("⬆️ 升级为管理员", key=f"up_{user_name}_{index}", use_container_width=True,
                                             type="primary"):
                                    if update_user_field(user_name, 'role', '👑 Admin'):
                                        add_audit_log(current_admin, f"权限变更：将账户 [{user_name}] 提权为 Admin",
                                                      "✅ 提权成功")
                                        st.toast(f"✅ [{user_name}] 已升级为管理员。")
                                        time.sleep(1)
                                        st.rerun()

                    divider_html = "<hr style='margin: 8px 0 8px 0; border: none; border-bottom: 1px dashed rgba(255,255,255,0.5);'>"
                    st.markdown(divider_html.replace('\n', ' '), unsafe_allow_html=True)

        # ------------------ Tab 3: 系统运维与空间清理 ------------------
        with tab3:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # ====== 核心修复：实时精准计算【真正可清理的冗余文件】数量 ======
            redundant_history_cnt = 0
            redundant_avatar_cnt = 0

            # 1. 计算真实的废弃历史图 (深度遍历所有子文件夹，并排除受保护的最新记录)
            protected_imgs = set()
            if HISTORY_JSON_PATH and os.path.exists(HISTORY_JSON_PATH):
                try:
                    with open(HISTORY_JSON_PATH, 'r', encoding='utf-8') as f:
                        history_data = json.load(f)
                    from collections import defaultdict
                    user_records = defaultdict(list)
                    for r in history_data:
                        user_records[r.get("user_id", "unknown")].append(r)
                    for uid, records in user_records.items():
                        records.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
                        for r in records[:30]:  # 与底层的保留前30条逻辑对齐
                            if r.get("img_path"):
                                protected_imgs.add(os.path.basename(r["img_path"]))
                except Exception:
                    pass

            if HISTORY_DIR and os.path.exists(HISTORY_DIR):
                for root, dirs, files in os.walk(HISTORY_DIR):  # 穿透子文件夹扫描
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            if file not in protected_imgs:
                                redundant_history_cnt += 1

            # 2. 计算真实的废弃头像 (深度遍历，排除当前所有用户正在使用的头像)
            protected_avatars = set()
            if USERS_PROFILE_JSON_PATH and os.path.exists(USERS_PROFILE_JSON_PATH):
                try:
                    with open(USERS_PROFILE_JSON_PATH, 'r', encoding='utf-8') as f:
                        users_profile = json.load(f)
                    for uid, profile in users_profile.items():
                        if profile.get("avatar"):
                            protected_avatars.add(os.path.basename(profile["avatar"]))
                except Exception:
                    pass

            if AVATARS_DIR and os.path.exists(AVATARS_DIR):
                for root, dirs, files in os.walk(AVATARS_DIR):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            if file not in protected_avatars:
                                redundant_avatar_cnt += 1
            # =========================================================

            mc1, mc2 = st.columns(2, gap="large")

            with mc1:
                card1_html = (
                    '<div class="ops-card-premium">'
                    '<div class="ops-header">'
                    '<div class="ops-icon">💾</div>'
                    '<div class="ops-title">历史文件与磁盘清理</div>'
                    '</div>'
                    '<div class="ops-desc">智能扫描并清理超过保留期限的历史测算图片，以及用户更换后遗留的废弃头像。此操作安全可靠，绝不影响前台用户的正常记录展示。</div>'
                    f'<div class="ops-stats-pill">可释放空间：废弃历史图 {redundant_history_cnt} 张 &nbsp;|&nbsp; 废弃头像 {redundant_avatar_cnt} 张</div>'
                    '</div>'
                )
                st.markdown(card1_html, unsafe_allow_html=True)

                if st.button("✨ 一键安全清理冗余文件", use_container_width=True, type="primary"):
                    del_imgs, del_avatars = perform_smart_cleanup()
                    add_audit_log(current_admin, f"磁盘运维：清理过期历史测算图 {del_imgs} 张，废弃头像 {del_avatars} 张",
                                  "✅ 清理成功")
                    st.toast(f"✅ 清理完成！已释放过期测算图 {del_imgs} 张，废弃头像 {del_avatars} 张。")
                    time.sleep(1.5)
                    st.rerun()

            with mc2:
                # 动态获取系统的缓存清理状态
                last_clear_time = st.session_state.get("last_cache_clear_time", None)

                if last_clear_time:
                    # 清理后的健康绿色状态
                    pill_style = "background: rgba(46, 204, 113, 0.12); color: #27ae60; border: 1px solid rgba(46, 204, 113, 0.3);"
                    pill_text = f"🟢 状态极佳 | 上次释放：{last_clear_time}"
                else:
                    # 默认的活跃占用警告状态
                    pill_style = "background: rgba(229, 152, 155, 0.12); color: #B56576; border: 1px solid rgba(229, 152, 155, 0.3);"
                    pill_text = "🟡 系统状态：应用缓存处于活跃占用中"

                card2_html = (
                    '<div class="ops-card-premium">'
                    '<div class="ops-header">'
                    '<div class="ops-icon">⚡</div>'
                    '<div class="ops-title">运行内存与缓存释放</div>'
                    '</div>'
                    '<div class="ops-desc">一键清空系统长时间运行积累的页面缓存与计算残留。当您感觉网页加载缓慢或卡顿时，点击此按钮可迅速释放占用，恢复系统巅峰流畅度。</div>'
                    f'<div class="ops-stats-pill" style="{pill_style}">{pill_text}</div>'
                    '</div>'
                )
                st.markdown(card2_html, unsafe_allow_html=True)

                if st.button("🚀 一键释放系统运行内存", use_container_width=True, type="secondary"):
                    # 真实执行底层的缓存清理指令
                    st.cache_data.clear()
                    st.cache_resource.clear()

                    # 记录清理完成的时间，并写入会话状态触发 UI 更新
                    current_time = datetime.now().strftime("%H:%M:%S")
                    st.session_state.last_cache_clear_time = current_time

                    add_audit_log(current_admin, "内存运维：手动释放系统页面及运行计算缓存", "✅ 释放成功")
                    st.toast("✅ 释放成功！系统缓存已清空，平台运行更加流畅。")
                    time.sleep(1)  # 稍微停顿让提示框歇一会儿
                    st.rerun()  # 立即强制刷新页面，让绿色的极速状态生效

    # ------------------ Tab 4: 审计日志 ------------------
    with tab4:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        real_logs = load_audit_logs()
        df_logs = pd.DataFrame(real_logs) if real_logs else pd.DataFrame()

        log_col1, log_col2 = st.columns([5, 1.5], vertical_alignment="center")
        with log_col1:
            log_title1 = '<div style="font-size: 18px; font-weight: 800; color: #355070; margin-bottom: 5px;">📝 系统合规审计记录</div>'
            log_title2 = '<div style="font-size: 13px; color: #8D99AE; margin-bottom: 15px;">记录系统核心管控操作，保障数据安全与溯源 (展示最近 100 条)</div>'
            st.markdown(log_title1.replace('\n', ' '), unsafe_allow_html=True)
            st.markdown(log_title2.replace('\n', ' '), unsafe_allow_html=True)

        with log_col2:
            if not df_logs.empty:
                st.download_button(
                    "📥 导出合规日志 (.csv)",
                    data=df_logs.to_csv(index=False).encode('utf-8-sig'),
                    file_name=f"system_audit_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="secondary"
                )

        if df_logs.empty:
            st.info("系统提示：当前暂无任何审计日志记录。")
        else:
            st.dataframe(df_logs, use_container_width=True, hide_index=True, height=450)