import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import mimetypes
from datetime import datetime


# ==============================================================================
# 1. 核心资源读取器
# ==============================================================================
def get_local_file_content(filepath, mode="r", encoding="utf-8"):
    if os.path.exists(filepath):
        with open(filepath, mode, encoding=encoding) as f:
            return f.read()
    return f"/* Error: 找不到文件 {filepath} */"


def get_local_image_base64(filepath):
    if os.path.exists(filepath):
        # 强制正确识别 SVG，防止图片裂开
        mime_type, _ = mimetypes.guess_type(filepath)
        if not mime_type:
            mime_type = "image/svg+xml" if filepath.lower().endswith('.svg') else "image/jpeg"
        with open(filepath, "rb") as f:
            data = f.read()
        return f"data:{mime_type};base64,{base64.b64encode(data).decode()}"
    return ""


# ==============================================================================
# 2. 动态相对路径解析器 (完美适配你的项目结构)
# ==============================================================================
def get_project_paths():
    """动态获取相对路径，确保在任何电脑上都能运行"""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 向上寻找包含 assets 和 dataset 的根目录
    if os.path.exists(os.path.join(current_dir, "assets")) and os.path.exists(os.path.join(current_dir, "dataset")):
        base_root = current_dir
    elif os.path.exists(os.path.join(current_dir, "..", "assets")):
        base_root = os.path.abspath(os.path.join(current_dir, ".."))
    else:
        base_root = current_dir  # 默认降级方案

    stars_base_path = os.path.join(base_root, "dataset", "Best_Images")
    todo_assets_path = os.path.join(base_root, "assets", "views_todo")

    return stars_base_path, todo_assets_path


def get_stars_list(stars_base_path):
    if os.path.exists(stars_base_path):
        try:
            stars = [d for d in os.listdir(stars_base_path) if os.path.isdir(os.path.join(stars_base_path, d))]
            if stars:
                return sorted(stars)
        except Exception:
            pass
    return []


