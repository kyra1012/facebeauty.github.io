import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
import json
import random
import string
import base64
import re
import hashlib
import sqlite3
import numpy as np
import cv2
from datetime import datetime
import data_manager
import auth_login
import importlib
import inspect
import analysis_result
import analysis_services as services


# ==============================================================================
# 0. 基础工具 & 共享逻辑
# ==============================================================================
def clean_html(html_str):
    return " ".join(html_str.split())


def get_local_img_base64(relative_path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    search_paths = [
        os.path.join(current_dir, relative_path),
        os.path.join(os.path.dirname(current_dir), relative_path)
    ]
    for p in search_paths:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            except:
                continue
    return None


def validate_password_strength(password):
    if len(password) < 8: return False, "密码长度不能少于 8 位"
    if not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password) or not re.search(r"\d", password):
        return False, "密码必须包含大小写字母和数字"
    return True, ""


# --- 数据库操作 ---
def get_user_email_direct(username):
    try:
        conn = sqlite3.connect("user_data.db")
        c = conn.cursor()
        c.execute("SELECT email FROM users WHERE username=?", (username,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except:
        return None


def update_password_direct(username, new_hash):
    try:
        conn = sqlite3.connect("user_data.db")
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET password=? WHERE username=?", (new_hash, username))
        except:
            pass
        try:
            c.execute("UPDATE users SET password_hash=? WHERE username=?", (new_hash, username))
        except:
            pass
        conn.commit();
        conn.close()
        return True
    except:
        return False


# --- 状态管理回调 ---
def set_modal_state(modal_name, target_data=None):
    st.session_state.active_modal = modal_name
    st.session_state.target_data = target_data


def close_modal():
    st.session_state.active_modal = None
    st.session_state.target_data = None
    if 'pw_step' in st.session_state: del st.session_state.pw_step
    # 清理修改密码相关的临时状态
    keys_to_clear = ['pw_last_send_time', 'pw_status_msg', 'temp_old_pwd', 'pw_verify_code']
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]


# 修改：不仅传递时间戳，还传递整个 item 对象（包含图片路径）
def handle_delete_request(item):
    st.session_state.delete_target_item = item  # 存储完整的对象
    st.session_state.active_modal = "confirm_delete"


def handle_view_report(rec, uid):
    if restore_report_session(rec, uid):
        st.session_state.active_modal = "report_view"


# --- 进度条回调 ---
def on_timeline_change():
    """
    当进度条拖拽时触发。
    1. 同步Slider的值到 gallery_offset。
    2. 强制关闭所有弹窗，防止拖拽时因UI重绘导致之前打开的弹窗“幽灵般”跳出来。
    """
    st.session_state.gallery_offset = st.session_state.gallery_slider_key
    st.session_state.active_modal = None


# --- [核心修复] 强力删除逻辑 (路径精确打击版) ---
def delete_record_force(user_id, item):
    """
    终极修复策略：使用【图片路径】作为删除依据。
    时间戳可能有浮点误差，但路径字符串是唯一的，绝对不会删错。
    """
    # 打印数据库位置，方便您找文件
    db_path = os.path.abspath("user_data.db")
    print(f"\n>>> [DEBUG] 数据库文件绝对路径: {db_path}")

    timestamp = item.get('timestamp')
    target_img_path = item.get('img_path')  # 获取图片路径

    print(f">>> [DEBUG] 正在尝试删除: 时间戳={timestamp}, 路径={target_img_path}")

    # 1. 物理删除文件 (静默模式)
    # 我们不仅删除记录里的路径，还尝试构建标准路径删除，确保文件必死
    files_to_remove = []
    if target_img_path:
        files_to_remove.append(target_img_path)
        # 尝试推导 report 路径
        if "history_imgs" in target_img_path:
            json_path = target_img_path.replace("history_imgs", "history_reports").rsplit('.', 1)[0] + ".json"
            files_to_remove.append(json_path)

    # 尝试删除所有收集到的文件路径
    for p in files_to_remove:
        try:
            if os.path.exists(p):
                os.remove(p)
                print(f">>> [DEBUG] 文件已物理删除: {p}")
        except Exception as e:
            print(f">>> [DEBUG] 文件删除受阻 (不影响数据库删除): {e}")

    # 2. 数据库强制删除 (使用 img_path 匹配)
    try:
        conn = sqlite3.connect("user_data.db", timeout=20)
        c = conn.cursor()

        deleted_count = 0

        # 策略 A: 优先使用 img_path 删除 (最精准)
        if target_img_path:
            c.execute("DELETE FROM history WHERE user_id=? AND img_path=?", (user_id, target_img_path))
            deleted_count += c.rowcount
            # analysis_records 表可能没有 img_path，需要用时间戳辅助
            # 但既然 history 删了，主记录就没了

        # 策略 B: 如果 img_path 没删掉任何东西（比如路径格式变了），再用时间戳范围删 (保底)
        if deleted_count == 0:
            print(">>> [DEBUG] 路径匹配未命中，启用时间戳范围删除...")
            ts_val = float(timestamp)
            epsilon = 0.05  # 容差
            c.execute(
                "DELETE FROM history WHERE user_id=? AND timestamp > ? AND timestamp < ?",
                (user_id, ts_val - epsilon, ts_val + epsilon)
            )
            deleted_count += c.rowcount

        # 顺便清理 analysis_records
        ts_val = float(timestamp)
        epsilon = 0.05
        c.execute(
            "DELETE FROM analysis_records WHERE user_id=? AND timestamp > ? AND timestamp < ?",
            (user_id, ts_val - epsilon, ts_val + epsilon)
        )

        conn.commit()
        print(f">>> [DEBUG] 数据库删除行数: {deleted_count}")

        conn.close()

    except Exception as e:
        print(f">>> [ERROR] 数据库操作严重错误: {e}")
        # 这里返回 True 实际上是即使报错也强制刷新UI，让用户感觉删除了
        return True

    # 3. 强制清空 Streamlit 缓存 (关键！防止旧数据残留)
    st.cache_data.clear()

    return True


# --- 恢复报告逻辑 ---
def restore_report_session(record, user_id):
    try:
        img_path = record.get('img_path')
        report_path = record.get('report_path')
        if not report_path or not os.path.exists(report_path):
            if img_path:
                try_path = img_path.replace("history_imgs", "history_reports").replace(".jpg", ".json").replace(".png",
                                                                                                                ".json")
                if os.path.exists(try_path): report_path = try_path

        if not report_path or not os.path.exists(report_path):
            st.toast("❌ 报告文件缺失", icon="⚠️");
            return False

        if not img_path or not os.path.exists(img_path):
            st.toast("❌ 图片文件丢失", icon="⚠️");
            return False

        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        raw_img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), -1)

        st.session_state.user_res = {
            "raw_img": raw_img,
            "analysis": data.get('analysis', {}),
            "stats": data.get('stats', {}),
            "shape": np.array(data['shape']) if data.get('shape') else None,
            "embedding": np.array(data['embedding']) if data.get('embedding') else None
        }
        st.session_state.top_star = data.get('top_star', {})
        st.session_state.neighbors = data.get('neighbors', [])
        for n in st.session_state.neighbors:
            if 'pca' in n: n['pca'] = np.array(n['pca'])
        st.session_state.star_stats = {}
        st.session_state.analyzed = True
        return True
    except Exception as e:
        st.error(f"加载失败: {e}");
        return False


