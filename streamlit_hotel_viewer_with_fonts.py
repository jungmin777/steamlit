import streamlit as st
import pandas as pd
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="Google Maps 마커 앱",
    page_icon="🗺️",
    layout="wide"
)

# 제목
st.title("🗺️ Google Maps 마커 표시 앱")

# Google Maps API 키 가져오기
try:
    api_key = st.secrets["google_maps"]["api_key"]
except:
    api_key = st.text_input("Google Maps API Key 입력", type="password")
    if not api_key:
        st.warning("Google Maps API 키를 입력해주세요.")
        st.stop()

# 예시 데이터 생성
@st.cache_data
def load_data():
    # 예시 데이터: 한국의 주요 도시들
    data = {
        '도시': ['서울', '부산', '인천', '대구', '광주', '대전', '울산', '세종', '제주'],
        '위도': [37.5665, 35.1796, 37.4563, 35.8714, 35.1601, 36.3504, 35.5384, 36.4801, 33.4996],
        '경도': [126.9780, 129.0756, 126.7052, 128.6014, 126.8513, 127.3845, 129.3114, 127.2890, 126.5312],
        '인구(만)': [974, 339, 295, 243, 145, 146, 114, 36, 67],
        '설명': [
            '대한민국의 수도', 
            '대한민국 제2의 도시, 항구도시', 
            '국제공항과 항구가 있는 도시', 
            '대한민국 동남부의 대도시', 
            '호남 지방의 중심 도시', 
            '중부지방의 과학도시', 
            '산업도시', 
            '행정중심복합도시', 
            '대한민국의 유명한 관광지'
        ]
    }
    return pd.DataFrame(data)

# 데이터 불러오기
df = load_data()

# 데이터 표시
st.subheader("📊 위치 데이터")
st.dataframe(df)

# 사용자 입력 옵션
st.subheader("🔍 데이터 필터링")
min_population = st.slider("최소 인구 (만 명)", 0, 1000, 0)
filtered_df = df[df['인구(만)'] >= min_population]

# 지도에 표시할 데이터 준비
map_data = filtered_df.copy()

# HTML 생성 함수
def create_google_maps_html(locations, api_key):
    markers = ""
    for _, row in locations.iterrows():
        markers += f"""
        new google.maps.Marker({{
            position: {{ lat: {row['위도']}, lng: {row['경도']} }},
            map: map,
            title: '{row['도시']}'
        }});
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Google Maps</title>
        <style>
            #map {{
                height: 600px;
                width: 100%;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            function initMap() {{
                const centerLat = {locations['위도'].mean()};
                const centerLng = {locations['경도'].mean()};
                
                const map = new google.maps.Map(document.getElementById("map"), {{
                    zoom: 7,
                    center: {{ lat: centerLat, lng: centerLng }}
                }});
                
                // 마커 추가
                {markers}
                
                // 정보창 설정
                const infoWindow = new google.maps.InfoWindow();
                
                // 모든 마커에 클릭 이벤트 추가
                document.querySelectorAll('[title]').forEach(marker => {{
                    marker.addListener('click', () => {{
                        const city = marker.getTitle();
                        const cityData = {locations.to_json(orient='records')}.find(item => item.도시 === city);
                        
                        if (cityData) {{
                            infoWindow.setContent(`
                                <div>
                                    <h3>${{cityData.도시}}</h3>
                                    <p>인구: ${{cityData['인구(만)']}}</p>
                                    <p>${{cityData.설명}}</p>
                                </div>
                            `);
                            infoWindow.open(map, marker);
                        }}
                    }});
                }});
            }}
        </script>
        <script async defer
            src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap">
        </script>
    </body>
    </html>
    """
    return html

# Google Maps HTML 생성
google_maps_html = create_google_maps_html(map_data, api_key)

# 지도 표시
st.subheader("🗺️ Google Maps 지도")
st.components.v1.html(google_maps_html, height=600)

# 사용자 지정 마커 추가 기능
st.subheader("📍 새 마커 추가")
col1, col2 = st.columns(2)

with col1:
    new_name = st.text_input("장소 이름")
    new_desc = st.text_area("설명")

