import streamlit as st
import requests
import folium
import polyline
from streamlit_folium import folium_static
import pandas as pd

# 제목 설정
st.title("경로 안내 시스템")
st.write("현재위치에서 경복궁, 창경궁을 거쳐 코엑스까지 가는 경로를 보여줍니다.")

# Google Maps API 키 (실제로 사용할 API 키로 대체해야 합니다)
api_key = st.secrets["google_maps_api_key"]  # Streamlit secrets에서 API 키 가져오기

# 위치 정보 (위도, 경도)
locations = {
    "현재위치": {"lat": 37.5665, "lng": 126.9780},  # 서울 시청 (사용자 위치로 대체 가능)
    "경복궁": {"lat": 37.5796, "lng": 126.9770},
    "창경궁": {"lat": 37.5784, "lng": 126.9953},
    "코엑스": {"lat": 37.5127, "lng": 127.0590}
}

# 사용자가 현재 위치를 입력할 수 있는 옵션
use_custom_location = st.checkbox("현재 위치 직접 입력하기")

if use_custom_location:
    col1, col2 = st.columns(2)
    with col1:
        current_lat = st.number_input("현재 위치 위도", value=locations["현재위치"]["lat"], format="%.6f")
    with col2:
        current_lng = st.number_input("현재 위치 경도", value=locations["현재위치"]["lng"], format="%.6f")
    
    locations["현재위치"]["lat"] = current_lat
    locations["현재위치"]["lng"] = current_lng

# 교통수단 선택
travel_mode = st.selectbox(
    "교통수단 선택",
    ["DRIVING", "WALKING", "BICYCLING", "TRANSIT"]
)

# API 요청 함수
def get_directions(origin, destination, waypoints, mode, api_key):
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    
    # 웨이포인트 형식 변환
    waypoints_str = "|".join([f"{wp['lat']},{wp['lng']}" for wp in waypoints])
    
    params = {
        "origin": f"{origin['lat']},{origin['lng']}",
        "destination": f"{destination['lat']},{destination['lng']}",
        "waypoints": waypoints_str,
        "mode": mode.lower(),
        "language": "ko",  # 한국어로 결과 반환
        "key": api_key
    }
    
    response = requests.get(base_url, params=params)
    return response.json()

# 경로 요청 버튼
if st.button("경로 검색"):
    with st.spinner("경로를 검색 중입니다..."):
        # API 요청을 위한 파라미터 준비
        origin = locations["현재위치"]
        destination = locations["코엑스"]
        waypoints = [locations["경복궁"], locations["창경궁"]]
        
        # Google Directions API 호출
        directions_result = get_directions(origin, destination, waypoints, travel_mode, api_key)
        
        # API 응답 확인
        if directions_result["status"] == "OK":
            # 결과 표시
            st.success("경로를 찾았습니다!")
            
            # 지도 생성
            m = folium.Map(location=[origin["lat"], origin["lng"]], zoom_start=12)
            
            # 시작점 마커 추가
            folium.Marker(
                [origin["lat"], origin["lng"]],
                popup="출발지: 현재위치",
                icon=folium.Icon(color="green", icon="play")
            ).add_to(m)
            
            # 경유지 마커 추가
            folium.Marker(
                [locations["경복궁"]["lat"], locations["경복궁"]["lng"]],
                popup="경유지: 경복궁",
                icon=folium.Icon(color="blue")
            ).add_to(m)
            
            folium.Marker(
                [locations["창경궁"]["lat"], locations["창경궁"]["lng"]],
                popup="경유지: 창경궁",
                icon=folium.Icon(color="blue")
            ).add_to(m)
            
            # 도착지 마커 추가
            folium.Marker(
                [destination["lat"], destination["lng"]], 
                popup="도착지: 코엑스",
                icon=folium.Icon(color="red", icon="stop")
            ).add_to(m)
            
            # 경로 정보 및 폴리라인 추가
            route = directions_result["routes"][0]
            
            # 전체 경로의 폴리라인 추가
            for leg in route["legs"]:
                leg_polyline = leg["overview_polyline"]["points"]
                points = polyline.decode(leg_polyline)
                folium.PolyLine(points, color="blue", weight=3, opacity=0.7).add_to(m)
            
            # 지도 표시
            folium_static(m)
            
            # 경로 세부 정보 표시
            total_distance = 0
            total_duration = 0
            
            st.subheader("경로 세부 정보")
            
            # 각 구간별 정보
            segments = []
            
            for i, leg in enumerate(route["legs"]):
                total_distance += leg["distance"]["value"]
                total_duration += leg["duration"]["value"]
                
                if i == 0:
                    start = "현재위치"
                    end = "경복궁"
                elif i == 1:
                    start = "경복궁"
                    end = "창경궁"
                else:
                    start = "창경궁"
                    end = "코엑스"
                    
                segments.append({
                    "구간": f"{start} → {end}",
                    "거리": leg["distance"]["text"],
                    "소요 시간": leg["duration"]["text"]
                })
            
            # 구간별 정보를 표로 표시
            df = pd.DataFrame(segments)
            st.table(df)
            
            # 전체 요약 정보
            st.info(f"총 거리: {total_distance/1000:.2f} km, 총 소요 시간: {total_duration//60} 분")
            
        else:
            st.error(f"경로를 찾을 수 없습니다. 오류: {directions_result['status']}")
            if "error_message" in directions_result:
                st.error(directions_result["error_message"])

# 주의사항 표시
st.markdown("---")
st.caption("이 앱을 사용하려면 유효한 Google Maps API 키가 필요합니다. API 키는 'Google Cloud Console'에서 발급받을 수 있습니다.")
st.caption("Google Maps Directions API는 사용량에 따라 요금이 부과될 수 있습니다.")
