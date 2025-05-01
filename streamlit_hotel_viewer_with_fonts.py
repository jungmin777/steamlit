import streamlit as st
import folium
from streamlit_folium import st_folium

st.title("간단한 지도 테스트")

# 기본 지도 생성
map_center = [37.5665, 126.9780]  # 서울 시청
m = folium.Map(location=map_center, zoom_start=13)

# 마커 추가
folium.Marker(
    map_center, 
    tooltip="서울 시청", 
    icon=folium.Icon(color="red")
).add_to(m)

# 지도 표시
st_folium(m, width=700, height=500)

# 버튼 추가
if st.button("마커 추가"):
    st.write("마커를 추가합니다.")
    m2 = folium.Map(location=map_center, zoom_start=13)
    
    # 여러 마커 추가
    folium.Marker([37.5665, 126.9780], tooltip="서울 시청").add_to(m2)
    folium.Marker([37.5796, 126.9770], tooltip="경복궁").add_to(m2)
    folium.Marker([37.5511, 126.9882], tooltip="남산타워").add_to(m2)
    
    st_folium(m2, width=700, height=500, key="second_map")
