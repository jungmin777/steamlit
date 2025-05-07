import streamlit as st
import googlemaps
import pandas as pd

# Streamlit secrets에서 API 키를 가져옵니다.
gmaps_api_key = st.secrets["google_maps_api_key"]

# Google Maps 클라이언트를 초기화합니다.
gmaps = googlemaps.Client(key=gmaps_api_key)

# 위도, 경도 정보를 사용하여 장소 3곳을 정의합니다.
locations = [
    {"name": "서울시청", "lat": 37.5665, "lng": 126.9780},
    {"name": "코엑스", "lat": 37.5172, "lng": 127.0473},
    {"name": "강남역", "lat": 37.4979, "lng": 127.0276},
]

# 출발지는 사용자 위치로 가정합니다.
origin = "서울, 대한민국"  # 사용자의 현재 위치를 동적으로 가져올 수 있다면 더 좋습니다.

# 좌표 문자열 형식으로 변환 (Google Maps API가 기대하는 형식)
waypoints = [f"{loc['lat']},{loc['lng']}" for loc in locations[1:]]
destination = f"{locations[0]['lat']},{locations[0]['lng']}"  # 첫 번째 장소를 목적지로 설정

# Directions API를 호출하여 경로를 계산합니다.
directions_result = gmaps.directions(
    origin,
    destination,  # 첫 번째 장소 (서울시청)을 목적지로 설정
    waypoints=waypoints,  # 나머지 장소들을 경유지로 설정 (코엑스, 강남역)
    optimize_waypoints=False,  # 경유지 순서 최적화 비활성화
    mode="driving",  # 이동 수단 설정 (운전)
)

# 디버깅을 위해 결과 출력
st.write("API 응답 결과:")
st.write(f"결과 개수: {len(directions_result)}")

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
    total_distance = 0
    total_duration = 0
    
    for i, leg in enumerate(route["legs"]):
        st.write(f"### 구간 {i+1}")
        st.write(f"출발지: {leg['start_address']}")
        st.write(f"도착지: {leg['end_address']}")
        st.write(f"거리: {leg['distance']['text']}")
        st.write(f"소요 시간: {leg['duration']['text']}")
        total_distance += leg['distance']['value']
        total_duration += leg['duration']['value']
    
    # 총 거리와 시간 계산
    total_distance_km = total_distance / 1000
    total_duration_min = total_duration / 60
    
    st.write("## 총 이동 정보")
    st.write(f"총 거리: {total_distance_km:.2f} km")
    st.write(f"총 소요 시간: {total_duration_min:.0f} 분")
    
    # 경유지 순서를 표시합니다.
    waypoint_order = route.get("waypoint_order")
    if waypoint_order:
        st.write("## 최적화된 경유지 순서:")
        # 출발지
        st.write(f"1. 출발지: {origin}")
        # 중간 경유지
        for i, wp_idx in enumerate(waypoint_order):
            st.write(f"{i+2}. {locations[wp_idx+1]['name']} ({locations[wp_idx+1]['lat']}, {locations[wp_idx+1]['lng']})")
        # 도착지
        st.write(f"{len(waypoint_order)+2}. 도착지: {locations[0]['name']} ({locations[0]['lat']}, {locations[0]['lng']})")
    else:
        st.write("## 경유지 순서:")
        # 출발지
        st.write(f"1. 출발지: {origin}")
        # 중간 경유지
        for i in range(1, len(locations)):
            st.write(f"{i+1}. {locations[i]['name']} ({locations[i]['lat']}, {locations[i]['lng']})")
        # 도착지
        st.write(f"{len(locations)+1}. 도착지: {locations[0]['name']} ({locations[0]['lat']}, {locations[0]['lng']})")
else:
    st.error("경로를 찾을 수 없습니다.")
    
    # 디버깅 정보 추가
    st.write("### 디버깅 정보")
    st.write(f"API 키 설정 여부: {'성공' if gmaps_api_key else '실패'}")
    st.write(f"출발지: {origin}")
    st.write(f"목적지: {destination}")
    st.write(f"경유지: {waypoints}")
