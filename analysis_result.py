from datetime import datetime

import streamlit as st
import analysis_services as services
import base64
import os
import cv2
import numpy as np
import math
import json
import yaml
import data_manager
import streamlit.components.v1 as components
from streamlit_echarts import st_echarts
import plotly.graph_objects as go
from imutils import face_utils

# ==============================================================================
# 结果页专属 CSS (V71.0 - 修复排版：右侧显示完整6项排名，高度对齐)
# ==============================================================================
RESULT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Montserrat:wght@300;400;500;600&display=swap');

/* 全局背景 */
.stApp { 
    background: linear-gradient(180deg, #FDFBF9 0%, #F4F8FB 100%); 
    font-family: 'Montserrat', sans-serif; 
}
.block-container { padding-top: 1rem; padding-bottom: 5rem; max-width: 95% !important; }

/* ------ 标题 ------ */
.res-h2 { 
    font-family: 'Noto Serif SC', serif; font-size: 26px; font-weight: 700; color: #5D4037; 
    margin: 20px 0 10px 0; display: flex; align-items: center; gap: 12px;
    break-after: avoid; 
}
.res-h2::before { 
    content: ''; width: 8px; height: 28px; 
    background: linear-gradient(to bottom, #FFCDD2, #E1BEE7); 
    border-radius: 6px; 
}

/* ------ P1: 维度解密 ------ */
.equal-height-container { display: flex; flex-direction: row; gap: 25px; height: 620px; min-height: 300px; margin-bottom: 40px; align-items: stretch; break-inside: avoid; }

.left-image-box { 
    flex: 0 0 460px; position: relative; border-radius: 24px; overflow: hidden; 
    box-shadow: 0 15px 40px rgba(255, 205, 210, 0.2); background: #fff; 
}
.left-image-box img { width: 100%; height: 100%; object-fit: cover; display: block; border: none !important; padding: 0 !important; }
.image-tag { 
    position: absolute; bottom: 25px; left: 25px; 
    background: rgba(255,255,255,0.75); padding: 6px 18px; border-radius: 30px; 
    font-size: 12px; font-weight: 700; color: #880E4F; backdrop-filter: blur(8px);
}
.right-info-box { flex: 1; display: flex; flex-direction: column; overflow-y: visible; padding-right: 0px; }

/* 信息卡片 */
.info-card { 
    background: rgba(255, 255, 255, 0.6); 
    backdrop-filter: blur(12px);
    border-radius: 20px; padding: 8px 14px; margin-bottom: 12px; 
    border: 1px solid rgba(255, 255, 255, 0.9); 
    box-shadow: 0 4px 15px rgba(233, 30, 99, 0.02); 
    transition: all 0.3s ease; display: flex; justify-content: space-between; align-items: flex-start; 
}
.info-card:hover { 
    background: rgba(255, 255, 255, 0.9);
    transform: translateY(-2px); 
    box-shadow: 0 8px 25px rgba(248, 187, 208, 0.2); 
    border-color: #FFCDD2;
}
.card-icon { font-size: 24px; margin-right: 15px; width: 30px; text-align: center; }
.card-content { flex: 1; }
.card-title { font-family: 'Noto Serif SC'; font-size: 16px; font-weight: 700; color: #6D4C41; margin-bottom: 6px; }
.card-desc { font-size: 13px; color: #78909C; line-height: 1.6; text-align: justify; font-weight: 400; }
.card-meta { text-align: right; min-width: 90px; margin-left: 15px;}

.meta-tag { 
    display: inline-block; padding: 5px 12px; border-radius: 12px; 
    font-size: 11px; font-weight: 700; 
    background: #FFF3E0; color: #EF6C00; 
    margin-bottom: 12px; white-space: nowrap; box-shadow: 0 2px 5px rgba(0,0,0,0.03);
}
.meta-val { font-size: 11px; color: #B0BEC5; font-family: monospace; }
.ratio-bar-container { width: 100%; height: 5px; background: rgba(200,200,200,0.15); border-radius: 3px; margin-top: 10px; overflow: hidden; display: flex; }
.rb-seg { height: 100%; transition: width 0.5s; }

/* ------ P2: 雷达图 & 榜单 (Split Layout) ------ */
.radar-split-container {
    margin-top: 0px; 
    margin-bottom: 10px;
    display: flex; 
    align-items: stretch; 
    margin-left: -40px;
}

/* 垂直完整榜单样式 */
.rank-v-container {
    display: flex;
    flex-direction: column;
    justify-content: space-between; /* 关键：让6个卡片均匀填满高度 */
    height: 450px; /* 强制与雷达图 Echarts 高度一致 */
    margin-left: -20px;
    max-width: 380px;
    padding-bottom: 10px;
    padding-top: 30px;
}

.rank-v-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.7) 0%, rgba(255,250,250,0.7) 100%);
    backdrop-filter: blur(8px);
    border-radius: 12px;
    padding: 15px 40px; /* 减小内边距以容纳6个 */
    box-shadow: 0 3px 10px rgba(0,0,0,0.03);
    border: 1px solid rgba(255, 255, 255, 0.8);
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: transform 0.2s ease;
    min-height: 60px;
}
.rank-v-card:hover {
    transform: translateX(-5px);
    background: #FFF;
    box-shadow: 0 5px 15px rgba(233, 30, 99, 0.08);
}

.rank-v-left { display: flex; align-items: center; gap: 10px; }
.rank-badge {
    font-size: 12px; color: #FFF; padding: 6px 6px; border-radius: 8px; font-weight: 800;
    min-width: 45px; text-align: center;
}
/* 前三名彩色 */
.v-rank-1 { background: linear-gradient(135deg, #FF80AB 0%, #F48FB1 100%); box-shadow: 0 2px 5px rgba(255, 128, 171, 0.3); } 
.v-rank-2 { background: linear-gradient(135deg, #CE93D8 0%, #BA68C8 100%); box-shadow: 0 2px 5px rgba(206, 147, 216, 0.3); } 
.v-rank-3 { background: linear-gradient(135deg, #80DEEA 0%, #4DD0E1 100%); box-shadow: 0 2px 5px rgba(128, 222, 234, 0.3); } 
/* 后三名灰色 */
.v-rank-gray { background: #CFD8DC; color: #607D8B; }

.rank-name { font-family: 'Noto Serif SC'; font-size: 13px; font-weight: 700; color: #5D4037; }
.rank-v-right { text-align: right; }
.rank-score { font-family: 'Montserrat'; font-size: 16px; font-weight: 800; color: #EC407A; line-height: 1; }
.rank-unit { font-size: 8px; color: #B0BEC5; }

/* 下方三卡片 Grid */
.radar-grid { 
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; width: 100%; box-sizing: border-box; 
}

/* 雷达分析卡片 */
.radar-card {
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(12px);
    border-radius: 24px;
    padding: 35px 18px;
    border: 1px solid rgba(255, 255, 255, 0.9);
    box-shadow: 0 15px 40px rgba(233, 30, 99, 0.05);
    display: flex;
    flex-direction: column;
    transition: all 0.3s ease;
    height: 100%; /* 等高 */
}
.radar-card:hover {
    transform: translateY(-5px);
    background: rgba(255, 255, 255, 0.85);
    box-shadow: 0 20px 50px rgba(233, 30, 99, 0.1);
    border-color: #FFCDD2;
}

.radar-card-header {
    text-align: center;
    margin-bottom: 10px;
    border-bottom: 1px dashed rgba(200,200,200,0.3);
    padding-bottom: 15px;
}
.radar-card-title {
    font-family: 'Noto Serif SC', serif;
    font-size: 18px;
    font-weight: 700;
    color: #5D4037;
    display: inline-block;
}

/* Advice Styles */
.advice-container { display: flex; flex-direction: column; gap: 12px; }
.advice-row { 
    background: transparent;
    border-bottom: 1px dashed rgba(200,200,200,0.2);
    padding: 0 0 10px 0;
}
.advice-row:last-child { border-bottom: none; }
.advice-header {
    font-family: 'Noto Serif SC', serif; font-weight: 700; color: #EC407A; font-size: 14px;
    margin-bottom: 6px; display: flex; justify-content: space-between;
}
.advice-content { color: #546E7A; line-height: 1.8; font-size: 12px; text-align: justify; }
.advice-item { display: block; margin-bottom: 4px; }
.advice-item b { color: #880E4F; font-weight: 700; background: rgba(255, 205, 210, 0.2); padding: 0 4px; border-radius: 4px; }

/* ====== P3 & P4 ====== */
.muse-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; width: 100%; margin-top: 10px; box-sizing: border-box; break-inside: avoid; }
.muse-card { background: rgba(255, 255, 255, 0.55); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.9); border-radius: 20px; padding: 20px 15px; display: flex; flex-direction: column; align-items: center; text-align: center; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); box-shadow: 0 4px 15px rgba(233, 30, 99, 0.02); min-width: 0; }
.muse-card:hover { transform: translateY(-8px); background: rgba(255, 255, 255, 0.85); border-color: #F8BBD0; box-shadow: 0 15px 30px rgba(244, 143, 177, 0.2); }
.muse-avatar-box { width: 80px; height: 80px; border-radius: 50%; padding: 3px; background: linear-gradient(135deg, #FFCDD2 0%, #E1BEE7 100%); margin-bottom: 12px; box-shadow: 0 4px 10px rgba(233, 30, 99, 0.1); }
.muse-avatar { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; border: 3px solid #FFF; }
.muse-name { font-family: 'Noto Serif SC', serif; font-size: 16px; font-weight: 700; color: #5D4037; margin-bottom: 4px; }
.muse-sim { background: #FFF0F5; color: #EC407A; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 10px; margin-bottom: 12px; }
.muse-desc-box { background: rgba(255, 255, 255, 0.6); border-radius: 12px; padding: -5px; width: 100%; text-align: justify; border: 1px solid rgba(255, 255, 255, 0.5); }
.muse-desc-title { color: #AB47BC; font-size: 12px; font-weight: 700; margin-bottom: 12px; display: block; text-align: center; }
.muse-desc-text { color: #78909C; font-size: 11px; line-height: 1.6; }

#.highlight-card { background: linear-gradient(180deg, #FFFFFF 0%, #FFF8F9 100%); border-radius: 24px; padding: 5px; box-shadow: 0 15px 50px rgba(255, 205, 210, 0.15); border: 1px solid rgba(255,255,255,1); backdrop-filter: blur(20px); break-inside: avoid;}
.compare-row { display: flex; gap: 100px; justify-content: center; margin-bottom: 25px; align-items: center; position: relative; }
.compare-column { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.compare-img-box { width: 280px; aspect-ratio: 3 / 4; position: relative; border-radius: 30px; overflow: hidden; box-shadow: 0 8px 25px rgba(0,0,0,0.06); border: 2px solid #FFF; transition: all 0.4s ease; background: #F8F8F8; display: flex; }
.compare-img-box:hover { transform: scale(1.02); box-shadow: 0 12px 35px rgba(233, 30, 99, 0.12); }
.compare-img-box img { width: 100%; height: 100%; object-fit: cover; object-position: center top; }
.external-label { font-family: 'Montserrat', sans-serif; background: rgba(255, 255, 255, 0.8); padding: 5px 20px; border-radius: 30px; font-size: 10px; font-weight: 800; color: #5D4037; border: 1px solid #F0F0F0; box-shadow: 0 4px 10px rgba(0,0,0,0.05); letter-spacing: 1px; text-transform: uppercase; }
.analysis-text-box { background: linear-gradient(135deg, #FFFDE7 0%, #FFF8E1 100%); border-radius: 18px; padding: 5px; border-left: 6px solid #FBC02D; color: #5D4037; line-height: 1.3; font-size: 14px; text-align: justify; box-shadow: 0 5px 20px rgba(255, 238, 88, 0.08); }
.analysis-title { font-family: 'Noto Serif SC'; font-weight: 800; font-size: 18px; margin-bottom: 12px; color: #F57F17; display: flex; align-items: center; gap: 10px; }
.vs-badge { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 10; width: 60px; height: 60px; border-radius: 80%; background: linear-gradient(135deg, #FFF 0%, #F8BBD0 100%); display: flex; align-items: center; justify-content: center; font-weight: 900; color: #D81B60; font-size: 23px; font-style: italic; box-shadow: 0 0 0 4px rgba(255,255,255,0.65), 0 8px 20px rgba(233, 30, 99, 0.2); margin-top: -20px; }

@media print {
    /* 1. 强制统一背景：全部转为纯白，防止分页导致的背景丢失 */
    * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        box-shadow: none !important;
        text-shadow: none !important;
    }
    
    html, body, .stApp, [data-testid="stAppViewContainer"], .block-container {
        background-color: #FFFFFF !important;
        background-image: none !important;
        color: #000000 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 2. 彻底移除导航栏、页眉、装饰线和按钮 (包括“大屏导览”等) */
    header, 
    [data-testid="stHeader"], 
    [data-testid="stToolbar"], 
    [data-testid="stDecoration"],
    footer, 
    .stDeployButton, 
    .stButton {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 3. 极速消除顶部空白：利用负 Margin 强制置顶 */
    .block-container {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        margin-top: -80px !important; /* 强制抵消 system 导航栏占位 */
        max-width: 100% !important;
    }

    /* 4. 修复 P1: 维度解密 - 锁定 3:4 比例且等高对齐 */
    .equal-height-container {
        display: flex !important;
        flex-direction: row !important;
        align-items: stretch !important; /* 强制右侧卡片拉伸到与左图等高 */
        gap: 20px !important;
        height: 580px !important; /* 固定一个合适的高度，防止内容溢出或留白过多 */
        margin-bottom: 20px !important;
        page-break-inside: avoid !important;
    }

    .left-image-box {
        flex: 0 0 auto !important;
        height: 100% !important;
        aspect-ratio: 3 / 4 !important; /* 严格执行 3:4 比例 */
        border: 1px solid #EEE !important;
    }

    .left-image-box img {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important; /* 保证图片不拉伸变形 */
    }

    .right-info-box {
        flex: 1 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important; /* 卡片均匀分布以对齐高度 */
    }

    .info-card {
        padding: 8px 15px !important;
        margin-bottom: 5px !important;
        flex: 1 !important; /* 自动填充间距 */
        border: 1px solid #F5F5F5 !important;
    }

    /* 5. 修复 P3/P4 模块：压缩高度防止截断，移除阴影 */
    [data-testid="stPlotlyChart"], .js-plotly-plot, .stEcharts {
        height: 420px !important; /* 压缩图表高度 */
        width: 100% !important;
        page-break-inside: avoid !important;
    }

    .radar-split-container {
        display: flex !important;
        flex-direction: row !important;
        margin-left: 0 !important;
        gap: 15px !important;
    }

    .rank-v-container {
        height: 420px !important;
        margin-left: 0 !important;
    }

    /* 6. 通用排版：缩小标题，减少模块间留白 */
    .res-h2 {
        margin: 10px 0 8px 0 !important;
        font-size: 20px !important;
        break-after: avoid !important;
    }

    .radar-grid, .muse-grid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 10px !important;
        margin-top: 10px !important;
    }

    .highlight-card {
        page-break-inside: avoid !important;
        margin-top: 10px !important;
        border: 1px solid #F0F0F0 !important;
    }
}

/* ==============================================================================
   按钮样式 - 去圆点、文字居中、宽度占满 
   ============================================================================== */
div.stButton { 
    text-align: center; /* 确保外层容器居中 */
    margin-bottom: -5px; /* 调整负边距为正常值，避免组件重叠  */
    margin-top: -5px; 
    width: 100%; 
}

div.stButton > button {
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.95) 0%, rgba(245, 247, 250, 0.85) 100%) !important;
    backdrop-filter: blur(15px) !important; 
    -webkit-backdrop-filter: blur(15px) !important;
    border: 1px solid rgba(255, 255, 255, 1.0) !important;
    color: #455A64 !important; 
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important; 
    font-weight: 600 !important; 
    letter-spacing: 1.2px !important;
    white-space: nowrap !important; 
    border-radius: 100px !important;
    
    /* 修改点 1：将 padding 改为对称，移除原先为圆点预留的左边距  */
    padding: 12px 25px !important; 
    
    /* 修改点 2：宽度设为 100% 以占满列容器  */
    width: 100% !important; 
    
    box-shadow: 0 8px 20px -5px rgba(144, 164, 174, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.5) inset !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    position: relative !important; 
    display: flex !important; /* 使用 flex 布局实现完美居中  */
    align-items: center !important;
    justify-content: center !important; /* 文字水平居中  */
    overflow: hidden !important; 
}

div.stButton > button p::before { display: none; }

/* 修改点 3：彻底隐藏圆点伪元素  */
div.stButton > button::before {
    display: none !important;
    content: "" !important;
}

div.stButton > button:hover {
    background: linear-gradient(145deg, #FFF, #FFF0F5) !important; 
    border-color: #F8BBD0 !important; 
    color: #880E4F !important; 
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 25px -5px rgba(236, 64, 122, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.8) inset !important;
}

/* 确保 Hover 状态下圆点也不会出现  */
div.stButton > button:hover::before { 
    display: none !important; 
}

div.stButton > button:active {
    transform: translateY(1px) scale(0.98) !important; 
    background: #F5F5F5 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
}

div.stButton > button:focus { 
    outline: none !important; 
    color: #880E4F !important; 
}
@media print {
    /* 1. 解决只有两页被截断的问题：强行解除所有滚动条和高度限制 */
    html, body, .stApp, [data-testid="stAppViewContainer"], .block-container, div[data-testid="stVerticalBlock"] {
        height: auto !important;
        max-height: none !important;
        overflow: visible !important;
        position: static !important;
    }

    /* 2. 解决文字变透明消失的问题：必须关掉毛玻璃，并给卡片兜底纯白背景 */
    * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
    }
    
    .info-card, .radar-card, .muse-card, .highlight-card, .rank-v-card { 
        background: #FFFFFF !important; 
        border: 1px solid #EEEEEE !important;
        break-inside: avoid !important; 
        page-break-inside: avoid !important; 
    }

    /* 3. 满足你的核心诉求：绝对保留原网页排布 */
    /* P1 维度解密：强制同行显示 */
    .equal-height-container { 
        display: flex !important; 
        flex-direction: row !important; 
        gap: 15px !important; 
    }
    /* 核心缩放：为了让 A4 纸能装下并排内容，把左图的固定 460px 改为按比例占 40% */
    .left-image-box { flex: 0 0 40% !important; max-width: 40% !important; height: auto !important; }
    .right-info-box { flex: 1 !important; max-width: 60% !important; }

    /* 下方卡片：严格保持 3 列网格 */
    .radar-grid, .muse-grid { 
        display: grid !important; 
        grid-template-columns: repeat(3, 1fr) !important; 
        gap: 15px !important; 
    }

    /* P2 雷达图与榜单：严格保持左右并排 */
    .radar-split-container { 
        display: flex !important; 
        flex-direction: row !important; 
        width: 100% !important; 
        gap: 10px !important; 
    }
    [data-testid="stHorizontalBlock"] { 
        display: flex !important; 
        flex-direction: row !important; 
        flex-wrap: nowrap !important; 
        gap: 15px !important; 
        align-items: stretch !important; 
    }
    [data-testid="column"] { 
        flex: 1 1 0 !important; 
        width: auto !important; 
        display: block !important; 
    }

    /* 4. 隐藏无关组件，重置页边距 */
    header[data-testid="stHeader"], footer, [data-testid="stToolbar"], .stDeployButton, .stButton { 
        display: none !important; visibility: hidden !important; height: 0 !important; 
    }
    .stApp { margin-top: 0 !important; padding-top: 0 !important; background: #FDFBF9 !important; }
    .block-container { padding-top: 0 !important; margin-top: 0 !important; max-width: 100% !important; }
    
    /* 图表：稍微压低高度，防止一页放不下被强行切断 */
    iframe, .stEcharts, [data-testid="stPlotlyChart"], .js-plotly-plot, .plotly-graph-div { 
        height: 400px !important; 
        width: 100% !important; 
        page-break-inside: avoid !important; 
        opacity: 1 !important; 
    }
}
</style>
"""


# ==============================================================================
# Helper to Load YAMLs
# ==============================================================================
def load_yaml(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "assets", "content", filename)
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(base_dir), "assets", "content", filename)

    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    print(f"Warning: YAML file not found at {path}")
    return {}


# ----------------- 辅助函数 -----------------
def get_image_base64(path):
    if path and os.path.exists(path):
        with open(path, "rb") as img_file: return base64.b64encode(img_file.read()).decode().replace('\n', '')
    return ""


# 🔥 核心新增：智能多策略明星路径解析器，彻底抹平云端 Linux 与本地 Windows 的路径不一致问题
def resolve_star_image_path(image_path):
    if not image_path:
        return ""
    
    current_dir = os.path.dirname(os.path.abspath(__file__)) # 即 face/ 目录
    repo_root = os.path.abspath(os.path.join(current_dir, "..")) # 即代码总仓库根目录
    
    # 统一清洗 Windows 的反斜杠 \ 为 Linux 标准斜杠 /
    clean_path = image_path.replace("\\", "/")
    base_name = os.path.basename(clean_path)
    
    # 智能探测优先级链条
    candidates = [
        clean_path,
        os.path.join(current_dir, clean_path),
        os.path.join(repo_root, clean_path),
        os.path.join(current_dir, "dataset", "Best_Images", base_name),
        os.path.join(current_dir, "dataset", clean_path),
        os.path.join(repo_root, "dataset", "Best_Images", base_name),
    ]
    
    # 如果全局服务中包含底层的 IMAGES_ROOT 配置，也一并加入校验
    if 'services' in globals() and hasattr(services, 'IMAGES_ROOT'):
        candidates.append(os.path.join(services.IMAGES_ROOT, clean_path))
        candidates.append(os.path.join(services.IMAGES_ROOT, "dataset", "Best_Images", base_name))
        
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
            
    # 兜底降级策略：默认寻找当前子视图目录下的 Best_Images 文件夹
    return os.path.join(current_dir, "dataset", "Best_Images", base_name)


def array_to_base64(img_array):
    _, buffer = cv2.imencode('.jpg', img_array);
    return base64.b64encode(buffer).decode().replace('\n', '')


def apply_feature_mask_overlay(image, shape, feature_type):
    h_img, w_img = image.shape[:2]
    if feature_type == 'eye':
        indices = list(range(17, 27)) + list(range(36, 48))
        pad_ratio_top = 0.3;
        pad_ratio_bot = 0.6
    elif feature_type == 'nose':
        indices = list(range(27, 36))
        pad_ratio_top = 0.2;
        pad_ratio_bot = 0.2
    elif feature_type == 'lip':
        indices = list(range(48, 68))
        pad_ratio_top = 0.4;
        pad_ratio_bot = 0.6
    else:
        indices = list(range(0, 68))
        pad_ratio_top = 0.1;
        pad_ratio_bot = 0.1

    pts = shape[indices]
    y_min = np.min(pts[:, 1]);
    y_max = np.max(pts[:, 1])
    h_feat = y_max - y_min

    y1 = max(0, int(y_min - h_feat * pad_ratio_top))
    y2 = min(h_img, int(y_max + h_feat * pad_ratio_bot))

    mask = np.zeros((h_img, w_img), dtype=np.float32)
    fade_h = max(5, int((y2 - y1) * 0.15))
    cv2.rectangle(mask, (0, y1 + fade_h), (w_img, y2 - fade_h), 1.0, -1)

    sigma_y = max(1.0, fade_h * 0.6)
    k_size_y = (int(fade_h * 4) | 1);
    k_size_y = max(3, k_size_y)
    mask = cv2.GaussianBlur(mask, (1, k_size_y), sigmaX=0, sigmaY=sigma_y)

    mask_3c = np.dstack([mask] * 3)
    white_bg = np.ones_like(image) * 255
    result = (image * mask_3c + white_bg * (1 - mask_3c)).astype(np.uint8)
    return result


def crop_portrait_3_4(image, shape):
    h_img, w_img = image.shape[:2]
    x_min, y_min = np.min(shape, axis=0)
    x_max, y_max = np.max(shape, axis=0)
    core_h = y_max - y_min
    target_h = int(core_h * 1.6);
    target_w = int(target_h * 0.75)
    cx = (x_min + x_max) // 2;
    cy = (y_min + y_max) // 2 - int(core_h * 0.15)
    x1 = max(0, cx - target_w // 2);
    y1 = max(0, cy - target_h // 2)
    x2 = min(w_img, cx + target_w // 2);
    y2 = min(h_img, cy + target_h // 2)
    if y1 == 0: y2 = min(h_img, target_h)
    if y2 == h_img: y1 = max(0, h_img - target_h)
    if x1 == 0: x2 = min(w_img, target_w)
    if x2 == w_img: x1 = max(0, w_img - target_w)
    return image[y1:y2, x1:x2]


def generate_rich_descriptions(info, skin_res, ratios):
    prop_data = info.get('prop', {})
    prop_desc = prop_data.get('desc', prop_data.get('comments', '三庭比例分析完成。'))
    skin_desc = skin_res.get('desc', '自然色')
    skin_full = skin_res.get('full_desc', '')
    return {
        "face": info['face'][1], "prop": prop_desc,
        "skin": f"检测为<b>{skin_desc}</b>。{skin_full}",
        "eyes": info['eyes'][1], "nose": info['nose'][1], "lip": info['lip'][1], "brow": info['brow'][1]
    }


# ----------------- 交互文案生成引擎 (Revised: Top3 Logic Extracted) -----------------
class InteractiveInsightGenerator:
    def __init__(self, user_s, star_s, s_name, cats, raw_ratios, p2_data):
        self.u = user_s;
        self.s = star_s;
        self.n = s_name;
        self.c = [c.split(' ')[0] for c in cats];
        self.raw = raw_ratios
        self.p2 = p2_data if p2_data else {}
        self.cat_map = {
            '眼间距': 'eye_distance',
            '眉眼距': 'brow_eye_distance',
            '三庭': 'thirds_balance',
            '折叠度': 'face_fold',
            '聚集度': 'feature_compact',
            '鼻型': 'nose_shape'
        }

    def get_top3(self):
        indices = np.argsort(self.u)[::-1][:3];
        return [(self.c[i], self.u[i]) for i in indices]

    def _get_score_range(self, score):
        ranges = self.p2.get('score_ranges', {})
        high = ranges.get('high_score', [80, 100])
        mid = ranges.get('mid_score', [51, 79])
        if high[0] <= score <= high[1]: return 'high_score'
        if mid[0] <= score <= mid[1]: return 'mid_score'
        return 'low_score'

    def get_content_by_mode(self, mode):
        top3 = self.get_top3()
        mode_key_map = {
            "🔍 个人特质": "personal_trait",
            "⚖️ 差异对比": "difference_comparison",
            "💄 变美策略": "beauty_strategy"
        }

        yaml_section = mode_key_map.get(mode)
        text_html = '<div class="advice-container">'

        if yaml_section:
            for idx, (trait_name, score) in enumerate(top3):
                yaml_feat_key = self.cat_map.get(trait_name)
                if not yaml_feat_key: continue

                range_key = self._get_score_range(score)
                data_list = []
                try:
                    section_data = self.p2.get(yaml_section, {})
                    if section_data:
                        feat_data = section_data.get(yaml_feat_key, {})
                        if feat_data:
                            data_list = feat_data.get(range_key, [])
                except:
                    data_list = []

                if mode == "⚖️ 差异对比":
                    s_score_idx = self.c.index(trait_name) if trait_name in self.c else 0
                    s_score = self.s[s_score_idx] if len(self.s) > s_score_idx else 50
                    diff_score = int(abs(score - s_score))
                    formatted_list = []
                    if isinstance(data_list, list):
                        for item in data_list:
                            if isinstance(item, str):
                                try:
                                    formatted_list.append(item.format(star_name=self.n, diff_score=diff_score))
                                except:
                                    formatted_list.append(item)
                    data_list = formatted_list

                if data_list:
                    combined_text = ""
                    if isinstance(data_list, list):
                        for item in data_list:
                            safe_item = str(item).replace("【", "<b>【").replace("】", "】</b>").strip()
                            combined_text += f'<span class="advice-item">{safe_item}</span>'
                    elif isinstance(data_list, str):
                        combined_text = data_list
                    text_html += f'<div class="advice-row"><div class="advice-header"><span>{trait_name}</span><span>{score}分</span></div><div class="advice-content">{combined_text}</div></div>'

        text_html += '</div>'
        return text_html


# ----------------- 缪斯文案生成器 -----------------
def get_muse_content(star_name, p3_data):
    if not p3_data:
        return ("独特气质", f"您的面部架构与{star_name}有异曲同工之妙。")
    data = p3_data.get(star_name, {})
    if not data:
        return ("独特气质", f"您的面部架构与{star_name}有异曲同工之妙。")
    return (data.get('style', "独特气质"), data.get('desc', ""))


# ----------------- Helper for P4 Formatting -----------------
def get_p4_context(shape, stats, star_name):
    def dist(i, j): return np.linalg.norm(shape[i] - shape[j])

    context = {
        'star_name': star_name,
        'ear': stats.get('eye_dist', 0.36),
        'ratio': stats.get('nose', 0.7),
    }
    dy = shape[39][1] - shape[36][1]
    dx = shape[39][0] - shape[36][0]
    angle = np.degrees(np.arctan2(dy, dx))
    h_l = dist(37, 41);
    w_l = dist(36, 39)
    ear = h_l / (w_l + 1e-6)

    context.update({'angle': angle, 'ear': ear, 'radius': 4.5, 'height': h_l})

    nose_w = dist(31, 35);
    nose_h = dist(27, 33)
    nose_ratio = nose_w / (nose_h + 1e-6)
    face_w = dist(1, 15)

    context.update(
        {'tip_size': nose_w * 0.3, 'slope': 1.8, 'roundness': 0.6, 'face_ratio': nose_w / face_w, 'length': nose_h,
         'straightness': 0.95})

    mouth_w = dist(48, 54)
    up_thick = shape[62][1] - shape[51][1]
    low_thick = shape[57][1] - shape[62][1]

    context.update(
        {'bead_height': 3.0, 'thickness_ratio': up_thick / low_thick if low_thick > 0 else 1.0, 'width': mouth_w,
         'width_ratio': mouth_w / face_w, 'nose_ratio': mouth_w / nose_w, 'blur': 0.5,
         'center_thickness': up_thick + low_thick})

    brow_w = dist(17, 21)
    context.update({'position': 5.0, 'arc': 0.4, 'pos_ratio': 0.6, 'tail_ratio': 0.8, 'height_ratio': 0.1, 'diff': 2.0,
                    'eye_ratio': brow_w / w_l, 'straight': 0.9})
    return context


# ----------------- 主渲染逻辑 -----------------
def show():
    st.markdown(RESULT_CSS, unsafe_allow_html=True)
    if 'user_res' not in st.session_state: st.error("数据丢失"); st.stop()

    p2_data = load_yaml("p2_radar.yaml")
    p3_data = load_yaml("p3_universe.yaml")
    p4_data = load_yaml("p4_highlight.yaml")

    user_res = st.session_state.user_res
    engine = st.session_state.engine
    neighbors = st.session_state.neighbors
    top_star = st.session_state.top_star
    star_stats = st.session_state.star_stats
    info = user_res['analysis']

    # ================= 按钮区域 (修复版：布局对齐 + 逻辑增强) =================
    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
    c_btn_back, c_btn_save, c_btn_print = st.columns([0.15, 0.15, 1], gap="medium")

    # --- 1. 生成当前照片的唯一“特征指纹” ---
    current_signature = None
    if 'embedding' in user_res:
        current_signature = hash(user_res['embedding'].tobytes())

    # --- 2. 初始化保存记录 ---
    if 'saved_signatures' not in st.session_state:
        st.session_state.saved_signatures = set()

    with c_btn_back:
        if st.button("← 返回页面", key="btn_back", type="secondary"):
            st.session_state.analyzed = False
            if 'uploaded_file' in st.session_state:
                del st.session_state.uploaded_file
            if 'user_res' in st.session_state:
                del st.session_state.user_res
            st.rerun()

        # ================= 保存逻辑 =================
        with c_btn_save:
            current_user = st.session_state.get("current_user_id", "guest")

            if current_user != "guest":
                if st.button("💾 保存记录", key="btn_save"):
                    user_res = st.session_state.user_res
                    stats = user_res.get('stats', {})  
                    info = user_res.get('analysis', {})  

                    current_signature = None
                    if 'embedding' in user_res:
                        current_signature = hash(user_res['embedding'].tobytes())

                    if current_signature and current_signature in st.session_state.saved_signatures:
                        st.toast("当前图片已保存，请勿重复操作", icon="⚠️")
                    else:
                        try:
                            def make_serializable(obj):
                                if isinstance(obj, (np.ndarray, np.generic)):
                                    return obj.tolist()
                                if isinstance(obj, (np.float32, np.float64)):
                                    return float(obj)
                                if isinstance(obj, (np.int32, np.int64)):
                                    return int(obj)
                                if isinstance(obj, dict):
                                    return {k: make_serializable(v) for k, v in obj.items()}
                                if isinstance(obj, list):
                                    return [make_serializable(i) for i in obj]
                                return obj

                            # 1. 准备目录
                            base_assets = "assets"
                            img_dir = os.path.join(base_assets, "history_imgs", current_user)
                            report_dir = os.path.join(base_assets, "history_reports", current_user)

                            if not os.path.exists(img_dir): os.makedirs(img_dir)
                            if not os.path.exists(report_dir): os.makedirs(report_dir)

                            # 2. 清理旧数据
                            try:
                                existing_imgs = sorted(
                                    [os.path.join(img_dir, f) for f in os.listdir(img_dir) if
                                     f.endswith(('.jpg', '.png'))],
                                    key=os.path.getmtime
                                )
                                while len(existing_imgs) >= 30:
                                    oldest_img = existing_imgs.pop(0)
                                    try:
                                        os.remove(oldest_img)
                                        basename = os.path.splitext(os.path.basename(oldest_img))[0]
                                        old_json = os.path.join(report_dir, f"{basename}.json")
                                        if os.path.exists(old_json): os.remove(old_json)
                                    except:
                                        pass
                            except Exception as e_clean:
                                print(f"清理警告: {e_clean}")

                            # 3. 生成文件名
                            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
                            img_filename = f"{timestamp_str}.jpg"
                            report_filename = f"{timestamp_str}.json"

                            img_full_path = os.path.join(img_dir, img_filename)
                            report_full_path = os.path.join(report_dir, report_filename)

                            # 4. 保存图片
                            cv2.imwrite(img_full_path, user_res['raw_img'])

                            # 5. 保存 JSON
                            raw_report_data = {
                                "timestamp": timestamp_str,
                                "stats": stats,
                                "analysis": info,
                                "top_star": st.session_state.get('top_star', {}),
                                "neighbors": st.session_state.get('neighbors', []),
                                "shape": user_res.get('shape'),
                                "embedding": user_res.get('embedding')
                            }

                            # 序列化清洗
                            clean_report_data = make_serializable(raw_report_data)

                            with open(report_full_path, "w", encoding='utf-8') as f:
                                json.dump(clean_report_data, f, ensure_ascii=False, indent=2)

                            # 6. 存入数据库
                            if 'total_score' in stats:
                                final_score = float(stats['total_score'])
                            else:
                                user_scores_list = services.AdvancedFeatureCalculator.normalize_for_radar(stats)
                                final_score = float(
                                    sum(user_scores_list) / len(user_scores_list)) if user_scores_list else 85.0

                            style_tag = info['face'][0] if info.get('face') else "未知风格"
                            feature_tag = info['eyes'][0] if info.get('eyes') else "未知特征"

                            try:
                                data_manager.save_analysis_record(
                                    user_id=current_user,
                                    score=round(final_score, 1),
                                    style_tag=style_tag,
                                    feature_tag=feature_tag,
                                    img_path=img_full_path,
                                    report_path=report_full_path
                                )
                            except TypeError:
                                data_manager.save_analysis_record(
                                    user_id=current_user,
                                    score=round(final_score, 1),
                                    style_tag=style_tag,
                                    feature_tag=feature_tag,
                                    img_path=img_full_path
                                )

                            if current_signature:
                                st.session_state.saved_signatures.add(current_signature)

                            st.toast(f"✅ 档案已归档", icon="📂")

                        except Exception as e:
                            import traceback
                            st.error(f"保存失败: {str(e)}")
                            print(traceback.format_exc())
            else:
                if st.button("🔒 登录后保存", key="btn_save_guest"):
                    st.toast("请登录账号以解锁保存功能", icon="🔒")
    with c_btn_print:
        if st.button("🖨️ 生成报告", key="btn_print"):
            components.html(
                """<script>setTimeout(function(){window.parent.print();}, 500);</script>""",
                height=0, width=0
            )
            
    # ================= P1: 维度解密 =================
    st.markdown('<div class="res-h2">维度解密 (Dimension Decoding)</div>', unsafe_allow_html=True)
    portrait_img = crop_portrait_3_4(user_res['raw_img'], user_res['shape'])
    b64_img = array_to_base64(portrait_img)
    skin_res = info.get('skin', {'desc': '自然色', 'hex': '#e0ac69'})
    ratios = info['prop']['ratios']
    r_u, r_m, r_l = [r * 100 for r in ratios]
    rich_text = generate_rich_descriptions(info, skin_res, ratios)

    cards = []
    cards.append(
        f"""<div class="info-card"><div class="card-icon">🦴</div><div class="card-content"><div class="card-title">脸型轮廓</div><div class="card-desc">{rich_text['face']}</div></div><div class="card-meta"><span class="meta-tag" style="background:#FCE4EC; color:#EC407A;">{info['face'][0]}</span><div class="meta-val">{info['face'][2]}</div></div></div>""")
    cards.append(
        f"""<div class="info-card"><div class="card-icon">🎨</div><div class="card-content"><div class="card-title">肤色基调</div><div class="card-desc">{rich_text['skin']}</div></div><div class="card-meta"><span class="meta-tag" style="background:#FFF3E0; color:#EF6C00;">{skin_res.get('desc')}</span></div></div>""")
    cards.append(
        f"""<div class="info-card"><div class="card-icon">📏</div><div class="card-content"><div class="card-title">三庭比例</div><div class="ratio-bar-container"><div class="rb-seg" style="width:{r_u}%; background:#FFCDD2;" title="上庭"></div><div class="rb-seg" style="width:{r_m}%; background:#E1BEE7;" title="中庭"></div><div class="rb-seg" style="width:{r_l}%; background:#B2DFDB;" title="下庭"></div></div><div class="card-desc" style="margin-top:8px;">{rich_text['prop']}</div></div><div class="card-meta"><span class="meta-tag" style="background:#E3F2FD; color:#1976D2;">1 : 1 : 1</span><div class="meta-val">上{ratios[0]:.2f} 中{ratios[1]:.2f} 下{ratios[2]:.2f}</div></div></div>""")
    for icon, title, key in [("👁️", "眼部系统", "eyes"), ("👃", "鼻部形态", "nose"), ("💋", "唇部风格", "lip"),
                             ("〰️", "眉形走势", "brow")]:
        data = info[key]
        cards.append(
            f"""<div class="info-card"><div class="card-icon">{icon}</div><div class="card-content"><div class="card-title">{title}</div><div class="card-desc">{rich_text[key]}</div></div><div class="card-meta"><span class="meta-tag" style="background:#F3E5F5; color:#AB47BC;">{data[0]}</span><div class="meta-val">{data[2] if len(data) > 2 else ''}</div></div></div>""")

    st.markdown(
        f"""<div class="equal-height-container"><div class="left-image-box"><img src="data:image/jpeg;base64,{b64_img}"><div class="image-tag">RAW PORTRAIT</div></div><div class="right-info-box">{"".join(cards)}</div></div>""",
        unsafe_allow_html=True)

    # ================= P2: 雷达图 MAX (Split Layout) =================
    st.markdown('<div class="res-h2">六维美学雷达 (Aesthetic Radar)</div>', unsafe_allow_html=True)
    raw_stats = user_res.get('stats', {})
    user_scores = services.AdvancedFeatureCalculator.normalize_for_radar(raw_stats)
    if star_stats:
        star_scores = services.AdvancedFeatureCalculator.normalize_for_radar(star_stats)
    else:
        star_scores = [min(95, max(45, s + np.random.randint(-10, 10))) for s in user_scores]
    categories = ['眼间距 (舒展)', '眉眼距 (深邃)', '三庭 (均衡)', '折叠度 (立体)', '聚集度 (惊艳)', '鼻型 (精致)']
    avg_scores = [60, 58, 62, 60, 58, 55]

    insight_gen = InteractiveInsightGenerator(user_scores, star_scores, top_star['name'], categories, raw_stats,
                                              p2_data)

    st.markdown('<div class="radar-split-container">', unsafe_allow_html=True)

    c_chart, c_rank = st.columns([2.5, 1])

    with c_chart:
        option = {
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "item"},
            "legend": {"bottom": "-5", "left": "32%", "data": ["我的数据", f"VS {top_star['name']}", "VS 大众平均"],
                       "icon": "circle", "textStyle": {"color": "#90A4AE"}},
            "radar": {
                "indicator": [{"name": c, "max": 100} for c in categories],
                "radius": "75%", "center": ["45%", "50%"],
                "shape": "circle", "splitNumber": 4,
                "axisName": {"color": "#909399", "fontSize": 12, "backgroundColor": "rgba(255,255,255,0.6)",
                             "borderRadius": 8, "padding": [4, 8]},
                "splitLine": {"lineStyle": {
                    "color": ["rgba(255, 205, 210, 0.2)", "rgba(255, 205, 210, 0.3)", "rgba(255, 205, 210, 0.4)",
                              "rgba(255, 205, 210, 0.5)"].reverse()}},
                "splitArea": {"show": False}, "axisLine": {"lineStyle": {"color": "rgba(255, 205, 210, 0.3)"}}
            },
            "series": [{"name": "美学对比", "type": "radar", "symbol": "circle", "symbolSize": 6, "data": [
                {"value": user_scores, "name": "我的数据", "itemStyle": {"color": "#F48FB1"}, "lineStyle": {"width": 3},
                 "areaStyle": {"color": "rgba(244, 143, 177, 0.2)"}},
                {"value": star_scores, "name": f"VS {top_star['name']}", "itemStyle": {"color": "#FFE082"},
                 "lineStyle": {"type": "dashed", "width": 2}, "areaStyle": {"opacity": 0}},
                {"value": avg_scores, "name": "VS 大众平均", "itemStyle": {"color": "#CFD8DC"},
                 "lineStyle": {"width": 1, "opacity": 0.5}, "areaStyle": {"color": "rgba(207, 216, 220, 0.15)"}}]}]
        }
        st_echarts(options=option, height="450px", key="radar_main")

    with c_rank:
        cat_short = [c.split(' ')[0] for c in categories]
        sorted_indices = np.argsort(user_scores)[::-1]
        sorted_data = [(cat_short[i], user_scores[i]) for i in sorted_indices]

        html_rank = '<div class="rank-v-container">'
        for idx, (name, score) in enumerate(sorted_data):
            rank = idx + 1
            if rank == 1:
                badge_cls = "v-rank-1"
            elif rank == 2:
                badge_cls = "v-rank-2"
            elif rank == 3:
                badge_cls = "v-rank-3"
            else:
                badge_cls = "v-rank-gray"

            html_rank += f'<div class="rank-v-card"><div class="rank-v-left"><span class="rank-badge {badge_cls}">TOP {rank}</span><span class="rank-name">{name}</span></div><div class="rank-v-right"><div class="rank-score">{score}</div><div class="rank-unit">分值</div></div></div>'
        html_rank += '</div>'
        st.markdown(html_rank, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Bottom Section: 3 Info Cards
    modes = [("🔍 个人特质", "personal_trait"), ("⚖️ 差异对比", "difference_comparison"),
             ("💄 变美策略", "beauty_strategy")]
    cards_html = ""
    for mode_label, _ in modes:
        content = insight_gen.get_content_by_mode(mode_label)
        card_str = f'<div class="radar-card"><div class="radar-card-header"><span class="radar-card-title">{mode_label}</span></div>{content}</div>'
        cards_html += card_str

    st.markdown(f'<div class="radar-grid">{cards_html}</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:5px"></div>', unsafe_allow_html=True)

    # ================= P3: 星云定位 =================
    st.markdown('<div class="res-h2">星云定位 (Aesthetic Universe)</div>', unsafe_allow_html=True)
    user_pt = engine.pca.transform(user_res['embedding'].reshape(1, -1))[0]
    bg_x, bg_y, bg_z = engine.pca_result[:, 0], engine.pca_result[:, 1], engine.pca_result[:, 2]
    fig_neb = go.Figure()
    fig_neb.add_trace(go.Scatter3d(x=bg_x, y=bg_y, z=bg_z, mode='markers', name='Others',
                                   marker=dict(size=7, color='#FFCDD2', opacity=0.5, symbol='circle',
                                               line=dict(width=0)), hoverinfo='skip'))
    for n in neighbors:
        pt = n['pca']
        fig_neb.add_trace(
            go.Scatter3d(x=[user_pt[0], pt[0]], y=[user_pt[1], pt[1]], z=[user_pt[2], pt[2]], mode='lines',
                         line=dict(color='#64B5F6', width=3, dash='dash'), hoverinfo='none', showlegend=False))
        fig_neb.add_trace(go.Scatter3d(x=[pt[0]], y=[pt[1]], z=[pt[2]], mode='markers+text', text=[n['name']],
                                       textposition="middle center",
                                       textfont=dict(color="#9575CD", size=11, family="Montserrat", weight="bold"),
                                       marker=dict(size=15, color='#E1BEE7', opacity=0.9, symbol='circle',
                                                   line=dict(width=0)),
                                       hovertemplate=f"<b>⭐ {n['name']}</b><br>🔮 相似度: {n['sim_score']:.1f}%<extra></extra>"))
    fig_neb.add_trace(go.Scatter3d(x=[user_pt[0]], y=[user_pt[1]], z=[user_pt[2]], mode='markers+text', text=["YOU"],
                                   textposition="middle center",
                                   textfont=dict(color="#FBC02D", size=15, family="Montserrat", weight="bold"),
                                   marker=dict(size=18, color='#FFF9C4', opacity=1.0, symbol='circle',
                                               line=dict(width=0)), hovertemplate="<b>📍 我的坐标</b><extra></extra>"))
    fig_neb.update_layout(scene=dict(xaxis=dict(visible=False, showgrid=False, showbackground=False),
                                     yaxis=dict(visible=False, showgrid=False, showbackground=False),
                                     zaxis=dict(visible=False, showgrid=False, showbackground=False), aspectmode='data',
                                     bgcolor='rgba(0,0,0,0)', camera=dict(eye=dict(x=1.6, y=1.6, z=0.8))),
                          margin=dict(l=0, r=0, t=0, b=0), height=580, showlegend=False, paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(0,0,0,0)',
                          hoverlabel=dict(bgcolor="rgba(255, 255, 255, 0.95)", font_size=13, font_family="Montserrat",
                                          bordercolor="#FFCDD2"), dragmode='turntable')
    st.plotly_chart(fig_neb, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})

    muse_cards_html = ""
    for star in neighbors:
        # 🔥 核心修复：调用智能解析器对卡片头像路径进行环境自适应
        img_path = resolve_star_image_path(star['image_path'])
        b64_s = get_image_base64(img_path)
        img_src = f"data:image/jpeg;base64,{b64_s}" if b64_s else "https://via.placeholder.com/80"
        tag, insight = get_muse_content(star['name'], p3_data)
        muse_cards_html += f"""<div class="muse-card"><div class="muse-avatar-box"><img class="muse-avatar" src="{img_src}"></div><div class="muse-name">{star['name']}</div><div class="muse-sim">相似度 {star['sim_score']:.1f}%</div><div class="muse-desc-box"><span class="muse-desc-title">✨ {tag}</span><div class="muse-desc-text">{insight}</div></div></div>"""
    st.markdown(f'<div class="muse-grid">{muse_cards_html}</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:70px"></div>', unsafe_allow_html=True)

    # ================= P4: 五官高光 =================
    c_title, c_toggle = st.columns([4, 1])
    with c_title:
        st.markdown('<div class="res-h2" style="margin:0;"> 五官高光时刻 (Feature Highlight)</div>',
                    unsafe_allow_html=True)
    with c_toggle:
        mask_on = st.toggle("🔍 沉浸式专注模式", value=False)

    best_feat, score = engine.find_best_feature_match(user_res['shape'], star_stats)
    star_n = top_star['name']
    user_img_bgr = user_res['raw_img']
    star_img_bgr = None
    
    # 🔥 核心修复：调用智能解析器对高光模块比对图进行路径多重对齐
    resolved_top_star_path = resolve_star_image_path(top_star['image_path'])
    if resolved_top_star_path and os.path.exists(resolved_top_star_path):
        star_img_bgr = cv2.imdecode(
            np.fromfile(resolved_top_star_path, dtype=np.uint8), -1)

    if mask_on:
        user_masked = apply_feature_mask_overlay(user_img_bgr, user_res['shape'], best_feat)
        user_img_final = crop_portrait_3_4(user_masked, user_res['shape'])
    else:
        user_img_final = crop_portrait_3_4(user_img_bgr, user_res['shape'])

    user_full_b64 = array_to_base64(user_img_final)
    star_full_b64 = ""
    if star_img_bgr is not None:
        star_shape = None
        if 'shape' in top_star and top_star['shape'] is not None:
            star_shape = top_star['shape']
        else:
            try:
                gray_s = cv2.cvtColor(star_img_bgr, cv2.COLOR_BGR2GRAY)
                rects_s = engine.detector(gray_s, 1)
                if len(rects_s) > 0:
                    rect_s = max(rects_s, key=lambda r: r.width() * r.height())
                    shape_obj = engine.predictor(gray_s, rect_s)
                    star_shape = face_utils.shape_to_np(shape_obj)
            except:
                pass

        if mask_on and star_shape is not None:
            star_masked = apply_feature_mask_overlay(star_img_bgr, star_shape, best_feat)
            star_img_final = crop_portrait_3_4(star_masked, star_shape)
        elif not mask_on and star_shape is not None:
            star_img_final = crop_portrait_3_4(star_img_bgr, star_shape)
        else:
            h_s, w_s = star_img_bgr.shape[:2]
            target_w_s = int(h_s * 0.75)
            cx_s = w_s // 2
            star_img_final = star_img_bgr[:, max(0, cx_s - target_w_s // 2):min(w_s, cx_s + target_w_s // 2)]
        star_full_b64 = array_to_base64(star_img_final)

    feat_title = f"✨ 高光时刻 ({best_feat})"
    feat_desc = "AI分析数据生成中..."

    if p4_data and 'highlight_features' in p4_data:
        subtype_name = "Standard"
        mapping = {'eye': 'eyes', 'nose': 'nose', 'lip': 'lip', 'brow': 'brow'}
        analysis_key = mapping.get(best_feat)
        if analysis_key and analysis_key in info:
            subtype_name = info[analysis_key][0]

        hl_data = p4_data['highlight_features'].get(best_feat, {})
        clean_subtype = subtype_name.split(' ')[0]

        if clean_subtype in hl_data:
            template = hl_data[clean_subtype]
            fmt_context = get_p4_context(user_res['shape'], raw_stats, star_n)
            fmt_context['score'] = score  

            try:
                core_detail = template.get('core_detail', '').format(**fmt_context)
                makeup_advice = template.get('makeup_advice', '').format(**fmt_context)
                tool_tips = template.get('tool_tips', '').format(**fmt_context)

                full_sim_text = template.get('star_similarity', '').format(**fmt_context)
                advice_part = full_sim_text.split("建设性建议：</b>")[
                    -1].strip() if "建设性建议：</b>" in full_sim_text else full_sim_text

                poetic_mapping = {
                    'eye': '明眸善睐',
                    'brow': '娥眉如画',
                    'nose': '琼鼻挺拔',
                    'lip': '朱唇皓齿'
                }
                display_label = poetic_mapping.get(best_feat, clean_subtype)
                feat_title = f"✨ {display_label}"

                feat_desc = (
                    f"<div style='margin-bottom:12px; font-weight:700; color:#EC407A; font-size:15px;'>📍 经测算，你与{star_n}的相似度为 {score:.1f}%</div>"
                    f"<div style='margin-bottom:15px; color:#546E7A; line-height:1.6;'>{core_detail}</div>"
                    f"<div style='margin-bottom:15px;'><b style='color:#5D4037; font-size:14px;'>💡 1对1建设性建议：</b><br>"
                    f"<span style='font-size:13px; color:#78909C; line-height:1.8;'>{advice_part}</span></div>"
                    f"<div style='margin-bottom:15px;'><b style='color:#5D4037; font-size:14px;'>💄 落地实操妆容建议：</b><br>"
                    f"<span style='font-size:13px; color:#78909C; line-height:1.8;'>{makeup_advice}</span></div>"
                    f"<div><b style='color:#5D4037; font-size:14px;'>🛠️ 专家推荐工具：</b><br>"
                    f"<span style='font-size:13px; color:#78909C; line-height:1.8;'>{tool_tips}</span></div>"
                )
            except Exception as e:
                feat_desc = f"文案格式化异常: {e}"
        else:
            feat_desc = f"您的五官比例极佳，具有天然的辨识度。"

    html_block = (
        f"<div class='highlight-card'>"
        f"<div class='compare-row'>"
        f"<div class='compare-column'>"
        f"<div class='compare-img-box'><img src='data:image/jpeg;base64,{user_full_b64}'></div>"
        f"<div class='external-label'>YOU</div>"
        f"</div>"
        f"<div class='vs-badge'>VS</div>"
        f"<div class='compare-column'>"
        f"<div class='compare-img-box'><img src='data:image/jpeg;base64,{star_full_b64}'></div>"
        f"<div class='external-label'>{star_n.upper()}</div>"
        f"</div>"
        f"</div>"
        f"<div class='analysis-text-box'>"
        f"<div class='analysis-title' style='margin-bottom:15px;'>{feat_title}</div>"
        f"{feat_desc}"
        f"</div>"
        f"</div>"
    )
    st.markdown(html_block, unsafe_allow_html=True)
