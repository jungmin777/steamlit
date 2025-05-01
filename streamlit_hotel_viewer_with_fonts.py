import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
import time
from datetime import datetime
import json
import numpy as np

st.set_page_config(page_title="서울 위치 데이터 통합 지도", layout="wide")

# -------------------------------
# 초기 세션 상태 설정
if "users" not in st.session_state:
    st.session_state.users = {"admin": "admin"}  # 기본 관리자 계정

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "current_page" not in st.session_state:
    st.session_state.current_page = "login"  # 기본 시작 페이지를 로그인으로 설정

if 'clicked_location' not in st.session_state:
    st.session_state.clicked_location = None
if 'nearby_places' not in st.session_state:
    st.session_state.nearby_places = []
if 'selected_recommendations' not in st.session_state:
    st.session_state.selected_recommendations = []
if 'language' not in st.session_state:
    st.session_state.language = "한국어"
    
# 추가: 지도 유형 설정 (folium 또는 google)
if 'map_type' not in st.session_state:
    st.session_state.map_type = "folium"

# 추가: Google Maps API 키 저장
if 'google_maps_api_key' not in st.session_state:
    st.session_state.google_maps_api_key = ""
    
# 사용자별 방문 기록 저장
if "user_visits" not in st.session_state:
    st.session_state.user_visits = {}