with col2:
    new_lat = st.number_input("위도", value=37.5665, format="%.4f")
    new_lng = st.number_input("경도", value=126.9780, format="%.4f")
    new_pop = st.number_input("인구(만)", value=0, min_value=0, format="%d")

if st.button("마커 추가"):
    new_data = pd.DataFrame({
        '도시': [new_name],
        '위도': [new_lat],
        '경도': [new_lng],
        '인구(만)': [new_pop],
        '설명': [new_desc]
    })
    df = pd.concat([df, new_data], ignore_index=True)
    st.success(f"'{new_name}' 추가 완료! 위 데이터 표를 확인하세요.")
    st.experimental_rerun()

# 푸터
st.markdown("---")
st.markdown("### Google Maps API 사용 가이드")
st.markdown("""
이 앱이 작동하려면 다음 Google Maps API가 필요합니다:
1. **Maps JavaScript API** - 지도 표시
2. **Geocoding API** - 위치 검색

Google Cloud Console에서 이 API들을 활성화하고 API 키를 생성하세요.
API 키를 생성할 때 제한을 설정하는 것이 좋습니다:
- HTTP 리퍼러 제한 (Streamlit 배포 URL)
- API 사용량 쿼터 제한
""")

# import streamlit as st
# import pandas as pd
# import folium
# from streamlit_folium import st_folium
# from streamlit_js_eval import get_geolocation
# from geopy.distance import geodesic
# import time
# from datetime import datetime
# import json

# st.set_page_config(page_title="서울 위치 데이터 통합 지도", layout="wide")

# # -------------------------------
# # 초기 세션 상태 설정
# if "users" not in st.session_state:
#     st.session_state.users = {"admin": "admin"}  # 기본 관리자 계정

# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False

# if "username" not in st.session_state:
#     st.session_state.username = ""

# if "current_page" not in st.session_state:
#     st.session_state.current_page = "login"  # 기본 시작 페이지를 로그인으로 설정

# if 'clicked_location' not in st.session_state:
#     st.session_state.clicked_location = None
# if 'nearby_places' not in st.session_state:
#     st.session_state.nearby_places = []
# if 'selected_recommendations' not in st.session_state:
#     st.session_state.selected_recommendations = []
# if 'language' not in st.session_state:
#     st.session_state.language = "한국어"
    
# # 사용자별 방문 기록 저장
# if "user_visits" not in st.session_state:
#     st.session_state.user_visits = {}

# # 앱 시작시 저장된 데이터 불러오기 시도
# if "data_loaded" not in st.session_state:
#     try:
#         with open("session_data.json", "r", encoding="utf-8") as f:
#             data = json.load(f)
#             # 데이터 복원
#             st.session_state.users = data.get("users", {"admin": "admin"})
#             st.session_state.user_visits = data.get("user_visits", {})
#     except:
#         pass  # 파일이 없거나 오류 발생 시 무시
#     st.session_state.data_loaded = True

# # -------------------------------
# # 페이지 전환 함수
# def change_page(page):
#     st.session_state.current_page = page
#     # 페이지 전환 시 일부 상태 초기화
#     if page != "map":
#         st.session_state.clicked_location = None
#         st.session_state.nearby_places = []
#         st.session_state.selected_recommendations = []

# # -------------------------------
# # 사용자 인증 함수
# def authenticate_user(username, password):
#     return username in st.session_state.users and st.session_state.users[username] == password

# def register_user(username, password):
#     if username in st.session_state.users:
#         return False
#     st.session_state.users[username] = password
#     return True

# # -------------------------------
# # 방문 기록 추가 함수
# def add_visit(username, place_name, lat, lng):
#     if username not in st.session_state.user_visits:
#         st.session_state.user_visits[username] = []
    
#     # 방문 데이터 생성
#     visit_data = {
#         "place_name": place_name,
#         "latitude": lat,
#         "longitude": lng,
#         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "date": datetime.now().strftime("%Y-%m-%d"),
#         "rating": None  # 나중에 평점을 추가할 수 있음
#     }
    
#     # 중복 방문 검사 (같은 날, 같은 장소)
#     is_duplicate = False
#     for visit in st.session_state.user_visits[username]:
#         if (visit["place_name"] == place_name and 
#             visit["date"] == visit_data["date"]):
#             is_duplicate = True
#             break
    