def get_star_image(stars_base_path, star_name):
    star_dir = os.path.join(stars_base_path, star_name)
    if os.path.exists(star_dir):
        files = [f for f in os.listdir(star_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if files:
            return os.path.join(star_dir, files[0])
    return None


# ==============================================================================
# 3. 原版 HTML 框架注入 (Todo List)
# ==============================================================================
RAW_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Todo List Online</title>
    <style>
    {NORMALIZE_CSS_PLACEHOLDER}
    {STYLE_CSS_PLACEHOLDER}

    /* ====== 完美的局部居中与防滚动 ====== */
    html, body { 
        overflow: hidden !important; 
        height: 100%; 
        padding: 0 !important; 
        margin: 0 !important; 
        background: transparent !important;
    }

    .todo-wrapper { 
        margin: 0 !important; 
        padding: 10px 0 0 0 !important;
        display: flex !important;
        justify-content: flex-start !important; /* 让 Todo 应用在右侧 iframe 中完美居中 */
        align-items: flex-start !important;
        width: 100% !important;
        height: 100% !important;
    }

    /* 恢复合理的固定宽度，不再无限拉伸 */
    .todo-app {
        margin: 10 auto !important; 
        width: 100% !important;
        max-width: 900px !important; /* 刚刚好的宽度，保证快捷操作栏有空间显示 */
    }

    /* 锁定高度防止全局滚动 */
    .todo-list-box {
        height: 470px !important; 
        display: flex;
        flex-direction: column;
        overflow: hidden;
        margin-bottom: 0px !important;
    }

    /* 计划列表区域滚动条 */
    .todo-list {
        flex: 1;
        overflow-y: auto !important;
        padding-right: 10px !important;
        margin-top: 10px !important;
    }
    .todo-list::-webkit-scrollbar { width: 8px; display: block !important; }
    .todo-list::-webkit-scrollbar-thumb { background: #33322E; border: 2px solid #F9F3E5; border-radius: 10px; }
    .todo-list::-webkit-scrollbar-track { background: #F9F3E5; }

    /* 弹窗美化 */
    .custom-alert-overlay { background: transparent !important; }
    .custom-alert { box-shadow: 6px 6px 0px #33322E !important; border: 2px solid #33322E !important; }
    </style>
    <script>
        const browserLanguage = navigator.language || navigator.userLanguage;
        const languageCode = browserLanguage.split('-')[0].toLowerCase();
        if (!localStorage.getItem('uiineed-todos-lang')) localStorage.setItem('uiineed-todos-lang', languageCode);
    </script>
    <script>
        const nativeAlert = window.alert;
        window.alert = function(message, title = '提示') {
            return new Promise((resolve) => {
                const overlay = document.createElement('div');
                overlay.className = 'custom-alert-overlay';
                const alertBox = document.createElement('div');
                alertBox.className = 'custom-alert';
                alertBox.innerHTML = `<div class="custom-alert-title">${title}</div><div class="custom-alert-content">${message}</div><div class="custom-alert-buttons"><button class="custom-alert-btn confirm">确定</button></div>`;
                overlay.appendChild(alertBox);
                document.body.appendChild(overlay);
                const confirmBtn = alertBox.querySelector('.confirm');
                confirmBtn.addEventListener('click', () => {
                    alertBox.style.animation = 'popOut 0.3s forwards';
                    setTimeout(() => { document.body.removeChild(overlay); resolve(true); }, 300);
                });
            });
        };
        const nativeConfirm = window.alert;
        window.confirm = function(message, title = '请确认') {
            return new Promise((resolve) => {
                const overlay = document.createElement('div');
                overlay.className = 'custom-alert-overlay';
                const alertBox = document.createElement('div');
                alertBox.className = 'custom-alert';
                alertBox.innerHTML = `<div class="custom-alert-title">${title}</div><div class="custom-alert-content">${message}</div><div class="custom-alert-buttons"><button class="custom-alert-btn cancel">取消</button><button class="custom-alert-btn confirm">确定</button></div>`;
                overlay.appendChild(alertBox);
                document.body.appendChild(overlay);
                const confirmBtn = alertBox.querySelector('.confirm');
                const cancelBtn = alertBox.querySelector('.cancel');
                confirmBtn.addEventListener('click', () => {
                    alertBox.style.animation = 'popOut 0.3s forwards';
                    setTimeout(() => { document.body.removeChild(overlay); resolve(true); }, 300);
                });
                cancelBtn.addEventListener('click', () => {
                    alertBox.style.animation = 'popOut 0.3s forwards';
                    setTimeout(() => { document.body.removeChild(overlay); resolve(false); }, 300);
                });
            });
        };
    </script>
    <script>{VUE_JS_PLACEHOLDER}</script>
</head>
<body>
    <div class="todo-wrapper">
        <div id="todo-app" class="todo-app" >
            <div class="container header " style="margin-bottom: 12px;">
                <div class="todo-input">
                    <h1 class="title">
                        <img src="{TODO_SVG_PLACEHOLDER}" alt="" class="title-1" draggable="false">
                        <div class="ani-vector"><span></span><span></span></div>
                        <div class="pendulums">
                            <div class="pendulum"><div class="bar"></div><div class="motion"><div class="string"></div><div class="weight"></div></div></div>
                            <div class="pendulum shadow"><div class="bar"></div><div class="motion"><div class="string"></div><div class="weight"></div></div></div>
                        </div>
                    </h1>
                    <div class="add-content-wrapper">
                        <input type="text" rows="3" class="add-content" placeholder="新增待办事项..." v-model="newTodoTitle" @keyup.enter="addTodo" :class='{empty:emptyChecked}' />
                        <transition name="tips"><div class="tips" v-if='emptyChecked' style="color:red">💡请输入内容！</div></transition>
                        <button class="btn submit-btn" type="button" @click="addTodo">提交</button>
                    </div>
                </div>
            </div>

            <div class="container main">
                <div class="todo-list-box">
                    <div class="bar-message">
                        <input type="button" class="btn btn-label btn-allFinish" value="全部标为完成" @click="markAllAsCompleted" v-if="todos.length || recycleBin.length" />
                        <template>
                            <div>
                                <div v-if="!isEditing" @dblclick="editText" class="bar-message-text">{{ slogan }}</div>
                                <div v-else>
                                    <input v-model="slogan" ref="sloganInput" class="slogan-input"  @keyup.enter="saveText" @keyup.esc="cancelText"/>
                                    <div class="todo-btn btn-edit-submit slogan-btn" @click="saveText"><img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTkiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAxOSAyMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTE2LjUwODQgMTAuMzEwOUMxNy4yMzI0IDEwLjU4MjMgMTguMDM5NCAxMC4yMTU1IDE4LjMxMDkgOS40OTE1N0MxOC41ODIzIDguNzY3NiAxOC4yMTU1IDcuOTYwNjMgMTcuNDkxNiA3LjY4OTE0TDE2LjUwODQgMTAuMzEwOVpNOC45OTk5IDJMMTAuMTMyMSAxLjE3NjU1QzkuODU1OCAwLjc5NjYxOCA5LjQwNzM1IDAuNTgwNjA1IDguOTM4MDIgMC42MDEzNjhDOC40Njg3IDAuNjIyMTMgOC4wNDEwNyAwLjg3Njg5OSA3Ljc5OTM4IDEuMjc5NzRMOC45OTk5IDJaTTcuNjcxNzUgMTcuNTU3MkM3LjQyNzIyIDE4LjI5MDcgNy44MjM2MiAxOS4wODM2IDguNTU3MTMgMTkuMzI4MUM5LjI5MDY0IDE5LjU3MjcgMTAuMDgzNSAxOS4xNzYzIDEwLjMyOCAxOC40NDI4TDcuNjcxNzUgMTcuNTU3MlpNMS4wOTk2MyA3LjkyNzkzQzAuNTA3NTQxIDguNDI1MTkgMC40MzA2NjkgOS4zMDgyOCAwLjkyNzkzMSA5LjkwMDM3QzEuNDI1MTkgMTAuNDkyNSAyLjMwODI4IDEwLjU2OTMgMi45MDAzNyAxMC4wNzIxTDEuMDk5NjMgNy45Mjc5M1pNMTcuNDkxNiA3LjY4OTE0QzE1LjgwMjMgNy4wNTU2NSAxMy45ODQxIDUuNTAzNiAxMi41MDk5IDMuOTY3OTVDMTEuNzkzIDMuMjIxMjIgMTEuMTkzOSAyLjUxNzQgMTAuNzc0NCAyLjAwMDU2QzEwLjU2NTEgMS43NDI2OSAxMC40MDE3IDEuNTMyNzYgMTAuMjkxOSAxLjM4OTA4QzEwLjIzNyAxLjMxNzI3IDEwLjE5NTYgMS4yNjIxMSAxMC4xNjg2IDEuMjI1OUMxMC4xNTUxIDEuMjA3OCAxMC4xNDUzIDEuMTk0NDQgMTAuMTM5MSAxLjE4NjEyQzEwLjEzNjEgMS4xODE5NSAxMC4xMzQgMS4xNzkwNSAxMC4xMzI4IDEuMTc3NDRDMTAuMTMyMiAxLjE3NjY0IDEwLjEzMTggMS4xNzYxNiAxMC4xMzE3IDEuMTc2MDFDMTAuMTMxNyAxLjE3NTkzIDEwLjEzMTcgMS4xNzU5NCAxMC4xMzE3IDEuMTc2MDNDMTAuMTMxOCAxLjE3NjA3IDEwLjEzMTkgMS4xNzYyIDEwLjEzMTkgMS4xNzYyM0MxMC4xMzIgMS4xNzYzNyAxMC4xMzIxIDEuMTc2NTUgOC45OTk5IDJDNy44Njc2NyAyLjgyMzQ1IDcuODY3ODMgMi44MjM2NyA3Ljg2OCAyLjgyMzlDNy44NjgwOCAyLjgyNDAxIDcuODY4MjYgMi44MjQyNiA3Ljg2ODQyIDIuODI0NDdDNy44Njg3MiAyLjgyNDkgNy44NjkwOSAyLjgyNTQgNy44Njk1MyAyLjgyNTk5QzcuODcwMzkgMi44MjcxOCA3Ljg3MTUgMi44Mjg2OSA3Ljg3Mjg1IDIuODMwNTRDNy44NzU1NCAyLjgzNDIzIDcuODc5MjIgMi44MzkyNCA3Ljg4Mzg1IDIuODQ1NTNDNy44OTMxIDIuODU4MTEgNy45MDYxOSAyLjg3NTgyIDcuOTIyOTggMi44OTgzN0M3Ljk1NjU2IDIuOTQzNDUgOC4wMDQ5OSAzLjAwNzkyIDguMDY3MyAzLjA4OTQ0QzguMTkxODUgMy4yNTIzOSA4LjM3MjE3IDMuNDgzODcgOC42MDAzOCAzLjc2NTA2QzkuMDU1OTMgNC4zMjYzNSA5LjcwNjg1IDUuMDkxMjggMTAuNDkgNS45MDcwNUMxMi4wMTU4IDcuNDk2NCAxNC4xOTc3IDkuNDQ0MzUgMTYuNTA4NCAxMC4zMTA5TDE3LjQ5MTYgNy42ODkxNFpNNy42MTM5NyAyLjE5ODAxQzguMTA2NjkgNS42NDY2OSA4LjM0OTk3IDguODI5MjYgOC4zNDk5NyAxMS41QzguMzQ5OTcgMTQuMjAxNSA4LjEwMDE0IDE2LjI3MjIgNy42NzE3NSAxNy41NTcyTDEwLjMyOCAxOC40NDI4QzEwLjg5OTggMTYuNzI3OCAxMS4xNSAxNC4yOTg2IDExLjE1IDExLjVDMTEuMTUgOC42NzA3NiAxMC44OTMyIDUuMzUzMzExMC4zODU4IDEuODAxOTlMNy42MTM5NyAyLjE5ODAxWk0yLjkwMDM3IDEwLjA3MjFDMy44ODIyOCA5LjI0NzQyIDUuMjk2MzYgOC4wOTAzMyA2LjY0Mzc5IDYuODMwMUM3Ljk3NjY0IDUuNTgzNTIgOS4zNDU4NyA0LjE0NDU4IDEwLjIwMDQgMi43MjAyNkw3Ljc5OTM4IDEuMjc5NzRDNy4xNTQwMiAyLjM1NTQyIDYuMDIzMzEgMy41NzY2MyA0LjczMTE4IDQuNzg1MTNDMy40NTM2NCA1Ljk3OTk4IDIuMTE3NzIgNy4wNzI4OSAxLjA5OTYzIDcuOTI3OTNMMi45MDAzNyAxMC4wNzIxWiIgZmlsbD0iIzMzMzIyRSIvPjwvc3ZnPgo=" alt="提交" draggable="false"></div>
                                </div>
                            </div>
                        </template>
                    </div>
                    <ul v-if="!todos.length && showEmptyTips" class="empty-tips">
                        <li> 添加你的第一个美学计划！📝</li>
                        <li>食用方法💡：</li>
                        <li>✔️ 所有提交操作支持Enter回车键提交</li>
                        <li>✔️ 拖拽Todo上下移动可排序</li>
                        <li>✔️ 双击上面的标语和 Todo 可进行编辑</li>
                        <li>✔️ 所有的计划数据存储在浏览器本地</li>
                    </ul>
                    <transition-group name="drag" class="todo-list" tag="ul" mode="in-out" @before-enter="beforeEnter" @enter="enter" @after-enter="afterEnter" :css="false" appear>
                        <li v-for='(todo, index) in filteredTodos' :key='todo.id' class='todo-item' @dragenter="dragenter($event, index)" @dragover="dragover($event, index)" @dragstart="dragstart(index)" :data-delay="index * 150 * delayTime" v-show="show" :draggable="!(editedTodo !== null && editedTodo.id === todo.id)">
                            <div class="todo-content" :class='{completed:todo.completed}' @dblclick="editdTodo(todo)">{{todo.title}}</div>
                            <div class="todo-btn btn-finish" v-if="!todo.completed" @click="markAsCompleted(todo)"></div>

                            <div class="todo-btn btn-unfinish" v-if="todo.completed" @click="markAsUncompleted(todo)">
                                <img src="{FINISH_SVG_PLACEHOLDER}" alt="标为未完成" class="icon-finish" draggable="false">
                            </div>

                            <div v-if="todo.removed" class="todo-btn btn-restore" @click="restoreTodo(todo)">
                                <img src="{RESTORE_SVG_PLACEHOLDER}" alt="还原" draggable="false">
                            </div>

                            <div class="todo-btn btn-delete" v-else @click="removeTodo(todo)">
                                <img src="{DELETE_SVG_PLACEHOLDER}" alt="删除" draggable="false">
                            </div>

                            <div class="edit-todo-wrapper" v-if="editedTodo !== null && editedTodo.id === todo.id">
                                <input type="text" class="edit-todo" value="编辑 Todo..." v-if="editedTodo !== null && editedTodo.id === todo.id" v-model="todo.title" v-focus="true" @keyup.enter="editDone(todo)" @keyup.esc="cancelEdit(todo)" @dragstart.stop.prevent @mousedown.stop />
                                <div class="todo-btn btn-edit-submit" @click="editDone(todo)"><img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTkiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAxOSAyMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTE2LjUwODQgMTAuMzEwOUMxNy4yMzI0IDEwLjU4MjMgMTguMDM5NCAxMC4yMTU1IDE4LjMxMDkgOS40OTE1N0MxOC41ODIzIDguNzY3NiAxOC4yMTU1IDcuOTYwNjMgMTcuNDkxNiA3LjY4OTE0TDE2LjUwODQgMTAuMzEwOVpNOC45OTk5IDJMMTAuMTMyMSAxLjE3NjU1QzkuODU1OCAwLjc5NjYxOCA5LjQwNzM1IDAuNTgwNjA1IDguOTM4MDIgMC42MDEzNjhDOC40Njg3IDAuNjIyMTMgOC4wNDEwNyAwLjg3Njg5OSA3Ljc5OTM4IDEuMjc5NzRMOC45OTk5IDJaTTcuNjcxNzUgMTcuNTU3MkM3LjQyNzIyIDE4LjI5MDcgNy44MjM2MiAxOS4wODM2IDguNTU3MTMgMTkuMzI4MUM5LjI5MDY0IDE5LjU3MjcgMTAuMDgzNSAxOS4xNzYzIDEwLjMyOCAxOC40NDI4TDcuNjcxNzUgMTcuNTU3MlpNMS4wOTk2MyA3LjkyNzkzQzAuNTA3NTQxIDguNDI1MTkgMC40MzA2NjkgOS4zMDgyOCAwLjkyNzkzMSA5LjkwMDM3QzEuNDI1MTkgMTAuNDkyNSAyLjMwODI4IDEwLjU2OTMgMi45MDAzNyAxMC4wNzIxTDEuMDk5NjMgNy45Mjc5M1pNMTcuNDkxNiA3LjY4OTE0QzE1LjgwMjMgNy4wNTU2NSAxMy45ODQxIDUuNTAzNiAxMi41MDk5IDMuOTY3OTVDMTEuNzkzIDMuMjIxMjIgMTEuMTkzOSAyLjUxNzQgMTAuNzc0NCAyLjAwMDU2QzEwLjU2NTEgMS43NDI2OSAxMC40MDE3IDEuNTMyNzYgMTAuMjkxOSAxLjM4OTA4QzEwLjIzNyAxLjMxNzI3IDEwLjE5NTYgMS4yNjIxMSAxMC4xNjg2IDEuMjI1OUMxMC4xNTUxIDEuMjA3OCAxMC4xNDUzIDEuMTk0NDQgMTAuMTM5MSAxLjE4NjEyQzEwLjEzNjEgMS4xODE5NSAxMC4xMzQgMS4xNzkwNSAxMC4xMzI4IDEuMTc3NDRDMTAuMTMyMiAxLjE3NjY0IDEwLjEzMTggMS4xNzYxNiAxMC4xMzE3IDEuMTc2MDFDMTAuMTMxNyAxLjE3NTkzIDEwLjEzMTcgMS4xNzU5NCAxMC4xMzE3IDEuMTc2MDNDMTAuMTMxOCAxLjE3NjA3IDEwLjEzMTkgMS4xNzYyIDEwLjEzMTkgMS4xNzYyM0MxMC4xMzIgMS4xNzYzNyAxMC4xMzIxIDEuMTc2NTUgOC45OTk5IDJDNy44Njc2NyAyLjgyMzQ1IDcuODY3ODMgMi44MjM2NyA3Ljg2OCAyLjgyMzlDNy44NjgwOCAyLjgyNDAxIDcuODY4MjYgMi44MjQyNiA3Ljg2ODQyIDIuODI0NDdDNy44Njg3MiAyLjgyNDkgNy44NjkwOSAyLjgyNTQgNy44Njk1MyAyLjgyNTk5QzcuODcwMzkgMi44MjcxOCA3Ljg3MTUgMi44Mjg2OSA3Ljg3Mjg1IDIuODMwNTRDNy44NzU1NCAyLjgzNDIzIDcuODc5MjIgMi44MzkyNCA3Ljg4Mzg1IDIuODQ1NTNDNy44OTMxIDIuODU4MTEgNy45MDYxOSAyLjg3NTgyIDcuOTIyOTggMi44OTgzN0M3Ljk1NjU2IDIuOTQzNDUgOC4wMDQ5OSAzLjAwNzkyIDguMDY3MyAzLjA4OTQ0QzguMTkxODUgMy4yNTIzOSA4LjM3MjE3IDMuNDgzODcgOC42MDAzOCAzLjc2NTA2QzkuMDU1OTMgNC4zMjYzNSA5LjcwNjg1IDUuMDkxMjggMTAuNDkgNS45MDcwNUMxMi4wMTU4IDcuNDk2NCAxNC4xOTc3IDkuNDQ0MzUgMTYuNTA4NCAxMC4zMTA5TDE3LjQ5MTYgNy42ODkxNFpNNy42MTM5NyAyLjE5ODAxQzguMTA2NjkgNS42NDY2OSA4LjM0OTk3IDguODI5MjYgOC4zNDk5NyAxMS41QzguMzQ5OTcgMTQuMjAxNSA4LjEwMDE0IDE2LjI3MjIgNy42NzE3NSAxNy41NTcyTDEwLjMyOCAxOC40NDI4QzEwLjg5OTggMTYuNzI3OCAxMS4xNSAxNC4yOTg2IDExLjE1IDExLjVDMTEuMTUgOC42NzA3NiAxMC44OTMyIDUuMzUzMzExMC4zODU4IDEuODAxOTlMNy42MTM5NyAyLjE5ODAxWk0yLjkwMDM3IDEwLjA3MjFDMy44ODIyOCA5LjI0NzQyIDUuMjk2MzYgOC4wOTAzMyA2LjY0Mzc5IDYuODMwMUM3Ljk3NjY0IDUuNTgzNTIgOS4zNDU4NyA0LjE0NDU4IDEwLjIwMDQgMi43MjAyNkw3Ljc5OTM4IDEuMjc5NzRDNy4xNTQwMiAyLjM1NTQyIDYuMDIzMzEgMy41NzY2MyA0LjczMTE4IDQuNzg1MTNDMy40NTM2NCA1Ljk3OTk4IDIuMTE3NzIgNy4wNzI4OSAxLjA5OTYzIDcuOTI3OTNMMi45MDAzNyAxMC4wNzIxWiIgZmlsbD0iIzMzMzIyRSIvPjwvc3ZnPgo=" alt="提交" draggable="false"></div>
                            </div>
                        </li>
                    </transition-group>
                    <div class="bar-message bar-bottom">
                        <div class="bar-message-text">
                            <span v-if="leftTodosCount">剩余 {{leftTodosCount}} 项未完成</span>
                            <span v-else-if="completedTodosCount">完美收工！</span>
                        </div>
                    </div>
                </div>
                <div class="footer side-bar" >
                    <div class="side-shortcut" @click="shortCutAction()" :class="{fold: isShow}">
                        <div class="shortcut-switch"><span class="shortcut-title">{{shortCut}}</span><span class="shortcut-name">快捷操作 </span></div>
                    </div>
                    <div class="todo-footer-box">
                        <ul class="todo-func-list filter">
                            <li><input class="btn-small action-showAll" type="button" value="全部" :class="{selected: intention === 'all'}" @click="intention ='all'"></li>
                            <li v-if="completedTodosCount"><input class="btn-small action-progress" type="button" value="进行中" v-if="leftTodosCount" :class="{selected: intention === 'ongoing'}" @click="intention ='ongoing'"></li>
                            <li v-if="completedTodosCount"><input class="btn-small action-completed" type="button" value="已完成" v-if="completedTodosCount" :class="{selected: intention === 'completed'}" @click="intention='completed'"></li>
                            <li v-if="recycleBin.length"><input class="btn-small action-deleted" type="button" v-if="recycleBin.length" :class="{selected: intention === 'removed'}" value="回收站" @click="intention='removed'" /></li>
                        </ul>
                        <ul class="todo-func-list batch">
                            <li v-if="leftTodosCount"><input type="button" class="btn-small completed-all" v-if="leftTodosCount" value="全部标为已完成" @click="markAllAsCompleted"></li>
                            <li v-if="completedTodosCount"><input type="button" value="清除已完成" class="btn-small completed-clear" v-if="completedTodosCount" @click="clearCompleted"></li>
                            <li v-if="todos.length"><input type="button" class="btn-small clear-all" value="清除全部" @click="clearAll"></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        var STORAGE_KEY = 'uiineed-todos';
        var todoStorage = {
            fetch: function () {
                var todos = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
                todos.forEach(function (todo, index) { todo.id = index; });
                todoStorage.uid = todos.length;
                return todos
            },
            save: function (todos) { localStorage.setItem(STORAGE_KEY, JSON.stringify(todos)) }
        }
    </script>
    <script>
        var app = new Vue({
            el: '#todo-app',
            data: function () {
                return {
                    todos: todoStorage.fetch(), newTodoTitle: '', editedTodo: null, intention: 'all', checkEmpty: false,
                    recycleBin: [], dragIndex: '', enterIndex: '', show: true, delayTime: '1', isShow: false,
                    shortCut:'开✨', popShow:true, windowWidth: document.documentElement.clientWidth,
                    slogan: this.getSlogan(), isEditing: false, originalSlogan: ""
                }
            },
            watch: {
                windowWidth (val) { console.log("实时屏幕宽度：",val); },
                todos: { handler: function (todos) { todoStorage.save(todos) }, deep: true }
            },
            methods: {
                editText() { this.originalSlogan = this.slogan; this.isEditing = true; this.$nextTick(() => { this.$refs.sloganInput.focus(); }); },
                saveText() { this.isEditing = false; localStorage.setItem('uiineed-slogan', this.slogan); },
                cancelText() { this.slogan = this.originalSlogan; this.isEditing = false; },
                getSlogan() { return localStorage.getItem('uiineed-slogan') || "今日事今日毕，勿将今事待明日!.☕"; },
                contorlScreen:function(){ if(this.windowWidth < 768){ this.isShow = !this.isShow; return this.shortCut = 'Filter' } },
                togglePop: function(){ this.popShow = !this.popShow; },
                shortCutAction: function(){ this.isShow = !this.isShow; if(this.isShow){ return this.shortCut = '关' }else{ return this.shortCut = '开✨' } },
                shuffle: function () { this.filteredTodos = _.shuffle(this.filteredTodos); },
                addTodo: function (e) {
                    if (this.newTodoTitle === '') { this.checkEmpty = true; return }
                    this.todos.unshift({ id: todoStorage.uid++, title: this.newTodoTitle, completed: false, removed: false });
                    this.newTodoTitle = ''; this.checkEmpty = false; this.delayTime = '0';
                },
                markAsCompleted: function (todo) { todo.completed = true; },
                markAsUncompleted: function (todo) { todo.completed = false },
                markAllAsCompleted: function () {
                    confirm('确认一键勾选完成全部待办事项？').then((confirmed) => {
                        if (confirmed) { this.todos.map(function (todo) { if (!todo.completed) todo.completed = true; }) }
                    }); 
                },
                removeTodo: function (todo) {
                    let removedTodo = this.todos.splice(this.todos.indexOf(todo), 1)[0];
                    removedTodo.removed = true; this.recycleBin.unshift(removedTodo);
                },
                restoreTodo: function (todo) {
                    todo.removed = false; this.todos.unshift(todo);
                    let pos = this.recycleBin.indexOf(todo); this.recycleBin.splice(pos, 1);
                },
                editdTodo: function (todo) { this.editedTodo = { id: todo.id, title: todo.title } },
                editDone: function (todo) { if (todo.title === '') { this.removeTodo(todo) } this.editedTodo = null; },
                cancelEdit: function (todo) { todo.title = this.editedTodo.title; this.editedTodo = null },
                clearCompleted: function () {
                    confirm('确认清除全部已完成的代办事项?').then((confirmed) => {
                        if (confirmed) { this.completedTodos.map(todo => todo.removed = true); this.recycleBin.unshift(...this.completedTodos); this.todos = this.leftTodos; }
                    });
                },
                clearAll: function () {
                    confirm('确认清除全部待办事项?').then((confirmed) => {
                        if (confirmed) { this.todos.map(todo => todo.removed = true); this.recycleBin.unshift(...this.todos); this.todos = [] }
                    });
                },
                dragstart: function (index) { this.dragIndex = index; },
                dragenter: function (e, index) {
                    e.preventDefault();
                    if (this.dragIndex !== index) {
                        const source = this.filteredTodos[this.dragIndex];
                        this.filteredTodos.splice(this.dragIndex, 1); this.filteredTodos.splice(index, 0, source);
                        this.dragIndex = index;
                    }
                },
                dragover: function (e, index) { e.preventDefault(); },
                beforeEnter(dom) { dom.classList.add('drag-enter-active'); },
                enter(dom, done) {
                    let delay = dom.dataset.delay;
                    setTimeout(() => {
                        this.delayTime = '1'; dom.classList.remove('drag-enter-active'); dom.classList.add('drag-enter-to');
                        let transitionend = window.ontransitionend ? "transitionend" :"webkitTransitionEnd";
                        dom.addEventListener(transitionend, function onEnd() { dom.removeEventListener(transitionend, onEnd); done(); })
                    }, delay);
                },
                afterEnter(dom) { dom.classList.remove('drag-enter-to'); }
            },
            mounted() {
                this.show = true; var that = this; this.contorlScreen();
                window.onresize = () => { return (() => { window.fullWidth = document.documentElement.clientWidth; that.windowWidth = window.fullWidth; })() };
            },
            directives: { focus: { inserted: function (el) { el.focus() } } },
            computed: {
                emptyChecked: function () { return this.newTodoTitle.length === 0 && this.checkEmpty },
                leftTodos: function () { return this.todos.filter(function (todo) { return !todo.completed }) },
                leftTodosCount: function () { return this.leftTodos.length },
                completedTodos: function () { return this.todos.filter(function (todo) { return todo.completed }) },
                completedTodosCount: function () { return this.completedTodos.length },
                filteredTodos: function () {
                    if (this.intention === 'ongoing') { return this.leftTodos } 
                    else if (this.intention === 'completed') { return this.completedTodos } 
                    else if (this.intention === 'removed') { return this.recycleBin } 
                    else { return this.todos }
                },
                showEmptyTips() { return this.filteredTodos.length === 0 && this.intention !== 'removed'; },
            },
        })
    </script>
</body>
</html>
"""

# ==============================================================================
# 4. 专属左侧 CSS (完美的居中控制)
# ==============================================================================
LEFT_PANEL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;700;800&family=Noto+Serif+SC:wght@600;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&display=swap');

/* --- 1. 彻底隐藏所有容器的滚动条轨道 --- */
*::-webkit-scrollbar {
    width: 0px !important;
    height: 0px !important;
    display: none !important;
}

/* --- 2. 精准锁死最外层视图，严禁产生溢出滚动，同时不触动 Flex 比例 --- */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
    overflow: hidden !important;
    scrollbar-width: none !important; /* 兼容 Firefox */
    -ms-overflow-style: none !important;  /* 兼容 IE/Edge */
}

/* ====== 保持你原来的黄金比例居中布局代码，绝不改动任何数值 ====== */
[data-testid="block-container"] { 
    padding-top: 2rem !important;
    padding-bottom: 0rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1200px !important; 
    margin: 0 auto !important;    
}

footer { display: none !important; }

[data-testid="stHorizontalBlock"] {
    gap: 2rem !important; 
}

[data-testid="column"]:nth-of-type(1) {
    padding-left: 80px !important; 
}

/* --- 拍立得样式 --- */
.polaroid {
    background: #fff;
    padding: 12px 12px 1px 12px;
    border: 2px solid #33322E;
    box-shadow: 4px 4px 0px #33322E;
    border-radius: 12px;
    width: 92%;          
    margin: 8px auto;
}
.polaroid-img-wrapper {
    width: 100%;
    aspect-ratio: 1 / 1;
    overflow: hidden;
    border-radius: 6px;
    border: 2px solid #33322E;
}
.polaroid-img-wrapper img { width: 100%; height: 100%; object-fit: cover; }
.polaroid-caption {
    font-weight: 500; font-size: 19px; color: #33322E;
    text-align: center;
    font-family: 'ZCOOL KuaiLe', 'YouYuan', 'Comic Sans MS', cursive;
    margin-top: 1px;
}

/* --- 语录框 --- */
.quote-box {
    padding: 10px 18px; 
    background: #F9F3E5; 
    border: 2px solid #33322E;
    box-shadow: 4px 4px 0px #33322E;
    border-radius: 12px; 
    font-size: 13px; color: #33322E; font-weight: 600; line-height: 1.5;
    text-align: center;
}

/* --- 搜索框 --- */
div[data-baseweb="select"] { 
    background-color: #fff !important;
    border: 2px solid #33322E !important;
    border-radius: 12px !important; 
    width: 98%;
    box-shadow: 4px 4px 0px #33322E !important;
    height: 45px !important;
}

div[data-baseweb="select"] > div {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    background-color: transparent !important;
}

div[data-baseweb="select"] svg { display: none !important; }
div[data-baseweb="select"] > div > div:last-child::after {
    content: "🔍"; font-size: 16px; position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
}
</style>
"""


# ==============================================================================
# 5. 主程序渲染
# ==============================================================================
def show():
    st.markdown(LEFT_PANEL_CSS, unsafe_allow_html=True)

    # 1. 动态获取基于项目根目录的相对路径
    stars_base_path, todo_assets_path = get_project_paths()

    # 2. 定位具体的静态资源目录
    css_dir = os.path.join(todo_assets_path, "css")
    js_dir = os.path.join(todo_assets_path, "js")
    img_dir = os.path.join(todo_assets_path, "img")

    # 3. 读取核心文件内容
    css_path = os.path.join(css_dir, "style.css")
    normalize_path = os.path.join(css_dir, "normalize.css")
    vue_path = os.path.join(js_dir, "vue.js")

    style_css = get_local_file_content(css_path)
    normalize_css = get_local_file_content(normalize_path)
    vue_js = get_local_file_content(vue_path)

    # 4. 动态读取本地的 SVG 图像（转 Base64 注入，一劳永逸修复图标破损）
    todo_svg = get_local_image_base64(os.path.join(img_dir, "todo.svg"))
    delete_svg = get_local_image_base64(os.path.join(img_dir, "delete.svg"))
    restore_svg = get_local_image_base64(os.path.join(img_dir, "restore.svg"))
    finish_svg = get_local_image_base64(os.path.join(img_dir, "complete.svg"))

    # 5. 替换模板占位符
    final_html = RAW_HTML_TEMPLATE.replace("{STYLE_CSS_PLACEHOLDER}", style_css)
    final_html = final_html.replace("{NORMALIZE_CSS_PLACEHOLDER}", normalize_css)
    final_html = final_html.replace("{VUE_JS_PLACEHOLDER}", vue_js)

    final_html = final_html.replace("{TODO_SVG_PLACEHOLDER}", todo_svg)
    final_html = final_html.replace("{DELETE_SVG_PLACEHOLDER}", delete_svg)
    final_html = final_html.replace("{RESTORE_SVG_PLACEHOLDER}", restore_svg)
    final_html = final_html.replace("{FINISH_SVG_PLACEHOLDER}", finish_svg)

    # ====== 采用黄金布局比例 ======
    # 1:1.6 能让左边图片足够清晰，右侧列表宽度恰当且功能不被隐藏
    col_left, col_right = st.columns([1.2, 2.5], gap="large")

    with col_left:
        stars_base_path, todo_assets_path = get_project_paths()
        stars_list = get_stars_list(stars_base_path)

        if stars_list:
            # --- 核心修改：在 star 文件夹内创建记录文件 ---
            star_folder_path = os.path.join(todo_assets_path, "star")
            star_record_file = os.path.join(star_folder_path, "selected_star.txt")

            default_star = "Adelaide Kane" if "Adelaide Kane" in stars_list else stars_list[0]

            # 1. 初始加载逻辑：优先读文件，确保跨页面/关浏览器不丢失
            if "current_star" not in st.session_state:
                if os.path.exists(star_record_file):
                    try:
                        with open(star_record_file, "r", encoding="utf-8") as f:
                            saved_star = f.read().strip()
                            st.session_state.current_star = saved_star if saved_star in stars_list else default_star
                    except:
                        st.session_state.current_star = default_star
                else:
                    st.session_state.current_star = default_star

            # 2. 定义更新并保存的函数
            def save_star_choice():
                try:
                    # 确保 star 文件夹存在
                    os.makedirs(star_folder_path, exist_ok=True)
                    with open(star_record_file, "w", encoding="utf-8") as f:
                        f.write(st.session_state.current_star)
                    # 同步 URL 参数
                    st.query_params["star"] = st.session_state.current_star
                except Exception as e:
                    st.error(f"无法保存选择到文件: {e}")

            st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size: 32px; text-align: center; font-weight: 500; color: #33322E; margin-bottom: 10px; font-family: \"ZCOOL KuaiLe\", \"YouYuan\", cursive;'>🌟 星愿搜索台</div>",
                unsafe_allow_html=True)

            # 3. 渲染下拉框：绑定 on_change 事件，一旦切换立即修改文件
            selected_star = st.selectbox(
                "搜索或选择",
                options=stars_list,
                key="current_star",
                label_visibility="collapsed",
                on_change=save_star_choice
            )

            # 4. 实时同步 URL 和文件（处理初次运行没有文件的情况）
            if not os.path.exists(star_record_file):
                save_star_choice()
            if st.query_params.get("star") != selected_star:
                st.query_params["star"] = selected_star

            # --- 图片显示逻辑 ---
            img_path = get_star_image(stars_base_path, selected_star)
            if img_path:
                img_b64 = get_local_image_base64(img_path)
                st.markdown(f"""
                    <div class=\"polaroid\">
                        <div class=\"polaroid-img-wrapper\"><img src=\"{img_b64}\"></div>
                        <div class=\"polaroid-caption\">{selected_star}</div>
                    </div>
                    <div class=\"quote-box\">
                        “像 <b>{selected_star}</b> 一样闪闪发光！完成右侧的清单，向理想迈进！”
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("暂未找到照片")

    with col_right:
        # 稳定的高度装下整个列表与操作栏，永不触发全局滚动条
        components.html(final_html, height=700, scrolling=False)


if __name__ == "__main__":
    show()