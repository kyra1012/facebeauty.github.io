import json
import os
from datetime import datetime

# 数据路径
DATA_DIR = os.path.join(os.path.dirname(__file__), "assets", "data")
USER_DB_PATH = os.path.join(DATA_DIR, "users_profile.json")  # 注意：这是档案JSON，不是鉴权的SQLite
HISTORY_DB_PATH = os.path.join(DATA_DIR, "history.json")

# 确保目录存在
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


# --- 初始化 JSON 数据库 ---
def init_json_db():
    if not os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)  # 空字典开始

    if not os.path.exists(HISTORY_DB_PATH):
        with open(HISTORY_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)


# --- 关键：获取用户信息（自动初始化新用户） ---
def get_user_info(user_id):
    init_json_db()

    with open(USER_DB_PATH, 'r', encoding='utf-8') as f:
        users = json.load(f)

    # 核心逻辑：如果JSON里没这个用户，但既然他能登录进来，说明SQLite里有
    # 生成一个默认的“空档案”
    if user_id not in users:
        new_user_profile = {
            "name": user_id,  # 默认昵称就是账号名
            "password": "",  # JSON不存密码，密码在SQLite
            "avatar": "",
            "title": "新晋体验官",
            "level": "Lv.1",
            "signature": "这个人很懒，还没有设置签名。",
            "login_days": 1
        }
        # 存进去
        users[user_id] = new_user_profile
        with open(USER_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
        return new_user_profile

    return users[user_id]


# --- 更新用户信息 ---
def update_user_info(user_id, new_data):
    init_json_db()
    with open(USER_DB_PATH, 'r', encoding='utf-8') as f:
        users = json.load(f)

    # 确保用户存在
    if user_id not in users:
        get_user_info(user_id)  # 触发初始化
        with open(USER_DB_PATH, 'r', encoding='utf-8') as f:  # 重新读
            users = json.load(f)

    if user_id in users:
        users[user_id].update(new_data)
        with open(USER_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
        return True
    return False


# --- 历史记录 (只保存，不负责读取) ---
def save_analysis_record(user_id, score, style_tag, feature_tag, img_path):
    init_json_db()
    record = {
        "user_id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "timestamp": datetime.now().timestamp(),
        "score": float(score),
        "style": style_tag,
        "feature": feature_tag,
        "img_path": img_path
    }

    with open(HISTORY_DB_PATH, 'r', encoding='utf-8') as f:
        history = json.load(f)

    history.append(record)

    with open(HISTORY_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)


# --- 获取特定用户的历史 ---
def get_user_history(user_id):
    init_json_db()
    with open(HISTORY_DB_PATH, 'r', encoding='utf-8') as f:
        history = json.load(f)
    # 只筛选当前 user_id 的数据
    return [r for r in history if r.get('user_id') == user_id]