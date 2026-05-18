import streamlit as st
import analysis_home    # 导入首页视图
import analysis_result  # 导入结果页视图

def show():
    # 状态管理
    if 'analyzed' not in st.session_state:
        st.session_state.analyzed = False

    # 简单的条件路由
    if not st.session_state.analyzed:
        analysis_home.show()   # 显示首页
    else:
        analysis_result.show() # 显示结果页

if __name__ == "__main__":
    show()