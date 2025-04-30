import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from geopy.distance import geodesic
import streamlit.components.v1 as components
from itertools import permutations

st.set_page_config(page_title="서울 위치 데이터 통합 지도", layout="wide")

# -------------------------------
# 초기 세션 상태 설정
if "users" not in st.session_state:
    st.session_state.users = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

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

# -------------------------------
# 사용자 인증 (기존 코드 유지)
def authenticate_user(username, password):
    return username in st.session_state.users and st.session_state.users[username] == password

def register_user(username, password):
    if username in st.session_state.users:
        return False
    st.session_state.users[username] = password
    return True

# -------------------------------
# 로그인/회원가입 (기존 코드 유지)
def login_page():
    st.title("🔐 로그인 또는 회원가입")
    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if authenticate_user(username, password):
                st.success("🎉 로그인 성공!")
                st.session_state.logged_in = True
                st.session_state.username = username
                st.experimental_rerun()
            else:
                st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")

    with tab2:
        new_user = st.text_input("새 아이디")
        new_pw = st.text_input("새 비밀번호", type="password")
        if st.button("회원가입"):
            if register_user(new_user, new_pw):
                st.success("✅ 회원가입 완료!")
                st.session_state.logged_in = True
                st.session_state.username = new_user
                st.experimental_rerun()
            else:
                st.warning("⚠️ 이미 존재하는 아이디입니다.")

# -------------------------------
# 사용자 위치
def get_user_location():
    location = get_geolocation()
    if location and "coords" in location:
        return [location["coords"]["latitude"], location["coords"]["longitude"]]
    return [37.5665, 126.9780]

# -------------------------------
# 지도 페이지
def map_page():
    st.title("📍 서울시 공공 위치 데이터 통합 지도")

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

    # 파일 목록 (기존 코드 유지)
    file_list = [
        "서울시 외국인전용 관광기념품 판매점 정보(한국어+영어+중국어).xlsx",
        "서울시 문화행사 공공서비스예약 정보(한국어+영어+중국어).xlsx",
        "서울시 종로구 관광데이터 정보 (한국어+영어).xlsx",
        "서울시 체육시설 공연행사 정보 (한국어+영어+중국어).xlsx",
        "서울시립미술관 전시정보 (한국어+영어+중국어).xlsx"
    ]

    selected_file = st.selectbox("📁 데이터 파일 선택", file_list)

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

    # 필수 열 존재 확인 (기존 코드 유지)
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

        st.subheader(" 주변 장소 (1km 이내)")
        for i, (dist, name, lat, lng) in enumerate(st.session_state.nearby_places):
            cols = st.columns([0.1, 1, 0.3])
            cols[1].markdown(f"**{name}** - {dist:.1f}m")
            if cols[2].button(f"선택 {i+1}", key=f"nearby_select_{i}"):
                if len(st.session_state.selected_recommendations) < 3:
                    st.session_state.selected_recommendations.append((name, lat, lng))
                else:
                    st.warning("최대 3개까지 선택할 수 있습니다.")
                st.experimental_rerun() # 선택 후 UI 업데이트

    if st.session_state.selected_recommendations:
        st.subheader("✅ 선택된 추천 장소")
        for name, lat, lng in st.session_state.selected_recommendations:
            st.write(f"{name} - ({lat:.5f}, {lng:.5f})")

    if st.button("경로 추천"):
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
                route_description = "추천드리는 경로는 "
                for i in range(1, len(route_names) - 1):
                    route_description += f"{route_names[i]}을(를) 들리고 "
                route_description += f"최종 목적지({route_names[-1]})로 가는 것을 추천드립니다. (총 예상 거리: {min_distance:.2f}m)"
                st.success(route_description)
        else:
            st.warning("최종 목적지를 지도에서 클릭하고, 추천 장소를 1개 이상 선택해야 경로 추천이 가능합니다.")

# -------------------------------
# 앱 실행 (기존 코드 유지)
if st.session_state.get("logged_in"):
    map_page()
else:
    login_page()




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