#     if not is_duplicate:
#         st.session_state.user_visits[username].append(visit_data)
#         return True
#     return False

# # -------------------------------
# # 세션 상태 데이터 저장/불러오기 함수
# def save_session_data():
#     """세션 데이터를 JSON 파일로 저장"""
#     try:
#         data = {
#             "users": st.session_state.users,
#             "user_visits": st.session_state.user_visits
#         }
#         with open("session_data.json", "w", encoding="utf-8") as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#         return True
#     except Exception as e:
#         st.error(f"데이터 저장 오류: {e}")
#         return False

# def load_session_data():
#     """저장된 세션 데이터를 JSON 파일에서 불러오기"""
#     try:
#         with open("session_data.json", "r", encoding="utf-8") as f:
#             data = json.load(f)
            
#         # 데이터 복원
#         st.session_state.users = data.get("users", {})
#         st.session_state.user_visits = data.get("user_visits", {})
#         return True
#     except FileNotFoundError:
#         # 파일이 없는 경우 초기 상태 유지
#         return False
#     except Exception as e:
#         st.error(f"데이터 불러오기 오류: {e}")
#         return False

# # -------------------------------
# # 사용자 위치 가져오기
# def get_user_location():
#     try:
#         location = get_geolocation()
#         if location and "coords" in location:
#             return [location["coords"]["latitude"], location["coords"]["longitude"]]
#     except:
#         pass
#     return [37.5665, 126.9780]  # 기본 서울 시청 좌표

# # -------------------------------
# # 로그인/회원가입 페이지
# def login_page():
#     st.title("🔐 로그인 또는 회원가입")
#     tab1, tab2 = st.tabs(["로그인", "회원가입"])

#     with tab1:
#         username = st.text_input("아이디", key="login_username")
#         password = st.text_input("비밀번호", type="password", key="login_password")
#         if st.button("로그인"):
#             if authenticate_user(username, password):
#                 st.success("🎉 로그인 성공!")
#                 st.session_state.logged_in = True
#                 st.session_state.username = username
#                 change_page("menu")  # 로그인 성공 시 메뉴 페이지로 이동
#                 st.rerun()
#             else:
#                 st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")

#     with tab2:
#         new_user = st.text_input("새 아이디", key="register_username")
#         new_pw = st.text_input("새 비밀번호", type="password", key="register_password")
#         if st.button("회원가입"):
#             if register_user(new_user, new_pw):
#                 st.success("✅ 회원가입 완료!")
#                 st.session_state.logged_in = True
#                 st.session_state.username = new_user
#                 change_page("menu")  # 회원가입 성공 시 메뉴 페이지로 이동
#                 st.rerun()
#             else:
#                 st.warning("⚠️ 이미 존재하는 아이디입니다.")

# # -------------------------------
# # 메뉴 페이지
# def menu_page():
#     st.title(f"👋 {st.session_state.username}님, 환영합니다!")
    
#     st.subheader("메뉴를 선택해주세요")
    
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         if st.button("📍 지도 보기", use_container_width=True):
#             change_page("map")
#             st.rerun()
    
#     with col2:
#         if st.button("📝 내 방문 기록", use_container_width=True):
#             change_page("history")
#             st.rerun()
    
#     with col3:
#         if st.button("⚙️ 설정", use_container_width=True):
#             change_page("settings")
#             st.rerun()
    
#     # 로그아웃 버튼
#     if st.button("🔓 로그아웃", key="logout_button"):
#         st.session_state.logged_in = False
#         st.session_state.username = ""
#         change_page("login")
#         st.rerun()

# # -------------------------------
# # 지도 페이지
# def map_page():
#     st.title("📍 서울시 공공 위치 데이터 통합 지도")
    
#     # 뒤로가기 버튼
#     if st.button("← 메뉴로 돌아가기"):
#         change_page("menu")
#         st.rerun()

#     col1, col2, col3 = st.columns([6, 1, 2])
#     with col3:
#         selected_language = st.selectbox(
#             "🌏 Language", 
#             ["🇰🇷 한국어", "🇺🇸 English", "🇨🇳 中文"],
#             index=0 if st.session_state.language == "한국어" else 1 if st.session_state.language == "영어" else 2
#         )
#         language_map_display = {
#             "🇰🇷 한국어": "한국어",
#             "🇺🇸 English": "영어",
#             "🇨🇳 中文": "중국어"
#         }
#         st.session_state.language = language_map_display[selected_language]