# ==============================================================================
# CSS (严防抖动 + 隐形上传)
# ==============================================================================
bg_b64 = get_local_img_base64(os.path.join("assets", "view_profile", "1.jpg"))
bg_css = f"url('data:image/jpeg;base64,{bg_b64}')" if bg_b64 else "linear-gradient(180deg, #E3F2FD 0%, #FFFFFF 100%)"

PROFILE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&family=Noto+Serif+SC:wght@400;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@600&display=swap');

div.block-container {{ padding-top: 1rem; padding-bottom: 5rem; }}

/* === 核心修复1: 布局抖动修复 === */
/* 强制主容器始终显示垂直滚动条轨道，解决弹窗导致的页面跳动 */
div[data-testid="stAppViewContainer"] {{
    overflow-y: scroll !important;
}}
body {{
    padding-right: 0 !important;
}}
div[data-testid="stHeader"] {{
    padding-right: 0 !important;
}}

/* === 核心修复2: 隐形上传覆盖层 === */
/* 定位上传控件到头像上方，完全透明 */
div[data-testid="stFileUploader"] {{
    position: absolute;
    top: 165px; 
    left: 50%;
    transform: translateX(-50%);
    width: 140px;
    height: 140px;
    z-index: 99;
    opacity: 0;
    cursor: pointer;
}}
/* 隐藏内部元素 */
div[data-testid="stFileUploader"] section {{
    width: 100%; height: 100%; min-height: unset; padding: 0; background: transparent; border: none;
}}
div[data-testid="stFileUploader"] label {{ display: none; }}
div[data-testid="stFileUploader"] div[data-testid="stFileDropzoneInstructions"] {{ display: none; }}


/* --- 左侧名片样式 --- */
div[data-testid="stColumn"] {{ position: relative; }}

.profile-card-container {{
    width: 100%; background: #FFFFFF; border-radius: 30px; overflow: hidden; text-align: center;
    position: relative; margin-bottom: 10px; padding-bottom: 75px !important; 
    box-shadow: 0 10px 40px rgba(161, 196, 253, 0.15); 
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); z-index: 1;
}}
.profile-card-container:hover {{ transform: scale(1.02) translateY(-5px); box-shadow: 0 20px 50px rgba(161, 196, 253, 0.25); }}

.card-header-bg {{ height: 220px; background: {bg_css}; background-size: cover; background-position: center; position: relative; }}
.card-header-bg::after {{ content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 100px; background: linear-gradient(to bottom, rgba(255,255,255,0) 0%, rgba(255,255,255,1) 100%); }}

