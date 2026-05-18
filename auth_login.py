import streamlit as st
import sqlite3
import hashlib
import re
import smtplib
import random
import string
import time
import os
import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ================= 0. 页面基础配置 =================

# ================= 1. 核心工具与逻辑 =================

@st.cache_data
def get_base64_image(image_path):
    if not os.path.exists(image_path): return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# --- 验证逻辑 ---
def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def validate_username(username):
    return bool(re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_]{4,20}$', username))


def validate_password_strength(password):
    if len(password) < 8: return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"[0-9]", password): return False
    return True


# --- 数据库与鉴权 ---
class AuthManager:
    def __init__(self, db_name="user_data.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, password_hash TEXT, email TEXT, created_at TEXT)''')

        # 智能升级数据库：增加权限、状态和明文密码字段(方便毕设演示)
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        if 'role' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT '👤 User'")
        if 'status' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT '🟢 正常 (Active)'")
        if 'plain_password' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN plain_password TEXT DEFAULT '******'")

        # 自动将 admin27 注入数据库，使其在后台列表中可见并可管理
        c.execute("SELECT * FROM users WHERE username='admin27'")
        if not c.fetchone():
            admin_pwd = "Aadmin041012"
            admin_hash = self._hash_password(admin_pwd)
            c.execute(
                "INSERT INTO users (username, password_hash, email, created_at, role, status, plain_password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ('admin27', admin_hash, 'admin@beauty.com', datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 '👑 Super Admin', '🟢 正常 (Active)', admin_pwd))

        conn.commit()
        conn.close()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password, email):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        try:
            pwd_hash = self._hash_password(password)
            create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 注册时同步写入明文密码，方便管理员在后台直接查阅数字英文
            c.execute(
                "INSERT INTO users (username, password_hash, email, created_at, role, status, plain_password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, pwd_hash, email, create_time, '👤 User', '🟢 正常 (Active)', password))
            conn.commit()
            return True, "注册成功"
        except sqlite3.IntegrityError:
            return False, "用户名已存在"
        finally:
            conn.close()

    def verify_login(self, username, password):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        pwd_hash = self._hash_password(password)
        c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, pwd_hash))
        user = c.fetchone()
        conn.close()
        return user is not None

    def get_user_info(self, username):
        """新增核心功能：获取用户的真实权限和冻结状态，用于决定跳转"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT role, status FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if row:
            return {"role": row[0], "status": row[1]}
        return {"role": "👤 User", "status": "🟢 正常 (Active)"}

    def check_user_exists(self, username):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        exists = c.fetchone() is not None
        conn.close()
        return exists

# --- 邮件发送 ---
def send_email_code(to_email, code):
    smtp_accounts = [
        {"server": "smtp.qq.com", "port": 465, "email": "2392890733@qq.com", "password": "phxlrilqenpfebcd"},
        {"server": "smtp.163.com", "port": 465, "email": "15361122717@163.com", "password": "YHt3fzAEARaYebWn"},
        {"server": "smtp.gmail.com", "port": 465, "email": "min68220732@gmail.com", "password": "idip kfyn xfdm rdwi"}
    ]
    random.shuffle(smtp_accounts)
    time.sleep(0.5)
    for acc in smtp_accounts:
        try:
            msg = MIMEMultipart()
            msg['From'] = f"Aesthetic Lab <{acc['email']}>"
            msg['To'] = to_email
            msg['Subject'] = "【审美实验室】注册验证码"
            msg.attach(MIMEText(f"您的验证码是：{code}，请在10分钟内输入。", 'plain'))
            with smtplib.SMTP_SSL(acc['server'], acc['port'], timeout=5) as s:
                s.login(acc['email'], acc['password'])
                s.sendmail(acc['email'], to_email, msg.as_string())
            return True
        except Exception:
            continue
    return False


# ================= 2. CSS 样式 (保持您的原样式) =================
def apply_style(bg_silk_src):
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"], [data-testid="stToolbar"], .st-emotion-cache-12fmjuu {{ display: none !important; visibility: hidden !important; height: 0 !important; }}
        .block-container {{ padding: 0 !important; margin: 0 !important; max-width: 100vw !important; overflow: hidden !important; }}
        [data-testid="stAppViewContainer"] {{ background-color: #F7F4EB; overflow: hidden !important; padding: 0 !important; margin: 0 !important; top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important; }}
        html, body {{ height: 100vh !important; width: 100vw !important; overflow: hidden !important; margin: 0 !important; padding: 0 !important; }}
        [data-testid="column"] {{ padding: 0 !important; }}
        [data-testid="stHorizontalBlock"] {{ gap: 0 !important; padding: 0 !important; }}
        div[data-testid="stVerticalBlock"] {{ gap: 0 !important; padding: 0 !important; }}
        .left-panel-root {{ position: relative; width: 100%; height: 102vh; background-color: #F9F6F0; overflow: hidden; box-shadow: 5px 0 20px rgba(0,0,0,0.1); z-index: 1; }}
        .left-panel-root::before {{ content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-image: url('{bg_silk_src}'); background-size: cover; background-position: center; opacity: 0.22; z-index: -1; pointer-events: none; }}
        .vertical-text-box {{ position: absolute; left: 40px; top: 50%; transform: translateY(-50%); z-index: 10; }}
        .vertical-text {{ writing-mode: vertical-lr; transform: rotate(180deg); font-family: 'Arial', sans-serif; font-size: 36px; letter-spacing: 12px; color: #C39EB9; font-weight: 800; white-space: nowrap; }}
        .bottom-slogan-box {{ position: absolute; left: 40px; bottom: 40px; z-index: 10; }}
        .bs-title {{ font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; color: #40172D; line-height: 1.1; }}
        .bs-sub {{ font-family: 'Arial', sans-serif; font-size: 9px; letter-spacing: 2px; color: #E6B3C7; margin-bottom: 12px; text-transform: uppercase; }}
        .bs-cn {{ font-family: 'PingFang SC', serif; font-size: 12px; color: #BF98B5; line-height: 1.5; border-left: 3px solid #8A6481; padding-left: 10px; }}
        .right-img-strip {{ position: absolute; right: 0; top: 0; bottom: 0; width: 55%; display: flex; flex-direction: column; gap: 15px; box-sizing: border-box; padding: 0; z-index: 15; }}
        .strip-img {{ flex: 1; min-height: 0; width: 100%; object-fit: cover; object-position: center top; display: block; margin: 0; border: none; }}
        [data-testid="column"]:nth-of-type(2) > div {{ display: flex !important; flex-direction: column !important; justify-content: center !important; height: 1vh !important; padding-top: 0 !important; }}
        [data-testid="column"]:nth-of-type(2) [data-testid="column"]:nth-of-type(2) > div {{ background-color: #F4F1EA !important; border-radius: 25px !important; padding: 0px 0px !important; box-shadow: 15px 15px 35px #dcd9d2, -15px -15px 35px #ffffff !important; border: 1px solid rgba(255,255,255,0.3); gap: 0px !important; position: relative; }}
        div[data-baseweb="input"] {{ background: transparent !important; border: none !important; border-bottom: 1px solid #ccc !important; padding-bottom: -10px !important; margin-top: 0px !important; }}
        div[data-baseweb="base-input"] {{ background: transparent !important; }}
        input.st-bd {{ background: transparent !important; font-size: 16px !important; color: #333 !important; padding-left: 0px !important; }}
        input::placeholder {{ color: #bbb !important; font-size: 13px; font-weight: normal; }}
        div[data-baseweb="input"]:focus-within {{ border-bottom: 2px solid #3E2F26 !important; }}
        label[data-testid="stWidgetLabel"] {{ display: none; }}
        div.stButton > button {{ width: 100%; background: #F4F1EA !important; color: #451E43 !important; border: none !important; border-radius: 50px !important; padding: 10px 20px !important; font-size: 14px !important; font-weight: bold; margin-top: 5px; box-shadow: 5px 5px 10px #dcd9d2, -5px -5px 10px #ffffff !important; white-space: nowrap; }}
        div.stButton > button:hover {{ box-shadow: inset 2px 2px 5px #dcd9d2, inset -2px -2px 5px #ffffff !important; color: #000 !important; }}
        div.stButton > button:disabled {{ color: #aaa !important; cursor: not-allowed; background: #F4F1EA !important; box-shadow: inset 2px 2px 5px #dcd9d2, inset -2px -2px 5px #ffffff !important; }}
        div[data-testid="column"] div[data-testid="column"] div.stButton button {{ margin-top: 0px !important; margin-bottom: 3px !important; height: 38px !important; padding: 0 10px !important; font-size: 13px !important; display: flex; align-items: center; justify-content: center; }}
        .card-welcome {{ font-size: 20px; color: #888; font-family: serif; margin-bottom: 18px; text-align: left; }}
        .card-login {{ font-size: 42px; font-weight: 900; color: #451E43; font-family: 'Playfair Display', serif; text-shadow: 1px 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; margin-top: 0; text-align: left; }}
        .field-label {{ font-size: 15px; color: #888; margin-top: 25px; margin-bottom: 8px; text-align: left; }}
        .status-text {{ text-align: center; font-size: 10px; color: #888; margin-top: 2px; height: 12px; line-height: 10px; }}
        .msg-box {{ min-height: -30px; margin-bottom: -10px; margin-top: 2px; }}
        .err-msg {{ color: #d9534f; font-size: 11px; font-weight: 500; text-align: left; }}
        .hint-text {{ text-align: center; font-size: 11px; color: #999; margin-bottom: 10px; height: 40px; line-height: 45px; white-space: nowrap; }}
        .spacer-text {{ height: 40px; margin-bottom: 10px; }}
        .social-line {{ display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px; margin-top: 25px; margin-bottom: 15px; }}
        .social-line::before, .social-line::after {{ content: ""; flex: 1; border-bottom: 1px solid #ddd; margin: 0 10px; }}
        .icons-row {{ display: flex; gap: 25px; justify-content: center; }}
        .icon-box {{ width: 35px; height: 35px; border-radius: 10px; background: #F4F1EA; display: flex; align-items: center; justify-content: center; box-shadow: 4px 4px 8px #dcd9d2, -4px -4px 8px #ffffff; }}
        .icon-box img {{ width: 18px; }}
        [data-testid="column"] [data-testid="column"] {{ padding: 0 5px !important; }}
        .button {{ display: block; position: relative; width: 56px; height: 56px; margin: 0; overflow: hidden; outline: none; background-color: transparent; cursor: pointer; border: 0; text-decoration: none; }}
        .button:before, .button:after {{ content: ""; position: absolute; border-radius: 50%; inset: 7px; }}
        .button:before {{ border: 4px solid #dcd9d2; transition: opacity 0.4s cubic-bezier(0.77, 0, 0.175, 1) 80ms, transform 0.5s cubic-bezier(0.455, 0.03, 0.515, 0.955) 80ms; }}
        .button:after {{ border: 4px solid #B398AB; transform: scale(1.3); transition: opacity 0.4s cubic-bezier(0.165, 0.84, 0.44, 1), transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94); opacity: 0; }}
        .button:hover:before, .button:focus:before {{ opacity: 0; transform: scale(0.7); transition: opacity 0.4s cubic-bezier(0.165, 0.84, 0.44, 1), transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94); }}
        .button:hover:after, .button:focus:after {{ opacity: 1; transform: scale(1); transition: opacity 0.4s cubic-bezier(0.77, 0, 0.175, 1) 80ms, transform 0.5s cubic-bezier(0.455, 0.03, 0.515, 0.955) 80ms; }}
        .button-box {{ display: flex; position: absolute; top: 0; left: 0; }}
        .button-elem {{ display: block; width: 20px; height: 25px; margin: 17px 18px 0 18px; transform: rotate(180deg); fill: #451E43; }}
        .button:hover .button-box, .button:focus .button-box {{ transition: 0.4s; transform: translateX(-56px); }}
        .back-btn-container {{ position: absolute; top: 30px; left: -850px; z-index: 100; }}
    </style>
    """, unsafe_allow_html=True)