#     # 카테고리 선택을 사이드바로 이동
#     with st.sidebar:
#         st.header("카테고리 선택")
        
#         # 카테고리명으로 변환하여 표시
#         category_names = [
#             "외국인전용 관광기념품 판매점",
#             "문화행사 공공서비스예약",
#             "종로구 관광데이터",
#             "체육시설 공연행사",
#             "시립미술관 전시정보"
#         ]
        
#         selected_category = st.selectbox("📁 카테고리", category_names)
    
#     # 사용자 위치 가져오기
#     user_location = get_user_location()
#     center = user_location
#     st.session_state.user_location = center

#     st.subheader("🗺️ 지도")
    
#     # 기본 지도 생성
#     m = folium.Map(location=center, zoom_start=13)
    
#     # 현재 위치 마커 추가
#     folium.Marker(
#         center, 
#         tooltip="📍 내 위치", 
#         icon=folium.Icon(color="blue", icon="star")
#     ).add_to(m)

#     # 샘플 장소 마커 추가
#     sample_locations = [
#         {"name": "경복궁", "lat": 37.5796, "lng": 126.9770},
#         {"name": "남산타워", "lat": 37.5511, "lng": 126.9882},
#         {"name": "동대문 디자인 플라자", "lat": 37.5669, "lng": 127.0093},
#         {"name": "명동성당", "lat": 37.5635, "lng": 126.9877},
#         {"name": "서울숲", "lat": 37.5445, "lng": 127.0374},
#     ]
    
#     # 카테고리에 따라 다른 위치 표시 (시뮬레이션)
#     if selected_category == "외국인전용 관광기념품 판매점":
#         locations = sample_locations[:2]  # 앞의 두개만
#     elif selected_category == "문화행사 공공서비스예약":
#         locations = sample_locations[1:3]  # 중간 두개
#     elif selected_category == "종로구 관광데이터":
#         locations = sample_locations[2:4]  # 중간~끝
#     else:
#         locations = sample_locations  # 전체
    
#     # 마커 추가
#     for loc in locations:
#         folium.Marker(
#             location=[loc["lat"], loc["lng"]],
#             tooltip=loc["name"],
#             icon=folium.Icon(color="green"),
#             popup=folium.Popup(f"{loc['name']}<br>({loc['lat']:.5f}, {loc['lng']:.5f})", max_width=300)
#         ).add_to(m)
    
#     # 방문했던 장소 마커 추가 (보라색 마커로 표시)
#     username = st.session_state.username
#     if username in st.session_state.user_visits and st.session_state.user_visits[username]:
#         for visit in st.session_state.user_visits[username]:
#             folium.Marker(
#                 location=[visit["latitude"], visit["longitude"]],
#                 tooltip=f"✅ 방문: {visit['place_name']}",
#                 icon=folium.Icon(color="purple", icon="check"),
#                 popup=folium.Popup(f"방문: {visit['place_name']}<br>날짜: {visit['date']}", max_width=300)
#             ).add_to(m)
    
#     # 지도 표시
#     map_data = st_folium(m, width=700, height=500, key="main_map")
    
#     # 클릭 이벤트 처리
#     if map_data and 'last_clicked' in map_data:
#         clicked_lat, clicked_lng = map_data['last_clicked']['lat'], map_data['last_clicked']['lng']
#         st.session_state.clicked_location = {'lat': clicked_lat, 'lng': clicked_lng}
        
#         st.subheader(f"📍 클릭한 위치: ({clicked_lat:.5f}, {clicked_lng:.5f})")
        
#         # 주변 장소 찾기 (가장 가까운 샘플 장소들 찾기)
#         nearby_places = []
#         for loc in sample_locations:
#             place_lat, place_lng = loc["lat"], loc["lng"]
#             distance = geodesic((clicked_lat, clicked_lng), (place_lat, place_lng)).meters
#             if distance <= 2000:  # 2km 이내
#                 nearby_places.append((distance, loc["name"], place_lat, place_lng))
        
