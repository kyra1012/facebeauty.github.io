import streamlit as st
import styles
from data_processor import data_service
import streamlit.components.v1 as components


def show():
    st.markdown('<div class="section-header">🏆 十年冠军殿堂 (Hall of Fame)</div>', unsafe_allow_html=True)
    st.caption("历年登顶冠军风采回顾 / A gallery of the #1 champion face from each year.")

    champ_data = data_service.get_champion_gallery()

    # 构建一个更高级的 Swiper 卡片展示
    slides = ""
    for item in champ_data:
        img_src = data_service.get_image_base64(item['img_path'])
        slides += f"""
        <div class="swiper-slide">
            <img src="{img_src}" />
            <div class="slide-content">
                <div class="slide-year">{item['year']}</div>
                <div class="slide-desc">{item['desc']}</div>
            </div>
        </div>"""

    html_code = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8"/><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css" />
    <style>
        body {{ margin:0; font-family: sans-serif; }}
        .swiper {{ width: 100%; padding-top: 50px; padding-bottom: 50px; }}
        .swiper-slide {{
            background-position: center; background-size: cover;
            width: 300px; height: 450px;
            background: #fff; border-radius: 20px; overflow: hidden;
            box-shadow: 0 15px 50px rgba(0,0,0,0.2);
        }}
        .swiper-slide img {{ display: block; width: 100%; height: 75%; object-fit: cover; }}
        .slide-content {{ height: 25%; padding: 20px; text-align: center; }}
        .slide-year {{ font-size: 32px; font-weight: 900; color: #EC407A; line-height: 1; }}
        .slide-desc {{ font-size: 14px; color: #666; margin-top: 10px; font-weight: bold; }}
    </style></head><body>
    <div class="swiper mySwiper"><div class="swiper-wrapper">{slides}</div><div class="swiper-pagination"></div></div>
    <script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
    <script>
        var swiper = new Swiper(".mySwiper", {{
            effect: "coverflow",
            grabCursor: true,
            centeredSlides: true,
            slidesPerView: "auto",
            coverflowEffect: {{ rotate: 50, stretch: 0, depth: 100, modifier: 1, slideShadows: true }},
            pagination: {{ el: ".swiper-pagination" }}
        }});
    </script>
    </body></html>
    """
    components.html(html_code, height=600)