# 앱 시작시 저장된 데이터 불러오기 시도
if "data_loaded" not in st.session_state:
    try:
        with open("session_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # 데이터 복원
            st.session_state.users = data.get("users", {"admin": "admin"})
            st.session_state.user_visits = data.get("user_visits", {})
            # API 키도 복원 (있는 경우)
            if "google_maps_api_key" in data:
                st.session_state.google_maps_api_key = data["google_maps_api_key"]
            # 지도 유형 복원 (있는 경우)
            if "map_type" in data:
                st.session_state.map_type = data["map_type"]
    except:
        pass  # 파일이 없거나 오류 발생 시 무시
    st.session_state.data_loaded = True

# -------------------------------
# Google Maps HTML 생성 함수
def create_google_map_html(center_lat, center_lng, locations, api_key, language="ko"):
    # 언어 코드 설정
    lang_code = "ko" if language == "한국어" else "en" if language == "영어" else "zh-CN"
    
    # 마커 데이터 생성
    markers_js = ""
    for idx, loc in enumerate(locations):
        name = loc["name"].replace("'", "\\'")  # 따옴표 이스케이프 처리
        lat, lng = loc["lat"], loc["lng"]
        
        # 방문 장소인지 확인하여 아이콘 설정
        icon_color = "purple" if loc.get("visited", False) else "green"
        icon_url = f"http://maps.google.com/mapfiles/ms/icons/{icon_color}-dot.png"
        
        markers_js += f"""
        var marker{idx} = new google.maps.Marker({{
            position: {{ lat: {lat}, lng: {lng} }},
            map: map,
            title: '{name}',
            icon: '{icon_url}'
        }});

        var infowindow{idx} = new google.maps.InfoWindow({{
            content: '<div style="padding: 10px;"><strong>{name}</strong><br>({lat:.5f}, {lng:.5f})</div>'
        }});

        marker{idx}.addListener('click', function() {{
            closeAllInfoWindows();
            infowindow{idx}.open(map, marker{idx});
            openInfoWindow = infowindow{idx};
            
            // 클릭 이벤트 데이터를 부모 창으로 전달
            parent.postMessage({{
                'type': 'marker_click',
                'name': '{name}',
                'lat': {lat},
                'lng': {lng},
                'idx': {idx}
            }}, "*");
        }});
        
        // 마커에 마우스 오버 시 애니메이션
        marker{idx}.addListener('mouseover', function() {{
            this.setAnimation(google.maps.Animation.BOUNCE);
            setTimeout(() => {{ this.setAnimation(null); }}, 750);
        }});
        """

    # 현재 위치 마커 추가
    current_location_js = f"""
    // 현재 위치 마커
    var currentLocationMarker = new google.maps.Marker({{
        position: {{ lat: {center_lat}, lng: {center_lng} }},
        map: map,
        title: '내 위치',
        icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
    }});
    
    var currentLocationInfo = new google.maps.InfoWindow({{
        content: '<div style="padding: 10px;"><strong>내 현재 위치</strong><br>({center_lat:.5f}, {center_lng:.5f})</div>'
    }});
    
    currentLocationMarker.addListener('click', function() {{
        closeAllInfoWindows();
        currentLocationInfo.open(map, currentLocationMarker);
        openInfoWindow = currentLocationInfo;
    }});
    """

    # HTML 생성
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>서울 위치 데이터 통합 지도</title>
        <meta charset="utf-8">
        <style>
            #map {{
                height: 500px;
                width: 100%;
            }}
            .custom-map-control-button {{
                background-color: #fff;
                border: 0;
                border-radius: 2px;
                box-shadow: 0 1px 4px -1px rgba(0, 0, 0, 0.3);
                margin: 10px;
                padding: 0 0.5em;
                font: 400 18px Roboto, Arial, sans-serif;
                overflow: hidden;
                height: 40px;
                cursor: pointer;
            }}
            .custom-map-control-button:hover {{
                background: rgb(235, 235, 235);
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            // 전역 변수로 현재 열린 정보창 저장
            var openInfoWindow = null;
            
            // 모든 정보창 닫기 함수
            function closeAllInfoWindows() {{
                if (openInfoWindow) {{
                    openInfoWindow.close();
                }}
            }}
            
            function initMap() {{
                // 서울 중심으로 지도 생성
                var map = new google.maps.Map(document.getElementById('map'), {{
                    zoom: 12,
                    center: {{ lat: {center_lat}, lng: {center_lng} }},
                    mapTypeControl: true,
                    zoomControl: true,
                    scaleControl: true,
                    streetViewControl: true,
                    fullscreenControl: true,
                }});
                
                // 현재 위치 가져오기 함수
                function getCurrentLocation() {{
                    if (navigator.geolocation) {{
                        navigator.geolocation.getCurrentPosition(function(position) {{
                            var currentLocation = {{
                                lat: position.coords.latitude,
                                lng: position.coords.longitude
                            }};
                            
                            // 부모 창에 현재 위치 전달
                            parent.postMessage({{
                                'type': 'current_location',
                                'lat': currentLocation.lat,
                                'lng': currentLocation.lng
                            }}, "*");
                            
                            map.setCenter(currentLocation);
                            map.setZoom(15);
                            
                            // 현재 위치 마커 위치 업데이트
                            currentLocationMarker.setPosition(currentLocation);
                            
                        }}, function() {{
                            alert('위치 정보를 가져올 수 없습니다.');
                        }});
                    }} else {{
                        alert('이 브라우저에서는 위치 정보 기능을 지원하지 않습니다.');
                    }}
                }}
                
                // 현재 위치 버튼 생성
                var locationButton = document.createElement('button');
                locationButton.textContent = '📍 내 위치 찾기';
                locationButton.classList.add('custom-map-control-button');
                locationButton.addEventListener('click', getCurrentLocation);
                
                // 버튼을 지도의 오른쪽 상단에 추가
                map.controls[google.maps.ControlPosition.TOP_RIGHT].push(locationButton);

                // 지도 클릭 이벤트 처리
                map.addListener('click', function(e) {{
                    var clickedLat = e.latLng.lat();
                    var clickedLng = e.latLng.lng();
                    
                    // 클릭 위치를 부모 창에 전달
                    parent.postMessage({{
                        'type': 'map_click',
                        'lat': clickedLat,
                        'lng': clickedLng
                    }}, "*");
                    
                    // 열린 정보창 닫기
                    closeAllInfoWindows();
                }});
                
                // 현재 위치 마커 추가
                {current_location_js}
                
                // 마커 추가
                {markers_js}
            }}
        </script>
        <script async defer
                src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap&language={lang_code}">
        </script>
    </body>
    </html>
    """
    return html

# -------------------------------
# 페이지 전환 함수
def change_page(page):
    st.session_state.current_page = page
    # 페이지 전환 시 일부 상태 초기화
    if page != "map":
        st.session_state.clicked_location = None
        st.session_state.nearby_places = []
        st.session_state.selected_recommendations = []

# -------------------------------
# 사용자 인증 함수
def authenticate_user(username, password):
    return username in st.session_state.users and st.session_state.users[username] == password

def register_user(username, password):
    if username in st.session_state.users:
        return False
    st.session_state.users[username] = password
    return True

# -------------------------------
# 방문 기록 추가 함수
def add_visit(username, place_name, lat, lng):
    if username not in st.session_state.user_visits:
        st.session_state.user_visits[username] = []
    
    # 방문 데이터 생성
    visit_data = {
        "place_name": place_name,
        "latitude": lat,
        "longitude": lng,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "rating": None  # 나중에 평점을 추가할 수 있음
    }
    
    # 중복 방문 검사 (같은 날, 같은 장소)
    is_duplicate = False
    for visit in st.session_state.user_visits[username]:
        if (visit["place_name"] == place_name and 
            visit["date"] == visit_data["date"]):
            is_duplicate = True
            break
    
    if not is_duplicate:
        st.session_state.user_visits[username].append(visit_data)
        return True
    return False

# -------------------------------
# 세션 상태 데이터 저장/불러오기 함수
def save_session_data():
    """세션 데이터를 JSON 파일로 저장"""
    try:
        data = {
            "users": st.session_state.users,
            "user_visits": st.session_state.user_visits,
            "google_maps_api_key": st.session_state.google_maps_api_key,
            "map_type": st.session_state.map_type
        }
        with open("session_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"데이터 저장 오류: {e}")
        return False

def load_session_data():
    """저장된 세션 데이터를 JSON 파일에서 불러오기"""
    try:
        with open("session_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 데이터 복원
        st.session_state.users = data.get("users", {})
        st.session_state.user_visits = data.get("user_visits", {})
        
        # API 키 복원 (있는 경우)
        if "google_maps_api_key" in data:
            st.session_state.google_maps_api_key = data["google_maps_api_key"]
            
        # 지도 유형 복원 (있는 경우)
        if "map_type" in data:
            st.session_state.map_type = data["map_type"]
            
        return True
    except FileNotFoundError:
        # 파일이 없는 경우 초기 상태 유지
        return False
    except Exception as e:
        st.error(f"데이터 불러오기 오류: {e}")
        return False

# -------------------------------
# 사용자 위치 가져오기
def get_user_location():
    try:
        location = get_geolocation()
        if location and "coords" in location:
            return [location["coords"]["latitude"], location["coords"]["longitude"]]
    except:
        pass
    return [37.5665, 126.9780]  # 기본 서울 시청 좌표

# -------------------------------
# 로그인/회원가입 페이지
def login_page():
    st.title("🔐 로그인 또는 회원가입")
    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
        username = st.text_input("아이디", key="login_username")
        password = st.text_input("비밀번호", type="password", key="login_password")
        if st.button("로그인"):
            if authenticate_user(username, password):
                st.success("🎉 로그인 성공!")
                st.session_state.logged_in = True
                st.session_state.username = username
                change_page("menu")  # 로그인 성공 시 메뉴 페이지로 이동
                st.rerun()
            else:
                st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")

    with tab2:
        new_user = st.text_input("새 아이디", key="register_username")
        new_pw = st.text_input("새 비밀번호", type="password", key="register_password")
        if st.button("회원가입"):
            if register_user(new_user, new_pw):
                st.success("✅ 회원가입 완료!")
                st.session_state.logged_in = True
                st.session_state.username = new_user
                change_page("menu")  # 회원가입 성공 시 메뉴 페이지로 이동
                st.rerun()
            else:
                st.warning("⚠️ 이미 존재하는 아이디입니다.")

# -------------------------------
# 메뉴 페이지
def menu_page():
    st.title(f"👋 {st.session_state.username}님, 환영합니다!")
    
    st.subheader("메뉴를 선택해주세요")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📍 지도 보기", use_container_width=True):
            change_page("map")
            st.rerun()
    
    with col2:
        if st.button("📝 내 방문 기록", use_container_width=True):
            change_page("history")
            st.rerun()
    
    with col3:
        if st.button("⚙️ 설정", use_container_width=True):
            change_page("settings")
            st.rerun()
    
    # 로그아웃 버튼
    if st.button("🔓 로그아웃", key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        change_page("login")
        st.rerun()

# -------------------------------
# 지도 페이지
def map_page():
    st.title("📍 서울시 공공 위치 데이터 통합 지도")
    
    # 뒤로가기 버튼
    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        st.rerun()

    col1, col2, col3 = st.columns([6, 1, 2])
    with col3:
        selected_language = st.selectbox(
            "🌏 Language", 
            ["🇰🇷 한국어", "🇺🇸 English", "🇨🇳 中文"],
            index=0 if st.session_state.language == "한국어" else 1 if st.session_state.language == "영어" else 2
        )
        language_map_display = {
            "🇰🇷 한국어": "한국어",
            "🇺🇸 English": "영어",
            "🇨🇳 中文": "중국어"
        }
        st.session_state.language = language_map_display[selected_language]

        # 지도 유형 선택 - 이 부분 추가
        map_type = st.radio(
            "지도 유형",
            ["Folium", "Google Maps"],
            index=0 if st.session_state.map_type == "folium" else 1
        )
        st.session_state.map_type = map_type.lower().replace(" ", "_")

    # 카테고리 선택을 사이드바로 이동
    with st.sidebar:
        st.header("카테고리 선택")
        
        # 카테고리명으로 변환하여 표시
        category_names = [
            "외국인전용 관광기념품 판매점",
            "문화행사 공공서비스예약",
            "종로구 관광데이터",
            "체육시설 공연행사",
            "시립미술관 전시정보"
        ]
        
        selected_category = st.selectbox("📁 카테고리", category_names)
    
    # 사용자 위치 가져오기
    user_location = get_user_location()
    center = user_location
    st.session_state.user_location = center

    # 샘플 장소 마커 추가
    sample_locations = [
        {"name": "경복궁", "lat": 37.5796, "lng": 126.9770},
        {"name": "남산타워", "lat": 37.5511, "lng": 126.9882},
        {"name": "동대문 디자인 플라자", "lat": 37.5669, "lng": 127.0093},
        {"name": "명동성당", "lat": 37.5635, "lng": 126.9877},
        {"name": "서울숲", "lat": 37.5445, "lng": 127.0374},
    ]
    
    # 카테고리에 따라 다른 위치 표시 (시뮬레이션)
    if selected_category == "외국인전용 관광기념품 판매점":
        locations = sample_locations[:2]  # 앞의 두개만
    elif selected_category == "문화행사 공공서비스예약":
        locations = sample_locations[1:3]  # 중간 두개
    elif selected_category == "종로구 관광데이터":
        locations = sample_locations[2:4]  # 중간~끝
    else:
        locations = sample_locations  # 전체
    
    # 방문했던 장소 표시 처리
    username = st.session_state.username
    visited_places = []
    if username in st.session_state.user_visits and st.session_state.user_visits[username]:
        for visit in st.session_state.user_visits[username]:
            visited_places.append({
                "name": visit["place_name"],
                "lat": visit["latitude"],
                "lng": visit["longitude"],
                "visited": True
            })
    
    # Google Maps나 Folium 중 선택한 지도 유형 표시
    st.subheader("🗺️ 지도")
    
    if st.session_state.map_type == "google_maps":
        # Google Maps API 키 가져오기
        api_key = st.session_state.google_maps_api_key
        
        if not api_key:
            api_key = st.text_input("Google Maps API 키를 입력하세요", type="password")
            if api_key:
                st.session_state.google_maps_api_key = api_key
                save_session_data()  # API 키 저장
            else:
                st.warning("Google Maps를 사용하려면 API 키가 필요합니다.")
                st.info("Google Cloud Console에서 Maps JavaScript API를 활성화하고 API 키를 생성하세요.")
                
        if api_key:
            # Google Maps로 표시
            all_locations = locations.copy()
            
            # 방문 장소 추가
            for place in visited_places:
                # 이미 표시된 위치는 건너뛰기 
                if not any(loc["lat"] == place["lat"] and loc["lng"] == place["lng"] for loc in all_locations):
                    all_locations.append(place)
            
            google_map_html = create_google_map_html(
                center_lat=center[0], 
                center_lng=center[1], 
                locations=all_locations, 
                api_key=api_key,
                language=st.session_state.language
            )
            
            # 지도 표시
            st.components.v1.html(google_map_html, height=500, scrolling=False)
            
            # JavaScript 메시지 이벤트 처리 (클릭 이벤트 등)
            # 참고: 실제로는 추가 JavaScript 작업이 필요할 수 있음
            
            # 클릭한 위치가 있을 경우 처리 (임시로 session_state 사용)
            if st.session_state.clicked_location:
                clicked_lat, clicked_lng = st.session_state.clicked_location["lat"], st.session_state.clicked_location["lng"]
                st.subheader(f"📍 클릭한 위치: ({clicked_lat:.5f}, {clicked_lng:.5f})")
                
                # 나머지 처리는 Folium 예제와 동일하게...
                # (이 부분은 실제로 Google Maps에서 데이터를 받아와 처리해야 함)
    else:
        # Folium으로 지도 표시 (기존 코드)
        m = folium.Map(location=center, zoom_start=13)
        
        # 현재 위치 마커 추가
        folium.Marker(
            center, 
            tooltip="📍 내 위치", 
            icon=folium.Icon(color="blue", icon="star")
        ).add_to(m)
    
        # 마커 추가
        for loc in locations:
            folium.Marker(
                location=[loc["lat"], loc["lng"]],
                tooltip=loc["name"],
                icon=folium.Icon(color="green"),
                popup=folium.Popup(f"{loc['name']}<br>({loc['lat']:.5f}, {loc['lng']:.5f})", max_width=300)
            ).add_to(m)
        
        # 방문했던 장소 마커 추가 (보라색 마커로 표시)
        if username in st.session_state.user_visits and st.session_state.user_visits[username]:
            for visit in st.session_state.user_visits[username]:
                folium.Marker(
                    location=[visit["latitude"], visit["longitude"]],
                    tooltip=f"✅ 방문: {visit['place_name']}",
                    icon=folium.Icon(color="purple", icon="check"),
                    popup=folium.Popup(f"방문: {visit['place_name']}<br>날짜: {visit['date']}", max_width=300)
                ).add_to(m)
        
        # 지도 표시
        map_data = st_folium(m, width=700, height=500, key="main_map")
        
        # 클릭 이벤트 처리
        if map_data and 'last_clicked' in map_data:
            clicked_lat, clicked_lng = map_data['last_clicked']['lat'], map_data['last_clicked']['lng']
            st.session_state.clicked_location = {'lat': clicked_lat, 'lng': clicked_lng}
            
            st.subheader(f"📍 클릭한 위치: ({clicked_lat:.5f}, {clicked_lng:.5f})")
            
            # 주변 장소 찾기 (가장 가까운 샘플 장소들 찾기)
            nearby_places = []
            for loc in sample_locations:
                place_lat, place_lng = loc["lat"], loc["lng"]
                distance = geodesic((clicked_lat, clicked_lng), (place_lat, place_lng)).meters
                if distance <= 2000:  # 2km 이내
                    nearby_places.append((distance, loc["name"], place_lat, place_lng))
            
            nearby_places.sort(key=lambda x: x[0])
            st.session_state.nearby_places = nearby_places
    
    # 주변 장소 표시 (지도 유형에 상관없이 동일하게 작동)
    if st.session_state.clicked_location and st.session_state.nearby_places:
        st.subheader("🔍 주변 장소 (2km 이내)")
        if st.session_state.nearby_places:
            for i, (dist, name, lat, lng) in enumerate(st.session_state.nearby_places):
                cols = st.columns([0.1, 0.7, 0.2, 0.2])
                cols[1].markdown(f"**{name}** - {dist:.1f}m")
                
                # 장소 선택 버튼
                if cols[2].button(f"선택 {i+1}", key=f"nearby_select_{i}"):
                    if len(st.session_state.selected_recommendations) < 3:
                        st.session_state.selected_recommendations.append((name, lat, lng))
                    else:
                        st.warning("최대 3개까지 선택할 수 있습니다.")
                    st.rerun()
                
                # 방문 기록 추가 버튼
                if cols[3].button(f"방문 🏁", key=f"visit_{i}"):
                    if add_visit(st.session_state.username, name, lat, lng):
                        st.success(f"'{name}' 방문 기록이 추가되었습니다!")
                        # 1초 후 페이지 새로고침
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info("이미 오늘 방문한 장소입니다.")
        else:
            st.info("주변 2km 이내에 장소가 없습니다.")
    
    if st.session_state.selected_recommendations:
        st.subheader("✅ 선택된 추천 장소")
        for i, (name, lat, lng) in enumerate(st.session_state.selected_recommendations):
            cols = st.columns([0.05, 0.85, 0.1])
            cols[1].write(f"{name} - ({lat:.5f}, {lng:.5f})")
            if cols[2].button("❌", key=f"remove_{i}"):
                st.session_state.selected_recommendations.pop(i)
                st.rerun()

    # Excel 파일 업로드 섹션 추가 (Google Maps API 테스트를 위한 데이터)
    st.divider()
    st.subheader("📊 엑셀 데이터 업로드")
    
    uploaded_file = st.file_uploader("서울시 위치 데이터 Excel 파일 업로드", type=["xlsx"])
    if uploaded_file is not None:
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # 필요한 열 확인
            required_cols = ['명칭(한국어)', 'X좌표', 'Y좌표']
            if all(col in df.columns for col in required_cols):
                # 데이터 미리보기
                st.write("데이터 미리보기:")
                st.dataframe(df[required_cols].head())
                
                # 유효한 좌표 데이터만 필터링
                df = df.dropna(subset=['X좌표', 'Y좌표'])
                valid_coords = (df['X좌표'] >= 124) & (df['X좌표'] <= 132) & (df['Y좌표'] >= 33) & (df['Y좌표'] <= 43)
                df = df[valid_coords]
                
                if not df.empty:
                    st.success(f"총 {len(df)}개의 유효한 위치 데이터를 찾았습니다.")
                    
                    # 지도에 표시하기 버튼
                    if st.button("이 데이터를 지도에 표시하기"):
                        # 데이터 형식 변환
                        excel_locations = []
                        for _, row in df.iterrows():
                            excel_locations.append({
                                "name": row['명칭(한국어)'],
                                "lat": row['Y좌표'],
                                "lng": row['X좌표']
                            })
                        
                        # Google Maps인 경우 HTML 재생성
                        if st.session_state.map_type == "google_maps" and st.session_state.google_maps_api_key:
                            google_map_html = create_google_map_html(
                                center_lat=center[0], 
                                center_lng=center[1], 
                                locations=excel_locations, 
                                api_key=st.session_state.google_maps_api_key,
                                language=st.session_state.language
                            )
                            
                            # 지도 새로 표시
                            st.subheader("🗺️ 업로드한 데이터 지도")
                            st.components.v1.html(google_map_html, height=500, scrolling=False)
                        
                        # Folium인 경우 새 지도 생성
                        else:
                            excel_map = folium.Map(location=center, zoom_start=11)
                            
                            # 현재 위치 마커
                            folium.Marker(
                                center, 
                                tooltip="📍 내 위치", 
                                icon=folium.Icon(color="blue", icon="star")
                            ).add_to(excel_map)
                            
                            # 엑셀 데이터 마커 추가
                            for loc in excel_locations:
                                folium.Marker(
                                    location=[loc["lat"], loc["lng"]],
                                    tooltip=loc["name"],
                                    icon=folium.Icon(color="red"),  # 엑셀 데이터는 빨간색으로 구분
                                    popup=folium.Popup(f"{loc['name']}<br>({loc['lat']:.5f}, {loc['lng']:.5f})", max_width=300)
                                ).add_to(excel_map)
                            
                            # 지도 표시
                            st.subheader("🗺️ 업로드한 데이터 지도")
                            st_folium(excel_map, width=700, height=500, key="excel_map")
                else:
                    st.warning("유효한 좌표 데이터가 없습니다.")
            else:
                st.error("필요한 열(명칭(한국어), X좌표, Y좌표)이 엑셀 파일에 존재하지 않습니다.")
        except Exception as e:
            st.error(f"엑셀 파일 처리 중 오류가 발생했습니다: {str(e)}")

# -------------------------------
# 방문 기록 페이지
def history_page():
    st.title("📝 나의 방문 기록")
    
    # 뒤로가기 버튼
    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        st.rerun()
    
    username = st.session_state.username
    
    # 방문 기록 표시
    if username in st.session_state.user_visits and st.session_state.user_visits[username]:
        # 방문기록 지도로 보기
        st.subheader("🗺️ 방문 기록 지도")
        
        # 사용자 위치 또는 서울 시청을 중심으로
        user_location = get_user_location()
        
        # Google Maps와 Folium 중 선택
        if st.session_state.map_type == "google_maps" and st.session_state.google_maps_api_key:
            # 방문 장소 목록 생성
            visit_locations = []
            for visit in st.session_state.user_visits[username]:
                visit_locations.append({
                    "name": visit["place_name"],
                    "lat": visit["latitude"],
                    "lng": visit["longitude"],
                    "visited": True
                })
            
            # Google Maps HTML 생성
            visit_map_html = create_google_map_html(
                center_lat=user_location[0], 
                center_lng=user_location[1], 
                locations=visit_locations, 
                api_key=st.session_state.google_maps_api_key,
                language=st.session_state.language
            )
            
            # 지도 표시
            st.components.v1.html(visit_map_html, height=400, scrolling=False)
        else:
            # Folium 지도 생성
            visit_map = folium.Map(location=user_location, zoom_start=12)
            
            # 현재 위치 마커
            folium.Marker(
                user_location, 
                tooltip="📍 내 현재 위치", 
                icon=folium.Icon(color="blue", icon="star")
            ).add_to(visit_map)
            
            # 방문 장소 마커 추가
            for idx, visit in enumerate(st.session_state.user_visits[username]):
                popup_content = f"""
                <b>{visit['place_name']}</b><br>
                방문 일시: {visit['timestamp']}<br>
                """
                
                if visit.get('rating'):
                    stars = "⭐" * int(visit['rating'])
                    popup_content += f"평점: {stars} ({visit['rating']})"
                
                # 마커 색상은 방문 순서에 따라 다양하게
                colors = ["purple", "darkpurple", "cadetblue", "pink", "darkred", "darkblue"]
                color_idx = idx % len(colors)
                
                folium.Marker(
                    location=[visit["latitude"], visit["longitude"]],
                    tooltip=f"{idx+1}. {visit['place_name']}",
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(color=colors[color_idx])
                ).add_to(visit_map)
            
            # 지도 표시
            st_folium(visit_map, width=700, height=400, key="history_map")
        
        # 목록으로 방문 기록 표시
        st.subheader("📋 방문 기록 목록")
        
        # 정렬 옵션
        sort_option = st.radio(
            "정렬 방식",
            ["최신순", "오래된순", "이름순"],
            horizontal=True
        )
        
        if sort_option == "최신순":
            sorted_visits = sorted(st.session_state.user_visits[username], 
                                  key=lambda x: x['timestamp'], reverse=True)
        elif sort_option == "오래된순":
            sorted_visits = sorted(st.session_state.user_visits[username], 
                                  key=lambda x: x['timestamp'])
        else:  # 이름순
            sorted_visits = sorted(st.session_state.user_visits[username], 
                                  key=lambda x: x['place_name'])
        
        for i, visit in enumerate(sorted_visits):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{visit['place_name']}**")
                st.markdown(f"방문 일시: {visit['timestamp']}")
                
                # 평점 입력 또는 표시
                if 'rating' not in visit or visit['rating'] is None:
                    new_rating = st.slider(f"평점 입력: {visit['place_name']}", 
                                          min_value=1, max_value=5, value=3, 
                                          key=f"rating_{i}")
                    if st.button("평점 저장", key=f"save_rating_{i}"):
                        visit['rating'] = new_rating
                        st.success(f"{visit['place_name']}에 대한 평점이 저장되었습니다!")
                        save_session_data()  # 평점 저장 시 데이터도 저장
                        time.sleep(1)
                        st.rerun()
                else:
                    st.markdown(f"⭐ 평점: {'⭐' * int(visit['rating'])} ({visit['rating']})")
            
            with col2:
                # 삭제 버튼
                if st.button("🗑️ 삭제", key=f"delete_visit_{i}"):
                    st.session_state.user_visits[username].remove(visit)
                    save_session_data()  # 삭제 시 데이터도 저장
                    st.success("방문 기록이 삭제되었습니다.")
                    time.sleep(1)
                    st.rerun()
            
            st.divider()
        
        # 방문 통계
        st.subheader("📊 방문 통계")
        total_visits = len(st.session_state.user_visits[username])
        unique_places = len(set([v['place_name'] for v in st.session_state.user_visits[username]]))
        avg_rating = 0
        rated_visits = [v for v in st.session_state.user_visits[username] if v.get('rating') is not None]
        if rated_visits:
            avg_rating = sum([v['rating'] for v in rated_visits]) / len(rated_visits)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("총 방문 횟수", f"{total_visits}회")
        col2.metric("방문한 장소 수", f"{unique_places}곳")
        col3.metric("평균 평점", f"{avg_rating:.1f}/5")
        
        # 데이터 내보내기
        st.subheader("💾 데이터 내보내기")
        
        # JSON 형식으로 데이터 변환
        visit_data_json = json.dumps(st.session_state.user_visits[username], ensure_ascii=False, indent=2)
        
        st.download_button(
            label="📥 방문 기록 다운로드 (JSON)",
            data=visit_data_json,
            file_name=f"{username}_visit_history.json",
            mime="application/json"
        )
        
    else:
        st.info("아직 방문 기록이 없습니다. 지도에서 장소를 방문하면 여기에 기록됩니다.")
        
        # 예시 데이터 보여주기
        if st.button("예시 데이터 생성"):
            example_visits = [
                {"place_name": "경복궁", "latitude": 37.5796, "longitude": 126.9770, "timestamp": "2023-10-15 14:30:00", "date": "2023-10-15", "rating": 5},
                {"place_name": "남산타워", "latitude": 37.5511, "longitude": 126.9882, "timestamp": "2023-10-10 12:15:00", "date": "2023-10-10", "rating": 4},
                {"place_name": "동대문 디자인 플라자", "latitude": 37.5669, "longitude": 127.0093, "timestamp": "2023-10-05 16:45:00", "date": "2023-10-05", "rating": 4.5}
            ]
            
            if username not in st.session_state.user_visits:
                st.session_state.user_visits[username] = []
                
            st.session_state.user_visits[username].extend(example_visits)
            save_session_data()  # 예시 데이터 생성 시 저장
            st.success("예시 방문 기록이 생성되었습니다!")
            time.sleep(1)
            st.rerun()

# -------------------------------
# 설정 페이지
def settings_page():
    st.title("⚙️ 설정")
    
    # 뒤로가기 버튼
    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        st.rerun()
    
    # 언어 설정
    st.subheader("언어 설정")
    language = st.radio(
        "선호하는 언어를 선택하세요",
        ["한국어", "영어", "중국어"],
        index=["한국어", "영어", "중국어"].index(st.session_state.language)
    )
    st.session_state.language = language
    
    # 지도 설정 (추가)
    st.subheader("🗺️ 지도 설정")
    map_type = st.radio(
        "기본 지도 유형",
        ["Folium (기본)", "Google Maps (API 키 필요)"],
        index=0 if st.session_state.map_type == "folium" else 1
    )
    
    if "google" in map_type.lower():
        st.session_state.map_type = "google_maps"
        
        # Google Maps API 키 설정
        current_api_key = st.session_state.google_maps_api_key
        api_key = st.text_input(
            "Google Maps API 키", 
            value=current_api_key if current_api_key else "",
            type="password",
            help="Google Cloud Console에서 Maps JavaScript API 키를 생성하세요."
        )
        
        if api_key != current_api_key:
            st.session_state.google_maps_api_key = api_key
            if api_key:
                st.success("API 키가 저장되었습니다.")
            else:
                st.warning("API 키가 비어 있습니다. Google Maps 기능이 제한됩니다.")
    else:
        st.session_state.map_type = "folium"
        st.info("Folium은 API 키 없이 사용할 수 있는 오픈소스 지도 라이브러리입니다.")
    
    # 데이터 관리
    st.subheader("📊 데이터 관리")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 모든 데이터 저장", help="현재 앱의 모든 사용자 및 방문 데이터를 저장합니다."):
            if save_session_data():
                st.success("데이터가 성공적으로 저장되었습니다!")
            else:
                st.error("데이터 저장 중 오류가 발생했습니다.")
    
    with col2:
        if st.button("📤 데이터 불러오기", help="저장된 데이터를 불러옵니다."):
            if load_session_data():
                st.success("데이터를 성공적으로 불러왔습니다!")
            else:
                st.warning("저장된 데이터가 없거나 불러오기 중 오류가 발생했습니다.")
    
    # 알림 설정
    st.subheader("🔔 알림 설정")
    st.checkbox("이메일 알림 받기", value=True)
    st.checkbox("푸시 알림 받기", value=False)
    
    # 계정 설정
    st.subheader("👤 계정 설정")
    if st.button("🔑 비밀번호 변경"):
        old_pw = st.text_input("현재 비밀번호", type="password")
        new_pw = st.text_input("새 비밀번호", type="password")
        confirm_pw = st.text_input("비밀번호 확인", type="password")
        
        if st.button("비밀번호 변경 확인"):
            username = st.session_state.username
            if username in st.session_state.users and st.session_state.users[username] == old_pw:
                if new_pw == confirm_pw:
                    st.session_state.users[username] = new_pw
                    st.success("비밀번호가 변경되었습니다!")
                    save_session_data()  # 변경사항 저장
                else:
                    st.error("새 비밀번호와 확인 비밀번호가 일치하지 않습니다.")
            else:
                st.error("현재 비밀번호가 일치하지 않습니다.")
    
    # 위험 영역
    st.divider()
    st.subheader("⚠️ 위험 영역", help="이 작업은 되돌릴 수 없습니다!")
    
    delete_visit_data = st.checkbox("내 방문 기록 삭제")
    if delete_visit_data:
        if st.button("방문 기록 전체 삭제", type="primary", help="모든 방문 기록을 영구적으로 삭제합니다."):
            username = st.session_state.username
            if username in st.session_state.user_visits:
                st.session_state.user_visits[username] = []
                st.success("모든 방문 기록이 삭제되었습니다.")
                save_session_data()  # 변경사항 저장
    
    delete_account = st.checkbox("계정 삭제")
    if delete_account:
        if st.button("계정 영구 삭제", type="primary", help="계정과 모든 데이터를 영구적으로 삭제합니다."):
            username = st.session_state.username
            confirm_text = st.text_input("계정을 삭제하려면 '삭제 확인'을 입력하세요")
            
            if confirm_text == "삭제 확인":
                if username in st.session_state.users:
                    del st.session_state.users[username]
                    if username in st.session_state.user_visits:
                        del st.session_state.user_visits[username]
                    st.session_state.logged_in = False
                    st.session_state.username = ""
                    save_session_data()  # 변경사항 저장
                    st.success("계정이 삭제되었습니다.")
                    change_page("login")
                    time.sleep(2)
                    st.rerun()

# -------------------------------
# 앱 실행 흐름 제어
if st.session_state.logged_in:
    if st.session_state.current_page == "menu":
        menu_page()
    elif st.session_state.current_page == "map":
        map_page()
    elif st.session_state.current_page == "history":
        history_page()
    elif st.session_state.current_page == "settings":
        settings_page()
    else:
        menu_page()  # 기본적으로 메뉴 페이지 표시
else:
    login_page()  # 로그인하지 않은 경우 로그인 페이지 표시