#         nearby_places.sort(key=lambda x: x[0])
#         st.session_state.nearby_places = nearby_places
        
#         st.subheader("🔍 주변 장소 (2km 이내)")
#         if nearby_places:
#             for i, (dist, name, lat, lng) in enumerate(st.session_state.nearby_places):
#                 cols = st.columns([0.1, 0.7, 0.2, 0.2])
#                 cols[1].markdown(f"**{name}** - {dist:.1f}m")
                
#                 # 장소 선택 버튼
#                 if cols[2].button(f"선택 {i+1}", key=f"nearby_select_{i}"):
#                     if len(st.session_state.selected_recommendations) < 3:
#                         st.session_state.selected_recommendations.append((name, lat, lng))
#                     else:
#                         st.warning("최대 3개까지 선택할 수 있습니다.")
#                     st.rerun()
                
#                 # 방문 기록 추가 버튼
#                 if cols[3].button(f"방문 🏁", key=f"visit_{i}"):
#                     if add_visit(st.session_state.username, name, lat, lng):
#                         st.success(f"'{name}' 방문 기록이 추가되었습니다!")
#                         # 1초 후 페이지 새로고침
#                         time.sleep(1)
#                         st.rerun()
#                     else:
#                         st.info("이미 오늘 방문한 장소입니다.")
#         else:
#             st.info("주변 2km 이내에 장소가 없습니다.")
    
#     if st.session_state.selected_recommendations:
#         st.subheader("✅ 선택된 추천 장소")
#         for i, (name, lat, lng) in enumerate(st.session_state.selected_recommendations):
#             cols = st.columns([0.05, 0.85, 0.1])
#             cols[1].write(f"{name} - ({lat:.5f}, {lng:.5f})")
#             if cols[2].button("❌", key=f"remove_{i}"):
#                 st.session_state.selected_recommendations.pop(i)
#                 st.rerun()

# # -------------------------------
# # 방문 기록 페이지
# def history_page():
#     st.title("📝 나의 방문 기록")
    
#     # 뒤로가기 버튼
#     if st.button("← 메뉴로 돌아가기"):
#         change_page("menu")
#         st.rerun()
    
#     username = st.session_state.username
    
#     # 방문 기록 표시
#     if username in st.session_state.user_visits and st.session_state.user_visits[username]:
#         # 방문기록 지도로 보기
#         st.subheader("🗺️ 방문 기록 지도")
        
#         # 사용자 위치 또는 서울 시청을 중심으로
#         user_location = get_user_location()
#         visit_map = folium.Map(location=user_location, zoom_start=12)
        
#         # 현재 위치 마커
#         folium.Marker(
#             user_location, 
#             tooltip="📍 내 현재 위치", 
#             icon=folium.Icon(color="blue", icon="star")
#         ).add_to(visit_map)
        
#         # 방문 장소 마커 추가
#         for idx, visit in enumerate(st.session_state.user_visits[username]):
#             popup_content = f"""
#             <b>{visit['place_name']}</b><br>
#             방문 일시: {visit['timestamp']}<br>
#             """
            
#             if visit.get('rating'):
#                 stars = "⭐" * int(visit['rating'])
#                 popup_content += f"평점: {stars} ({visit['rating']})"
            
#             # 마커 색상은 방문 순서에 따라 다양하게
#             colors = ["purple", "darkpurple", "cadetblue", "pink", "darkred", "darkblue"]
#             color_idx = idx % len(colors)
            
#             folium.Marker(
#                 location=[visit["latitude"], visit["longitude"]],
#                 tooltip=f"{idx+1}. {visit['place_name']}",
#                 popup=folium.Popup(popup_content, max_width=300),
#                 icon=folium.Icon(color=colors[color_idx])
#             ).add_to(visit_map)
        
#         # 지도 표시
#         st_folium(visit_map, width=700, height=400, key="history_map")
        
#         # 목록으로 방문 기록 표시
#         st.subheader("📋 방문 기록 목록")
        
#         # 정렬 옵션
#         sort_option = st.radio(
#             "정렬 방식",
#             ["최신순", "오래된순", "이름순"],
#             horizontal=True
#         )
        
