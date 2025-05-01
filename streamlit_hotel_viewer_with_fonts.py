import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
import streamlit.components.v1 as components
from itertools import permutations
import json
import time
from datetime import datetime

st.set_page_config(page_title="서울 위치 데이터 통합 지도", layout="wide")

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
        visit_map = folium.Map(location=user_location, zoom_start=12)
        
        # 현재 위치 마커
        folium.Marker(
            user_location, 
            tooltip="📍 내 현재 위치", 
            icon=folium.Icon(color="blue", icon="star")
        ).add_to(visit_map)
        
        # 타임라인 표시를 위한 선 생성
        visit_points = []
        for visit in sorted(st.session_state.user_visits[username], key=lambda x: x['timestamp']):
            visit_points.append([visit["latitude"], visit["longitude"]])
        
        if len(visit_points) > 1:
            folium.PolyLine(
                visit_points,
                color="#ae00ff",  # 보라색
                weight=3,
                opacity=0.7,
                dash_array="5, 8",  # 점선 스타일
                tooltip="방문 타임라인"
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
                icon=folium.Icon(color=colors[color_idx], icon="check", prefix="fa")
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
                        time.sleep(1)
                        st.rerun()
                else:
                    st.markdown(f"⭐ 평점: {'⭐' * int(visit['rating'])} ({visit['rating']})")
            
            with col2:
                # 삭제 버튼
                if st.button("🗑️ 삭제", key=f"delete_visit_{i}"):
                    st.session_state.user_visits[username].remove(visit)
                    st.success("방문 기록이 삭제되었습니다.")
                    time.sleep(1)
                    st.rerun()
            
            st.divider()# -------------------------------
# 세션 상태 데이터 저장/불러오기 함수
def save_session_data():
    """세션 데이터를 JSON 파일로 저장"""
    try:
        data = {
            "users": st.session_state.users,
            "user_visits": st.session_state.user_visits
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
        return True
    except FileNotFoundError:
        # 파일이 없는 경우 초기 상태 유지
        return False
    except Exception as e:
        st.error(f"데이터 불러오기 오류: {e}")
        return False

# 앱 시작시 저장된 데이터 불러오기 시도
if "data_loaded" not in st.session_state:
    load_session_data()
    st.session_state.data_loaded = True


# -------------------------------
# 초기 세션 상태 설정
if "users" not in st.session_state:
    st.session_state.users = {}

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
if 'final_destination' not in st.session_state:
    st.session_state.final_destination = None
if 'language' not in st.session_state:
    st.session_state.language = "한국어"
    
# 사용자별 방문 기록 저장
if "user_visits" not in st.session_state:
    st.session_state.user_visits = {}
    
# 임시 저장소 - 현재 세션의 방문 장소
if "current_visit" not in st.session_state:
    st.session_state.current_visit = None

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
# 사용자 위치 가져오기
def get_user_location():
    location = get_geolocation()
    if location and "coords" in location:
        return [location["coords"]["latitude"], location["coords"]["longitude"]]
    return [37.5665, 126.9780]  # 기본 서울 시청 좌표

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
        selected_language = st.selectbox("🌏 Language", ["🇰🇷 한국어", "🇺🇸 English", "🇨🇳 中文"], index=["🇰🇷 한국어", "🇺🇸 English", "🇨🇳 中文"].index(f"🇰🇷 {st.session_state.language}" if st.session_state.language == "한국어" else f"🇺🇸 {st.session_state.language}" if st.session_state.language == "영어" else f"🇨🇳 {st.session_state.language}"))
        language_map_display = {
            "🇰🇷 한국어": "한국어",
            "🇺🇸 English": "영어",
            "🇨🇳 中文": "중국어"
        }
        st.session_state.language = language_map_display[selected_language]

    name_col = f"명칭({st.session_state.language})"

    # 카테고리 선택을 사이드바로 이동
    with st.sidebar:
        st.header("카테고리 선택")
        
        # 파일 목록 (카테고리로 표시)
        file_list = [
            "서울시 외국인전용 관광기념품 판매점 정보(한국어+영어+중국어).xlsx",
            "서울시 문화행사 공공서비스예약 정보(한국어+영어+중국어).xlsx",
            "서울시 종로구 관광데이터 정보 (한국어+영어).xlsx",
            "서울시 체육시설 공연행사 정보 (한국어+영어+중국어).xlsx",
            "서울시립미술관 전시정보 (한국어+영어+중국어).xlsx"
        ]
        
        # 카테고리명으로 변환하여 표시
        category_names = [
            "외국인전용 관광기념품 판매점",
            "문화행사 공공서비스예약",
            "종로구 관광데이터",
            "체육시설 공연행사",
            "시립미술관 전시정보"
        ]
        
        selected_category = st.selectbox("📁 카테고리", category_names)
        selected_file = file_list[category_names.index(selected_category)]

    try:
        df = pd.read_excel(selected_file)
    except Exception as e:
        try:
            df = pd.read_excel(selected_file, encoding='utf-8')
        except Exception:
            try:
                df = pd.read_excel(selected_file, encoding='cp949')
            except Exception as e:
                st.error(f"파일을 불러오는 중 오류 발생: {e}")
                return

    # 필수 열 존재 확인
    if name_col not in df.columns or "X좌표" not in df.columns or "Y좌표" not in df.columns:
        st.error("필수 열이 누락되었습니다.")
        return

    df = df.dropna(subset=["X좌표", "Y좌표"])
    user_location = get_user_location()
    center = user_location
    st.session_state.user_location = center

    st.subheader("🗺️ 지도")
    m = folium.Map(location=center, zoom_start=13)
    marker_cluster = MarkerCluster().add_to(m)

    # 현재 위치 별표 표시
    folium.Marker(center, tooltip="📍 내 위치", icon=folium.Icon(color="blue", icon="star")).add_to(m)

    # 방문했던 장소 마커 추가 (보라색 마커로 표시)
    username = st.session_state.username
    if username in st.session_state.user_visits and st.session_state.user_visits[username]:
        for visit in st.session_state.user_visits[username]:
            folium.Marker(
                location=[visit["latitude"], visit["longitude"]],
                tooltip=f"✅ 방문: {visit['place_name']}",
                icon=folium.Icon(color="purple", icon="check"),
                popup=folium.Popup(f"방문: {visit['place_name']}<br>날짜: {visit['date']}", max_width=300)
            ).add_to(m)  # 클러스터에 추가하지 않고 지도에 직접 추가하여 항상 표시

    # 데이터셋의 장소 마커 추가
    for index, row in df.iterrows():
        lat, lng = row["Y좌표"], row["X좌표"]
        name = row[name_col]
        folium.Marker(
            location=[lat, lng],
            tooltip=name,
            icon=folium.Icon(color="green"),
            popup=folium.Popup(f"{name}<br>({lat:.5f}, {lng:.5f})", max_width=300)
        ).add_to(marker_cluster)

    # 지도 클릭 이벤트 처리
    map_data = st_folium(
        m,
        width=700,
        height=500,
        key="main_map",
        feature_group_to_add=marker_cluster,
        callback=lambda x: st.session_state.update({'clicked_location': x['last_clicked'] if x and 'last_clicked' in x else None})
    )

    if st.session_state.clicked_location:
        clicked_lat, clicked_lng = st.session_state.clicked_location['lat'], st.session_state.clicked_location['lng']
        st.subheader(f"📍 클릭한 위치: ({clicked_lat:.5f}, {clicked_lng:.5f})")

        nearby_places = []
        for index, row in df.iterrows():
            place_lat, place_lng = row["Y좌표"], row["X좌표"]
            distance = geodesic((clicked_lat, clicked_lng), (place_lat, place_lng)).meters
            if distance <= 1000:
                nearby_places.append((distance, row[name_col], place_lat, place_lng))

        nearby_places.sort(key=lambda x: x[0])
        st.session_state.nearby_places = nearby_places

        st.subheader("🔍 주변 장소 (1km 이내)")
        if nearby_places:
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
                        st.empty()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info("이미 오늘 방문한 장소입니다.")
        else:
            st.info("주변 1km 이내에 장소가 없습니다.")


    if st.session_state.selected_recommendations:
        st.subheader("✅ 선택된 추천 장소")
        for i, (name, lat, lng) in enumerate(st.session_state.selected_recommendations):
            cols = st.columns([0.05, 0.85, 0.1])
            cols[1].write(f"{name} - ({lat:.5f}, {lng:.5f})")
            if cols[2].button("❌", key=f"remove_{i}"):
                st.session_state.selected_recommendations.pop(i)
                st.rerun()

    if st.button("🗺️ 경로 추천", disabled=not st.session_state.clicked_location or not st.session_state.selected_recommendations):
        if st.session_state.clicked_location and st.session_state.selected_recommendations:
            final_lat, final_lng = st.session_state.clicked_location['lat'], st.session_state.clicked_location['lng']
            start_point = st.session_state.user_location
            dest_point = (final_lat, final_lng)
            selected_places = [(name, lat, lng) for name, lat, lng in st.session_state.selected_recommendations]

            locations = [start_point] + [(lat, lng) for _, lat, lng in selected_places] + [dest_point]
            names = ["현재 위치"] + [name for name, _, _ in selected_places] + ["최종 목적지"]

            min_distance = float('inf')
            best_route_indices = None

            if selected_places:
                place_indices = list(range(1, len(selected_places) + 1))
                for perm in permutations(place_indices):
                    current_route_indices = [0] + list(perm) + [len(locations) - 1]
                    total_distance = 0
                    for i in range(len(current_route_indices) - 1):
                        point1 = locations[current_route_indices[i]]
                        point2 = locations[current_route_indices[i+1]]
                        total_distance += geodesic(point1, point2).meters

                    if total_distance < min_distance:
                        min_distance = total_distance
                        best_route_indices = current_route_indices
            else:
                min_distance = geodesic(start_point, dest_point).meters
                best_route_indices = [0, len(locations) - 1]

            if best_route_indices:
                route_names = [names[i] for i in best_route_indices]
                
                # 경로 시각화를 위한 새 지도 생성
                route_map = folium.Map(location=start_point, zoom_start=13)
                
                # 경로 지점 표시
                for i, idx in enumerate(best_route_indices):
                    location = locations[idx]
                    name = route_names[i]
                    
                    # 아이콘 색상 설정
                    if i == 0:  # 시작점
                        icon_color = "blue"
                    elif i == len(best_route_indices) - 1:  # 종료점
                        icon_color = "red"
                    else:  # 중간 경유지
                        icon_color = "green"
                    
                    folium.Marker(
                        location=location,
                        tooltip=f"{i+1}. {name}",
                        icon=folium.Icon(color=icon_color),
                        popup=folium.Popup(f"{i+1}. {name}", max_width=300)
                    ).add_to(route_map)
                
                # 경로 연결선 표시
                points = [locations[i] for i in best_route_indices]
                folium.PolyLine(
                    points,
                    color="blue",
                    weight=5,
                    opacity=0.7,
                    tooltip="추천 경로"
                ).add_to(route_map)
                
                # 결과 설명
                route_description = "🧭 추천드리는 경로는 "
                for i in range(1, len(route_names) - 1):
                    route_description += f"{route_names[i]}, "
                route_description = route_description.rstrip(", ")
                route_description += f"을(를) 들리고 최종 목적지로 가는 것입니다."
                st.success(route_description)
                
                # 총 거리 표시
                st.info(f"📏 총 예상 거리: {min_distance:.2f}m")
                
                # 지도 표시
                st.subheader("🗺️ 추천 경로 지도")
                st_folium(route_map, width=700, height=500, key="route_map")

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
        visit_map = folium.Map(location=user_location, zoom_start=12)
        
        # 현재 위치 마커
        folium.Marker(
            user_location, 
            tooltip="📍 내 현재 위치", 
            icon=folium.Icon(color="blue", icon="star")
        ).add_to(visit_map)
        
        # 타임라인 표시를 위한 선 생성
        visit_points = []
        for visit in sorted(st.session_state.user_visits[username], key=lambda x: x['timestamp']):
            visit_points.append([visit["latitude"], visit["longitude"]])
        
        if len(visit_points) > 1:
            folium.PolyLine(
                visit_points,
                color="#ae00ff",  # 보라색
                weight=3,
                opacity=0.7,
                dash_array="5, 8",  # 점선 스타일
                tooltip="방문 타임라인"
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
                icon=folium.Icon(color=colors[color_idx], icon="check", prefix="fa")
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
                        time.sleep(1)
                        st.rerun()
                else:
                    st.markdown(f"⭐ 평점: {'⭐' * int(visit['rating'])} ({visit['rating']})")
            
            with col2:
                # 삭제 버튼
                if st.button("🗑️ 삭제", key=f"delete_visit_{i}"):
                    st.session_state.user_visits[username].remove(visit)
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
# 방문 기록 추가 함수
def add_visit(username, place_name, lat, lng):
    from datetime import datetime
    
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




# import streamlit as st
# import pandas as pd
# import folium
# from folium.plugins import MarkerCluster
# from streamlit_folium import st_folium
# from streamlit_js_eval import get_geolocation
# import random
# from geopy.distance import geodesic
# import os
# import streamlit.components.v1 as components

# # -------------------------------
# st.set_page_config(page_title="서울 위치 데이터 통합 지도", layout="wide")

# # -------------------------------
# # 초기 세션 상태 설정
# if "users" not in st.session_state:
#     st.session_state.users = {}

# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False

# if "username" not in st.session_state:
#     st.session_state.username = ""

# if "clicked_locations" not in st.session_state:
#     st.session_state.clicked_locations = []


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
# # 로그인 / 회원가입 페이지
# def login_page():
#     st.title("🔐 로그인 또는 회원가입")

#     tab1, tab2 = st.tabs(["로그인", "회원가입"])

#     with tab1:
#         username = st.text_input("아이디")
#         password = st.text_input("비밀번호", type="password")
#         if st.button("로그인"):
#             if authenticate_user(username, password):
#                 st.success("🎉 로그인 성공!")
#                 st.session_state.logged_in = True
#                 st.session_state.username = username
#                 st.experimental_rerun()
#             else:
#                 st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")

#     with tab2:
#         new_user = st.text_input("새 아이디")
#         new_pw = st.text_input("새 비밀번호", type="password")
#         if st.button("회원가입"):
#             if register_user(new_user, new_pw):
#                 st.success("✅ 회원가입 완료!")
#                 # 자동 로그인 처리
#                 st.session_state.logged_in = True
#                 st.session_state.username = new_user
    
#                 # JS로 input에 값을 채우고, 포커스아웃 시키기
#                 components.html(
#                     f"""
#                     <script>
#                     setTimeout(function() {{
#                         const inputBox = window.parent.document.querySelector('input[placeholder="아이디"]');
#                         if (inputBox) {{
#                             inputBox.value = "{new_user}";
#                             inputBox.dispatchEvent(new Event('input', {{ bubbles: true }}));
#                             inputBox.blur();  // 포커스 아웃
#                         }}
#                     }}, 500);
#                     </script>
#                     """,
#                     height=0,
#                     width=0
#                 )
#             else:
#                 st.warning("⚠️ 이미 존재하는 아이디입니다.")




# # -------------------------------
# # 초기 상태 초기화
# if 'clicked_locations' not in st.session_state:
#     st.session_state.clicked_locations = []
# if 'selected_recommendations' not in st.session_state:
#     st.session_state.selected_recommendations = []
# if 'final_destination' not in st.session_state:
#     st.session_state.final_destination = None

# # 유저 위치
# def get_user_location():
#     location = get_geolocation()
#     if location and "coords" in location:
#         return [location["coords"]["latitude"], location["coords"]["longitude"]]
#     else:
#         return [37.5665, 126.9780]  # 기본 서울 시청 좌표

# # 지도 페이지
# def map_page():
#     st.title("📍 서울시 공공 위치 데이터 통합 지도")

#     col1, col2, col3 = st.columns([6, 1, 2])
#     with col3:
#         selected_language = st.selectbox("🌏 Language", ["🇰🇷 한국어", "🇺🇸 English", "🇨🇳 中文"])

#     language_map = {
#         "🇰🇷 한국어": "한국어",
#         "🇺🇸 English": "영어",
#         "🇨🇳 中文": "중국어"
#     }
#     language = language_map[selected_language]

#     # if "clicked_locations" not in st.session_state:
#     #     st.session_state.clicked_locations = []
#     # if "final_selected_places" not in st.session_state:
#     #     st.session_state.final_selected_places = []

        
#     # 언어별 파일 정보 (파일명과 좌표 컬럼명)
#     csv_info_ko = {
#         "서울시 외국인전용 관광기념품 판매점 정보(국문).csv": ("위치정보(Y)", "위치정보(X)"),
#         "서울시 문화행사 공공서비스예약 정보(국문).csv": ("장소Y좌표", "장소X좌표"),
#         "서울시립미술관 전시정보 (국문).csv": ("y좌표", "x좌표"),
#         "서울시 체육시설 공연행사 정보 (국문).csv": ("y좌표", "x좌표"),
#         "서울시 종로구 관광데이터 정보 (국문).csv": ("Y 좌표", "X 좌표"),
#         "서울시 자랑스러운 한국음식점 정보 (국문,영문,중문).xlsx": ("Longitude", "Latitude")
#     }

#     csv_info_en = {
#         "서울시 외국인전용 관광기념품 판매점 정보(영문).csv": ("위치정보(Y)", "위치정보(X)"),
#         "서울시 문화행사 공공서비스예약 정보(영문).csv": ("장소Y좌표", "장소X좌표"),
#         "서울시립미술관 전시정보 (영문).csv": ("y좌표", "x좌표"),
#         "서울시 체육시설 공연행사 정보 (영문).csv": ("y좌표", "x좌표"),
#         "서울시 종로구 관광데이터 정보 (영문).csv": ("Y 좌표", "X 좌표"),
#         "서울시 자랑스러운 한국음식점 정보 (국문,영문,중문).xlsx": ("Longitude", "Latitude")
#     }

#     csv_info_cn = {
#         "서울시 외국인전용 관광기념품 판매점 정보(중문).csv": ("위치정보(Y)", "위치정보(X)"),
#         "서울시 문화행사 공공서비스예약 정보(중문).csv": ("장소Y좌표", "장소X좌표"),
#         "서울시립미술관 전시정보 (중문).csv": ("y좌표", "x좌표"),
#         "서울시 체육시설 공연행사 정보 (중문).csv": ("y좌표", "x좌표"),
#         "서울시 종로구 관광데이터 정보 (중문).csv": ("Y 좌표", "X 좌표"),
#         "서울시 자랑스러운 한국음식점 정보 (국문,영문,중문).xlsx": ("Longitude", "Latitude")
#     }

#     # 선택한 언어에 따라 파일 정보 설정
#     if language == "한국어":
#         all_info = csv_info_ko
#     elif language == "영어":
#         all_info = csv_info_en
#     else:
#         all_info = csv_info_cn


#     user_location = get_geolocation()
#     center = [user_location["coords"]["latitude"], user_location["coords"]["longitude"]]

#     selected_category = list(all_info.keys())[0]
#     lat_col, lng_col = all_info[selected_category]
#     df = pd.read_csv(selected_category, encoding='utf-8').dropna(subset=[lat_col, lng_col])

#     st.session_state.clicked_category = selected_category
#     st.session_state.user_location = center

#     st.subheader("🗺️ 지도")
#     m = folium.Map(location=center, zoom_start=13)
#     marker_cluster = MarkerCluster().add_to(m)

#     # 내 위치 마커
#     folium.Marker(center, tooltip="📍 내 위치", icon=folium.Icon(color="blue")).add_to(m)

#     for _, row in df.iterrows():
#         lat, lng = row[lat_col], row[lng_col]
#         folium.Marker(
#             location=[lat, lng],
#             tooltip="추천 장소",
#             icon=folium.Icon(color="green"),
#             popup=folium.Popup(f"{lat:.5f}, {lng:.5f}", max_width=300)
#         ).add_to(marker_cluster)

#     map_data = st_folium(m, width=700, height=500)

#     if map_data and map_data.get("last_clicked"):
#         st.session_state.final_destination = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])
#         st.success(f"마커 선택됨: {st.session_state.final_destination}")

#     st.divider()
#     if st.session_state.final_destination:
#         st.subheader("📍 주변 추천 장소")

#         def find_nearby(df, base_location, max_count=10):
#             results = []
#             for _, row in df.iterrows():
#                 lat, lng = row[lat_col], row[lng_col]
#                 dist = geodesic(base_location, (lat, lng)).meters
#                 if 0 < dist <= 2000:
#                     results.append((dist, row))
#             return sorted(results, key=lambda x: x[0])[:max_count]

#         nearby = find_nearby(df, st.session_state.final_destination)

#         for i, (dist, row) in enumerate(nearby):
#             name = next((row[c] for c in ["명칭", "시설명", "장소명", "이름", "상호명", "Name"] if c in row and not pd.isna(row[c])), "장소")
#             lat, lng = row[lat_col], row[lng_col]
#             st.markdown(f"**{name}** - 거리 {dist:.1f}m")
#             if st.button(f"➕ 선택 {i+1}", key=f"select_{i}"):
#                 if len(st.session_state.selected_recommendations) < 3:
#                     st.session_state.selected_recommendations.append((name, lat, lng))
#                 else:
#                     st.warning("최대 3개까지 선택할 수 있습니다.")

#     if st.session_state.selected_recommendations:
#         st.subheader("✅ 선택된 장소")
#         for name, lat, lng in st.session_state.selected_recommendations:
#             st.write(f"{name} - ({lat:.5f}, {lng:.5f})")

#     if st.button("📌 최종 목적지로 확정"):
#         st.subheader("🎯 선택 결과 시각화")
#         result_map = folium.Map(location=center, zoom_start=13)
#         folium.Marker(center, tooltip="내 위치", icon=folium.Icon(color="blue")).add_to(result_map)

#         for name, lat, lng in st.session_state.selected_recommendations:
#             folium.Marker([lat, lng], tooltip=name, icon=folium.Icon(color="green")).add_to(result_map)

#         if st.session_state.final_destination:
#             folium.Marker(st.session_state.final_destination, tooltip="🎯 목적지", icon=folium.Icon(color="red")).add_to(result_map)

#         st_folium(result_map, width=700, height=500)




    

    # category_options = ["전체"] + list(all_info.keys())
    # selected_category = st.selectbox("📂 카테고리 선택", category_options)
    # st.session_state.clicked_category = selected_category

    # m = folium.Map(location=center, zoom_start=12)
    # marker_cluster = MarkerCluster().add_to(m)
    # data_dict = {}

    # for file, (lat_col, lng_col) in all_info.items():
    #     if selected_category != "전체" and file != selected_category:
    #         continue
    #     try:
    #         file_ext = os.path.splitext(file)[1].lower()
    #         df = pd.read_csv(file, encoding="utf-8") if file_ext == '.csv' else pd.read_excel(file)
    #         df = df.dropna(subset=[lat_col, lng_col])
    #         data_dict[file] = df

    #         color = ["blue", "red", "green", "purple", "orange", "darkblue"][list(all_info.keys()).index(file) % 6]
    #         for _, row in df.iterrows():
    #             lat, lng = row[lat_col], row[lng_col]
    #             popup_content = f"""
    #             <b>카테고리:</b> {file.replace('.csv', '').replace('.xlsx', '')}<br>
    #             <b>위치:</b> {lat:.5f}, {lng:.5f}<br>
    #             """
    #             name_columns = ['명칭', '시장명', '장소명', '이름', '상호명', 'Name']
    #             for col_name in name_columns:
    #                 if col_name in row and not pd.isna(row[col_name]):
    #                     popup_content += f"<b>{col_name}:</b> {row[col_name]}<br>"
    #             folium.Marker(
    #                 location=[lat, lng],
    #                 tooltip=file.replace(".csv", "").replace(".xlsx", ""),
    #                 icon=folium.Icon(color=color, icon="info-sign"),
    #                 popup=folium.Popup(popup_content, max_width=300)
    #             ).add_to(marker_cluster)
    #     except Exception as e:
    #         st.error(f"{file} 로드 오류: {e}")

    # map_col, rec_col = st.columns([7, 3])
    # with map_col:
    #     map_data = st_folium(m, width="100%", height=600)
    #     clicked = map_data.get("last_object_clicked") or map_data.get("last_clicked")
    #     if clicked:
    #         lat, lng = clicked["lat"], clicked["lng"]
    #         if len(st.session_state.clicked_locations) >= 3:
    #             st.session_state.clicked_locations.pop(0)
    #         st.session_state.clicked_locations.append((lat, lng))

    # with rec_col:
    #     if st.session_state.clicked_locations:
    #         st.subheader("📍 선택한 장소 주부 추천")
    #         lat, lng = st.session_state.clicked_locations[-1]

    #         def find_nearby(df, lat_col, lng_col, base_location, distances=[500, 1000, 1500, 2000]):
    #             for d in distances:
    #                 candidates = df[df.apply(
    #                     lambda r: 0 < geodesic(base_location, (r[lat_col], r[lng_col])).meters <= d, axis=1)]
    #                 if not candidates.empty:
    #                     return candidates.sample(n=min(3, len(candidates)))
    #             return None

    #         for file, (lat_col, lng_col) in all_info.items():
    #             if st.session_state.clicked_category != "전체" and file != st.session_state.clicked_category:
    #                 continue
    #             df = data_dict.get(file)
    #             if df is not None:
    #                 recommended = find_nearby(df, lat_col, lng_col, (lat, lng))
    #                 if recommended is not None:
    #                     file_name = file.replace('.csv', '').replace('.xlsx', '')
    #                     st.write(f"**{file_name}** 카테고리")
    #                     for _, rec in recommended.iterrows():
    #                         rec_lat, rec_lng = rec[lat_col], rec[lng_col]
    #                         place_name = next((rec[col] for col in ['명칭', '시장명', '장소명', '이름', '상호명', 'Name'] if col in rec and not pd.isna(rec[col])), "장소")
    #                         distance = geodesic((lat, lng), (rec_lat, rec_lng)).meters
    #                         st.markdown(f"**{place_name}**<br>📍 거리: {distance:.1f}m<br>[🗌 길찾기](https://www.google.com/maps/dir/?api=1&origin=My+Location&destination={rec_lat},{rec_lng})", unsafe_allow_html=True)
    #                         if st.button(f"✅ 선택: {place_name}", key=f"{place_name}_{file}"):
    #                             if len(st.session_state.final_selected_places) >= 3:
    #                                 st.session_state.final_selected_places.pop(0)
    #                             st.session_state.final_selected_places.append({"file": file, "lat": rec_lat, "lng": rec_lng, "name": place_name})

    # # 하단에 최종 선택 지도 표시
    # if st.session_state.clicked_locations and st.session_state.final_selected_places:
    #     st.subheader("📍 최종 선택 위치")
    #     bottom_map = folium.Map(location=st.session_state.clicked_locations[-1], zoom_start=14)
    #     folium.Marker(location=st.session_state.clicked_locations[-1], tooltip="클릭 위치", icon=folium.Icon(color="red", icon="star")).add_to(bottom_map)
    #     for place in st.session_state.final_selected_places:
    #         folium.Marker(location=[place["lat"], place["lng"]], tooltip=place["name"], icon=folium.Icon(color="green", icon="ok-sign")).add_to(bottom_map)
    #     st_folium(bottom_map, width="100%", height=500)

    # if st.button("🔓 로그아웃"):
    #     st.session_state.logged_in = False
    #     st.session_state.username = ""
    #     st.experimental_rerun()



# # -------------------------------
# # 앱 실행 흐름 제어
# if st.session_state.get("logged_in"):
#     map_page()
# else:
#     login_page()