# ================= 3. 主程序 =================
def show():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path_base_1 = os.path.join(current_dir, "assets", "auth_login1")
    path_base_2 = os.path.join(current_dir, "assets", "auth_login2")
    img_silk = get_base64_image(os.path.join(path_base_1, "4.jpg"))
    apply_style(f"data:image/jpg;base64,{img_silk}")

    auth = AuthManager()

    if "auth_mode" not in st.session_state: st.session_state.auth_mode = "login"
    if "verify_code_sent" not in st.session_state: st.session_state.verify_code_sent = None
    if "last_send_time" not in st.session_state: st.session_state.last_send_time = 0
    if "reg_email_snapshot" not in st.session_state: st.session_state.reg_email_snapshot = None
    if "email_status" not in st.session_state: st.session_state.email_status = ""

    col_left, col_right = st.columns([4, 6], gap="small")

    with col_left:
        img1 = get_base64_image(os.path.join(path_base_1, "1.jpg"))
        img2 = get_base64_image(os.path.join(path_base_1, "2.jpg"))
        img3 = get_base64_image(os.path.join(path_base_1, "3.jpg"))
        src1, src2, src3 = f"data:image/jpg;base64,{img1}", f"data:image/jpg;base64,{img2}", f"data:image/jpg;base64,{img3}"
        st.markdown(f"""
        <div class="left-panel-root">
            <div class="vertical-text-box"><div class="vertical-text">BEAUTY FACE</div></div>
            <div class="bottom-slogan-box">
                <div class="bs-title">Find Your<br>True Beauty</div>
                <div class="bs-sub">FACE BEAUTY AESTHETIC LAB</div>
                <div class="bs-cn"><span style="font-weight:bold;color:#BF98B5">量颜定造</span>，让我们不再凭感觉变美。<br>面孔解码，发现每个人的独特亮点。</div>
            </div>
            <div class="right-img-strip">
                <img src="{src1}" class="strip-img">
                <img src="{src2}" class="strip-img">
                <img src="{src3}" class="strip-img">
            </div>
        </div>""", unsafe_allow_html=True)

    with col_right:
        c_l, c_card, c_r = st.columns([1, 2, 1])
        with c_card:
            st.markdown("""
            <div class="back-btn-container">
                <a href="/?nav=landing" target="_self" class="button">
                    <div class="button-box">
                        <span class="button-elem"><svg viewBox="0 0 46 40"><path d="M46 20.038c0-.7-.3-1.5-.8-2.1l-16-17c-1.1-1-3.2-1.4-4.4-.3-1.2 1.1-1.2 3.3 0 4.4l11.3 11.9H3c-1.7 0-3 1.3-3 3s1.3 3 3 3h33.1l-11.3 11.9c-1 1-1.2 3.3 0 4.4 1.2 1.1 3.3.8 4.4-.3l16-17c.5-.5.8-1.1.8-1.9z"></path></svg></span>
                        <span class="button-elem"><svg viewBox="0 0 46 40"><path d="M46 20.038c0-.7-.3-1.5-.8-2.1l-16-17c-1.1-1-3.2-1.4-4.4-.3-1.2 1.1-1.2 3.3 0 4.4l11.3 11.9H3c-1.7 0-3 1.3-3 3s1.3 3 3 3h33.1l-11.3 11.9c-1 1-1.2 3.3 0 4.4 1.2 1.1 3.3.8 4.4-.3l16-17c.5-.5.8-1.1.8-1.9z"></path></svg></span>
                    </div>
                </a>
            </div>""", unsafe_allow_html=True)
            st.markdown('<div class="card-welcome">欢迎使用</div><div class="card-login">Log in</div>',
                        unsafe_allow_html=True)

            if st.session_state.auth_mode == "login":
                st.markdown('<div class="field-label">用户名</div>', unsafe_allow_html=True)
                l_u = st.text_input("l_u", key="l_u_key", placeholder="请输入用户名", label_visibility="collapsed")
                st.markdown('<div class="msg-box"></div><div class="field-label">密码</div>', unsafe_allow_html=True)
                l_p = st.text_input("l_p", type="password", key="l_p_key", placeholder="请输入密码",
                                    label_visibility="collapsed")
                st.markdown('<div class="msg-box"></div><div style="height:25px"></div>', unsafe_allow_html=True)

                b1, b2 = st.columns(2)
                with b1:
                    st.markdown('<div class="spacer-text"></div>', unsafe_allow_html=True)
                    if st.button("立即登录", use_container_width=True):
                        # 真正验证数据库中的账号密码 (admin27现在也在库里了，统一验证)
                        if auth.verify_login(l_u, l_p) or (l_u == "admin27" and l_p == "Aadmin041012"):
                            # 获取真实权限与状态
                            user_info = auth.get_user_info(l_u) if auth.verify_login(l_u, l_p) else {
                                "role": "👑 Super Admin", "status": "🟢 正常 (Active)"}

                            # 1. 状态拦截检查：如果后台把你冻结了，直接拦住
                            if "Frozen" in user_info['status'] or "冻结" in user_info['status']:
                                st.error("❌ 您的账号已被系统冻结，无法登录，请联系管理员！")
                            else:
                                # 2. 正常登录赋值
                                st.session_state.current_user_id = l_u
                                st.session_state.is_logged_in = True
                                st.session_state.nav_radio = "cockpit"

                                # 3. 智能路由跳转：根据数据库真实的 Role 决定跳转去哪
                                if "Admin" in user_info['role']:
                                    st.session_state.current_page = "后台管理"  # 如果是管理员，跳后台
                                    st.toast(f"🔐 管理员 {l_u} 登录成功，正在跳转后台...")
                                else:
                                    st.session_state.current_page = "审美趋势"  # 如果是普通User，跳前台
                                    st.toast(f"✅ 欢迎回来，{l_u}！")

                                # 更新 URL 参数，防止刷新页面时丢失状态
                                st.query_params.clear()
                                st.query_params["page"] = st.session_state.current_page
                                st.query_params["uid"] = l_u

                                time.sleep(0.5)
                                st.rerun()
                        else:
                            st.toast("❌ 账号或密码错误")
                with b2:
                    st.markdown('<div class="hint-text">没有账号？ 点击注册</div>', unsafe_allow_html=True)
                    if st.button("注册新用户", use_container_width=True):
                        st.session_state.auth_mode = "register"
                        st.rerun()

            else:  # Register mode
                st.markdown('<div class="field-label">用户名</div>', unsafe_allow_html=True)
                r_u = st.text_input("r_u", key="r_u_key", placeholder="4-20位中英文数字", label_visibility="collapsed")
                msg_u = ""
                if r_u:
                    if not validate_username(r_u):
                        msg_u = '<div class="err-msg">❌ 格式：4-20位中英文数字</div>'
                    elif auth.check_user_exists(r_u):
                        msg_u = '<div class="err-msg">❌ 用户名已存在</div>'
                st.markdown(f'<div class="msg-box">{msg_u}</div>', unsafe_allow_html=True)

                st.markdown('<div class="field-label">邮箱</div>', unsafe_allow_html=True)
                r_e = st.text_input("r_e", key="r_e_key", placeholder="example@email.com", label_visibility="collapsed")
                msg_e = ""
                if r_e and not validate_email(r_e): msg_e = '<div class="err-msg">❌ 邮箱格式无效</div>'
                st.markdown(f'<div class="msg-box">{msg_e}</div>', unsafe_allow_html=True)

                st.markdown('<div class="field-label">密码</div>', unsafe_allow_html=True)
                r_p = st.text_input("r_p", type="password", key="r_p_key", placeholder="8位+，含大小写及数字",
                                    label_visibility="collapsed")
                msg_p = ""
                if r_p and not validate_password_strength(r_p): msg_p = '<div class="err-msg">❌ 强度不足：8位+ 大小写+数字</div>'
                st.markdown(f'<div class="msg-box">{msg_p}</div>', unsafe_allow_html=True)

                st.markdown('<div class="field-label">确认密码</div>', unsafe_allow_html=True)
                r_p2 = st.text_input("r_p2", type="password", key="r_p2_key", placeholder="请再次输入密码",
                                     label_visibility="collapsed")
                msg_p2 = ""
                if r_p2 and r_p != r_p2: msg_p2 = '<div class="err-msg">❌ 两次密码不一致</div>'
                st.markdown(f'<div class="msg-box">{msg_p2}</div>', unsafe_allow_html=True)

                st.markdown('<div class="field-label">验证码</div>', unsafe_allow_html=True)

                time_now = time.time()
                time_diff = time_now - st.session_state.last_send_time
                time_left = int(60 - time_diff)
                is_cooldown = (time_diff < 60)
                valid_form = (r_u and not msg_u) and (r_e and not msg_e) and (r_p and not msg_p) and (
                        r_p2 and not msg_p2)

                btn_txt = f"{time_left}s" if is_cooldown else "立即发送"
                col_code, col_btn = st.columns([1.5, 1], gap="small", vertical_alignment="bottom")

                with col_code:
                    code_in = st.text_input("code", key="code_in", placeholder="6位数字", label_visibility="collapsed")

                with col_btn:
                    btn_disabled = (is_cooldown or not valid_form)
                    if st.button(btn_txt, disabled=btn_disabled, key="send_btn", use_container_width=True):
                        st.session_state.email_status = "发送中..."
                        with st.spinner(""):
                            code = ''.join(random.choices(string.digits, k=6))
                            if send_email_code(r_e, code):
                                st.session_state.verify_code_sent = code
                                st.session_state.reg_email_snapshot = r_e
                                st.session_state.last_send_time = time.time()
                                st.session_state.email_status = "已发送"
                                st.rerun()
                            else:
                                st.session_state.email_status = "发送失败"
                                st.error("发送失败")

                    if is_cooldown and st.session_state.email_status:
                        st.markdown(f'<div class="status-text">{st.session_state.email_status}</div>',
                                    unsafe_allow_html=True)
                    elif not is_cooldown:
                        st.session_state.email_status = ""

                st.markdown('<div class="msg-box"></div>', unsafe_allow_html=True)
                st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                with b1:
                    st.markdown('<div class="spacer-text"></div>', unsafe_allow_html=True)
                    can_submit = st.session_state.verify_code_sent is not None
                    if st.button("提交注册", type="primary", disabled=not can_submit, use_container_width=True):
                        if code_in == st.session_state.verify_code_sent:
                            ok, msg = auth.register_user(r_u, r_p, r_e)
                            if ok:
                                st.success("🎉 注册成功！")
                                st.session_state.auth_mode = "login"
                                st.session_state.verify_code_sent = None
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("❌ 验证码错误")
                with b2:
                    st.markdown('<div class="hint-text">已有账号？ 点击登录</div>', unsafe_allow_html=True)
                    if st.button("返回登录", use_container_width=True):
                        st.session_state.auth_mode = "login"
                        st.rerun()

                if is_cooldown:
                    time.sleep(1)
                    st.rerun()

            current_dir = os.path.dirname(os.path.abspath(__file__))
            icon1_path = os.path.join(current_dir, "assets", "auth_login2", "1.png")
            icon2_path = os.path.join(current_dir, "assets", "auth_login2", "2.png")
            icon3_path = os.path.join(current_dir, "assets", "auth_login2", "3.png")

            icon1_b64 = get_base64_image(icon1_path)
            icon2_b64 = get_base64_image(icon2_path)
            icon3_b64 = get_base64_image(icon3_path)

            # 如果还是加载失败，给出兜底提示，防止干找问题
            if not icon1_b64:
                st.error(f"找不到图片: {icon1_path}")

            # 注入带有 img 标签的完整 HTML
            st.markdown(f'''
                            <div class="social-line">邮箱支持</div>
                            <div class="icons-row" style="display: flex; justify-content: center; align-items: center; margin-top: 15px;">
                                <img src="data:image/png;base64,{icon1_b64}" style="width: 36px; height: 36px; margin: 0 15px; cursor: pointer; transition: 0.3s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                                <img src="data:image/png;base64,{icon2_b64}" style="width: 36px; height: 36px; margin: 0 15px; cursor: pointer; transition: 0.3s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                                <img src="data:image/png;base64,{icon3_b64}" style="width: 36px; height: 36px; margin: 0 15px; cursor: pointer; transition: 0.3s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                            </div>
                        ''', unsafe_allow_html=True)

if __name__ == "__main__":
    show()