#         if sort_option == "최신순":
#             sorted_visits = sorted(st.session_state.user_visits[username], 
#                                   key=lambda x: x['timestamp'], reverse=True)
#         elif sort_option == "오래된순":
#             sorted_visits = sorted(st.session_state.user_visits[username], 
#                                   key=lambda x: x['timestamp'])
#         else:  # 이름순
#             sorted_visits = sorted(st.session_state.user_visits[username], 
#                                   key=lambda x: x['place_name'])
        
#         for i, visit in enumerate(sorted_visits):
#             col1, col2 = st.columns([3, 1])
            
#             with col1:
#                 st.markdown(f"**{visit['place_name']}**")
#                 st.markdown(f"방문 일시: {visit['timestamp']}")
                
#                 # 평점 입력 또는 표시
#                 if 'rating' not in visit or visit['rating'] is None:
#                     new_rating = st.slider(f"평점 입력: {visit['place_name']}", 
#                                           min_value=1, max_value=5, value=3, 
#                                           key=f"rating_{i}")
#                     if st.button("평점 저장", key=f"save_rating_{i}"):
#                         visit['rating'] = new_rating
#                         st.success(f"{visit['place_name']}에 대한 평점이 저장되었습니다!")
#                         time.sleep(1)
#                         st.rerun()
#                 else:
#                     st.markdown(f"⭐ 평점: {'⭐' * int(visit['rating'])} ({visit['rating']})")
            
#             with col2:
#                 # 삭제 버튼
#                 if st.button("🗑️ 삭제", key=f"delete_visit_{i}"):
#                     st.session_state.user_visits[username].remove(visit)
#                     st.success("방문 기록이 삭제되었습니다.")
#                     time.sleep(1)
#                     st.rerun()
            
#             st.divider()
        
#         # 방문 통계
#         st.subheader("📊 방문 통계")
#         total_visits = len(st.session_state.user_visits[username])
#         unique_places = len(set([v['place_name'] for v in st.session_state.user_visits[username]]))
#         avg_rating = 0
#         rated_visits = [v for v in st.session_state.user_visits[username] if v.get('rating') is not None]
#         if rated_visits:
#             avg_rating = sum([v['rating'] for v in rated_visits]) / len(rated_visits)
        
#         col1, col2, col3 = st.columns(3)
#         col1.metric("총 방문 횟수", f"{total_visits}회")
#         col2.metric("방문한 장소 수", f"{unique_places}곳")
#         col3.metric("평균 평점", f"{avg_rating:.1f}/5")
        
#         # 데이터 내보내기
#         st.subheader("💾 데이터 내보내기")
        
#         # JSON 형식으로 데이터 변환
#         visit_data_json = json.dumps(st.session_state.user_visits[username], ensure_ascii=False, indent=2)
        
#         st.download_button(
#             label="📥 방문 기록 다운로드 (JSON)",
#             data=visit_data_json,
#             file_name=f"{username}_visit_history.json",
#             mime="application/json"
#         )
        
#     else:
#         st.info("아직 방문 기록이 없습니다. 지도에서 장소를 방문하면 여기에 기록됩니다.")
        
#         # 예시 데이터 보여주기
#         if st.button("예시 데이터 생성"):
#             example_visits = [
#                 {"place_name": "경복궁", "latitude": 37.5796, "longitude": 126.9770, "timestamp": "2023-10-15 14:30:00", "date": "2023-10-15", "rating": 5},
#                 {"place_name": "남산타워", "latitude": 37.5511, "longitude": 126.9882, "timestamp": "2023-10-10 12:15:00", "date": "2023-10-10", "rating": 4},
#                 {"place_name": "동대문 디자인 플라자", "latitude": 37.5669, "longitude": 127.0093, "timestamp": "2023-10-05 16:45:00", "date": "2023-10-05", "rating": 4.5}
#             ]
            
#             if username not in st.session_state.user_visits:
#                 st.session_state.user_visits[username] = []
                
#             st.session_state.user_visits[username].extend(example_visits)
#             st.success("예시 방문 기록이 생성되었습니다!")
#             time.sleep(1)
#             st.rerun()

# # -------------------------------
# # 설정 페이지
# def settings_page():
#     st.title("⚙️ 설정")
    
#     # 뒤로가기 버튼
#     if st.button("← 메뉴로 돌아가기"):
#         change_page("menu")
#         st.rerun()
    