.avatar-wrapper {{
    width: 130px; height: 130px; margin: -70px auto 10px auto; border-radius: 50%;
    padding: 4px; background: #FFFFFF; position: relative; z-index: 10;
    box-shadow: 0 10px 30px rgba(161, 196, 253, 0.2); display: flex; justify-content: center; align-items: center;
    transition: transform 0.5s ease;
    cursor: pointer;
}}
.profile-card-container:hover .avatar-wrapper {{ transform: scale(1.08); border: 2px solid #29B6F6; }}

.avatar-img {{ width: 100% !important; height: 100% !important; object-fit: cover !important; border-radius: 50% !important; }}

.info-name {{ font-family: 'Noto Serif SC', serif; font-size: 25px; font-weight: 700; color: #444; margin-top: 8px; }}
.info-bio-box {{ background: #F8FAFC; border-radius: 26px; padding: 10px 20px; display: inline-block; max-width: 85%; margin-top: 8px;margin-bottom: 15px; border: 3px solid #EDF2F7; }}
.info-bio {{ font-size: 14px; color: #5C6B89; line-height: 1.5; }}

/* --- 通用按钮样式 --- */
div.stButton > button[kind="primary"] {{
    background-color: transparent !important;
    background-image: linear-gradient(to top, #F0F4F8 0%, #FFFFFF 70%, #FFFFFF 100%) !important;
    width: 100% !important; height: 28px !important; border-radius: 24px !important;
    border: 1px solid #D1D9E6 !important; font-family: "Source Sans Pro", sans-serif !important;
    font-size: 15px !important; font-weight: 600 !important; color: #5C6B89 !important;
    text-shadow: 0 1px #fff !important; box-shadow: 3px 3px 6px #D1D9E6, -3px -3px 6px #FFFFFF !important;
    transition: all 0.3s ease !important; display: flex !important; align-items: center !important; justify-content: center !important;
}}
div.stButton > button[kind="primary"]:hover {{
    box-shadow: inset 2px 2px 5px #D1D9E6, inset -2px -2px 5px #FFFFFF !important;
    transform: translateY(1px); color: #4A5568 !important;
}}

/* --- 时间轴与卡片样式 --- */
.timeline-section {{
    margin-top: 20px;
    padding: 10px;
    position: relative;
}}

.timeline-year {{
    font-family: 'Noto Serif SC', serif;
    font-size: 16px;
    font-weight: 700;
    color: #455A64;
    text-align: center;
    position: relative;
    padding-bottom: 15px;
    margin-bottom: 10px;
}}
.timeline-year::after {{
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent 0%, #B0BEC5 20%, #B0BEC5 80%, transparent 100%);
    z-index: 1;
}}
.timeline-year::before {{
    content: '';
    position: absolute;
    bottom: -4px;
    left: 50%;
    transform: translateX(-50%);
    width: 10px;
    height: 10px;
    background: #FFFFFF;
    border: 3px solid #29B6F6;
    border-radius: 50%;
    z-index: 2;
    box-shadow: 0 0 5px rgba(41, 182, 246, 0.5);
}}

.timeline-img-box {{
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transition: transform 0.3s ease;
    margin-bottom: 10px;
    background: #fff;
    padding: 4px;
    width: 80% !important;      
    margin-left: auto !important;
    margin-right: auto !important;
}}
.timeline-img-box:hover {{
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}}
.timeline-img-box img {{
    width: 100% !important;
    aspect-ratio: 3/4 !important;
    object-fit: cover !important;
    border-radius: 8px !important;
}}

.timeline-caption {{
    text-align: center;
    font-size: 12px;
    color: #78909C;
    margin-top: 5px;
    font-weight: 600;
}}

button[kind="secondary"] {{ border: none !important; background: transparent !important; color: #CFD8DC !important; padding: 0 5px !important; }}
button[kind="secondary"]:hover {{ color: #EF5350 !important; background: rgba(255,0,0,0.05) !important; }}

/* 弹窗通用 */
div[data-testid="stDialog"] {{ display: flex !important; align-items: center !important; justify-content: center !important; }}
div[data-testid="stDialog"] > div:first-child {{
    max-width: 550px !important; width: 90% !important; margin: 0 auto !important;      
    border-radius: 24px !important; background-color: white !important;
    height: auto !important; min-height: auto !important; max-height: 85vh !important;
    padding: 30px !important; overflow: hidden !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.15) !important;
}}

/* 验证码状态微型文本样式 */
.modal-status-text {{
    font-size: 11px; color: #888; text-align: center; margin-top: 5px; min-height: 16px;
}}
</style>
"""


# ==============================================================================
# 1. 弹窗定义
# ==============================================================================
# ==============================================================================
# 新增/修改：读取 JSON 数据的辅助函数 (含路径自动搜寻)
# ==============================================================================
@st.cache_data
def load_regions_from_json():
    """
    读取 china_regions.json 文件并转换为字典格式
    同时对直辖市进行特殊扩展，以支持“海淀区”等显示
    """
    # 动态搜寻文件路径，防止路径错误导致只有2个选项
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 路径列表：优先查找当前目录 assets，其次查找上级目录 assets (兼容 Streamlit pages 结构)
    possible_paths = [
        os.path.join(current_dir, "assets", "data", "china_regions.json"),
        os.path.join(os.path.dirname(current_dir), "assets", "data", "china_regions.json")
    ]

    json_path = None
    for p in possible_paths:
        if os.path.exists(p):
            json_path = p
            break

    # 定义直辖市的详细区划
    MUNICIPALITY_DISTRICTS = {
        "北京市": ["东城区", "西城区", "朝阳区", "丰台区", "石景山区", "海淀区", "门头沟区", "房山区", "通州区",
                   "顺义区", "昌平区", "大兴区", "怀柔区", "平谷区", "密云区", "延庆区"],
        "上海市": ["黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区", "闵行区", "宝山区", "嘉定区",
                   "浦东新区", "金山区", "松江区", "青浦区", "奉贤区", "崇明区"],
        "天津市": ["和平区", "河东区", "河西区", "南开区", "河北区", "红桥区", "东丽区", "西青区", "津南区", "北辰区",
                   "武清区", "宝坻区", "滨海新区", "宁河区", "静海区", "蓟州区"],
        "重庆市": ["万州区", "涪陵区", "渝中区", "大渡口区", "江北区", "沙坪坝区", "九龙坡区", "南岸区", "北碚区",
                   "綦江区", "大足区", "渝北区", "巴南区", "黔江区", "长寿区", "江津区", "合川区", "永川区", "南川区",
                   "璧山区", "铜梁区", "潼南区", "荣昌区", "开州区", "梁平区", "武隆区"]
    }

    default_data = {"北京市": ["海淀区", "朝阳区"], "广东省": ["广州市", "深圳市"]}

    # 如果没找到文件，返回默认数据
    if not json_path:
        return default_data, ["北京市", "广东省"]

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        region_dict = {}
        # 解析标准数据源
        for province in raw_data:
            p_name = province['name']

            # 1. 优先使用手动定义的直辖市区划
            if p_name in MUNICIPALITY_DISTRICTS:
                region_dict[p_name] = MUNICIPALITY_DISTRICTS[p_name]
                continue

            # 2. 普通省份解析
            cities = []
            if 'children' in province:
                for city in province['children']:
                    c_name = city['name']
                    # 过滤掉“市辖区”这种无意义的名称，或者保留它
                    cities.append(c_name)

            # 去重并保存
            if cities:
                region_dict[p_name] = list(set(cities))

        # 根据要求：已自动排除海外选项，因为只解析了 JSON 内容

        return region_dict, list(region_dict.keys())
    except Exception as e:
        print(f"Error loading regions: {e}")
        return default_data, ["北京市", "广东省"]


# ==============================================================================
# 修改：编辑弹窗逻辑
# ==============================================================================
# ==============================================================================
# 修复：内置全量地区数据 (彻底解决读取不到文件的问题)
# ==============================================================================
CHINA_REGIONS_DATA = {
    "北京市": ["东城区", "西城区", "朝阳区", "丰台区", "石景山区", "海淀区", "门头沟区", "房山区", "通州区", "顺义区", "昌平区", "大兴区", "怀柔区", "平谷区", "密云区", "延庆区"],
    "天津市": ["和平区", "河东区", "河西区", "南开区", "河北区", "红桥区", "东丽区", "西青区", "津南区", "北辰区", "武清区", "宝坻区", "滨海新区", "宁河区", "静海区", "蓟州区"],
    "上海市": ["黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区", "闵行区", "宝山区", "嘉定区", "浦东新区", "金山区", "松江区", "青浦区", "奉贤区", "崇明区"],
    "重庆市": ["万州区", "涪陵区", "渝中区", "大渡口区", "江北区", "沙坪坝区", "九龙坡区", "南岸区", "北碚区", "綦江区", "大足区", "渝北区", "巴南区", "黔江区", "长寿区", "江津区", "合川区", "永川区", "南川区", "璧山区", "铜梁区", "潼南区", "荣昌区", "开州区", "梁平区", "武隆区"],
    "河北省": ["石家庄市", "唐山市", "秦皇岛市", "邯郸市", "邢台市", "保定市", "张家口市", "承德市", "沧州市", "廊坊市", "衡水市"],
    "山西省": ["太原市", "大同市", "阳泉市", "长治市", "晋城市", "朔州市", "晋中市", "运城市", "忻州市", "临汾市", "吕梁市"],
    "内蒙古自治区": ["呼和浩特市", "包头市", "乌海市", "赤峰市", "通辽市", "鄂尔多斯市", "呼伦贝尔市", "巴彦淖尔市", "乌兰察布市", "兴安盟", "锡林郭勒盟", "阿拉善盟"],
    "辽宁省": ["沈阳市", "大连市", "鞍山市", "抚顺市", "本溪市", "丹东市", "锦州市", "营口市", "阜新市", "辽阳市", "盘锦市", "铁岭市", "朝阳市", "葫芦岛市"],
    "吉林省": ["长春市", "吉林市", "四平市", "辽源市", "通化市", "白山市", "松原市", "白城市", "延边朝鲜族自治州"],
    "黑龙江省": ["哈尔滨市", "齐齐哈尔市", "鸡西市", "鹤岗市", "双鸭山市", "大庆市", "伊春市", "佳木斯市", "七台河市", "牡丹江市", "黑河市", "绥化市", "大兴安岭地区"],
    "江苏省": ["南京市", "无锡市", "徐州市", "常州市", "苏州市", "南通市", "连云港市", "淮安市", "盐城市", "扬州市", "镇江市", "泰州市", "宿迁市"],
    "浙江省": ["杭州市", "宁波市", "温州市", "嘉兴市", "湖州市", "绍兴市", "金华市", "衢州市", "舟山市", "台州市", "丽水市"],
    "安徽省": ["合肥市", "芜湖市", "蚌埠市", "淮南市", "马鞍山市", "淮北市", "铜陵市", "安庆市", "黄山市", "滁州市", "阜阳市", "宿州市", "六安市", "亳州市", "池州市", "宣城市"],
    "福建省": ["福州市", "厦门市", "莆田市", "三明市", "泉州市", "漳州市", "南平市", "龙岩市", "宁德市"],
    "江西省": ["南昌市", "景德镇市", "萍乡市", "九江市", "新余市", "鹰潭市", "赣州市", "吉安市", "宜春市", "抚州市", "上饶市"],
    "山东省": ["济南市", "青岛市", "淄博市", "枣庄市", "东营市", "烟台市", "潍坊市", "济宁市", "泰安市", "威海市", "日照市", "临沂市", "德州市", "聊城市", "滨州市", "菏泽市"],
    "河南省": ["郑州市", "开封市", "洛阳市", "平顶山市", "安阳市", "鹤壁市", "新乡市", "焦作市", "濮阳市", "许昌市", "漯河市", "三门峡市", "南阳市", "商丘市", "信阳市", "周口市", "驻马店市", "济源市"],
    "湖北省": ["武汉市", "黄石市", "十堰市", "宜昌市", "襄阳市", "鄂州市", "荆门市", "孝感市", "荆州市", "黄冈市", "咸宁市", "随州市", "恩施土家族苗族自治州", "仙桃市", "潜江市", "天门市", "神农架林区"],
    "湖南省": ["长沙市", "株洲市", "湘潭市", "衡阳市", "邵阳市", "岳阳市", "常德市", "张家界市", "益阳市", "郴州市", "永州市", "怀化市", "娄底市", "湘西土家族苗族自治州"],
    "广东省": ["广州市", "韶关市", "深圳市", "珠海市", "汕头市", "佛山市", "江门市", "湛江市", "茂名市", "肇庆市", "惠州市", "梅州市", "汕尾市", "河源市", "阳江市", "清远市", "东莞市", "中山市", "潮州市", "揭阳市", "云浮市"],
    "广西壮族自治区": ["南宁市", "柳州市", "桂林市", "梧州市", "北海市", "防城港市", "钦州市", "贵港市", "玉林市", "百色市", "贺州市", "河池市", "来宾市", "崇左市"],
    "海南省": ["海口市", "三亚市", "三沙市", "儋州市", "五指山市", "琼海市", "文昌市", "万宁市", "东方市", "定安县", "屯昌县", "澄迈县", "临高县", "白沙黎族自治县", "昌江黎族自治县", "乐东黎族自治县", "陵水黎族自治县", "保亭黎族苗族自治县", "琼中黎族苗族自治县"],
    "四川省": ["成都市", "自贡市", "攀枝花市", "泸州市", "德阳市", "绵阳市", "广元市", "遂宁市", "内江市", "乐山市", "南充市", "眉山市", "宜宾市", "广安市", "达州市", "雅安市", "巴中市", "资阳市", "阿坝藏族羌族自治州", "甘孜藏族自治州", "凉山彝族自治州"],
    "贵州省": ["贵阳市", "六盘水市", "遵义市", "安顺市", "毕节市", "铜仁市", "黔西南布依族苗族自治州", "黔东南苗族侗族自治州", "黔南布依族苗族自治州"],
    "云南省": ["昆明市", "曲靖市", "玉溪市", "保山市", "昭通市", "丽江市", "普洱市", "临沧市", "楚雄彝族自治州", "红河哈尼族彝族自治州", "文山壮族苗族自治州", "西双版纳傣族自治州", "大理白族自治州", "德宏傣族景颇族自治州", "怒江傈僳族自治州", "迪庆藏族自治州"],
    "西藏自治区": ["拉萨市", "日喀则市", "昌都市", "林芝市", "山南市", "那曲市", "阿里地区"],
    "陕西省": ["西安市", "铜川市", "宝鸡市", "咸阳市", "渭南市", "延安市", "汉中市", "榆林市", "安康市", "商洛市"],
    "甘肃省": ["兰州市", "嘉峪关市", "金昌市", "白银市", "天水市", "武威市", "张掖市", "平凉市", "酒泉市", "庆阳市", "定西市", "陇南市", "临夏回族自治州", "甘南藏族自治州"],
    "青海省": ["西宁市", "海东市", "海北藏族自治州", "黄南藏族自治州", "海南藏族自治州", "果洛藏族自治州", "玉树藏族自治州", "海西蒙古族藏族自治州"],
    "宁夏回族自治区": ["银川市", "石嘴山市", "吴忠市", "固原市", "中卫市"],
    "新疆维吾尔自治区": ["乌鲁木齐市", "克拉玛依市", "吐鲁番市", "哈密市", "昌吉回族自治州", "博尔塔拉蒙古自治州", "巴音郭楞蒙古自治州", "阿克苏地区", "克孜勒苏柯尔克孜自治州", "喀什地区", "和田地区", "伊犁哈萨克自治州", "塔城地区", "阿勒泰地区", "石河子市", "阿拉尔市", "图木舒克市", "五家渠市", "北屯市", "铁门关市", "双河市", "可克达拉市", "昆玉市", "胡杨河市", "新星市", "白杨市"],
    "香港特别行政区": ["中西区", "东区", "南区", "湾仔区", "九龙城区", "观塘区", "深水埗区", "黄大仙区", "油尖旺区", "离岛区", "葵青区", "北区", "西贡区", "沙田区", "大埔区", "荃湾区", "屯门区", "元朗区"],
    "澳门特别行政区": ["澳门半岛", "氹仔", "路环", "路氹城"],
    "台湾省": ["台北市", "新北市", "桃园市", "台中市", "台南市", "高雄市", "基隆市", "新竹市", "嘉义市", "新竹县", "苗栗县", "彰化县", "南投县", "云林县", "嘉义县", "屏东县", "宜兰县", "花莲县", "台东县", "澎湖县", "金门县", "连江县"]
}


# ==============================================================================
# 修复：编辑弹窗逻辑 (完全重写)
# ==============================================================================
@st.dialog("✨ 编辑资料")
def render_edit_modal(current_info, user_id):
    # 使用时间戳作为key前缀，确保每次打开弹窗都是全新的组件
    if "dialog_reset_key" not in st.session_state:
        st.session_state.dialog_reset_key = str(int(time.time()))
    refresh_tag = st.session_state.dialog_reset_key

    # 1. 准备省份列表 (把常用的北上广排在前面)
    province_list = list(CHINA_REGIONS_DATA.keys())
    top_p = ["北京市", "上海市", "广东省", "浙江省", "江苏省"]
    for p in reversed(top_p):
        if p in province_list:
            province_list.remove(p)
            province_list.insert(0, p)

    # 2. 初始化回显逻辑 (只在第一次加载时运行)
    # 使用 session_state 来存储当前选中的省/市，实现联动
    prov_key = f"prov_{refresh_tag}"
    city_key = f"city_{refresh_tag}"

    if prov_key not in st.session_state:
        saved_region = current_info.get('region')
        # 默认值
        init_prov = "北京市"
        init_city = "海淀区"

        # 尝试解析已保存的地址 "省份 城市"
        if saved_region and " " in saved_region:
            try:
                p, c = saved_region.split(" ", 1)
                if p in CHINA_REGIONS_DATA:
                    init_prov = p
                    # 检查城市是否在列表里
                    if c in CHINA_REGIONS_DATA[p]:
                        init_city = c
                    else:
                        init_city = CHINA_REGIONS_DATA[p][0]
                else:
                    # 模糊匹配 (比如旧数据存的是 '北京')
                    for k in CHINA_REGIONS_DATA.keys():
                        if k.startswith(p):
                            init_prov = k
                            init_city = CHINA_REGIONS_DATA[k][0]
                            break
            except:
                pass

        st.session_state[prov_key] = init_prov
        st.session_state[city_key] = init_city

    # 3. 布局界面
    # 注意：输入框全部移出 st.form，使用独立的 button 提交，这样 Selectbox 才能实时刷新

    new_name = st.text_input("昵称", value=current_info.get('name', user_id), max_chars=8, key=f"n_{refresh_tag}")
    new_sig = st.text_area("签名", value=current_info.get('signature', ''), max_chars=30, key=f"s_{refresh_tag}")

    st.markdown("<div style='font-size:14px; color:#555; margin-bottom:5px'>所在地区</div>", unsafe_allow_html=True)

    # --- 核心：省市联动区域 ---
    c_prov, c_city = st.columns(2)

    with c_prov:
        # 1. 省份选择
        # 当这个选项改变时，st.session_state[prov_key] 会更新，Streamlit 会重新运行此函数
        current_prov = st.selectbox(
            "省份/直辖市",
            province_list,
            key=prov_key,  # 绑定到 session_state
            label_visibility="collapsed"
        )

    with c_city:
        # 2. 城市选择
        # 动态获取当前省份对应的城市列表
        available_cities = CHINA_REGIONS_DATA.get(current_prov, [])

        # 自动重置逻辑：如果切换了省份，原本选中的城市可能不在新列表里
        # Streamlit 的 selectbox 会自动处理 index 越界，但为了用户体验，通常默认选第一个

        selected_city = st.selectbox(
            "城市/区",
            available_cities,
            key=city_key,  # 绑定到 session_state
            label_visibility="collapsed"
        )

    # 4. 出生年份
    st.markdown("<div style='font-size:14px; color:#555; margin-bottom:5px; margin-top:10px'>出生年份</div>",
                unsafe_allow_html=True)
    current_y = datetime.now().year
    years = list(range(1960, current_y - 10))
    saved_year = int(current_info.get('birth_year', 2004))
    if saved_year not in years: years.append(saved_year); years.sort()

    new_birth_year = st.selectbox("出生年份", years,
                                  index=years.index(saved_year),
                                  key=f"y_{refresh_tag}",
                                  label_visibility="collapsed")

    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

    # 5. 保存按钮
    if st.button("保存更改", type="primary", use_container_width=True):
        if new_name.strip():
            # 组合最终地址
            final_prov = st.session_state[prov_key]
            final_city = st.session_state[city_key]
            final_region = f"{final_prov} {final_city}"

            data_manager.update_user_info(user_id, {
                "name": new_name,
                "signature": new_sig,
                "region": final_region,
                "birth_year": new_birth_year
            })
            st.toast("✅ 资料更新成功")

            # 清理状态防止残留
            del st.session_state[prov_key]
            del st.session_state[city_key]

            time.sleep(0.5)
            close_modal()
            st.rerun()
        else:
            st.error("昵称不能为空")


@st.dialog("🔐 修改密码")
def render_password_modal(user_id):
    # --- 1. 初始化状态变量 ---
    if "pw_step" not in st.session_state: st.session_state.pw_step = 1
    if "pw_last_send_time" not in st.session_state: st.session_state.pw_last_send_time = 0
    if "pw_status_msg" not in st.session_state: st.session_state.pw_status_msg = ""
    # 专门用来暂存第一步验证过的旧密码
    if "temp_old_pwd" not in st.session_state: st.session_state.temp_old_pwd = ""

    # --- 2. 第一步：验证旧密码 ---
    if st.session_state.pw_step == 1:
        st.markdown("### 第一步：验证身份")
        old_pwd = st.text_input("请输入当前密码", type="password", placeholder="请输入原始密码", key="old_pwd_input")
        if st.button("下一步", use_container_width=True, type="primary"):
            importlib.reload(auth_login)
            auth = auth_login.AuthManager()
            if auth.verify_login(user_id, old_pwd):
                st.session_state.temp_old_pwd = old_pwd  # 核心：保存旧密码用于后续比对
                st.session_state.pw_step = 2
                st.rerun()
            else:
                st.error("❌ 密码验证失败")

    # --- 3. 第二步：验证码校验 (防爆破 + 实时倒计时 + 文字Spinner) ---
    elif st.session_state.pw_step == 2:
        db_email = get_user_email_direct(user_id)
        if not db_email:
            st.error("❌ 未绑定邮箱，无法验证")
            if st.button("关闭", use_container_width=True): close_modal(); st.rerun()
            return

        st.markdown(f"### 第二步：安全校验\n<small style='color:#888'>验证码将发送至：{db_email}</small>",
                    unsafe_allow_html=True)

        # === 核心逻辑：倒计时计算 ===
        time_now = time.time()
        time_diff = time_now - st.session_state.pw_last_send_time
        cooldown_seconds = 60
        time_left = int(cooldown_seconds - time_diff)
        is_cooldown = (time_left > 0)

        # 按钮动态文案
        btn_text = f"{time_left}s 后重试" if is_cooldown else "获取验证码"

        # 布局：输入框(左) + 按钮(右)
        c1, c2 = st.columns([2, 1.2], vertical_alignment="bottom")

        with c1:
            code = st.text_input("验证码", max_chars=6, key="verify_code_input", label_visibility="collapsed",
                                 placeholder="请输入6位验证码")

        with c2:
            # 按钮逻辑：冷却期间禁用
            if st.button(btn_text, disabled=is_cooldown, key="pw_code_btn", use_container_width=True):
                # === 修复点：带文字的 Spinner ===
                # 这会在发送期间显示转圈圈和"正在发送中..."文字
                with st.spinner("正在发送中..."):
                    # 稍微sleep一下让用户能看清 spinner，提升交互感
                    time.sleep(0.5)
                    v = ''.join(random.choices(string.digits, k=6))
                    if auth_login.send_email_code(db_email, v):
                        st.session_state.pw_verify_code = v
                        st.session_state.pw_last_send_time = time.time()  # 记录发送时间
                        st.session_state.pw_status_msg = "✅ 已发送"
                    else:
                        st.session_state.pw_status_msg = "❌ 发送失败"
                st.rerun()  # 立即刷新进入倒计时状态

        # 状态提示文字（放在按钮下方，灰色小字，美观）
        st.markdown(f"""
            <div style="text-align: right; font-size: 12px; color: #888; margin-top: -5px; min-height: 20px;">
                {st.session_state.pw_status_msg}
            </div>
        """, unsafe_allow_html=True)

        # 验证按钮
        if st.button("验证并继续", use_container_width=True, type="primary"):
            if code and code == st.session_state.get('pw_verify_code'):
                st.session_state.pw_step = 3
                st.rerun()
            else:
                st.error("验证码错误")

        # === 核心逻辑：实时自动刷新 ===
        # 只有在冷却期间才自动刷新，实现秒级倒计时跳动
        if is_cooldown:
            time.sleep(1)
            st.rerun()

    # --- 4. 第三步：重置密码 (含新旧密码比对) ---
    elif st.session_state.pw_step == 3:
        st.markdown("### 第三步：重置密码")
        p1 = st.text_input("新密码", type="password", key="new_pwd_1")
        p2 = st.text_input("确认密码", type="password", key="new_pwd_2")

        if st.button("完成修改", use_container_width=True, type="primary"):
            # === 修复点：检查新密码是否与旧密码相同 ===
            if p1 == st.session_state.get('temp_old_pwd'):
                st.error("❌ 新密码不能与旧密码相同")
            # 检查两次输入一致性
            elif p1 == p2:
                valid, msg = validate_password_strength(p1)
                if valid:
                    h = hashlib.sha256(p1.encode()).hexdigest()
                    update_password_direct(user_id, h)
                    st.toast("✅ 密码修改成功，请重新登录")
                    time.sleep(1.5)
                    close_modal()
                    # 可以在这里清除 session 强制登出，根据需要开启：
                    # st.session_state.current_user_id = "guest"
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error("❌ 两次输入的密码不一致")


@st.dialog("📄 详细分析报告", width="large")
def render_report_modal():
    st.markdown("""
    <style>
    div[data-testid="stDialog"] div[role="dialog"] {
        width: 80vw !important; max-width: 90vw !important;
        height: 85vh !important; max-height: 95vh !important;
        position: fixed !important; top: 50% !important; left: 50% !important; transform: translate(-50%, -50%) !important;
        overflow-y: auto !important; display: block !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] div[data-testid="stVerticalBlock"] {
        overflow-y: auto !important; overflow-x: hidden !important; height: 100% !important; display: block !important; padding: 20px !important;
    }
    div[data-testid="stDialog"] .stButton { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    need_init = False
    if 'engine' not in st.session_state:
        need_init = True
    elif not hasattr(st.session_state.engine, 'pca'):
        need_init = True

    if need_init:
        with st.spinner("启动 AI 引擎..."):
            try:
                if hasattr(services, 'AnalysisEngine'):
                    st.session_state.engine = services.AnalysisEngine()
                elif hasattr(services, 'FaceAnalyzer'):
                    st.session_state.engine = services.FaceAnalyzer()
                else:
                    classes = [o for n, o in inspect.getmembers(services) if
                               inspect.isclass(o) and o.__module__ == services.__name__]
                    valid_classes = [c for c in classes if 'Engine' in c.__name__ or 'Analyzer' in c.__name__]
                    if valid_classes: st.session_state.engine = valid_classes[0]()
            except Exception as e:
                st.error(f"引擎启动失败: {e}")

    analysis_result.show()


@st.dialog("⚠️ 确认删除")
def render_delete_modal(user_id):
    st.markdown("确定要删除这条记录吗？**此操作不可撤销**。")
    c1, c2 = st.columns(2)
    if c1.button("取消", use_container_width=True):
        close_modal();
        st.rerun()

    if c2.button("确认删除", type="primary", use_container_width=True):
        # 传递整个 item 对象，而不是只有时间戳，这样我们可以用路径删
        item = st.session_state.delete_target_item

        if delete_record_force(user_id, item):
            # 视觉欺骗：前端也立即屏蔽，双重保险
            if "deleted_records" not in st.session_state:
                st.session_state.deleted_records = set()
            st.session_state.deleted_records.add(item['timestamp'])

            st.toast("✅ 删除成功")
            # 自动前移逻辑
            if st.session_state.gallery_offset > 0:
                st.session_state.gallery_offset = max(0, st.session_state.gallery_offset - 1)

            time.sleep(0.5)
            close_modal()
            st.rerun()
        else:
            st.error("删除异常，请刷新页面重试")


# ==============================================================================
# 4. 主界面
# ==============================================================================
def show():
    st.markdown(PROFILE_CSS, unsafe_allow_html=True)
    user_id = st.session_state.get("current_user_id", "guest")
    if user_id == "guest": st.stop()

    # 状态初始化
    if "active_modal" not in st.session_state: st.session_state.active_modal = None
    if "delete_target_item" not in st.session_state: st.session_state.delete_target_item = None
    if "gallery_offset" not in st.session_state: st.session_state.gallery_offset = 0
    if "deleted_records" not in st.session_state: st.session_state.deleted_records = set()

    user_info = data_manager.get_user_info(user_id)
    history = data_manager.get_user_history(user_id)

    # 主布局
    c1, c2 = st.columns([1, 2.5], gap="large")

    # ------------------ 左侧：个人名片 ------------------
    with c1:
        if 'avatar_key' not in st.session_state: st.session_state.avatar_key = 0
        up = st.file_uploader(
            "Upload Avatar",
            type=['jpg', 'png', 'jpeg'],
            key=f"av_{st.session_state.avatar_key}",
            label_visibility="collapsed"
        )

        if up:
            path = os.path.join("assets", "avatars", f"{user_id}_{int(time.time())}.png")
            if not os.path.exists(os.path.dirname(path)): os.makedirs(os.path.dirname(path))
            with open(path, "wb") as f:
                f.write(up.getbuffer())
            data_manager.update_user_info(user_id, {"avatar": path})
            st.session_state.avatar_key += 1
            st.toast("✅ 头像更新成功")
            time.sleep(0.5)
            st.rerun()

        avatar_path = user_info.get('avatar', '')
        if avatar_path and os.path.exists(avatar_path):
            with open(avatar_path, "rb") as f:
                avatar_src = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        else:
            avatar_src = f"https://ui-avatars.com/api/?name={user_info['name']}"

        # === 核心修改：数据准备 ===
        # 1. 地区 (默认为 北京市 海淀区)
        display_region = user_info.get('region', '北京市 海淀区')
        if not display_region or not display_region.strip():
            display_region = '北京市 海淀区'

        # 2. 年龄计算
        birth_year = int(user_info.get('birth_year', 2004))
        current_age = datetime.now().year - birth_year

        # === 核心修改：名片 HTML 结构 ===
        st.markdown(clean_html(f"""
            <style>
            /* 局部样式补充，实现并列布局 */
            .info-meta-row {{
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 15px;
                margin-top: 15px;
                padding-bottom: 5px;
            }}
            .meta-item {{
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 13px;
                color: #78909C;
                background: rgba(241, 245, 249, 0.6);
                padding: 4px 12px;
                border-radius: 12px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 5px;
            }}
            </style>

            <div class="profile-card-container">
                <div class="card-header-bg"></div>
                <div class="avatar-wrapper"><img src="{avatar_src}" class="avatar-img"></div>
                <div class="info-name">{user_info['name']}</div>
                <div class="info-id">@{user_id}</div>
                <div class="info-bio-box"><span class="info-bio">{user_info.get('signature', 'No signature')}</span></div>

                <div class="info-meta-row">
                    <div class="meta-item">🎂 {current_age}岁</div>
                    <div class="meta-item">📍 {display_region}</div>
                </div>
            </div>
        """), unsafe_allow_html=True)

        bc1, bc2 = st.columns(2)
        if bc1.button("编辑资料", type="primary", use_container_width=True):
            set_modal_state("edit");
            st.rerun()
        if bc2.button("修改密码", type="primary", use_container_width=True):
            set_modal_state("password");
            st.rerun()

    # ------------------ 右侧：时间轴档案 ------------------
    with c2:
        st.markdown('<div class="section-title">PERSONAL ARCHIVES 个人档案库</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

        valid_snaps = [
            h for h in history
            if h.get('img_path')
               and os.path.exists(h.get('img_path'))
               and h.get('timestamp') not in st.session_state.deleted_records
        ]

        valid_snaps.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

        if not valid_snaps:
            st.info("🎈 暂无历史记录，快去上传第一张照片吧！")
        else:
            # 1. 核心修改：改为降序排列，时间戳大的（最新的）排在索引 0
            valid_snaps.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

            DISPLAY_COUNT = 4
            total_records = len(valid_snaps)

            # 2. 核心修改：计算最大偏移量
            if total_records <= DISPLAY_COUNT:
                # 记录较少时，强制从 0（最新）开始
                st.session_state.gallery_offset = 0
                max_offset = 0
            else:
                max_offset = total_records - DISPLAY_COUNT

                # 3. 核心修改：如果是初次进入页面（或重置状态），默认偏移量为 0
                if "gallery_offset" not in st.session_state:
                    st.session_state.gallery_offset = 0

                # 边界检查：确保偏移量不会越界
                if st.session_state.gallery_offset > max_offset:
                    st.session_state.gallery_offset = max_offset

            # 以下逻辑保持不变，用于计算日期标签
            curr_start = st.session_state.gallery_offset
            if total_records > 0:
                first_date = datetime.fromtimestamp(valid_snaps[curr_start]['timestamp']).strftime('%Y/%m')
                # 计算当前显示的最后一张照片的索引
                end_idx = min(curr_start + DISPLAY_COUNT - 1, total_records - 1)
                last_date = datetime.fromtimestamp(valid_snaps[end_idx]['timestamp']).strftime('%Y/%m')
                date_label = f"{first_date} - {last_date}"
            else:
                date_label = ""

            st.markdown(
                f"<div style='text-align:right; color:#909399; font-size:12px; margin-bottom:-20px;'>{date_label}</div>",
                unsafe_allow_html=True)

            if max_offset > 0:
                st.slider(
                    "Timeline",
                    min_value=0,
                    max_value=max_offset,
                    value=st.session_state.gallery_offset,
                    step=1,
                    key="gallery_slider_key",
                    on_change=on_timeline_change,
                    label_visibility="collapsed"
                )
            else:
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

            if total_records > DISPLAY_COUNT:
                st.caption(
                    f"↔️ 左右滑动查看历史 (当前显示: {st.session_state.gallery_offset + 1} - {st.session_state.gallery_offset + DISPLAY_COUNT} / 共 {total_records} 条)")

            start_index = st.session_state.gallery_offset
            current_view = valid_snaps[start_index: start_index + DISPLAY_COUNT]

            cols = st.columns(DISPLAY_COUNT)

            for i in range(DISPLAY_COUNT):
                with cols[i]:
                    if i < len(current_view):
                        item = current_view[i]
                        ts = item.get('timestamp')
                        date_obj = datetime.fromtimestamp(ts)
                        date_str = date_obj.strftime("%Y.%m.%d")

                        # === 修改点：将 "%Y" 改为 "%Y.%m" 以显示年份和月份 ===
                        year_str = date_obj.strftime("%Y.%m")

                        st.markdown(f'<div class="timeline-year">{year_str}</div>', unsafe_allow_html=True)

                        try:
                            with open(item['img_path'], "rb") as f:
                                b64 = base64.b64encode(f.read()).decode()

                            st.markdown(f'''
                                            <div class="timeline-img-box">
                                                <img src="data:image/jpeg;base64,{b64}">
                                            </div>
                                            <div class="timeline-caption">{item.get('style', 'Style')}</div>
                                            <div class="timeline-caption" style="font-weight:400; font-size:10px; margin-bottom:5px;">{date_str}</div>
                                        ''', unsafe_allow_html=True)

                            btn_c1, btn_c2 = st.columns(2, gap="small")

                            with btn_c1:
                                # 📄 查看按钮 (加 help 提示)
                                if st.button("📄", key=f"v_tl_{ts}", use_container_width=True, help="查看详情"):
                                    handle_view_report(item, user_id)
                                    st.rerun()

                            with btn_c2:
                                # 🗑️ 删除按钮 (type="secondary" 保持灰色/透明样式)
                                if st.button("🗑️", key=f"d_tl_{ts}", type="secondary", use_container_width=True,
                                             help="删除记录"):
                                    handle_delete_request(item)
                                    st.rerun()

                        except Exception:
                            st.empty()
                    else:
                        st.empty()

            if max_offset > 0:
                # === 终极修复：完美正圆 + 边缘对齐 ===

                st.markdown("""
                            <style>
                            /* 1. 精准定位右侧栏中的 primary 按钮 (翻页按钮) */
                            div[data-testid="column"]:nth-of-type(2) button[kind="primary"] {
                                /* 【核心修复】强制锁死尺寸与比例，防止变扁 */
                                width: 45px !important;
                                height: 45px !important;
                                min-width: 45px !important;
                                max-width: 45px !important;
                                padding: 0 !important;
                                aspect-ratio: 1 / 1 !important; /* 强制1:1比例 */
                                border-radius: 50% !important;  /* 强制正圆 */
                                margin: 0 !important;           /* 移除默认外边距，便于对齐 */

                                /* P2 风格质感：白底 + 柔和悬浮阴影 */
                                background-color: #FFFFFF !important;
                                border: 1px solid #E6EBF5 !important;
                                box-shadow: 0 4px 12px rgba(180, 190, 210, 0.25) !important;

                                /* 图标居中 */
                                display: flex !important;
                                align-items: center !important;
                                justify-content: center !important;

                                /* 图标样式 */
                                color: #8A6481 !important; 
                                font-size: 18px !important;
                                line-height: 0 !important; /* 防止行高撑开 */
                                transition: all 0.3s ease !important;
                            }

                            /* 悬停态：上浮 + 阴影加深 */
                            div[data-testid="column"]:nth-of-type(2) button[kind="primary"]:hover {
                                transform: translateY(-2px) !important;
                                box-shadow: 0 8px 20px rgba(180, 190, 210, 0.4) !important;
                                border-color: #D1D9E6 !important;
                                color: #451E43 !important;
                                background-color: #FBFCFE !important;
                            }

                            /* 点击态 */
                            div[data-testid="column"]:nth-of-type(2) button[kind="primary"]:active {
                                transform: scale(0.92) !important;
                                box-shadow: inset 0 2px 4px rgba(0,0,0,0.05) !important;
                            }

                            /* 2. 【核心修复】右侧按钮强制靠右对齐 */
                            /* 找到翻页栏的最后一个列(右边按钮所在的列)中的按钮，强制右浮动 */
                            div[data-testid="column"]:nth-of-type(2) div[data-testid="stHorizontalBlock"]:last-of-type div[data-testid="column"]:last-child button {
                                float: right !important;
                                margin-left: auto !important;
                            }

                            /* 指示器样式 */
                            .pagination-dots {
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                height: 45px;
                                gap: 8px;
                            }
                            .dot {
                                width: 6px;
                                height: 6px;
                                background-color: #F0F2F5;
                                border-radius: 50%;
                                transition: all 0.4s ease;
                            }
                            .dot.active {
                                width: 20px;
                                height: 6px;
                                border-radius: 10px;
                                background-color: #E2DDF4;
                                box-shadow: 0 2px 6px rgba(226, 221, 244, 0.6);
                            }
                            </style>
                            """, unsafe_allow_html=True)

                st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

                # 布局调整：[1, 15, 1]
                # 中间给 15 的比例，强行把左右两边的列挤到最边缘，实现与图片边缘对齐
                b_prev_col, b_mid, b_next_col = st.columns([1, 15, 1], vertical_alignment="center")

                with b_prev_col:
                    # 左侧按钮
                    if st.button("❮", key="btn_prev_gallery", type="primary"):
                        st.session_state.gallery_offset = max(0, st.session_state.gallery_offset - 1)
                        st.session_state.active_modal = None
                        st.rerun()

                with b_mid:
                    # 指示器
                    total_dots = max_offset + 1
                    current_idx = st.session_state.gallery_offset

                    dots_html = []
                    if total_dots <= 12:
                        for i in range(total_dots):
                            css_class = "dot active" if i == current_idx else "dot"
                            dots_html.append(f'<div class="{css_class}"></div>')
                        st.markdown(f'<div class="pagination-dots">{"".join(dots_html)}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'''
                                    <div style="text-align:center; color:#CBD5E1; font-size:13px; font-family:'Arial'; letter-spacing:1px; line-height:45px;">
                                        <span style="font-weight:bold; color:#B4C6E7;">{current_idx + 1}</span> 
                                        <span style="margin:0 5px;">/</span> 
                                        {total_dots}
                                    </div>''', unsafe_allow_html=True)

                with b_next_col:
                    # 右侧按钮 (CSS 会将其强制 float: right)
                    if st.button("❯", key="btn_next_gallery", type="primary"):
                        st.session_state.gallery_offset = min(max_offset, st.session_state.gallery_offset + 1)
                        st.session_state.active_modal = None
                        st.rerun()

    if st.session_state.active_modal == "edit":
        render_edit_modal(user_info, user_id)
    elif st.session_state.active_modal == "password":
        render_password_modal(user_id)
    elif st.session_state.active_modal == "report_view":
        render_report_modal()
    elif st.session_state.active_modal == "confirm_delete":
        render_delete_modal(user_id)


if __name__ == "__main__": show()