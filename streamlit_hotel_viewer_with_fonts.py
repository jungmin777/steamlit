import streamlit as st
import googlemaps
import pandas as pd
from google.maps import routeoptimization_v1

# Streamlit secrets에서 API 키를 가져옵니다.
gmaps_api_key = st.secrets["google_maps_api_key"]

# Google Maps 클라이언트를 초기화합니다.
gmaps = googlemaps.Client(key=gmaps_api_key)

# Route Optimization API 클라이언트 초기화
client = routeoptimization_v1.RouteOptimizationClient()

# 장소 ID (maps_local 툴에서 얻은 값)
place_ids = [
    "ChIJKwjLMvOifDURqPAMQqxwK-k",  # 서울시청
    "ChIJl4xz5DalfDUR5J-cZDd1bDM",  # 코엑스
    "ChIJp_LDLFqhfDURyi8nlSdK5NI",  # 강남역
]

# 출발지 (서울, 대한민국)
origin = "서울, 대한민국"

# Shipment 모델 생성
shipments = []
for i, place_id in enumerate(place_ids):
    shipment = {
        "id": f"shipment{i+1}",
        "delivery": {"place": {"place_id": place_id}},
    }
    shipments.append(shipment)

# Vehicle 모델 생성 (단순화를 위해 차량 1대만 사용)
vehicles = [
    {
        "id": "vehicle1",
        "start_place": {"place_id": "ChIJKwjLMvOifDURqPAMQqxwK-k"},  # 출발지를 서울시청으로 설정
    }
]

# OptimizeToursRequest 생성
request = routeoptimization_v1.OptimizeToursRequest(
    parent="YOUR_PROJECT_ID",  # Google Cloud 프로젝트 ID로 변경해야 합니다.
    model={"shipments": shipments, "vehicles": vehicles},
)

try:
    # Route Optimization API 호출
    response = client.optimize_tours(request=request)

    # 결과 처리
    if response.routes:
        st.write("## 최적화된 경로:")
        for route in response.routes:
            st.write(f"차량 ID: {route.vehicle_id}")
            for stop in route.stops:
                if stop.waypoint.place.place_id:
                    # place_id를 사용하여 장소 이름 가져오기
                    place_details = gmaps.place(stop.waypoint.place.place_id)
                    st.write(f"- {place_details['result']['name']}")
                else:
                    st.write("- 출발지")  # 출발지
    else:
        st.error("최적화된 경로를 찾을 수 없습니다.")

except Exception as e:
    st.error(f"오류 발생: {e}")
