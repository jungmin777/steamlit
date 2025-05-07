import streamlit as st
import googlemaps
import pandas as pd

# Streamlit secrets에서 API 키를 가져옵니다.
gmaps_api_key = st.secrets["google_maps_api_key"]

# Google Maps 클라이언트를 초기화합니다.
gmaps = googlemaps.Client(key=gmaps_api_key)

# 위도, 경도 정보를 사용하여 장소 3곳을 정의합니다.
locations = [
    {"lat": 37.5665, "lng": 126.9780},  # 서울시청
    {"lat": 37.5172, "lng": 127.0473},  # 코엑스
    {"lat": 37.4979, "lng": 127.0276},  # 강남역
]

# 출발지는 사용자 위치로 가정합니다.
origin = "서울, 대한민국"  # 사용자의 현재 위치를 동적으로 가져올 수 있다면 더 좋습니다.

# 장소들의 위도, 경도를 스트링으로 변환합니다.
waypoints = [f"{loc['lat']},{loc['lng']}" for loc in locations]

# Directions API를 호출하여 경로를 계산합니다.
directions_result = gmaps.directions(
    origin,
    locations[0],  # 첫 번째 장소를 목적지로 설정
    waypoints=waypoints[1:],  # 나머지 장소들을 경유지로 설정
    optimize_waypoints=True,  # 경유지 순서 최적화
    mode="driving",  # 이동 수단 설정 (운전)
)

if directions_result:
    # 경로 정보를 추출합니다.
    route = directions_result[0]
    # 각 단계를 순회하며 위도, 경도 정보를 추출합니다.
    path = []
    for leg in route["legs"]:
        for step in leg["steps"]:
            lat = step["start_location"]["lat"]
            lng = step["start_location"]["lng"]
            path.append((lat, lng))
        # 마지막 단계의 도착 위치를 추가합니다.
        lat = leg["steps"][-1]["end_location"]["lat"]
        lng = leg["steps"][-1]["end_location"]["lng"]
        path.append((lat, lng))

    # 경로를 DataFrame으로 변환합니다.
    path_df = pd.DataFrame(path, columns=["lat", "lon"])

    # 스트림릿 지도를 사용하여 경로를 표시합니다.
    st.map(path_df)

    # 경로 요약 정보를 표시합니다.
    st.write("## 경로 요약")
    st.write(f"총 거리: {route['legs'][0]['distance']['text']}")
    st.write(f"총 소요 시간: {route['legs'][0]['duration']['text']}")

    # 경유지 순서를 표시합니다.
    waypoint_order = route.get("waypoint_order")
    if waypoint_order:
        st.write("## 최적화된 경유지 순서:")
        for i in waypoint_order:
            st.write(f"- {locations[i]}")
    else:
        st.write("## 경유지 순서:")
        for loc in locations:
            st.write(f"- {loc}")

else:
    st.error("경로를 찾을 수 없습니다.")