#     # 언어 설정
#     st.subheader("언어 설정")
#     language = st.radio(
#         "선호하는 언어를 선택하세요",
#         ["한국어", "영어", "중국어"],
#         index=["한국어", "영어", "중국어"].index(st.session_state.language)
#     )
#     st.session_state.language = language
    
#     # 데이터 관리
#     st.subheader("📊 데이터 관리")
#     col1, col2 = st.columns(2)
    
#     with col1:
#         if st.button("💾 모든 데이터 저장", help="현재 앱의 모든 사용자 및 방문 데이터를 저장합니다."):
#             if save_session_data():
#                 st.success("데이터가 성공적으로 저장되었습니다!")
#             else:
#                 st.error("데이터 저장 중 오류가 발생했습니다.")
    
#     with col2:
#         if st.button("📤 데이터 불러오기", help="저장된 데이터를 불러옵니다."):
#             if load_session_data():
#                 st.success("데이터를 성공적으로 불러왔습니다!")
#             else:
#                 st.warning("저장된 데이터가 없거나 불러오기 중 오류가 발생했습니다.")
    
#     # 알림 설정
#     st.subheader("🔔 알림 설정")
#     st.checkbox("이메일 알림 받기", value=True)
#     st.checkbox("푸시 알림 받기", value=False)
    
#     # 계정 설정
#     st.subheader("👤 계정 설정")
#     if st.button("🔑 비밀번호 변경"):
#         old_pw = st.text_input("현재 비밀번호", type="password")
#         new_pw = st.text_input("새 비밀번호", type="password")
#         confirm_pw = st.text_input("비밀번호 확인", type="password")
        
#         if st.button("비밀번호 변경 확인"):
#             username = st.session_state.username
#             if username in st.session_state.users and st.session_state.users[username] == old_pw:
#                 if new_pw == confirm_pw:
#                     st.session_state.users[username] = new_pw
#                     st.success("비밀번호가 변경되었습니다!")
#                     save_session_data()  # 변경사항 저장
#                 else:
#                     st.error("새 비밀번호와 확인 비밀번호가 일치하지 않습니다.")
#             else:
#                 st.error("현재 비밀번호가 일치하지 않습니다.")
    
#     # 위험 영역
#     st.divider()
#     st.subheader("⚠️ 위험 영역", help="이 작업은 되돌릴 수 없습니다!")
    
#     delete_visit_data = st.checkbox("내 방문 기록 삭제")
#     if delete_visit_data:
#         if st.button("방문 기록 전체 삭제", type="primary", help="모든 방문 기록을 영구적으로 삭제합니다."):
#             username = st.session_state.username
#             if username in st.session_state.user_visits:
#                 st.session_state.user_visits[username] = []
#                 st.success("모든 방문 기록이 삭제되었습니다.")
#                 save_session_data()  # 변경사항 저장
    
#     delete_account = st.checkbox("계정 삭제")
#     if delete_account:
#         if st.button("계정 영구 삭제", type="primary", help="계정과 모든 데이터를 영구적으로 삭제합니다."):
#             username = st.session_state.username
#             confirm_text = st.text_input("계정을 삭제하려면 '삭제 확인'을 입력하세요")
            
#             if confirm_text == "삭제 확인":
#                 if username in st.session_state.users:
#                     del st.session_state.users[username]
#                     if username in st.session_state.user_visits:
#                         del st.session_state.user_visits[username]
#                     st.session_state.logged_in = False
#                     st.session_state.username = ""
#                     save_session_data()  # 변경사항 저장
#                     st.success("계정이 삭제되었습니다.")
#                     change_page("login")
#                     time.sleep(2)
#                     st.rerun()

# # -------------------------------
# # 앱 실행 흐름 제어
# if st.session_state.logged_in:
#     if st.session_state.current_page == "menu":
#         menu_page()
#     elif st.session_state.current_page == "map":
#         map_page()
#     elif st.session_state.current_page == "history":
#         history_page()
#     elif st.session_state.current_page == "settings":
#         settings_page()
#     else:
#         menu_page()  # 기본적으로 메뉴 페이지 표시
# else:
#     login_page()  # 로그인하지 않은 경우 로그인 페이지 표시
