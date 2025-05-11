import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime
from pathlib import Path
from geopy.distance import geodesic
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="서울 관광앱",
    page_icon="🗼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

#################################################
# 상수 및 설정 값
#################################################

# Google Maps 기본 중심 위치 (서울시청)
DEFAULT_LOCATION = [37.5665, 126.9780]

# 카테고리별 마커 색상
CATEGORY_COLORS = {
    "체육시설": "blue",
    "공연행사": "purple",
    "관광기념품": "green",
    "한국음식점": "orange",
    "미술관/전시": "pink",
    "종로구 관광지": "red",
    "기타": "gray"
}

# 언어별 카테고리 정의
CATEGORIES_TRANSLATION = {
    "한국어": {
        "체육시설": "체육시설",
        "관광기념품": "관광기념품",
        "한국음식점": "한국음식점",
        "미술관/전시": "미술관/전시",
        "종로구 관광지": "종로구 관광지",
        "기타": "기타"
    },
    "영어": {
        "체육시설": "Sports Facilities",
        "관광기념품": "Tourism Souvenirs",
        "한국음식점": "Korean Restaurants",
        "미술관/전시": "Museums/Exhibitions",
        "종로구 관광지": "Jongno-gu Tourist Spots",
        "기타": "Others"
    },
    "중국어": {
        "체육시설": "体育设施",
        "관광기념품": "旅游纪念品",
        "한국음식점": "韩国餐厅",
        "미술관/전시": "美术馆/展览",
        "종로구 관광지": "钟路区旅游景点",
        "기타": "其他"
    }
}

# 파일 분류용 카테고리 매핑 (기존 FILE_CATEGORIES는 그대로 유지)
FILE_CATEGORIES = {
    "체육시설": ["체육시설", "공연행사"],
    "관광기념품": ["관광기념품", "외국인전용"],
    "한국음식점": ["음식점", "한국음식"],
    "미술관/전시": ["미술관", "전시"],
    "종로구 관광지": ["종로구", "관광데이터"]
}

# 세션 데이터 저장 파일
SESSION_DATA_FILE = "data/session_data.json"

# 경험치 설정
XP_PER_LEVEL = 200
PLACE_XP = {
    "경복궁": 80,
    "남산서울타워": 65,
    "동대문 DDP": 35,
    "명동": 25,
    "인사동": 40,
    "창덕궁": 70,
    "북촌한옥마을": 50,
    "광장시장": 30,
    "서울숲": 20,
    "63빌딩": 45
}

# 언어 코드 매핑
LANGUAGE_CODES = {
    "한국어": "ko",
    "영어": "en", 
    "중국어": "zh-CN"
}

# 추천 코스 데이터 (기본값, 실제 데이터가 없을 경우 사용)
RECOMMENDATION_COURSES = {
    "문화 코스": ["경복궁", "인사동", "창덕궁", "북촌한옥마을"],
    "쇼핑 코스": ["동대문 DDP", "명동", "광장시장", "남산서울타워"],
    "자연 코스": ["서울숲", "남산서울타워", "한강공원", "북한산"],
    "대중적 코스": ["경복궁", "명동", "남산서울타워", "63빌딩"]
}

# 여행 스타일별 카테고리 가중치
STYLE_CATEGORY_WEIGHTS = {
    "활동적인": {"체육시설": 1.5, "공연행사": 1.2, "종로구 관광지": 1.0},
    "휴양": {"미술관/전시": 1.3, "한국음식점": 1.2, "종로구 관광지": 1.0},
    "맛집": {"한국음식점": 2.0, "관광기념품": 1.0, "종로구 관광지": 0.8},
    "쇼핑": {"관광기념품": 2.0, "한국음식점": 1.0, "종로구 관광지": 0.8},
    "역사/문화": {"종로구 관광지": 1.5, "미술관/전시": 1.3, "공연행사": 1.2},
    "자연": {"종로구 관광지": 1.5, "체육시설": 1.0, "한국음식점": 0.8}
}

# 명시적으로 로드할 7개 파일 리스트
EXCEL_FILES = [
    "서울시 자랑스러운 한국음식점 정보 한국어영어중국어 1.xlsx",
    "서울시 종로구 관광데이터 정보 한국어영어 1.xlsx",
    "서울시 체육시설 공연행사 정보 한국어영어중국어 1.xlsx",
    "서울시 문화행사 공공서비스예약 정보한국어영어중국어 1.xlsx",
    "서울시 외국인전용 관광기념품 판매점 정보한국어영어중국어 1.xlsx",
    "서울시 종로구 관광데이터 정보 중국어 1.xlsx",
    "서울시립미술관 전시정보 한국어영어중국어 1.xlsx"
]






#################################################
# 유틸리티 함수
#################################################

def apply_custom_css():
    """앱 전체에 적용되는 커스텀 CSS"""
    st.markdown("""
    <style>
        .main-header {color:#1E88E5; font-size:30px; font-weight:bold; text-align:center;}
        .sub-header {color:#1976D2; font-size:24px; font-weight:bold; margin-top:20px;}
        .card {
            border-radius:10px; 
            padding:20px; 
            margin:10px 0px; 
            background-color:#f0f8ff; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }
        .blue-btn {
            background-color:#1976D2; 
            color:white; 
            padding:10px 20px; 
            border-radius:5px; 
            border:none;
            text-align:center;
            cursor:pointer;
            font-weight:bold;
        }
        .xp-text {
            color:#4CAF50; 
            font-weight:bold;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 4px 4px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        div[data-testid="stHorizontalBlock"] > div:first-child {
            border: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def page_header(title):
    """페이지 헤더 표시"""
    st.markdown(f'<div class="main-header">{title}</div>', unsafe_allow_html=True)

def display_user_level_info(lang="ko"):
    """사용자 레벨 및 경험치 정보 표시 (다국어 지원)"""
    # 다국어 메시지 정의
    messages = {
        "level": {
            "ko": "레벨",
            "en": "Level",
            "zh": "等级",
        },
        "xp_remaining": {
            "ko": "다음 레벨까지 {xp} XP 남음",
            "en": "{xp} XP remaining to next level",
            "zh": "距离下一等级还需 {xp} XP",
        }
    }

    username = st.session_state.username
    user_xp = st.session_state.user_xp.get(username, 0)
    user_level = calculate_level(user_xp)
    xp_percentage = calculate_xp_percentage(user_xp)
    xp_left = XP_PER_LEVEL - (user_xp % XP_PER_LEVEL)

    col1, col2 = st.columns([1, 4])

    with col1:
        main_image_path = Path("asset") / "SeoulTripView.png"
        if main_image_path.exists():
            st.image(main_image_path, use_container_width=True)
        else:
            st.info("이미지를 찾을 수 없습니다: asset/SeoulTripView.png")

    with col2:
        st.markdown(f"**{messages['level'][lang]} {user_level}** ({user_xp} XP)")
        st.progress(xp_percentage / 100)
        st.caption(messages["xp_remaining"][lang].format(xp=xp_left))


def change_page(page):
    """페이지 전환 함수"""
    st.session_state.current_page = page
    
    # 페이지 전환 시 일부 상태 초기화
    if page != "map":
        st.session_state.clicked_location = None
        st.session_state.navigation_active = False
        st.session_state.navigation_destination = None
        st.session_state.transport_mode = None

def authenticate_user(username, password):
    """사용자 인증 함수"""
    if "users" not in st.session_state:
        return False
    
    return username in st.session_state.users and st.session_state.users[username] == password

def register_user(username, password):
    """사용자 등록 함수"""
    if "users" not in st.session_state:
        st.session_state.users = {"admin": "admin"}
    
    if username in st.session_state.users:
        return False
    
    st.session_state.users[username] = password
    
    # 신규 사용자 데이터 초기화
    if "user_xp" not in st.session_state:
        st.session_state.user_xp = {}
    st.session_state.user_xp[username] = 0
    
    if "user_visits" not in st.session_state:
        st.session_state.user_visits = {}
    st.session_state.user_visits[username] = []
    
    save_session_data()
    return True

def logout_user():
    """로그아웃 함수"""
    st.session_state.logged_in = False
    st.session_state.username = ""
    change_page("login")

def init_session_state():
    """세션 상태 초기화"""
    # 로그인 관련 상태
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "login"
        
    # 사용자 데이터
    if "users" not in st.session_state:
        st.session_state.users = {"admin": "admin"}  # 기본 관리자 계정
    if "user_xp" not in st.session_state:
        st.session_state.user_xp = {}
    if "user_visits" not in st.session_state:
        st.session_state.user_visits = {}
        
    # 지도 관련 상태
    if 'language' not in st.session_state:
        st.session_state.language = "한국어"
        st.session_state.texts = {
            "한국어": {
                "app_title": "서울 관광앱",
                "login_tab": "로그인",
                "join_tab": "회원가입",
                "login_title": "로그인",
                "join_title": "회원가입",
                "id_label": "아이디",
                "pw_label": "비밀번호",
                "pw_confirm_label": "비밀번호 확인",
                "remember_id": "아이디 저장",
                "login_button": "로그인",
                "join_button": "가입하기",
                "login_success": "🎉 로그인 성공!",
                "login_failed": "❌ 아이디 또는 비밀번호가 올바르지 않습니다.",
                "input_required": "아이디와 비밀번호를 입력해주세요.",
                "pw_mismatch": "비밀번호와 비밀번호 확인이 일치하지 않습니다.",
                "join_success": "✅ 회원가입 완료!",
                "user_exists": "⚠️ 이미 존재하는 아이디입니다.",
                "new_id": "새 아이디",
                "new_pw": "새 비밀번호",
                "welcome_msg": "👋 {username}님, 환영합니다!",
                "select_menu": "원하는 메뉴를 선택하세요",
                "map_title": "🗺️ 서울 관광 장소 지도",
                "map_description": "서울의 주요 관광 명소를 지도에서 확인하고 길을 찾으세요.",
                "view_map_button": "관광 지도 보기",
                "course_title": "🗓️ 서울 여행 코스 추천",
                "course_description": "AI가 당신의 취향에 맞는 최적의 여행 코스를 추천해 드립니다.",
                "create_course_button": "여행 코스 만들기",
                "history_title": "📝 나의 여행 기록",
                "history_description": "방문했던 장소와 획득한 경험치를 확인하세요.",
                "view_history_button": "여행 기록 보기",
                "logout_button": "🔓 로그아웃",
                "map_back_to_menu": "← 메뉴로 돌아가기",
                "map_api_key_not_set": "Google Maps API 키가 설정되지 않았습니다.",
                "map_enter_api_key": "Google Maps API 키를 입력하세요",
                "map_api_key_set_success": "API 키가 설정되었습니다. 지도를 로드합니다.",
                "map_api_key_required_info": "Google Maps를 사용하려면 API 키가 필요합니다.",
                "language": "🌏 언어",
                "map_loading_data": "서울 관광 데이터를 로드하는 중...",
                "map_load_complete": "총 {num_markers}개의 관광지 로드 완료!",
                "map_load_failed": "관광지 데이터를 로드할 수 없습니다.",
                "map_my_location": "내 위치",
                "map_current_location": "현재 위치",
                "map_current_location_category": "현재 위치",
                "map_markers_displayed": "지도에 {num_markers}개의 장소를 표시했습니다.",
                "map_place_info": "장소 정보",
                "map_search_place": "장소 검색",
                "map_search_results": "검색 결과",
                "map_find_directions": "길찾기",
                "map_visit_history": "방문기록",
                "map_visited": "방문",
                "map_xp_earned": "획득",
                "map_already_visited_today": "이미 오늘 방문한 장소입니다.",
                "map_no_search_results": "'{search_term}'에 대한 검색 결과가 없습니다.",
                "map_places_by_category": "카테고리별 장소",
                "map_category": "분류",
                "map_other_category": "기타",
                "map_no_destination_info": "목적지 정보가 없습니다.",
                "map_back_to_map": "지도로 돌아가기",
                "map_navigation_to": "까지 내비게이션",
                "map_select_transport": "이동 수단 선택",
                "map_walking": "도보",
                "map_estimated_time": "예상 소요 시간",
                "map_minute": "분",
                "map_select_walk": "도보 선택",
                "map_transit": "대중교통",
                "map_select_transit": "대중교통 선택",
                "map_driving": "자동차",
                "map_select_drive": "자동차 선택",
                "map_route": "경로",
                "map_distance": "거리",
                "map_transport": "이동 수단",
                "map_route_guide": "경로 안내",
                "map_departure": "현재 위치에서 출발합니다",
                "map_straight_and_turn_right": "{distance:.0f}m 직진 후 오른쪽으로 턴",
                "map_straight_and_turn_left": "{distance:.0f}m 직진 후 왼쪽으로 턴",
                "map_arrive_at_destination": "{distance:.0f}m 직진 후 목적지 도착",
                "map_other_transport_modes": "다른 이동 수단",
                "map_end_navigation": "내비게이션 종료",
                "course_ai_recommendation_title": "AI 추천 코스",
                "course_ai_recommendation_description": "AI 추천 코스 설명",
                "history_page_title": "나의 관광 이력",
                "level_text": "레벨 {level}",
                "total_xp_text": "총 경험치: {xp} XP",
                "next_level_xp_text": "다음 레벨까지 {remaining_xp} XP",
                "total_visits_metric": "총 방문 횟수",
                "visited_places_metric": "방문한 장소 수",
                "earned_xp_metric": "획득한 경험치",
                "visit_history_tab": "📝 방문 기록",
                "all_tab": "전체",
                "recent_tab": "최근순",
                "xp_tab": "경험치순",
                "visit_map_title": "🗺️ 방문 지도",
                "no_visit_history": "아직 방문 기록이 없습니다. 지도에서 장소를 방문하면 여기에 기록됩니다.",
                "generate_sample_data": "예시 데이터 생성",
                "sample_data_success": "예시 데이터가 생성되었습니다! +{total_xp} XP 획득!",
                "visit_date": "방문일",
                "visits_count": "{count}회",
                "places_count": "{count}곳",
                "xp_points": "{xp} XP",
                "no_map_visits": "지도에 표시할 방문 기록이 없습니다.",
                "travel_info_input": "여행 정보 입력",
                "travel_style_active": "활동적인",
                "travel_style_relaxation": "휴양",
                "travel_style_food": "맛집",
                "travel_style_shopping": "쇼핑",
                "travel_style_history_culture": "역사/문화",
                "travel_style_nature": "자연",
                "generate_course_button": "코스 생성하기",
                "select_travel_style_warning": "최소 하나 이상의 여행 스타일을 선택해주세요.",
                "generating_course_spinner": "최적의 관광 코스를 생성 중입니다...",
                "course_generation_complete": "코스 생성 완료!",
                "recommended_course_title": "추천 코스",
                "insufficient_recommendations": "추천 장소가 부족합니다.",
                "morning_time_slot": "오전 (09:00-12:00)",
                "afternoon_time_slot": "오후 (13:00-16:00)",
                "evening_time_slot": "저녁 (16:00-19:00)",
                "category_label": "분류: {category}",
                "location_label": "위치: {address}",
                "default_spots": ["경복궁", "남산서울타워", "명동"],
                "tourist_spot": "관광지",
                "course_map_title": "🗺️ 코스 지도",
                "map_display_error": "코스 장소의 좌표 정보가 없어 지도에 표시할 수 없습니다.",
                "save_course_button": "이 코스 저장하기",
                "course_saved_success": "코스가 저장되었습니다!",
                "travel_date_start": "여행 시작일",
                "travel_date_end": "여행 종료일",
                "travel_people_count": "여행 인원",
                "travel_with_children": "아이 동반",
                "travel_style": "여행 스타일",
                "travel_days_total": "총 {days}일 일정",
                "course_history_culture": "서울 역사/문화 탐방 코스",
                "course_shopping_food": "서울 쇼핑과 미식 코스",
                "course_shopping": "서울 쇼핑 중심 코스", 
                "course_food": "서울 미식 여행 코스",
                "course_nature": "서울의 자연 코스",
                "course_active": "액티브 서울 코스",
                "course_healing": "서울 힐링 여행 코스",
            },
            "중국어": {
                "app_title": "首尔旅游应用",
                "login_tab": "登录",
                "join_tab": "注册",
                "login_title": "登录",
                "join_title": "注册",
                "id_label": "用户名",
                "pw_label": "密码",
                "pw_confirm_label": "确认密码",
                "remember_id": "记住用户名",
                "login_button": "登录",
                "join_button": "注册",
                "login_success": "🎉 登录成功！",
                "login_failed": "❌ 用户名或密码不正确。",
                "input_required": "请输入用户名和密码。",
                "pw_mismatch": "密码和确认密码不匹配。",
                "join_success": "✅ 注册完成！",
                "user_exists": "⚠️ 此用户名已存在。",
                "new_id": "新用户名",
                "new_pw": "新密码",
                "welcome_msg": "👋 欢迎，{username}！",
                "select_menu": "请选择菜单",
                "map_title": "🗺️ 首尔旅游地图",
                "map_description": "在地图上查看首尔的主要旅游景点并找到路线。",
                "view_map_button": "查看旅游地图",
                "course_title": "🗓️ 首尔旅游路线推荐",
                "course_description": "AI将根据您的喜好推荐最佳旅游路线。",
                "create_course_button": "创建旅游路线",
                "history_title": "📝 我的旅行记录",
                "history_description": "查看您访问过的地点和获得的经验值。",
                "view_history_button": "查看旅行记录",
                "logout_button": "🔓 登出",
                "map_back_to_menu": "← 返回菜单",
                "map_api_key_not_set": "Google Maps API密钥未设置。",
                "map_enter_api_key": "请输入Google Maps API密钥",
                "map_api_key_set_success": "API密钥已设置。正在加载地图。",
                "map_api_key_required_info": "使用Google Maps需要API密钥。",
                "language": "🌏 语言",
                "map_loading_data": "正在加载首尔旅游数据...",
                "map_load_complete": "已加载{num_markers}个旅游景点！",
                "map_load_failed": "无法加载旅游景点数据。",
                "map_my_location": "我的位置",
                "map_current_location": "当前位置",
                "map_current_location_category": "当前位置",
                "map_markers_displayed": "地图上显示了{num_markers}个地点。",
                "map_place_info": "地点信息",
                "map_search_place": "搜索地点",
                "map_search_results": "搜索结果",
                "map_find_directions": "查找路线",
                "map_visit_history": "访问记录",
                "map_visited": "已访问",
                "map_xp_earned": "获得",
                "map_already_visited_today": "今天已经访问过这个地点。",
                "map_no_search_results": "没有关于'{search_term}'的搜索结果。",
                "map_places_by_category": "按类别查看地点",
                "map_category": "类别",
                "map_other_category": "其他",
                "map_no_destination_info": "没有目的地信息。",
                "map_back_to_map": "返回地图",
                "map_navigation_to": "导航至",
                "map_select_transport": "选择交通方式",
                "map_walking": "步行",
                "map_estimated_time": "预计时间",
                "map_minute": "分钟",
                "map_select_walk": "选择步行",
                "map_transit": "公共交通",
                "map_select_transit": "选择公共交通",
                "map_driving": "驾车",
                "map_select_drive": "选择驾车",
                "map_route": "路线",
                "map_distance": "距离",
                "map_transport": "交通方式",
                "map_route_guide": "路线指南",
                "map_departure": "从当前位置出发",
                "map_straight_and_turn_right": "直行{distance:.0f}米后右转",
                "map_straight_and_turn_left": "直行{distance:.0f}米后左转",
                "map_arrive_at_destination": "直行{distance:.0f}米后到达目的地",
                "map_other_transport_modes": "其他交通方式",
                "map_end_navigation": "结束导航",
                "course_ai_recommendation_title": "AI推荐路线",
                "course_ai_recommendation_description": "AI推荐路线说明",
                "history_page_title": "我的旅游历史",
                "level_text": "等级 {level}",
                "total_xp_text": "总经验值: {xp} XP",
                "next_level_xp_text": "距离下一级还需 {remaining_xp} XP",
                "total_visits_metric": "总访问次数",
                "visited_places_metric": "已访问地点数",
                "earned_xp_metric": "获得的经验值",
                "visit_history_tab": "📝 访问记录",
                "all_tab": "全部",
                "recent_tab": "最近",
                "xp_tab": "按经验值",
                "visit_map_title": "🗺️ 访问地图",
                "no_visit_history": "尚无访问记录。在地图上访问地点后将在此处记录。",
                "generate_sample_data": "生成示例数据",
                "sample_data_success": "示例数据已生成！获得 +{total_xp} XP！",
                "visit_date": "访问日期",
                "visits_count": "{count}次",
                "places_count": "{count}处",
                "xp_points": "{xp} XP",
                "no_map_visits": "没有可显示在地图上的访问记录。",
                "travel_info_input": "旅行信息输入",
                "travel_style_active": "活动型",
                "travel_style_relaxation": "休闲型",
                "travel_style_food": "美食型",
                "travel_style_shopping": "购物型",
                "travel_style_history_culture": "历史/文化型",
                "travel_style_nature": "自然型",
                "generate_course_button": "生成路线",
                "select_travel_style_warning": "请至少选择一种旅行风格。",
                "generating_course_spinner": "正在生成最佳旅游路线...",
                "course_generation_complete": "路线生成完成！",
                "recommended_course_title": "推荐路线",
                "insufficient_recommendations": "推荐地点不足。",
                "morning_time_slot": "上午 (09:00-12:00)",
                "afternoon_time_slot": "下午 (13:00-16:00)",
                "evening_time_slot": "傍晚 (16:00-19:00)",
                "category_label": "类别: {category}",
                "location_label": "位置: {address}",
                "default_spots": ["景福宫", "首尔南山塔", "明洞"],
                "tourist_spot": "景点",
                "course_map_title": "🗺️ 路线地图",
                "map_display_error": "由于路线地点缺少坐标信息，无法在地图上显示。",
                "save_course_button": "保存此路线",
                "course_saved_success": "路线已保存！",
                "travel_date_start": "旅行开始日期",
                "travel_date_end": "旅行结束日期",
                "travel_people_count": "旅行人数",
                "travel_with_children": "携带儿童",
                "travel_style": "旅行风格",
                "travel_days_total": "共{days}天行程",
                "course_history_culture": "首尔历史/文化探索路线",
                "course_shopping_food": "首尔购物与美食路线",
                "course_shopping": "首尔购物中心路线",
                "course_food": "首尔美食之旅路线",
                "course_nature": "首尔自然风光路线",
                "course_active": "活力首尔路线",
                "course_healing": "首尔治愈之旅路线"
            },
            "영어": {
                "app_title": "Seoul Tourist App",
                "login_tab": "Login",
                "join_tab": "Sign Up",
                "login_title": "Login",
                "join_title": "Sign Up",
                "id_label": "Username",
                "pw_label": "Password",
                "pw_confirm_label": "Confirm Password",
                "remember_id": "Remember Username",
                "login_button": "Login",
                "join_button": "Sign Up",
                "login_success": "🎉 Login Successful!",
                "login_failed": "❌ Username or password is incorrect.",
                "input_required": "Please enter your username and password.",
                "pw_mismatch": "Password and confirm password do not match.",
                "join_success": "✅ Registration Complete!",
                "user_exists": "⚠️ This username already exists.",
                "new_id": "New Username",
                "new_pw": "New Password",
                "welcome_msg": "👋 Welcome, {username}!",
                "select_menu": "Please select a menu",
                "map_title": "🗺️ Seoul Tourist Map",
                "map_description": "View Seoul's major tourist attractions on the map and find directions.",
                "view_map_button": "View Tourist Map",
                "course_title": "🗓️ Seoul Travel Course Recommendations",
                "course_description": "AI will recommend the best travel course based on your preferences.",
                "create_course_button": "Create Travel Course",
                "history_title": "📝 My Travel Records",
                "history_description": "Check the places you've visited and the experience points you've earned.",
                "view_history_button": "View Travel Records",
                "logout_button": "🔓 Logout",
                "map_back_to_menu": "← Back to Menu",
                "map_api_key_not_set": "Google Maps API key is not set.",
                "map_enter_api_key": "Please enter Google Maps API key",
                "map_api_key_set_success": "API key has been set. Loading map.",
                "map_api_key_required_info": "API key is required to use Google Maps.",
                "language": "🌏 Language",
                "map_loading_data": "Loading Seoul tourist data...",
                "map_load_complete": "Loaded {num_markers} tourist attractions!",
                "map_load_failed": "Unable to load tourist attraction data.",
                "map_my_location": "My Location",
                "map_current_location": "Current Location",
                "map_current_location_category": "Current Location",
                "map_markers_displayed": "Displayed {num_markers} places on the map.",
                "map_place_info": "Place Information",
                "map_search_place": "Search Place",
                "map_search_results": "Search Results",
                "map_find_directions": "Find Directions",
                "map_visit_history": "Visit History",
                "map_visited": "Visited",
                "map_xp_earned": "Earned",
                "map_already_visited_today": "You've already visited this place today.",
                "map_no_search_results": "No search results for '{search_term}'.",
                "map_places_by_category": "Places by Category",
                "map_category": "Category",
                "map_other_category": "Other",
                "map_no_destination_info": "No destination information.",
                "map_back_to_map": "Back to Map",
                "map_navigation_to": "Navigation to",
                "map_select_transport": "Select Transport Mode",
                "map_walking": "Walking",
                "map_estimated_time": "Estimated Time",
                "map_minute": "minute(s)",
                "map_select_walk": "Select Walking",
                "map_transit": "Public Transit",
                "map_select_transit": "Select Public Transit",
                "map_driving": "Driving",
                "map_select_drive": "Select Driving",
                "map_route": "Route",
                "map_distance": "Distance",
                "map_transport": "Transport Mode",
                "map_route_guide": "Route Guide",
                "map_departure": "Departing from current location",
                "map_straight_and_turn_right": "Go straight for {distance:.0f}m then turn right",
                "map_straight_and_turn_left": "Go straight for {distance:.0f}m then turn left",
                "map_arrive_at_destination": "Go straight for {distance:.0f}m then arrive at destination",
                "map_other_transport_modes": "Other Transport Modes",
                "map_end_navigation": "End Navigation",
                "course_ai_recommendation_title": "AI Recommended Course",
                "course_ai_recommendation_description": "AI Recommended Course Description",
                "history_page_title": "My Tourism History",
                "level_text": "Level {level}",
                "total_xp_text": "Total XP: {xp} XP",
                "next_level_xp_text": "Next level in {remaining_xp} XP",
                "total_visits_metric": "Total Visits",
                "visited_places_metric": "Places Visited",
                "earned_xp_metric": "XP Earned",
                "visit_history_tab": "📝 Visit History",
                "all_tab": "All",
                "recent_tab": "Recent",
                "xp_tab": "By XP",
                "visit_map_title": "🗺️ Visit Map",
                "no_visit_history": "No visit history yet. Visit places on the map to record them here.",
                "generate_sample_data": "Generate Sample Data",
                "sample_data_success": "Sample data generated! +{total_xp} XP earned!",
                "visit_date": "Visit Date",
                "visits_count": "{count} visit(s)",
                "places_count": "{count} place(s)",
                "xp_points": "{xp} XP",
                "no_map_visits": "No visit records to display on the map.",
                "travel_info_input": "Travel Information Input",
                "travel_style_active": "Active",
                "travel_style_relaxation": "Relaxation",
                "travel_style_food": "Food",
                "travel_style_shopping": "Shopping",
                "travel_style_history_culture": "History/Culture",
                "travel_style_nature": "Nature",
                "generate_course_button": "Generate Course",
                "select_travel_style_warning": "Please select at least one travel style.",
                "generating_course_spinner": "Generating optimal tourist course...",
                "course_generation_complete": "Course generation complete!",
                "recommended_course_title": "Recommended Course",
                "insufficient_recommendations": "Insufficient recommended places.",
                "morning_time_slot": "Morning (09:00-12:00)",
                "afternoon_time_slot": "Afternoon (13:00-16:00)",
                "evening_time_slot": "Evening (16:00-19:00)",
                "category_label": "Category: {category}",
                "location_label": "Location: {address}",
                "default_spots": ["Gyeongbokgung Palace", "N Seoul Tower", "Myeongdong"],
                "tourist_spot": "Tourist Spot",
                "course_map_title": "🗺️ Course Map",
                "map_display_error": "Cannot display on map due to missing coordinate information for course locations.",
                "save_course_button": "Save This Course",
                "course_saved_success": "Course has been saved!",
                "travel_date_start": "Travel Start Date",
                "travel_date_end": "Travel End Date",
                "travel_people_count": "Number of Travelers",
                "travel_with_children": "Traveling with Children",
                "travel_style": "Travel Style",
                "travel_days_total": "Total {days} day itinerary",
                "course_history_culture": "Seoul History & Culture Exploration Course",
                "course_shopping_food": "Seoul Shopping & Gastronomy Course",
                "course_shopping": "Seoul Shopping-Focused Course",
                "course_food": "Seoul Culinary Tour Course",
                "course_nature": "Seoul Nature Course",
                "course_active": "Active Seoul Course",
                "course_healing": "Seoul Healing Travel Course"
            }
        }
    if 'clicked_location' not in st.session_state:
        st.session_state.clicked_location = None
    if 'navigation_active' not in st.session_state:
        st.session_state.navigation_active = False
    if 'navigation_destination' not in st.session_state:
        st.session_state.navigation_destination = None
    if 'transport_mode' not in st.session_state:
        st.session_state.transport_mode = None
    
    # 관광 데이터 관련 상태
    if 'all_markers' not in st.session_state:
        st.session_state.all_markers = []
    if 'markers_loaded' not in st.session_state:
        st.session_state.markers_loaded = False
    if 'tourism_data' not in st.session_state:
        st.session_state.tourism_data = []
    if 'saved_courses' not in st.session_state:
        st.session_state.saved_courses = []
        
    # Google Maps API 키
    if "google_maps_api_key" not in st.session_state:
        # secrets.toml에서 가져오기 시도
        try:
            st.session_state.google_maps_api_key = st.secrets["google_maps_api_key"]
        except:
            # 기본값 설정 (실제 사용시 자신의 API 키로 변경 필요)
            st.session_state.google_maps_api_key = "YOUR_GOOGLE_MAPS_API_KEY"
    
    # 저장된 세션 데이터 로드
    load_session_data()

def load_session_data():
    """저장된 세션 데이터 로드"""
    try:
        if os.path.exists(SESSION_DATA_FILE):
            with open(SESSION_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 데이터 복원
                st.session_state.users = data.get("users", {"admin": "admin"})
                st.session_state.user_visits = data.get("user_visits", {})
                st.session_state.user_xp = data.get("user_xp", {})
                st.session_state.saved_courses = data.get("saved_courses", [])
                return True
    except Exception as e:
        st.error(f"세션 데이터 로드 오류: {e}")
    return False

def save_session_data():
    """세션 데이터 저장"""
    try:
        # 데이터 폴더 생성
        os.makedirs(os.path.dirname(SESSION_DATA_FILE), exist_ok=True)
        
        data = {
            "users": st.session_state.users,
            "user_visits": st.session_state.user_visits,
            "user_xp": st.session_state.user_xp,
            "saved_courses": st.session_state.saved_courses
        }
        
        with open(SESSION_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"세션 데이터 저장 오류: {e}")
        return False

def calculate_level(xp):
    """레벨 계산 함수"""
    return int(xp / XP_PER_LEVEL) + 1

def calculate_xp_percentage(xp):
    """경험치 비율 계산 (다음 레벨까지)"""
    current_level = calculate_level(xp)
    xp_for_current_level = (current_level - 1) * XP_PER_LEVEL
    xp_for_next_level = current_level * XP_PER_LEVEL
    
    xp_in_current_level = xp - xp_for_current_level
    xp_needed_for_next = xp_for_next_level - xp_for_current_level
    
    return int((xp_in_current_level / xp_needed_for_next) * 100)

def add_visit(username, place_name, lat, lng):
    """방문 기록 추가"""
    if username not in st.session_state.user_visits:
        st.session_state.user_visits[username] = []
    
    # XP 획득
    if username not in st.session_state.user_xp:
        st.session_state.user_xp[username] = 0
    
    xp_gained = PLACE_XP.get(place_name, 10)  # 기본 10XP, 장소별로 다른 XP
    st.session_state.user_xp[username] += xp_gained
    
    # 방문 데이터 생성
    visit_data = {
        "place_name": place_name,
        "latitude": lat,
        "longitude": lng,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "xp_gained": xp_gained,
        "rating": None
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
        save_session_data()  # 방문 기록 저장
        return True, xp_gained
    return False, 0

def get_location_position():
    """사용자의 현재 위치를 반환"""
    try:
        from streamlit_js_eval import get_geolocation
        
        location = get_geolocation()
        if location and "coords" in location:
            return [location["coords"]["latitude"], location["coords"]["longitude"]]
    except Exception as e:
        st.warning(f"위치 정보를 가져올 수 없습니다: {e}")
        
    return DEFAULT_LOCATION  # 기본 위치 (서울시청)

#################################################
# 데이터 로드 함수
#################################################

def load_excel_files(language="한국어"):
    """데이터 폴더에서 Excel 파일 로드 - 개선된 버전"""
    data_folder = Path("asset")
    all_markers = []
    
    # 파일이 존재하는지 확인
    if not data_folder.exists():
        st.error(f"데이터 폴더({data_folder})가 존재하지 않습니다.")
        return []
    
    # 파일 목록 확인
    excel_files = list(data_folder.glob("*.xlsx"))
    
    if not excel_files:
        #st.error("Excel 파일을 찾을 수 없습니다. GitHub 저장소의 파일을 확인해주세요.")
        st.info("확인할 경로: asset/*.xlsx")
        return []
    
    # 찾은 파일 목록 표시
    #st.success(f"{len(excel_files)}개의 Excel 파일을 찾았습니다.")
    # for file_path in excel_files:
    #     st.info(f"파일 발견: {file_path.name}")
    
    # 각 파일 처리
    for file_path in excel_files:
        try:
            # 파일 카테고리 결정
            file_category = "기타"
            file_name_lower = file_path.name.lower()
            
            for category, keywords in FILE_CATEGORIES.items():
                if any(keyword.lower() in file_name_lower for keyword in keywords):
                    file_category = category
                    break
            
            # 파일 로드
            #st.info(f"'{file_path.name}' 파일을 '{file_category}' 카테고리로 로드 중...")
            df = pd.read_excel(file_path, engine='openpyxl')
            
            if df.empty:
                st.warning(f"'{file_path.name}' 파일에 데이터가 없습니다.")
                continue
            
            # 데이터프레임 기본 정보 출력
            #st.success(f"'{file_path.name}' 파일 로드 완료: {len(df)}행, {len(df.columns)}열")
            
            # 데이터 전처리 및 마커 변환
            markers = process_dataframe(df, file_category, language)
            
            if markers:
                all_markers.extend(markers)
                #st.success(f"'{file_path.name}'에서 {len(markers)}개 마커 추출 성공")
            else:
                st.warning(f"'{file_path.name}'에서 유효한 마커를 추출할 수 없습니다.")
            
        except Exception as e:
            st.error(f"'{file_path.name}' 파일 처리 오류: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
    
    if not all_markers:
        st.error("모든 파일에서 유효한 마커를 찾을 수 없습니다.")
    else:
        st.success(f"총 {len(all_markers)}개의 마커를 성공적으로 로드했습니다.")
    
    return all_markers

def process_dataframe(df, category, language="한국어"):
    """데이터프레임을 Google Maps 마커 형식으로 변환 - X, Y 좌표 처리 개선"""
    markers = []
    
    # 1. X, Y 좌표 열 감지 (대소문자 및 다양한 이름 형식 지원)
    x_candidates = [col for col in df.columns if ('x' in col.lower() or 'X' in col) and '좌표' in col]
    y_candidates = [col for col in df.columns if ('y' in col.lower() or 'Y' in col) and '좌표' in col]
    
    # 중국어 좌표 열 처리
    # if not x_candidates:
    #     x_candidates = [col for col in df.columns if 'X坐标' in col or 'x坐标' in col]
    # if not y_candidates:
    #     y_candidates = [col for col in df.columns if 'Y坐标' in col or 'y坐标' in col]
    
    # 단순 X, Y 열 확인
    # if not x_candidates:
    #     x_candidates = [col for col in df.columns if col.upper() == 'X' or col.lower() == 'x']
    # if not y_candidates:
    #     y_candidates = [col for col in df.columns if col.upper() == 'Y' or col.lower() == 'y']
    
    # 경도/위도 열 확인
    # if not x_candidates:
    #     x_candidates = [col for col in df.columns if '경도' in col or 'longitude' in col.lower() or 'lon' in col.lower()]
    # if not y_candidates:
    #     y_candidates = [col for col in df.columns if '위도' in col or 'latitude' in col.lower() or 'lat' in col.lower()]
    
    # X, Y 좌표 열 선택
    x_col = x_candidates[0] if x_candidates else None
    y_col = y_candidates[0] if y_candidates else None
    
    # 2. X, Y 좌표 열이 없는 경우 숫자 열에서 자동 감지
    if not x_col or not y_col:
        st.warning(f"'{category}' 데이터에서 명시적인 X, Y 좌표 열을 찾을 수 없습니다. 숫자 열에서 자동 감지를 시도합니다.")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_cols) >= 2:
            # 각 열의 값 범위를 분석하여 위경도 추정
            for col in numeric_cols:
                if df[col].dropna().empty:
                    continue
                    
                # 열의 값 통계 확인
                col_mean = df[col].mean()
                col_min = df[col].min()
                col_max = df[col].max()
                
                # 경도(X) 범위 확인: 한국 경도는 대략 124-132
                if 120 <= col_mean <= 140:
                    x_col = col
                    st.info(f"X좌표(경도)로 '{col}' 열을 자동 감지했습니다. 범위: {col_min:.2f}~{col_max:.2f}")
                
                # 위도(Y) 범위 확인: 한국 위도는 대략 33-43
                elif 30 <= col_mean <= 45:
                    y_col = col
                    st.info(f"Y좌표(위도)로 '{col}' 열을 자동 감지했습니다. 범위: {col_min:.2f}~{col_max:.2f}")
    
    # 3. 좌표 열을 여전히 못 찾은 경우 마지막 시도: 단순히 마지막 두 개의 숫자 열 사용
    # if not x_col or not y_col:
    #     numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    #     if len(numeric_cols) >= 2:
    #         x_col = numeric_cols[-2]  # 뒤에서 두 번째 숫자 열
    #         y_col = numeric_cols[-1]  # 마지막 숫자 열
    #         st.warning(f"좌표 추정: X좌표='{x_col}', Y좌표='{y_col}' (마지막 두 숫자 열)")
    
    # 4. 여전히 좌표 열을 찾지 못한 경우
    if not x_col or not y_col:
        st.error(f"'{category}' 데이터에서 X, Y 좌표 열을 찾을 수 없습니다.")
        st.error(f"사용 가능한 열: {', '.join(df.columns.tolist())}")
        return []
    
    # 5. 좌표 데이터 전처리
    #st.success(f"좌표 열 감지 성공: X='{x_col}', Y='{y_col}'")
    
    # NaN 값 처리
    df = df.dropna(subset=[x_col, y_col])
    
    # 문자열을 숫자로 변환
    # try:
    #     df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
    #     df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
    #     df = df.dropna(subset=[x_col, y_col])  # 변환 후 NaN이 된 값 제거
    # except Exception as e:
    #     st.warning(f"좌표 변환 오류: {str(e)}")
    
    # 0 값 제거
    df = df[(df[x_col] != 0) & (df[y_col] != 0)]
    
    # 6. 좌표 유효성 검증 및 교정
    # 한국 영역 좌표 체크 (경도 124-132, 위도 33-43)
    valid_coords = (df[x_col] >= 124) & (df[x_col] <= 132) & (df[y_col] >= 33) & (df[y_col] <= 43)
    
    # X,Y가 바뀐 경우 체크 (Y가 경도, X가 위도인 경우)
  #  swapped_coords = (df[y_col] >= 124) & (df[y_col] <= 132) & (df[x_col] >= 33) & (df[x_col] <= 43)
    
    # X,Y가 바뀐 경우 자동 교정
    # if swapped_coords.sum() > valid_coords.sum():
    #     st.warning(f"'{category}' 데이터의 X,Y 좌표가 바뀐 것으로 보입니다. 자동으로 교정합니다.")
    #     df['temp_x'] = df[x_col].copy()
    #     df[x_col] = df[y_col]
    #     df[y_col] = df['temp_x']
    #     df = df.drop('temp_x', axis=1)
        
        # 다시 유효성 검증
   #     valid_coords = (df[x_col] >= 124) & (df[x_col] <= 132) & (df[y_col] >= 33) & (df[y_col] <= 43)
    
    # 유효한 좌표만 필터링
    valid_df = df[valid_coords]
    
    if valid_df.empty:
        st.error(f"'{category}' 데이터에 유효한 한국 영역 좌표가 없습니다.")
        st.info(f"원본 좌표 범위: X({df[x_col].min():.2f}~{df[x_col].max():.2f}), Y({df[y_col].min():.2f}~{df[y_col].max():.2f})")
        
        # 좌표 값 10000으로 나누기 시도 (혹시 UTM 좌표계인 경우)
        if df[x_col].max() > 1000000 or df[y_col].max() > 1000000:
            st.warning("좌표값이 매우 큽니다. UTM 좌표계일 수 있어 10000으로 나누어 변환을 시도합니다.")
            df[x_col] = df[x_col] / 10000
            df[y_col] = df[y_col] / 10000
            
            # 다시 유효성 검증
            valid_coords = (df[x_col] >= 124) & (df[x_col] <= 132) & (df[y_col] >= 33) & (df[y_col] <= 43)
            valid_df = df[valid_coords]
            
            if not valid_df.empty:
                st.success(f"좌표 변환 성공! 유효한 좌표 {len(valid_df)}개 발견")
            else:
                st.error("좌표 변환 실패! 유효한 한국 영역 좌표를 찾을 수 없습니다.")
                return []
    
    # 7. 이름 열 결정
    name_col = get_name_column(df, category, language)
    
    # 8. 주소 열 결정
    address_col = get_address_column(df, language)
    
    # 9. 각 행을 마커로 변환
    success_count = 0
    for idx, row in valid_df.iterrows():
        try:
            # 기본 정보
            if name_col and pd.notna(row.get(name_col)):
                name = str(row[name_col])
            else:
                name = f"{category} #{idx+1}"
                
            # 좌표 추출
            lat = float(row[y_col])  # 위도 (Y좌표)
            lng = float(row[x_col])  # 경도 (X좌표)
            
            # 좌표값 유효성 최종 확인
            if not (33 <= lat <= 43 and 124 <= lng <= 132):
                continue  # 유효하지 않은 좌표 건너뛰기
            
            # 주소 정보
            address = ""
            if address_col and address_col in row and pd.notna(row[address_col]):
                address = row[address_col]
            
            # 정보창 HTML 구성
            info = build_info_html(row, name, address, category)
            
            # 마커 색상 결정
            color = CATEGORY_COLORS.get(category, "gray")
            
            # 마커 생성
            marker = {
                'lat': lat,
                'lng': lng,
                'title': name,
                'color': color,
                'category': category,
                'info': info,
                'address': address
            }
            markers.append(marker)
            success_count += 1
            
        except Exception as e:
            print(f"마커 생성 오류 (행 #{idx}): {e}")
            continue
    
    #st.success(f"'{category}' 데이터에서 {success_count}개의 마커를 성공적으로 생성했습니다.")
    return markers

# 이름 열 결정 함수
def get_name_column(df, category, language):
    """카테고리와 언어에 따른 이름 열 결정"""
    name_candidates = []
    
    # 언어별 기본 후보
    if language == "한국어":
        name_candidates = ['명칭(한국어)', '명칭', '이름', '시설명', '관광지명', '장소명', '상호', '상호명']
    elif language == "영어":
        name_candidates = ['명칭(영어)', 'PLACE', 'NAME', 'TITLE', 'ENGLISH_NAME', 'name']
    elif language == "중국어":
        name_candidates = ['명칭(중국어)', '名称', '中文名', '名稱']
    
    # 카테고리별 특수 처리
    if category == "종로구 관광지" and language == "중국어":
        name_candidates = ['名称'] + name_candidates
    elif category == "한국음식점":
        if language == "한국어":
            name_candidates = ['상호명(한글)', '상호명', '업소명'] + name_candidates
        elif language == "영어":
            name_candidates = ['상호명(영문)', '영문명'] + name_candidates
        elif language == "중국어":
            name_candidates = ['상호명(중문)', '중문명'] + name_candidates
    
    # 후보 열 중 존재하는 첫 번째 열 사용
    for col in name_candidates:
        if col in df.columns:
            return col
    
    # 명칭 열이 없으면 첫 번째 문자열 열 사용
    string_cols = [col for col in df.columns if df[col].dtype == 'object']
    if string_cols:
        return string_cols[0]
    
    return None

# 주소 열 결정 함수
def get_address_column(df, language):
    """언어에 따른 주소 열 결정"""
    address_candidates = []
    
    if language == "한국어":
        address_candidates = ['주소(한국어)', '주소', '소재지', '도로명주소', '지번주소', '위치', 'ADDRESS']
    elif language == "영어":
        address_candidates = ['주소(영어)', 'ENGLISH_ADDRESS', 'address', 'location']
    elif language == "중국어":
        address_candidates = ['주소(중국어)', '地址', '位置', '中文地址']
    
    # 후보 열 중 존재하는 첫 번째 열 사용
    for col in address_candidates:
        if col in df.columns:
            return col
    
    return None

# 정보창 HTML 구성 함수
def build_info_html(row, name, address, category):
    """마커 정보창 HTML 구성"""
    info = f"<div style='padding: 10px; max-width: 300px;'>"
    info += f"<h3 style='margin-top: 0; color: #1976D2;'>{name}</h3>"
    info += f"<p><strong>분류:</strong> {category}</p>"
    
    if address:
        info += f"<p><strong>주소:</strong> {address}</p>"
    
    info += "</div>"
    return info
    
def create_Maps_html(api_key, center_lat, center_lng, markers=None, zoom=13, language="ko",
                           navigation_mode=False, start_location=None, end_location=None, transport_mode=None,
                           route_points=None):
    """Google Maps HTML 생성 - 내비게이션 기능 및 일별 경로 연결선 기능 개선"""
    if markers is None:
        markers = []

    # 카테고리별 마커 그룹화 (기존 코드와 동일하게 CATEGORY_COLORS, CATEGORIES_TRANSLATION 사용 가정)
    # 이 부분은 사용자 코드의 CATEGORY_COLORS와 CATEGORIES_TRANSLATION 변수를 참조합니다.
    # 실제 앱에서는 이 변수들이 이 함수 범위 또는 전역 범위에서 접근 가능해야 합니다.
    # 예시로 간단히 남겨둡니다. 실제로는 앱의 상단에 정의된 변수를 사용합니다.
    _CATEGORY_COLORS_EXAMPLE = {
        "체육시설": "blue", "공연행사": "purple", "관광기념품": "green",
        "한국음식점": "orange", "미술관/전시": "pink", "종로구 관광지": "red",
        "기타": "gray", "코스장소": "darkred" # 코스 장소용 색상 추가 가능
    }
    
    categories_for_legend = {} # 범례용 카테고리 수집
    for marker in markers:
        cat = marker.get('category', '기타')
        color = marker.get('color', _CATEGORY_COLORS_EXAMPLE.get(cat, 'gray'))
        if cat not in categories_for_legend:
            categories_for_legend[cat] = {'color': color, 'count': 0}
        categories_for_legend[cat]['count'] += 1

    legend_items = []
    for category, data in categories_for_legend.items():
        # 아이콘 URL 생성 시 주의: 실제 Google Charts 아이콘 URL 형식을 따라야 합니다.
        # 예: http://maps.google.com/mapfiles/ms/icons/{color}-dot.png (단, 이 URL은 오래되었을 수 있음)
        # 좀 더 안정적인 방법은 커스텀 SVG 아이콘을 사용하거나, Google Maps API에서 제공하는 기본 아이콘을 활용하는 것입니다.
        # 여기서는 간단히 색상명만 표시합니다.
        icon_html = f'<span style="display:inline-block;width:12px;height:12px;background-color:{data["color"]};margin-right:5px;border-radius:50%;"></span>'
        legend_items.append(f'<div class="legend-item">{icon_html} {category} ({data["count"]})</div>')
    legend_html = "".join(legend_items)


    # 마커 JavaScript 코드 생성
    markers_js = ""
    unique_marker_objects = [] # 중복 마커 방지 (특히 코스 장소가 일반 마커에도 포함될 경우)
    processed_titles_for_markers = set()

    for i, marker_data in enumerate(markers):
        # 코스 마커와 일반 마커가 겹칠 수 있으므로, title 기준으로 한 번만 생성되도록 처리
        marker_title_check = marker_data.get('title', f"Marker_{i}")
        if marker_title_check in processed_titles_for_markers:
            continue
        processed_titles_for_markers.add(marker_title_check)

        lat = marker_data.get('lat')
        lng = marker_data.get('lng')
        if lat is None or lng is None:
            continue

        color = marker_data.get('color', 'red') # 기본 색상
        # Google Charts 아이콘 URL (예시, 실제 유효한 URL로 대체 필요)
        # icon_url = f"http://maps.google.com/mapfiles/ms/icons/{color}.png" # 색상명 직접 사용
        # 간단한 점 아이콘을 사용하거나, 카테고리별로 다른 아이콘 지정 가능
        icon_details = f"{{ path: google.maps.SymbolPath.CIRCLE, fillColor: '{color}', fillOpacity: 0.9, strokeWeight: 0, scale: 7 }}"


        title = str(marker_data.get('title', '')).replace("'", "\\'").replace("\n", "\\n")
        info_html = str(marker_data.get('info', '정보 없음')).replace("'", "\\'").replace("\n", "<br>")
        category = str(marker_data.get('category', '기타')).replace("'", "\\'")

        info_content = f"""
        <div style='padding: 10px; max-width: 280px; font-family: Arial, sans-serif; font-size: 14px;'>
            <h3 style='margin-top:0; margin-bottom:5px; color: #333; font-size:16px;'>{title}</h3>
            <p style='margin-bottom:3px;'><strong>카테고리:</strong> {category}</p>
            <div style='margin-top:5px; border-top: 1px solid #eee; padding-top:5px;'>{info_html}</div>
        </div>
        """.replace("\n", " ")

        markers_js += f"""
            var marker{i} = new google.maps.Marker({{
                position: {{ lat: {lat}, lng: {lng} }},
                map: map,
                title: '{title}',
                icon: {icon_details},
                animation: google.maps.Animation.DROP
            }});
            markers.push(marker{i}); // JS 전역 배열 'markers'에 추가
            markerCategories.push('{category}'); // JS 전역 배열 'markerCategories'에 추가

            var infowindow{i} = new google.maps.InfoWindow({{
                content: '{info_content}'
            }});
            infoWindows.push(infowindow{i}); // JS 전역 배열 'infoWindows'에 추가

            marker{i}.addListener('click', function() {{
                closeAllInfoWindows();
                infowindow{i}.open(map, marker{i});
                if (currentMarker !== marker{i}) {{
                    if (currentMarker) currentMarker.setAnimation(null);
                    // marker{i}.setAnimation(google.maps.Animation.BOUNCE); // 클릭 시 바운스
                    // currentMarker = marker{i};
                    // setTimeout(function() {{ marker{i}.setAnimation(null); }}, 750); // 바운스 시간
                }}
                 window.parent.postMessage({{type: 'marker_click', title: '{title}', lat: {lat}, lng: {lng}, category: '{category}'}}, '*');
            }});
        """
    # 경로 표시 JavaScript 코드
    route_js = ""
    if route_points and start_location:
        daily_routes_data = {}
        for point in route_points:
            day_val = point.get('day')
            if day_val is None and point.get('title') and 'Day ' in point.get('title'):
                try:
                    day_str = point.get('title').split('Day ')[1].split(' ')[0]
                    day_val = int(day_str)
                except:
                    day_val = 1 # Day 정보 파싱 실패 시 1일차로 간주
            
            if day_val is not None:
                if day_val not in daily_routes_data:
                    daily_routes_data[day_val] = []
                daily_routes_data[day_val].append({'lat': point['lat'], 'lng': point['lng']})
        
        # JavaScript에서 사용할 수 있도록 daily_routes_data를 JSON 문자열로 변환
        # 일자(key)를 기준으로 정렬하여 경로를 순서대로 그림
        sorted_daily_routes_for_js = "{\n"
        for day_num in sorted(daily_routes_data.keys()):
             # 각 일자별 경로 포인트가 최소 1개 이상 있어야 함
            if daily_routes_data[day_num]:
                sorted_daily_routes_for_js += f"      {day_num}: {json.dumps(daily_routes_data[day_num])},\n"
        sorted_daily_routes_for_js += "    }"


        # 경로 색상 배열
        route_colors_array = ['#E53935', '#1E88E5', '#43A047', '#FB8C00', '#8E24AA', '#5D4037', '#00ACC1']

        route_js = f"""
            var startLoc = {{ lat: {start_location[0]}, lng: {start_location[1]} }};
            var dailyRoutes = {sorted_daily_routes_for_js};
            var routeColors = {json.dumps(route_colors_array)};
            var bounds = new google.maps.LatLngBounds();

            // 출발지 마커
            var startMarker = new google.maps.Marker({{
                position: startLoc,
                map: map,
                title: '경로 시작점',
                icon: {{
                    url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png', // 출발지 아이콘
                    scaledSize: new google.maps.Size(40, 40)
                }},
                zIndex: google.maps.Marker.MAX_ZINDEX + 1
            }});
            bounds.extend(startLoc);

            var dayIndex = 0;
            var lastPointOfPreviousDay = startLoc; // 경로 시작점

            var sortedDays = Object.keys(dailyRoutes).map(Number).sort((a,b) => a - b); // 일자 순 정렬

            for (var dayKey of sortedDays) {{
                var dayPathCoordinates = [lastPointOfPreviousDay]; // 이전 지점에서 시작
                var currentDayPoints = dailyRoutes[dayKey];

                if (currentDayPoints && currentDayPoints.length > 0) {{
                    currentDayPoints.forEach(function(point) {{
                        var latLng = new google.maps.LatLng(point.lat, point.lng);
                        dayPathCoordinates.push(latLng);
                        bounds.extend(latLng);
                    }});

                    if (dayPathCoordinates.length > 1) {{ // 최소 2개 지점 있어야 경로 그림
                        var dayPolyline = new google.maps.Polyline({{
                            path: dayPathCoordinates,
                            geodesic: true,
                            strokeColor: routeColors[dayIndex % routeColors.length],
                            strokeOpacity: 0.9,
                            strokeWeight: 5,
                            map: map
                        }});
                        dailyRouteLines.push(dayPolyline); // 토글 위해 저장
                    }}
                    // 현재 날짜의 마지막 지점을 다음 날짜의 시작 연결점으로 업데이트
                    lastPointOfPreviousDay = currentDayPoints[currentDayPoints.length - 1];
                }}
                dayIndex++;
            }}

            // 모든 경로와 마커가 보이도록 지도 범위 조정
            if (Object.keys(dailyRoutes).length > 0 || markers.length > 0) {{
                 map.fitBounds(bounds);
                 // fitBounds 후 줌이 너무 축소되는 것을 방지
                 google.maps.event.addListenerOnce(map, 'bounds_changed', function() {{
                    if (this.getZoom() > 15) {{ // 최대 줌 레벨 제한
                        this.setZoom(15);
                    }}
                 }});
            }}
        """
    
    # 필터링 JS (기존 코드 사용)
    filter_js = """
        function filterMarkers(category) {
            for (var i = 0; i < markers.length; i++) {
                var shouldShow = category === 'all' || markerCategories[i] === category;
                markers[i].setVisible(shouldShow);
            }
            document.querySelectorAll('.filter-button').forEach(function(btn) {
                btn.classList.remove('active');
            });
            var safeCategory = category.replace(/[^a-zA-Z0-9_]/g, '-').toLowerCase(); // ID 안전하게
            var activeBtn = document.getElementById('filter-' + safeCategory);
            if (activeBtn) activeBtn.classList.add('active');
            else document.getElementById('filter-all').classList.add('active');
        }
    """
    # 필터 버튼 HTML 생성 (기존 코드 사용)
    # categories 변수는 JS 스코프 내의 markerCategories를 기반으로 동적 생성 필요
    # Python에서 미리 만들어서 전달하는 것이 더 간단할 수 있음
    # 여기서는 Python에서 카테고리 목록을 만들어서 전달한다고 가정하고, filter_buttons는 비워둠.
    # 실제로는 show_map_page 등에서 이 부분을 채워야 함.
    filter_buttons_html = ""
    unique_categories = sorted(list(set(marker.get('category', '기타') for marker in markers)))
    filter_buttons_html += '<button id="filter-all" class="filter-button active" onclick="filterMarkers(\'all\')">전체 보기</button>'
    for cat_name in unique_categories:
        safe_id = ''.join(c if c.isalnum() else '-' for c in cat_name).lower()
        filter_buttons_html += f' <button id="filter-{safe_id}" class="filter-button" onclick="filterMarkers(\'{cat_name}\')">{cat_name}</button>'


    # 마커 클러스터링 코드 (기존 코드 사용)
    clustering_js = """
        if (typeof markerClusterer !== 'undefined' && markers.length > 0) {
            new markerClusterer.MarkerClusterer({
                map: map,
                markers: markers, // JS 전역 배열 'markers' 사용
                algorithmOptions: { maxZoom: 15, radius: 60 } // algorithmOptions 사용
            });
        } else {
            console.log('MarkerClusterer not available or no markers to cluster.');
        }
    """
    
    # 내비게이션 JS (기존 코드 사용)
    directions_js = ""
    if navigation_mode and transport_mode and start_location and end_location :
        directions_js = f"""
        const directionsService = new google.maps.DirectionsService();
        const directionsRenderer = new google.maps.DirectionsRenderer({{
          panel: document.getElementById('directions-panel'),
          map: map
        }});
        
        function calculateAndDisplayRoute() {{
          const travelMode = '{transport_mode.upper()}'; // WALKING, TRANSIT, DRIVING
          directionsService.route({{
              origin: {{ lat: {start_location['lat']}, lng: {start_location['lng']} }},
              destination: {{ lat: {end_location['lat']}, lng: {end_location['lng']} }},
              travelMode: google.maps.TravelMode[travelMode],
            }})
            .then((response) => {{
              directionsRenderer.setDirections(response);
            }})
            .catch((e) => {{
              window.alert("Directions request failed due to " + e.status);
              console.error("Directions request failed: ", e);
            }});
        }}
        calculateAndDisplayRoute();
        """

    # HTML 템플릿
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Seoul Tourism Map</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            html, body {{ height: 100%; margin: 0; padding: 0; font-family: 'Noto Sans KR', Arial, sans-serif; }}
            #map {{ height: 100%; }}
            .map-controls {{
                position: absolute; top: 10px; left: 10px; z-index: 5;
                background-color: white; padding: 8px; border-radius: 4px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3); max-width: calc(100% - 20px);
                overflow-x: auto; white-space: nowrap;
            }}
            .filter-button {{
                margin: 3px; padding: 6px 10px; background-color: #fff;
                border: 1px solid #ccc; border-radius: 3px; cursor: pointer; font-size: 13px;
            }}
            .filter-button:hover {{ background-color: #f0f0f0; }}
            .filter-button.active {{ background-color: #4285F4; color: white; border-color: #4285F4; }}
            #legend {{
                position: absolute; bottom: 30px; right: 10px; z-index: 5;
                background-color: white; padding: 10px; border-radius: 4px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-size: 12px; max-height: 200px; overflow-y:auto;
            }}
            .legend-item {{ margin-bottom: 4px; display: flex; align-items: center; }}
            .custom-control-button {{ /* 현재 위치 버튼 스타일 */
                background-color: #fff; border: 0; border-radius: 2px; box-shadow: 0 1px 4px rgba(0,0,0,0.3);
                margin: 10px; padding: 8px 12px; font: 400 16px Roboto, Arial, sans-serif; cursor: pointer;
            }}
            #directions-panel {{ /* 내비게이션 안내 패널 */
                position: absolute; top: 70px; left: 10px; z-index: 5; width: 300px; max-height: 70%;
                overflow-y: auto; background-color: white; padding: 10px;
                border-radius: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-size: 13px;
            }}
             /* 경로 범례 스타일 */
            #route-legend {{
                font-family: 'Noto Sans KR', Arial, sans-serif; background-color: white;
                border: 1px solid #ccc; border-radius: 5px; bottom: {'180px' if legend_html else '30px'}; /* 범례 위치 조정 */
                box-shadow: 0 2px 6px rgba(0,0,0,.3); font-size: 12px; padding: 10px;
                position: absolute; right: 10px; z-index: 5; max-width: 180px;
                display: { 'block' if route_points else 'none' }; /* 경로 있을때만 표시 */
            }}
            .route-legend-item {{ margin-bottom: 5px; display: flex; align-items: center; }}
            .route-color-box {{ width: 20px; height: 10px; margin-right: 8px; display: inline-block; border: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="map-controls" id="category-filter-controls">
            <div style="margin-bottom: 5px; font-weight: bold; font-size:14px;">카테고리 필터</div>
            {filter_buttons_html}
        </div>
        
        {f'<div id="legend"><div style="font-weight: bold; margin-bottom: 8px;">범례</div>{legend_html}</div>' if legend_html else ''}

        <div id="route-legend">
            <div style="font-weight: bold; margin-bottom: 8px;">일별 경로</div>
            <div id="route-legend-items-container"></div>
        </div>
        
        { '<div id="directions-panel"></div>' if navigation_mode else '' }

        <script>
            var map;
            var markers = []; // 마커 객체 저장용
            var markerCategories = []; // 마커 카테고리 저장용
            var infoWindows = []; // 정보창 저장용
            var currentMarker = null; // 현재 활성화된 마커 (애니메이션 등)
            var dailyRouteLines = []; // 일별 경로 Polyline 객체 저장

            function closeAllInfoWindows() {{
                for (var i = 0; i < infoWindows.length; i++) {{ infoWindows[i].close(); }}
            }}
            
            function createRouteLegendDisplay(routeColorsArray, dailyRoutesData) {{
                var legendContainer = document.getElementById('route-legend-items-container');
                if (!legendContainer) return;
                legendContainer.innerHTML = ''; // 기존 범례 초기화
                var dayIdx = 0;
                var sortedDaysForLegend = Object.keys(dailyRoutesData).map(Number).sort((a,b) => a - b);

                for (var dayNum of sortedDaysForLegend) {{
                    if (dailyRoutesData[dayNum] && dailyRoutesData[dayNum].length > 0) {{
                        var color = routeColorsArray[dayIdx % routeColorsArray.length];
                        var legendItem = document.createElement('div');
                        legendItem.className = 'route-legend-item';
                        legendItem.innerHTML = 
                            '<span class="route-color-box" style="background-color: ' + color + ';"></span>' +
                            '<span>Day ' + dayNum + ' 경로</span>';
                        legendContainer.appendChild(legendItem);
                        dayIdx++;
                    }}
                }}
                document.getElementById('route-legend').style.display = dayIdx > 0 ? 'block' : 'none';
            }}

            {filter_js} // 필터 함수 정의

            function initMap() {{
                map = new new google.maps.Map(document.getElementById('map'), {{
                    center: {{ lat: {center_lat}, lng: {center_lng} }},
                    zoom: {zoom},
                    mapTypeControlOptions: {{ style: google.maps.MapTypeControlStyle.DROPDOWN_MENU }},
                    fullscreenControl: true,
                    streetViewControl: true,
                    zoomControl: true,
                    gestureHandling: 'greedy' // 모바일에서 부드러운 스크롤/줌
                }});

                const locationButton = document.createElement("button");
                locationButton.textContent = "📍 내 위치";
                locationButton.classList.add("custom-control-button");
                locationButton.addEventListener("click", () => {{
                    if (navigator.geolocation) {{
                        navigator.geolocation.getCurrentPosition(
                            (position) => {{
                                const pos = {{ lat: position.coords.latitude, lng: position.coords.longitude }};
                                map.setCenter(pos); map.setZoom(15);
                                new google.maps.Marker({{ position: pos, map: map, title: '현재 위치', icon: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png' }});
                                window.parent.postMessage({{type: 'current_location', lat: pos.lat, lng: pos.lng}}, '*');
                            }},
                            () => {{ alert("위치 정보를 가져오는 데 실패했습니다."); }}
                        );
                    }} else {{ alert("이 브라우저에서는 위치 정보 기능을 지원하지 않습니다."); }}
                }});
                map.controls[google.maps.ControlPosition.TOP_RIGHT].push(locationButton);

                // 마커 추가
                {markers_js}
                // 마커 클러스터링
                {clustering_js}
                // 경로 표시
                {route_js}
                // 내비게이션 (필요시)
                {directions_js}

                // 경로 범례 생성 (dailyRoutes 변수가 route_js에서 설정됨)
                if (typeof dailyRoutes !== 'undefined' && typeof routeColors !== 'undefined') {{
                    createRouteLegendDisplay(routeColors, dailyRoutes);
                }}
                
                map.addListener('click', function(event) {{
                    closeAllInfoWindows();
                    // if (currentMarker) currentMarker.setAnimation(null); // 이전 마커 애니메이션 중지
                    window.parent.postMessage({{type: 'map_click', lat: event.latLng.lat(), lng: event.latLng.lng()}}, '*');
                }});
                console.log("Google Map Initialized.");
            }}
        </script>
        <script async defer src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap&libraries=marker,places,directions&v=beta&language={language}"></script>
        </body>
    </html>
    """

    return html

    
def show_google_map(api_key, center_lat, center_lng, markers=None, zoom=13, height=600, language="한국어", 
                   navigation_mode=False, start_location=None, end_location=None, transport_mode=None):
    """Google Maps 컴포넌트 표시 - 내비게이션 기능 추가"""
    # 언어 코드 변환
    lang_code = LANGUAGE_CODES.get(language, "ko")
    
    try:
        # 디버깅 정보
        if navigation_mode:
            st.info(f"내비게이션 모드: {transport_mode}, 출발: ({start_location['lat']:.4f}, {start_location['lng']:.4f}), 도착: ({end_location['lat']:.4f}, {end_location['lng']:.4f})")
        
        # HTML 생성
        map_html = create_google_maps_html(
            api_key=api_key,
            center_lat=center_lat,
            center_lng=center_lng,
            markers=markers,
            zoom=zoom,
            language=lang_code,
            navigation_mode=navigation_mode,
            start_location=start_location,
            end_location=end_location,
            transport_mode=transport_mode
        )
        
        # HTML 컴포넌트로 표시
        st.components.v1.html(map_html, height=height, scrolling=False)
        return True
        
    except Exception as e:
        st.error(f"지도 렌더링 오류: {str(e)}")
        st.error("지도 로딩에 실패했습니다. 아래 대체 옵션을 사용해보세요.")
        
        # 대체 지도 옵션: folium 사용
        try:
            import folium
            from streamlit_folium import folium_static
            
            st.info("대체 지도를 로드합니다...")
            m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom)
            
            # 마커 추가
            if markers:
                for marker in markers:
                    folium.Marker(
                        [marker['lat'], marker['lng']], 
                        popup=marker.get('title', ''),
                        tooltip=marker.get('title', ''),
                        icon=folium.Icon(color=marker.get('color', 'red'))
                    ).add_to(m)
            
            # folium 지도 표시
            folium_static(m)
            return True
            
        except Exception as e2:
            st.error(f"대체 지도 로딩도 실패했습니다: {str(e2)}")
            
            # 비상용 텍스트 지도 표시
            st.warning("텍스트 기반 위치 정보:")
            if markers:
                for i, marker in enumerate(markers[:10]):  # 상위 10개만
                    st.text(f"{i+1}. {marker.get('title', '무제')} - 좌표: ({marker['lat']}, {marker['lng']})")
            return False

def display_visits(visits, current_lang_texts):
    """방문 기록 표시 함수"""
    if not visits:
        st.info(current_lang_texts["no_visit_history"])
        return
    
    for i, visit in enumerate(visits):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{visit['place_name']}**")
                st.caption(f"{current_lang_texts['visit_date']}: {visit['date']}")
            
            with col2:
                st.markdown(f"+{visit.get('xp_gained', 0)} XP")
            
            with col3:
                # 리뷰 또는 평점이 있는 경우 표시
                if 'rating' in visit and visit['rating']:
                    st.markdown("⭐" * int(visit['rating']))
                else:
                    # texts 딕셔너리에서 평가 버튼 텍스트 가져오기
                    if st.button(current_lang_texts["rate_button"], key=f"rate_{i}"):
                        # 평가 기능 구현 (실제로는 팝업이나 별도 UI가 필요)
                        st.session_state.rating_place = visit['place_name']
                        st.session_state.rating_index = i

#################################################
# 개선된 관광 코스 추천 함수
#################################################

def recommend_courses(data, travel_styles, num_days, include_children=False):
    """
    사용자 취향과 일정에 따른 관광 코스 추천 기능
    """
    # 언어 설정에 따른 텍스트 가져오기
    current_lang_texts = st.session_state.texts[st.session_state.language]

    if not data:
        st.warning(current_lang_texts["no_tourist_data"])
        # 기본 코스 반환
        if any(style in travel_styles for style in ["역사/문화", "History/Culture", "历史/文化型"]):
            course_type = current_lang_texts["course_history_culture"]
        elif any(style in travel_styles for style in ["쇼핑", "Shopping", "购物型"]) and any(style in travel_styles for style in ["맛집", "Food", "美食型"]):
            course_type = current_lang_texts["course_shopping_food"]
        elif any(style in travel_styles for style in ["쇼핑", "Shopping", "购物型"]):
            course_type = current_lang_texts["course_shopping"]
        elif any(style in travel_styles for style in ["맛집", "Food", "美食型"]):
            course_type = current_lang_texts["course_food"]
        elif any(style in travel_styles for style in ["자연", "Nature", "自然型"]):
            course_type = current_lang_texts["course_nature"]
        elif any(style in travel_styles for style in ["활동적인", "Active", "活动型"]):
            course_type = current_lang_texts["course_active"]
        else:
            course_type = current_lang_texts["course_healing"]
        return RECOMMENDATION_COURSES.get(course_type, []), course_type, []

    # 장소별 점수 계산
    scored_places = []

    for place in data:
        # 기본 점수는 중요도
        score = place.get('importance', 1.0)

        # 여행 스타일에 따른 가중치 적용
        style_match = False
        for style in travel_styles:
            if style in STYLE_CATEGORY_WEIGHTS:
                category_weights = STYLE_CATEGORY_WEIGHTS[style]
                if place['category'] in category_weights:
                    score *= category_weights[place['category']]
                    style_match = True

        # 여행 스타일과 맞지 않는 장소는 점수 감소
        if not style_match:
            score *= 0.5

        # 체육시설 점수 조정: 활동적인 스타일이 아니면 점수 대폭 감소
        if place['category'] == "체육시설" and not any(style in travel_styles for style in ["활동적인", "Active", "活动型"]):
            score *= 0.3  # 더 강력하게 감소

        # 아이 동반인 경우 가족 친화적인 장소 선호 (미술관/전시)
        if include_children and place['category'] == "미술관/전시":
            score *= 1.2

        # 최종 점수 저장
        scored_place = place.copy()
        scored_place['score'] = score
        scored_places.append(scored_place)

    # 점수별 정렬
    scored_places.sort(key=lambda x: x['score'], reverse=True)

    # 일수에 따른 장소 선택
    # 하루당 3곳 방문 가정 (아침, 점심, 저녁)
    places_per_day = 3
    total_places = num_days * places_per_day

    # 카테고리 다양성 확보: 같은 카테고리 장소가 너무 많이 선택되지 않도록 함
    category_counts = {}
    for place in scored_places[:total_places * 2]:  # 상위 후보에서만 카운트
        category = place['category']
        category_counts[category] = category_counts.get(category, 0) + 1

    # 특정 카테고리가 너무 많으면 일부 제외
    MAX_PLACES_PER_CATEGORY = max(2, total_places // 3)  # 최소 2개, 또는 총 장소의 1/3

    # 체육시설은 활동적인 스타일이 아니면 더 적게 포함
    if not any(style in travel_styles for style in ["활동적인", "Active", "活动型"]):
        MAX_PLACES_PER_CATEGORY_GYM = 1  # 최대 1개로 제한
    else:
        MAX_PLACES_PER_CATEGORY_GYM = MAX_PLACES_PER_CATEGORY

    filtered_places = []
    category_added = {}

    # 고득점 순으로 다양한 카테고리 장소 선택
    for place in scored_places:
        category = place['category']
        max_for_category = MAX_PLACES_PER_CATEGORY_GYM if category == "체육시설" else MAX_PLACES_PER_CATEGORY

        if category_added.get(category, 0) < max_for_category:
            filtered_places.append(place)
            category_added[category] = category_added.get(category, 0) + 1

        # 충분한 장소를 모았으면 중단
        if len(filtered_places) >= total_places * 2:
            break

    # 필터링된 장소가 충분하지 않으면 원래 목록 사용
    if len(filtered_places) < total_places:
        filtered_places = scored_places[:total_places * 2]

    # 동선 최적화: 그리디 알고리즘
    # 서울시청을 시작점으로 설정 (모든 날 아침에 숙소/시청에서 출발한다고 가정)
    seoul_city_hall = {"lat": 37.5665, "lng": 126.9780}

    daily_courses = []

    for day in range(num_days):
        daily_course = []
        current_position = seoul_city_hall

        # 이미 선택된 장소는 제외
        available_places = [p for p in filtered_places if not any(p['title'] == dp['title'] for dc in daily_courses for dp in dc)]

        if not available_places:
            break

        # 각 시간대별 최적 장소 선택
        for time_slot in range(places_per_day):
            if not available_places:
                break

            # 거리 가중치가 적용된 점수 계산
            for place in available_places:
                distance = geodesic(
                    (current_position['lat'], current_position['lng']),
                    (place['lat'], place['lng'])
                ).kilometers

                # 거리에 따른 점수 감소 (너무 먼 곳은 피함)
                distance_factor = max(0.5, 1 - (distance / 10))  # 10km 이상이면 점수 절반으로
                place['adjusted_score'] = place.get('score', 1.0) * distance_factor

            # 조정된 점수로 재정렬
            available_places.sort(key=lambda x: x.get('adjusted_score', 0), reverse=True)

            # 최고 점수 장소 선택
            next_place = available_places[0]
            daily_course.append(next_place)

            # 선택된 장소 제거
            available_places.remove(next_place)

            # 현재 위치 업데이트
            current_position = {"lat": next_place['lat'], "lng": next_place['lng']}

        daily_courses.append(daily_course)

    # 코스 이름 결정
    if any(style in travel_styles for style in ["역사/문화", "History/Culture", "历史/文化型"]):
        course_type = current_lang_texts["course_history_culture"]
    elif any(style in travel_styles for style in ["쇼핑", "Shopping", "购物型"]) and any(style in travel_styles for style in ["맛집", "Food", "美食型"]):
        course_type = current_lang_texts["course_shopping_food"]
    elif any(style in travel_styles for style in ["쇼핑", "Shopping", "购物型"]):
        course_type = current_lang_texts["course_shopping"]
    elif any(style in travel_styles for style in ["맛집", "Food", "美食型"]):
        course_type = current_lang_texts["course_food"]
    elif any(style in travel_styles for style in ["자연", "Nature", "自然型"]):
        course_type = current_lang_texts["course_nature"]
    elif any(style in travel_styles for style in ["활동적인", "Active", "活动型"]):
        course_type = current_lang_texts["course_active"]
    else:
        course_type = current_lang_texts["course_healing"]

    # 추천 장소 이름 목록 생성
    recommended_places = []
    for day_course in daily_courses:
        for place in day_course:
            recommended_places.append(place['title'])

    return recommended_places, course_type, daily_courses

#################################################
# 페이지 함수
#################################################

def show_login_page():
    """로그인 페이지 표시"""
    # 언어 설정 초기화
    if 'language' not in st.session_state:
        st.session_state.language = "한국어"
    
    # 언어별 텍스트 사전
    texts = {
        "한국어": {
                "app_title": "서울 관광앱",
                "login_tab": "로그인",
                "join_tab": "회원가입",
                "login_title": "로그인",
                "join_title": "회원가입",
                "id_label": "아이디",
                "pw_label": "비밀번호",
                "pw_confirm_label": "비밀번호 확인",
                "remember_id": "아이디 저장",
                "login_button": "로그인",
                "join_button": "가입하기",
                "login_success": "🎉 로그인 성공!",
                "login_failed": "❌ 아이디 또는 비밀번호가 올바르지 않습니다.",
                "input_required": "아이디와 비밀번호를 입력해주세요.",
                "pw_mismatch": "비밀번호와 비밀번호 확인이 일치하지 않습니다.",
                "join_success": "✅ 회원가입 완료!",
                "user_exists": "⚠️ 이미 존재하는 아이디입니다.",
                "new_id": "새 아이디",
                "new_pw": "새 비밀번호",
                "welcome_msg": "👋 {username}님, 환영합니다!",
                "select_menu": "원하는 메뉴를 선택하세요",
                "map_title": "🗺️ 서울 관광 장소 지도",
                "map_description": "서울의 주요 관광 명소를 지도에서 확인하고 길을 찾으세요.",
                "view_map_button": "관광 지도 보기",
                "course_title": "🗓️ 서울 여행 코스 추천",
                "course_description": "AI가 당신의 취향에 맞는 최적의 여행 코스를 추천해 드립니다.",
                "create_course_button": "여행 코스 만들기",
                "history_title": "📝 나의 여행 기록",
                "history_description": "방문했던 장소와 획득한 경험치를 확인하세요.",
                "view_history_button": "여행 기록 보기",
                "logout_button": "🔓 로그아웃",
                "map_back_to_menu": "← 메뉴로 돌아가기",
                "map_api_key_not_set": "Google Maps API 키가 설정되지 않았습니다.",
                "map_enter_api_key": "Google Maps API 키를 입력하세요",
                "map_api_key_set_success": "API 키가 설정되었습니다. 지도를 로드합니다.",
                "map_api_key_required_info": "Google Maps를 사용하려면 API 키가 필요합니다.",
                "language": "🌏 언어",
                "map_loading_data": "서울 관광 데이터를 로드하는 중...",
                "map_load_complete": "총 {num_markers}개의 관광지 로드 완료!",
                "map_load_failed": "관광지 데이터를 로드할 수 없습니다.",
                "map_my_location": "내 위치",
                "map_current_location": "현재 위치",
                "map_current_location_category": "현재 위치",
                "map_markers_displayed": "지도에 {num_markers}개의 장소를 표시했습니다.",
                "map_place_info": "장소 정보",
                "map_search_place": "장소 검색",
                "map_search_results": "검색 결과",
                "map_find_directions": "길찾기",
                "map_visit_history": "방문기록",
                "map_visited": "방문",
                "map_xp_earned": "획득",
                "map_already_visited_today": "이미 오늘 방문한 장소입니다.",
                "map_no_search_results": "'{search_term}'에 대한 검색 결과가 없습니다.",
                "map_places_by_category": "카테고리별 장소",
                "map_category": "분류",
                "map_other_category": "기타",
                "map_no_destination_info": "목적지 정보가 없습니다.",
                "map_back_to_map": "지도로 돌아가기",
                "map_navigation_to": "까지 내비게이션",
                "map_select_transport": "이동 수단 선택",
                "map_walking": "도보",
                "map_estimated_time": "예상 소요 시간",
                "map_minute": "분",
                "map_select_walk": "도보 선택",
                "map_transit": "대중교통",
                "map_select_transit": "대중교통 선택",
                "map_driving": "자동차",
                "map_select_drive": "자동차 선택",
                "map_route": "경로",
                "map_distance": "거리",
                "map_transport": "이동 수단",
                "map_route_guide": "경로 안내",
                "map_departure": "현재 위치에서 출발합니다",
                "map_straight_and_turn_right": "{distance:.0f}m 직진 후 오른쪽으로 턴",
                "map_straight_and_turn_left": "{distance:.0f}m 직진 후 왼쪽으로 턴",
                "map_arrive_at_destination": "{distance:.0f}m 직진 후 목적지 도착",
                "map_other_transport_modes": "다른 이동 수단",
                "map_end_navigation": "내비게이션 종료",
                "course_ai_recommendation_title": "AI 추천 코스",
                "course_ai_recommendation_description": "AI 추천 코스 설명",
                "history_page_title": "나의 관광 이력",
                "level_text": "레벨 {level}",
                "total_xp_text": "총 경험치: {xp} XP",
                "next_level_xp_text": "다음 레벨까지 {remaining_xp} XP",
                "total_visits_metric": "총 방문 횟수",
                "visited_places_metric": "방문한 장소 수",
                "earned_xp_metric": "획득한 경험치",
                "visit_history_tab": "📝 방문 기록",
                "all_tab": "전체",
                "recent_tab": "최근순",
                "xp_tab": "경험치순",
                "visit_map_title": "🗺️ 방문 지도",
                "no_visit_history": "아직 방문 기록이 없습니다. 지도에서 장소를 방문하면 여기에 기록됩니다.",
                "generate_sample_data": "예시 데이터 생성",
                "sample_data_success": "예시 데이터가 생성되었습니다! +{total_xp} XP 획득!",
                "visit_date": "방문일",
                "visits_count": "{count}회",
                "places_count": "{count}곳",
                "xp_points": "{xp} XP",
                "no_map_visits": "지도에 표시할 방문 기록이 없습니다.",
                "travel_info_input": "여행 정보 입력",
                "travel_style_active": "활동적인",
                "travel_style_relaxation": "휴양",
                "travel_style_food": "맛집",
                "travel_style_shopping": "쇼핑",
                "travel_style_history_culture": "역사/문화",
                "travel_style_nature": "자연",
                "generate_course_button": "코스 생성하기",
                "select_travel_style_warning": "최소 하나 이상의 여행 스타일을 선택해주세요.",
                "generating_course_spinner": "최적의 관광 코스를 생성 중입니다...",
                "course_generation_complete": "코스 생성 완료!",
                "recommended_course_title": "추천 코스",
                "insufficient_recommendations": "추천 장소가 부족합니다.",
                "morning_time_slot": "오전 (09:00-12:00)",
                "afternoon_time_slot": "오후 (13:00-16:00)",
                "evening_time_slot": "저녁 (16:00-19:00)",
                "category_label": "분류: {category}",
                "location_label": "위치: {address}",
                "default_spots": ["경복궁", "남산서울타워", "명동"],
                "tourist_spot": "관광지",
                "course_map_title": "🗺️ 코스 지도",
                "map_display_error": "코스 장소의 좌표 정보가 없어 지도에 표시할 수 없습니다.",
                "save_course_button": "이 코스 저장하기",
                "course_saved_success": "코스가 저장되었습니다!",
                "travel_date_start": "여행 시작일",
                "travel_date_end": "여행 종료일",
                "travel_people_count": "여행 인원",
                "travel_with_children": "아이 동반",
                "travel_style": "여행 스타일",
                "travel_days_total": "총 {days}일 일정",
                "course_history_culture": "서울 역사/문화 탐방 코스",
                "course_shopping_food": "서울 쇼핑과 미식 코스",
                "course_shopping": "서울 쇼핑 중심 코스", 
                "course_food": "서울 미식 여행 코스",
                "course_nature": "서울의 자연 코스",
                "course_active": "액티브 서울 코스",
                "course_healing": "서울 힐링 여행 코스",
            },
            "중국어": {
                "app_title": "首尔旅游应用",
                "login_tab": "登录",
                "join_tab": "注册",
                "login_title": "登录",
                "join_title": "注册",
                "id_label": "用户名",
                "pw_label": "密码",
                "pw_confirm_label": "确认密码",
                "remember_id": "记住用户名",
                "login_button": "登录",
                "join_button": "注册",
                "login_success": "🎉 登录成功！",
                "login_failed": "❌ 用户名或密码不正确。",
                "input_required": "请输入用户名和密码。",
                "pw_mismatch": "密码和确认密码不匹配。",
                "join_success": "✅ 注册完成！",
                "user_exists": "⚠️ 此用户名已存在。",
                "new_id": "新用户名",
                "new_pw": "新密码",
                "welcome_msg": "👋 欢迎，{username}！",
                "select_menu": "请选择菜单",
                "map_title": "🗺️ 首尔旅游地图",
                "map_description": "在地图上查看首尔的主要旅游景点并找到路线。",
                "view_map_button": "查看旅游地图",
                "course_title": "🗓️ 首尔旅游路线推荐",
                "course_description": "AI将根据您的喜好推荐最佳旅游路线。",
                "create_course_button": "创建旅游路线",
                "history_title": "📝 我的旅行记录",
                "history_description": "查看您访问过的地点和获得的经验值。",
                "view_history_button": "查看旅行记录",
                "logout_button": "🔓 登出",
                "map_back_to_menu": "← 返回菜单",
                "map_api_key_not_set": "Google Maps API密钥未设置。",
                "map_enter_api_key": "请输入Google Maps API密钥",
                "map_api_key_set_success": "API密钥已设置。正在加载地图。",
                "map_api_key_required_info": "使用Google Maps需要API密钥。",
                "language": "🌏 语言",
                "map_loading_data": "正在加载首尔旅游数据...",
                "map_load_complete": "已加载{num_markers}个旅游景点！",
                "map_load_failed": "无法加载旅游景点数据。",
                "map_my_location": "我的位置",
                "map_current_location": "当前位置",
                "map_current_location_category": "当前位置",
                "map_markers_displayed": "地图上显示了{num_markers}个地点。",
                "map_place_info": "地点信息",
                "map_search_place": "搜索地点",
                "map_search_results": "搜索结果",
                "map_find_directions": "查找路线",
                "map_visit_history": "访问记录",
                "map_visited": "已访问",
                "map_xp_earned": "获得",
                "map_already_visited_today": "今天已经访问过这个地点。",
                "map_no_search_results": "没有关于'{search_term}'的搜索结果。",
                "map_places_by_category": "按类别查看地点",
                "map_category": "类别",
                "map_other_category": "其他",
                "map_no_destination_info": "没有目的地信息。",
                "map_back_to_map": "返回地图",
                "map_navigation_to": "导航至",
                "map_select_transport": "选择交通方式",
                "map_walking": "步行",
                "map_estimated_time": "预计时间",
                "map_minute": "分钟",
                "map_select_walk": "选择步行",
                "map_transit": "公共交通",
                "map_select_transit": "选择公共交通",
                "map_driving": "驾车",
                "map_select_drive": "选择驾车",
                "map_route": "路线",
                "map_distance": "距离",
                "map_transport": "交通方式",
                "map_route_guide": "路线指南",
                "map_departure": "从当前位置出发",
                "map_straight_and_turn_right": "直行{distance:.0f}米后右转",
                "map_straight_and_turn_left": "直行{distance:.0f}米后左转",
                "map_arrive_at_destination": "直行{distance:.0f}米后到达目的地",
                "map_other_transport_modes": "其他交通方式",
                "map_end_navigation": "结束导航",
                "course_ai_recommendation_title": "AI推荐路线",
                "course_ai_recommendation_description": "AI推荐路线说明",
                "history_page_title": "我的旅游历史",
                "level_text": "等级 {level}",
                "total_xp_text": "总经验值: {xp} XP",
                "next_level_xp_text": "距离下一级还需 {remaining_xp} XP",
                "total_visits_metric": "总访问次数",
                "visited_places_metric": "已访问地点数",
                "earned_xp_metric": "获得的经验值",
                "visit_history_tab": "📝 访问记录",
                "all_tab": "全部",
                "recent_tab": "最近",
                "xp_tab": "按经验值",
                "visit_map_title": "🗺️ 访问地图",
                "no_visit_history": "尚无访问记录。在地图上访问地点后将在此处记录。",
                "generate_sample_data": "生成示例数据",
                "sample_data_success": "示例数据已生成！获得 +{total_xp} XP！",
                "visit_date": "访问日期",
                "visits_count": "{count}次",
                "places_count": "{count}处",
                "xp_points": "{xp} XP",
                "no_map_visits": "没有可显示在地图上的访问记录。",
                "travel_info_input": "旅行信息输入",
                "travel_style_active": "活动型",
                "travel_style_relaxation": "休闲型",
                "travel_style_food": "美食型",
                "travel_style_shopping": "购物型",
                "travel_style_history_culture": "历史/文化型",
                "travel_style_nature": "自然型",
                "generate_course_button": "生成路线",
                "select_travel_style_warning": "请至少选择一种旅行风格。",
                "generating_course_spinner": "正在生成最佳旅游路线...",
                "course_generation_complete": "路线生成完成！",
                "recommended_course_title": "推荐路线",
                "insufficient_recommendations": "推荐地点不足。",
                "morning_time_slot": "上午 (09:00-12:00)",
                "afternoon_time_slot": "下午 (13:00-16:00)",
                "evening_time_slot": "傍晚 (16:00-19:00)",
                "category_label": "类别: {category}",
                "location_label": "位置: {address}",
                "default_spots": ["景福宫", "首尔南山塔", "明洞"],
                "tourist_spot": "景点",
                "course_map_title": "🗺️ 路线地图",
                "map_display_error": "由于路线地点缺少坐标信息，无法在地图上显示。",
                "save_course_button": "保存此路线",
                "course_saved_success": "路线已保存！",
                "travel_info_input": "旅行信息输入",
                "travel_date_start": "旅行开始日期",
                "travel_date_end": "旅行结束日期",
                "travel_people_count": "旅行人数",
                "travel_with_children": "携带儿童",
                "travel_style": "旅行风格",
                "travel_days_total": "共{days}天行程",
                "course_history_culture": "首尔历史/文化探索路线",
                "course_shopping_food": "首尔购物与美食路线",
                "course_shopping": "首尔购物中心路线",
                "course_food": "首尔美食之旅路线",
                "course_nature": "首尔自然风光路线",
                "course_active": "活力首尔路线",
                "course_healing": "首尔治愈之旅路线"
            },
            "영어": {
                "app_title": "Seoul Tourist App",
                "login_tab": "Login",
                "join_tab": "Sign Up",
                "login_title": "Login",
                "join_title": "Sign Up",
                "id_label": "Username",
                "pw_label": "Password",
                "pw_confirm_label": "Confirm Password",
                "remember_id": "Remember Username",
                "login_button": "Login",
                "join_button": "Sign Up",
                "login_success": "🎉 Login Successful!",
                "login_failed": "❌ Username or password is incorrect.",
                "input_required": "Please enter your username and password.",
                "pw_mismatch": "Password and confirm password do not match.",
                "join_success": "✅ Registration Complete!",
                "user_exists": "⚠️ This username already exists.",
                "new_id": "New Username",
                "new_pw": "New Password",
                "welcome_msg": "👋 Welcome, {username}!",
                "select_menu": "Please select a menu",
                "map_title": "🗺️ Seoul Tourist Map",
                "map_description": "View Seoul's major tourist attractions on the map and find directions.",
                "view_map_button": "View Tourist Map",
                "course_title": "🗓️ Seoul Travel Course Recommendations",
                "course_description": "AI will recommend the best travel course based on your preferences.",
                "create_course_button": "Create Travel Course",
                "history_title": "📝 My Travel Records",
                "history_description": "Check the places you've visited and the experience points you've earned.",
                "view_history_button": "View Travel Records",
                "logout_button": "🔓 Logout",
                "map_back_to_menu": "← Back to Menu",
                "map_api_key_not_set": "Google Maps API key is not set.",
                "map_enter_api_key": "Please enter Google Maps API key",
                "map_api_key_set_success": "API key has been set. Loading map.",
                "map_api_key_required_info": "API key is required to use Google Maps.",
                "language": "🌏 Language",
                "map_loading_data": "Loading Seoul tourist data...",
                "map_load_complete": "Loaded {num_markers} tourist attractions!",
                "map_load_failed": "Unable to load tourist attraction data.",
                "map_my_location": "My Location",
                "map_current_location": "Current Location",
                "map_current_location_category": "Current Location",
                "map_markers_displayed": "Displayed {num_markers} places on the map.",
                "map_place_info": "Place Information",
                "map_search_place": "Search Place",
                "map_search_results": "Search Results",
                "map_find_directions": "Find Directions",
                "map_visit_history": "Visit History",
                "map_visited": "Visited",
                "map_xp_earned": "Earned",
                "map_already_visited_today": "You've already visited this place today.",
                "map_no_search_results": "No search results for '{search_term}'.",
                "map_places_by_category": "Places by Category",
                "map_category": "Category",
                "map_other_category": "Other",
                "map_no_destination_info": "No destination information.",
                "map_back_to_map": "Back to Map",
                "map_navigation_to": "Navigation to",
                "map_select_transport": "Select Transport Mode",
                "map_walking": "Walking",
                "map_estimated_time": "Estimated Time",
                "map_minute": "minute(s)",
                "map_select_walk": "Select Walking",
                "map_transit": "Public Transit",
                "map_select_transit": "Select Public Transit",
                "map_driving": "Driving",
                "map_select_drive": "Select Driving",
                "map_route": "Route",
                "map_distance": "Distance",
                "map_transport": "Transport Mode",
                "map_route_guide": "Route Guide",
                "map_departure": "Departing from current location",
                "map_straight_and_turn_right": "Go straight for {distance:.0f}m then turn right",
                "map_straight_and_turn_left": "Go straight for {distance:.0f}m then turn left",
                "map_arrive_at_destination": "Go straight for {distance:.0f}m then arrive at destination",
                "map_other_transport_modes": "Other Transport Modes",
                "map_end_navigation": "End Navigation",
                "course_ai_recommendation_title": "AI Recommended Course",
                "course_ai_recommendation_description": "AI Recommended Course Description",
                "history_page_title": "My Tourism History",
                "level_text": "Level {level}",
                "total_xp_text": "Total XP: {xp} XP",
                "next_level_xp_text": "Next level in {remaining_xp} XP",
                "total_visits_metric": "Total Visits",
                "visited_places_metric": "Places Visited",
                "earned_xp_metric": "XP Earned",
                "visit_history_tab": "📝 Visit History",
                "all_tab": "All",
                "recent_tab": "Recent",
                "xp_tab": "By XP",
                "visit_map_title": "🗺️ Visit Map",
                "no_visit_history": "No visit history yet. Visit places on the map to record them here.",
                "generate_sample_data": "Generate Sample Data",
                "sample_data_success": "Sample data generated! +{total_xp} XP earned!",
                "visit_date": "Visit Date",
                "visits_count": "{count} visit(s)",
                "places_count": "{count} place(s)",
                "xp_points": "{xp} XP",
                "no_map_visits": "No visit records to display on the map.",
                "travel_info_input": "Travel Information Input",
                "travel_style_active": "Active",
                "travel_style_relaxation": "Relaxation",
                "travel_style_food": "Food",
                "travel_style_shopping": "Shopping",
                "travel_style_history_culture": "History/Culture",
                "travel_style_nature": "Nature",
                "generate_course_button": "Generate Course",
                "select_travel_style_warning": "Please select at least one travel style.",
                "generating_course_spinner": "Generating optimal tourist course...",
                "course_generation_complete": "Course generation complete!",
                "recommended_course_title": "Recommended Course",
                "insufficient_recommendations": "Insufficient recommended places.",
                "morning_time_slot": "Morning (09:00-12:00)",
                "afternoon_time_slot": "Afternoon (13:00-16:00)",
                "evening_time_slot": "Evening (16:00-19:00)",
                "category_label": "Category: {category}",
                "location_label": "Location: {address}",
                "default_spots": ["Gyeongbokgung Palace", "N Seoul Tower", "Myeongdong"],
                "tourist_spot": "Tourist Spot",
                "course_map_title": "🗺️ Course Map",
                "map_display_error": "Cannot display on map due to missing coordinate information for course locations.",
                "save_course_button": "Save This Course",
                "course_saved_success": "Course has been saved!",
                "travel_date_start": "Travel Start Date",
                "travel_date_end": "Travel End Date",
                "travel_people_count": "Number of Travelers",
                "travel_with_children": "Traveling with Children",
                "travel_style": "Travel Style",
                "travel_days_total": "Total {days} day itinerary",
                "course_history_culture": "Seoul History & Culture Exploration Course",
                "course_shopping_food": "Seoul Shopping & Gastronomy Course",
                "course_shopping": "Seoul Shopping-Focused Course",
                "course_food": "Seoul Culinary Tour Course",
                "course_nature": "Seoul Nature Course",
                "course_active": "Active Seoul Course",
                "course_healing": "Seoul Healing Travel Course"
            }
        }
    
    
    # 현재 선택된 언어에 따른 텍스트 가져오기
    current_lang_texts = texts[st.session_state.language]

    # 메인 이미지
    pic1, pic2, pic3, pic4, pic5 = st.columns([1, 1, 1, 1, 1])

    with pic3:
        main_image_path = Path("asset") / "SeoulTripView.png"
        if main_image_path.exists():
            st.image(main_image_path, use_container_width=True)
        else:
            st.info("이미지를 찾을 수 없습니다: asset/SeoulTripView.png")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        page_header(current_lang_texts["app_title"])

        # 언어 선택 드롭다운
        language_options = {
            "🇰🇷 한국어": "한국어",
            "🇺🇸 English": "영어",
            "🇨🇳 中文": "중국어"
        }
        selected_lang = st.selectbox(
            "Language / 언어 / 语言",
            options=list(language_options.keys()),
            index=list(language_options.values()).index(st.session_state.language),
            key="language_selector"
        )
        
        # 언어 변경 시 session_state 업데이트
        if language_options[selected_lang] != st.session_state.language:
            st.session_state.language = language_options[selected_lang]
            st.rerun()  # 언어 변경 후 페이지 새로고침
        
        # 로그인/회원가입 탭
        tab1, tab2 = st.tabs([current_lang_texts["login_tab"], current_lang_texts["join_tab"]])
        
        with tab1:
            st.markdown(f"### {current_lang_texts['login_title']}")
            username = st.text_input(current_lang_texts["id_label"], key="login_username")
            password = st.text_input(current_lang_texts["pw_label"], type="password", key="login_password")
            
            col1, col2 = st.columns([1,1])
            with col1:
                remember = st.checkbox(current_lang_texts["remember_id"])
            with col2:
                st.markdown("")  # 빈 공간
            
            if st.button(current_lang_texts["login_button"], use_container_width=True):
                if authenticate_user(username, password):
                    st.success(current_lang_texts["login_success"])
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    change_page("menu")
                    st.rerun()
                else:
                    st.error(current_lang_texts["login_failed"])
        
        with tab2:
            st.markdown(f"### {current_lang_texts['join_title']}")
            new_user = st.text_input(current_lang_texts["new_id"], key="register_username")
            new_pw = st.text_input(current_lang_texts["new_pw"], type="password", key="register_password")
            new_pw_confirm = st.text_input(current_lang_texts["pw_confirm_label"], type="password", key="register_password_confirm")
            
            if st.button(current_lang_texts["join_button"], use_container_width=True):
                if not new_user or not new_pw:
                    st.error(current_lang_texts["input_required"])
                elif new_pw != new_pw_confirm:
                    st.error(current_lang_texts["pw_mismatch"])
                elif register_user(new_user, new_pw):
                    st.success(current_lang_texts["join_success"])
                    st.session_state.logged_in = True
                    st.session_state.username = new_user
                    change_page("menu")
                    st.rerun()
                else:
                    st.warning(current_lang_texts["user_exists"])

def show_menu_page():
    ##############################
    # 언어별 페이지 설정
    ##############################
    
    """메인 메뉴 페이지 표시"""
    # 언어 설정에 따른 텍스트 가져오기
    current_lang_texts = st.session_state.texts[st.session_state.language]
    
    page_header(current_lang_texts["app_title"])
    st.markdown(f"###  {current_lang_texts['welcome_msg'].format(username=st.session_state.username)}")
    
    # 사용자 레벨 및 경험치 정보 표시
    lang = "ko"
    if st.session_state.language == "영어":
        lang = "en"
    elif st.session_state.language == "중국어":
        lang = "zh"
    display_user_level_info(lang)
    
    st.markdown("---")
    st.markdown(f"### {current_lang_texts['select_menu']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="card">
            <h3>{current_lang_texts['map_title']}</h3>
            <p>{current_lang_texts['map_description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(current_lang_texts['view_map_button'], key="map_button", use_container_width=True):
            change_page("map")
            st.rerun()
    
    with col2:
        st.markdown(f"""
        <div class="card">
            <h3>{current_lang_texts['course_title']}</h3>
            <p>{current_lang_texts['course_description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(current_lang_texts['create_course_button'], key="course_button", use_container_width=True):
            change_page("course")
            st.rerun()
    
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="card">
            <h3>{current_lang_texts['history_title']}</h3>
            <p>{current_lang_texts['history_description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(current_lang_texts['view_history_button'], key="history_button", use_container_width=True):
            change_page("history")
            st.rerun()
            
    # 로그아웃 버튼
    st.markdown("---")
    if st.button(current_lang_texts['logout_button'], key="logout_button"):
        logout_user()
        st.rerun()


    

def show_map_page():
    """지도 페이지 표시 - 내비게이션 기능 개선"""
    current_lang_texts = st.session_state.texts[st.session_state.language]
    page_header(current_lang_texts.get("map_title", "서울 관광 장소 지도"))

    # 뒤로가기 버튼
    if st.button(current_lang_texts.get("map_back_to_menu")):
        change_page("menu")
        st.rerun()

    # API 키 확인
    api_key = st.session_state.google_maps_api_key
    if not api_key or api_key == "YOUR_GOOGLE_MAPS_API_KEY":
        st.error(current_lang_texts.get("map_api_key_not_set"))
        api_key = st.text_input(current_lang_texts.get("map_enter_api_key"), type="password")
        if api_key:
            st.session_state.google_maps_api_key = api_key
            #st.success(current_lang_texts.get("map_api_key_set_success"))
            st.rerun()
        else:
            st.info(current_lang_texts.get("map_api_key_required_info"))
            return

    # 언어 선택
    col1, col2 = st.columns([4, 1])
    with col2:
        selected_language = st.selectbox(
            current_lang_texts.get("language"),
            ["🇰🇷 한국어", "🇺🇸 English", "🇨🇳 中文"],
            index=0 if st.session_state.language == "한국어" else 1 if st.session_state.language == "영어" else 2
        )
        language_map = {
            "🇰🇷 한국어": "한국어",
            "🇺🇸 English": "영어",
            "🇨🇳 中文": "중국어"
        }
        st.session_state.language = language_map[selected_language]

    # 사용자 위치 가져오기
    user_location = get_location_position()

    # 자동으로 Excel 파일 로드 (아직 로드되지 않은 경우)
    if not st.session_state.markers_loaded or not st.session_state.all_markers:
        with st.spinner(current_lang_texts.get("map_loading_data")):
            all_markers = load_excel_files(st.session_state.language)
            if all_markers:
                st.session_state.all_markers = all_markers
                st.session_state.markers_loaded = True
                st.session_state.tourism_data = all_markers  # 코스 추천을 위해 저장
                #st.success(current_lang_texts.get("map_load_complete").format(num_markers=len(all_markers)))
            else:
                st.warning(current_lang_texts.get("map_load_failed"))

    # 내비게이션 모드가 아닌 경우 기본 지도 표시
    if not st.session_state.navigation_active:
        map_col, info_col = st.columns([2, 1])

        with map_col:
            # 마커 데이터 준비
            markers = []

            # 사용자 현재 위치 마커
            markers.append({
                'lat': user_location[0],
                'lng': user_location[1],
                'title': current_lang_texts.get("map_my_location"),
                'color': 'blue',
                'info': current_lang_texts.get("map_current_location"),
                'category': current_lang_texts.get("map_current_location_category")
            })

            # 로드된 데이터 마커 추가
            if st.session_state.all_markers:
                markers.extend(st.session_state.all_markers)
                #st.success(current_lang_texts.get("map_markers_displayed").format(num_markers=len(st.session_state.all_markers)))

            # Google Maps 표시
            show_google_map(
                api_key=api_key,
                center_lat=user_location[0],
                center_lng=user_location[1],
                markers=markers,
                zoom=12,
                height=600,
                language=st.session_state.language
            )

        with info_col:
            st.subheader(current_lang_texts.get("map_place_info"))

            # 검색 기능
            search_term = st.text_input(current_lang_texts.get("map_search_place"))
            if search_term and st.session_state.all_markers:
                search_results = [m for m in st.session_state.all_markers
                                  if search_term.lower() in m['title'].lower()]

                if search_results:
                    st.markdown(f"### 🔍 {current_lang_texts.get('map_search_results')} ({len(search_results)}개)")
                    for i, marker in enumerate(search_results[:5]):  # 상위 5개만
                        with st.container():
                            st.markdown(f"**{marker['title']}**")
                            st.caption(f"{current_lang_texts.get('map_category')}: {marker.get('category', current_lang_texts.get('map_other_category'))}")

                            col1, col2 = st.columns([1,1])
                            with col1:
                                if st.button(current_lang_texts.get("map_find_directions"), key=f"nav_{i}"):
                                    st.session_state.navigation_active = True
                                    st.session_state.navigation_destination = {
                                        "name": marker['title'],
                                        "lat": marker['lat'],
                                        "lng": marker['lng']
                                    }
                                    st.rerun()

                            with col2:
                                if st.button(current_lang_texts.get("map_visit_history"), key=f"visit_{i}"):
                                    success, xp = add_visit(
                                        st.session_state.username,
                                        marker['title'],
                                        marker['lat'],
                                        marker['lng']
                                    )
                                    if success:
                                        st.success(current_lang_texts.get("map_visited") + f" '{marker['title']}'! +{xp} XP " + current_lang_texts.get("map_xp_earned") + "!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.info(current_lang_texts.get("map_already_visited_today"))
                else:
                    st.info(current_lang_texts.get("map_no_search_results").format(search_term=search_term))

            # 카테고리별 통계 - 언어별 처리 개선
            if st.session_state.all_markers:
                st.subheader(current_lang_texts.get("map_places_by_category"))
                
                # 현재 언어에 해당하는 카테고리 번역 가져오기
                current_lang = st.session_state.language
                categories_translation = CATEGORIES_TRANSLATION.get(current_lang, CATEGORIES_TRANSLATION["한국어"])
                
                # 카테고리별 카운트
                categories = {}
                for m in st.session_state.all_markers:
                    # 원본 카테고리 이름 가져오기
                    raw_cat = m.get('category', '기타')
                    
                    # 번역된 카테고리 이름 찾기
                    if raw_cat in categories_translation:
                        translated_cat = categories_translation[raw_cat]
                    else:
                        # 기타 카테고리로 분류
                        translated_cat = categories_translation.get('기타', 'Others')
                    
                    if translated_cat not in categories:
                        categories[translated_cat] = 0
                    categories[translated_cat] += 1

                # 번역된 카테고리 이름으로 출력
                for cat, count in categories.items():
                    # current_lang에 맞게 '개' 번역
                    count_suffix = "개" if current_lang == "한국어" else \
                                  "places" if current_lang == "영어" else "处"
                    st.markdown(f"- **{cat}**: {count}{count_suffix}")
    else:
        # 내비게이션 모드 UI
        destination = st.session_state.navigation_destination
        if not destination:
            st.error(current_lang_texts.get("map_no_destination_info"))
            if st.button(current_lang_texts.get("map_back_to_map")):
                st.session_state.navigation_active = False
                st.rerun()
        else:
            st.subheader(f"🧭 {destination['name']} {current_lang_texts.get('map_navigation_to')}")

            # 목적지 정보 표시
            dest_lat, dest_lng = destination["lat"], destination["lng"]
            user_lat, user_lng = user_location

            # 직선 거리 계산
            distance = geodesic((user_lat, user_lng), (dest_lat, dest_lng)).meters

            if not st.session_state.transport_mode:
                st.markdown(f"### {current_lang_texts.get('map_select_transport')}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    walk_time = distance / 67  # 도보 속도 약 4km/h (67m/분)
                    st.markdown(f"""
                    <div class="card">
                        <h3>🚶 {current_lang_texts.get('map_walking')}</h3>
                        <p>{current_lang_texts.get('map_estimated_time')}: {walk_time:.0f}{current_lang_texts.get('map_minute')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(current_lang_texts.get("map_select_walk"), use_container_width=True):
                        st.session_state.transport_mode = "walking"
                        st.rerun()

                with col2:
                    transit_time = distance / 200  # 대중교통 속도 약 12km/h (200m/분)
                    st.markdown(f"""
                    <div class="card">
                        <h3>🚍 {current_lang_texts.get('map_transit')}</h3>
                        <p>{current_lang_texts.get('map_estimated_time')}: {transit_time:.0f}{current_lang_texts.get('map_minute')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(current_lang_texts.get("map_select_transit"), use_container_width=True):
                        st.session_state.transport_mode = "transit"
                        st.rerun()

                with col3:
                    car_time = distance / 500  # 자동차 속도 약 30km/h (500m/분)
                    st.markdown(f"""
                    <div class="card">
                        <h3>🚗 {current_lang_texts.get('map_driving')}</h3>
                        <p>{current_lang_texts.get('map_estimated_time')}: {car_time:.0f}{current_lang_texts.get('map_minute')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(current_lang_texts.get("map_select_drive"), use_container_width=True):
                        st.session_state.transport_mode = "driving"
                        st.rerun()

                if st.button(current_lang_texts.get("map_back_to_map"), use_container_width=True):
                    st.session_state.navigation_active = False
                    st.rerun()

            else:
                # 선택된 교통수단에 따른 내비게이션 표시
                transport_mode = st.session_state.transport_mode
                transport_icons = {
                    "walking": "🚶",
                    "transit": "🚍",
                    "driving": "🚗"
                }
                transport_names = {
                    "walking": current_lang_texts.get('map_walking'),
                    "transit": current_lang_texts.get('map_transit'),
                    "driving": current_lang_texts.get('map_driving')
                }

                st.markdown(f"### {transport_icons[transport_mode]} {transport_names[transport_mode]} {current_lang_texts.get('map_route')}")

                # 마커 데이터 준비
                markers = [
                    {
                        'lat': user_lat,
                        'lng': user_lng,
                        'title': current_lang_texts.get("map_my_location"),
                        'color': 'blue',
                        'info': current_lang_texts.get("map_departure"),
                        'category': current_lang_texts.get("map_my_location")
                    },
                    {
                        'lat': dest_lat,
                        'lng': dest_lng,
                        'title': destination["name"],
                        'color': 'red',
                        'info': f'{current_lang_texts.get("map_destination", "목적지")}: {destination["name"]}',
                        'category': current_lang_texts.get("map_destination", "목적지")
                    }
                ]

                # 내비게이션 UI
                nav_col, info_col = st.columns([2, 1])

                with nav_col:
                    # 내비게이션 모드일 때 지도 표시 부분 - 수정된 부분
                    show_google_map(
                        api_key=api_key,
                        center_lat=(user_lat + dest_lat) / 2,  # 중간 지점
                        center_lng=(user_lng + dest_lng) / 2,
                        markers=markers,
                        zoom=14,
                        height=600,
                        language=st.session_state.language,
                        navigation_mode=True,
                        start_location={"lat": user_lat, "lng": user_lng},
                        end_location={"lat": dest_lat, "lng": dest_lng},
                        transport_mode=transport_mode
                    )

                with info_col:
                    # 경로 정보 표시
                    st.markdown(f"### {current_lang_texts.get('map_route_info', '경로 정보')}")
                    st.markdown(f"**{destination['name']} {current_lang_texts.get('map_to', '까지')}**")
                    st.markdown(f"- {current_lang_texts.get('map_distance')}: {distance:.0f}m")

                    # 교통수단별 예상 시간
                    if transport_mode == "walking":
                        speed = 67  # m/min
                        transport_desc = current_lang_texts.get('map_walking')
                    elif transport_mode == "transit":
                        speed = 200  # m/min
                        transport_desc = current_lang_texts.get('map_transit')
                    else:  # driving
                        speed = 500  # m/min
                        transport_desc = current_lang_texts.get('map_driving')

                    time_min = distance / speed
                    st.markdown(f"- {current_lang_texts.get('map_estimated_time')}: {time_min:.0f}{current_lang_texts.get('map_minute')}")
                    st.markdown(f"- {current_lang_texts.get('map_transport')}: {transport_desc}")

                    # 턴바이턴 내비게이션 지시사항 (예시)
                    st.markdown(f"### {current_lang_texts.get('map_route_guide')}")
                    directions = [
                        current_lang_texts.get('map_departure'),
                        current_lang_texts.get('map_straight_and_turn_right').format(distance=distance*0.3),
                        current_lang_texts.get('map_straight_and_turn_left').format(distance=distance*0.2),
                        current_lang_texts.get('map_arrive_at_destination').format(distance=distance*0.5)
                    ]

                    for i, direction in enumerate(directions):
                        st.markdown(f"{i+1}. {direction}")

                    # 다른 교통수단 선택 버튼
                    st.markdown(f"### {current_lang_texts.get('map_other_transport_modes')}")
                    other_modes = {"walking": current_lang_texts.get('map_walking'), "transit": current_lang_texts.get('map_transit'), "driving": current_lang_texts.get('map_driving')}
                    del other_modes[transport_mode]  # 현재 모드 제거

                    cols = st.columns(len(other_modes))
                    for i, (mode, name) in enumerate(other_modes.items()):
                        with cols[i]:
                            if st.button(name):
                                st.session_state.transport_mode = mode
                                st.rerun()

                    if st.button(current_lang_texts.get("map_end_navigation"), use_container_width=True):
                        st.session_state.navigation_active = False
                        st.session_state.transport_mode = None
                        st.rerun()
                    
def show_course_page():
    """개선된 관광 코스 추천 페이지"""
    # 언어 설정에 따른 텍스트 가져오기
    current_lang_texts = st.session_state.texts[st.session_state.language]
    
    page_header(current_lang_texts["course_title"])
    
    # 뒤로가기 버튼
    if st.button(current_lang_texts["map_back_to_menu"]):
        change_page("menu")
        st.rerun()
    
    # 자동으로 데이터 로드 (아직 로드되지 않은 경우)
    if not st.session_state.markers_loaded or not st.session_state.all_markers:
        with st.spinner(current_lang_texts["map_loading_data"]):
            all_markers = load_excel_files(st.session_state.language)
            if all_markers:
                st.session_state.all_markers = all_markers
                st.session_state.markers_loaded = True
                st.session_state.tourism_data = all_markers
                #st.success(f"{current_lang_texts['map_load_complete'].format(num_markers=len(all_markers))}")
            else:
                st.warning(current_lang_texts["map_load_failed"])
    
    # AI 추천 아이콘 및 소개
    col1, col2 = st.columns([1, 5])
    with col1:
        main_image_path = Path("asset") / "SeoulTripView.png"
        if main_image_path.exists():
            st.image(main_image_path, use_container_width=True)
        else:
            st.info(current_lang_texts["course_image_not_found"])
    with col2:
        st.markdown(f"### {current_lang_texts['course_ai_recommendation_title']}")
        st.markdown(current_lang_texts["course_ai_recommendation_description"])
    
    # 여행 정보 입력 섹션
    st.markdown("---")
    st.subheader(current_lang_texts["travel_info_input"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(current_lang_texts.get("travel_date_start", "여행 시작일"))
    
    with col2:
        end_date = st.date_input(current_lang_texts.get("travel_date_end", "여행 종료일"), value=start_date)
    
    # 일수 계산
    delta = (end_date - start_date).days + 1
    st.caption(current_lang_texts.get("travel_days_total", "총 {days}일 일정").format(days=delta))
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_people = st.number_input(current_lang_texts.get("travel_people_count", "여행 인원"), min_value=1, max_value=10, value=2)
    
    with col2:
        include_children = st.checkbox(current_lang_texts.get("travel_with_children", "아이 동반"))
    
    # 여행 스타일 선택
    st.markdown(f"### {current_lang_texts.get('travel_style', '여행 스타일')}")
    
    # 여행 스타일 목록을 언어에 맞게 표시
    travel_styles = [
        current_lang_texts.get("travel_style_active", "활동적인"),
        current_lang_texts.get("travel_style_relaxation", "휴양"),
        current_lang_texts.get("travel_style_food", "맛집"),
        current_lang_texts.get("travel_style_shopping", "쇼핑"),
        current_lang_texts.get("travel_style_history_culture", "역사/문화"),
        current_lang_texts.get("travel_style_nature", "자연")
    ]
    
    # 3열로 버튼식 선택
    cols = st.columns(3)
    selected_styles = []
    
    for i, style in enumerate(travel_styles):
        with cols[i % 3]:
            if st.checkbox(style, key=f"style_{style}"):
                selected_styles.append(style)
    
    # 코스 생성 버튼
    st.markdown("---")
    generate_course = st.button(current_lang_texts["generate_course_button"], type="primary", use_container_width=True)
    
    if generate_course:
        if not selected_styles:
            st.warning(current_lang_texts["select_travel_style_warning"])
        else:
            with st.spinner(current_lang_texts["generating_course_spinner"]):
                # 코스 추천 실행
                recommended_places, course_type, daily_courses = recommend_courses(
                    st.session_state.all_markers if hasattr(st.session_state, 'all_markers') else [],
                    selected_styles,
                    delta,
                    include_children
                )
                
                st.success(current_lang_texts["course_generation_complete"])
                
                # 코스 표시
                st.markdown(f"## {current_lang_texts['recommended_course_title']}")
                st.markdown(f"**{course_type}** - {delta}일 일정")
                
                # 일별 코스 표시
                if daily_courses:
                    # 실제 데이터 기반 일별 코스 표시
                    for day_idx, day_course in enumerate(daily_courses):
                        st.markdown(f"### Day {day_idx + 1}")
                        
                        if not day_course:
                            st.info(current_lang_texts["insufficient_recommendations"])
                            continue
                        
                        # 시간대별 장소 표시
                        time_slots = [
                            current_lang_texts["morning_time_slot"],
                            current_lang_texts["afternoon_time_slot"],
                            current_lang_texts["evening_time_slot"]
                        ]
                        timeline = st.columns(len(day_course))
                        
                        for i, place in enumerate(day_course):
                            with timeline[i]:
                                time_idx = min(i, len(time_slots) - 1)
                                st.markdown(f"**{time_slots[time_idx]}**")
                                st.markdown(f"**{place['title']}**")
                                st.caption(current_lang_texts["category_label"].format(category=place['category']))
                                
                                # 간단한 설명 추가
                                info_text = ""
                                if 'address' in place and place['address']:
                                    info_text += current_lang_texts["location_label"].format(address=place['address'])
                                    if len(place['address']) > 20:
                                        info_text = info_text[:20] + "..."
                                st.caption(info_text)
                else:
                    # 기본 코스 데이터 표시
                    for day in range(1, min(delta+1, 4)):  # 최대 3일까지
                        st.markdown(f"### Day {day}")
                        
                        # 일별 방문 장소 선택
                        day_spots = []
                        if day == 1:
                            day_spots = recommended_places[:3]  # 첫날 3곳
                        elif day == 2:
                            day_spots = recommended_places[3:6] if len(recommended_places) > 3 else recommended_places[:3]
                        else:  # 3일차 이상
                            day_spots = recommended_places[6:9] if len(recommended_places) > 6 else recommended_places[:3]
                        
                        # 표시할 장소가 없으면 기본 추천
                        if not day_spots:
                            day_spots = current_lang_texts.get("default_spots", ["경복궁", "남산서울타워", "명동"])
                        
                        timeline = st.columns(len(day_spots))
                        
                        for i, spot_name in enumerate(day_spots):
                            # 시간대 설정
                            time_slots = [
                                current_lang_texts["morning_time_slot"],
                                current_lang_texts["afternoon_time_slot"],
                                current_lang_texts["evening_time_slot"]
                            ]
                            time_slot = time_slots[i % 3]
                            
                            with timeline[i]:
                                st.markdown(f"**{time_slot}**")
                                st.markdown(f"**{spot_name}**")
                                st.caption(current_lang_texts.get("tourist_spot", "관광지"))
                
                # 지도에 코스 표시
                st.markdown(f"### {current_lang_texts['course_map_title']}")
                
                # API 키 확인
                api_key = st.session_state.google_maps_api_key
                if not api_key or api_key == "YOUR_GOOGLE_MAPS_API_KEY":
                    st.error(current_lang_texts["map_api_key_missing"])
                    api_key = st.text_input(current_lang_texts["map_api_key_input"], type="password")
                    if api_key:
                        st.session_state.google_maps_api_key = api_key
                
                # 코스 마커 생성
                # show_course_page 함수 내의 map_markers 생성 부분 수정

                # 코스 마커 생성
                map_markers = []
                
                if daily_courses:
                    # 실제 데이터 기반 코스
                    # 시간대별 색상 및 일자별 경로 구성을 위한 코드 추가
                    time_slots_texts = [ # 현재 언어에 맞는 시간대 텍스트
                        current_lang_texts["morning_time_slot"],
                        current_lang_texts["afternoon_time_slot"],
                        current_lang_texts["evening_time_slot"]
                    ]
                    for day_idx, day_course in enumerate(daily_courses):
                         for time_idx, place in enumerate(day_course):
                            # 시간대별 마커 색상 (예시, 필요시 CATEGORY_COLORS와 연동)
                            # 현재는 장소의 카테고리 색상을 따르도록 하거나, 일관된 색상 사용 가능
                            # 여기서는 place에 color가 이미 있다고 가정하거나, CATEGORY_COLORS 사용
                            color = CATEGORY_COLORS.get(place['category'], "gray") # place 딕셔너리에 'category'가 있다고 가정

                            # title에 Day 정보가 이미 포함되어 있으므로, day 키를 명시적으로 추가
                            marker_title = f"Day {day_idx+1} - {place['title']}"
                            # info에 들어갈 시간대 정보
                            current_time_slot_text = time_slots_texts[time_idx % len(time_slots_texts)]

                            marker = {
                                'lat': place['lat'],
                                'lng': place['lng'],
                                'title': marker_title,
                                'info': f"Day {day_idx+1} {current_time_slot_text}<br>{place.get('info', '')}", # place에 info가 있을 수 있음
                                'category': place['category'], # place에 category가 있다고 가정
                                'color': color,
                                'day': day_idx + 1  # 명시적인 'day' 정보 추가
                            }
                            map_markers.append(marker)
                else:
                    # 기본 코스 - 좌표 데이터가 없어 지도 표시 불가
                    st.warning(current_lang_texts["map_display_error"])

                # 지도의 중심 좌표 계산
                if map_markers:
                    center_lat = sum(marker['lat'] for marker in map_markers) / len(map_markers)
                    center_lng = sum(marker['lng'] for marker in map_markers) / len(map_markers)
                    zoom_level = 12 # 경로가 있을 경우 좀 더 넓게
                else:
                    center_lat = DEFAULT_LOCATION[0]
                    center_lng = DEFAULT_LOCATION[1]
                    zoom_level = 13 # 경로 없을 시 기본 줌

                # create_Maps_html 함수에 route_points 와 start_location 전달
                # show_google_map 함수가 create_Maps_html을 호출하므로, show_google_map에 전달
                # start_location은 사용자의 현재 위치 또는 코스의 시작점으로 할 수 있습니다.
                # 여기서는 사용자의 현재 위치를 사용합니다.
                start_point_for_route = None
                if map_markers: # 코스가 있다면 코스의 첫번째 지점을 시작점으로 사용할 수도 있습니다.
                    # start_point_for_route = [map_markers[0]['lat'], map_markers[0]['lng']]
                    pass # 현재는 get_location_position()을 사용

                # `show_google_map` 호출 시 `route_points` 와 `start_location` 인자 사용
                show_google_map(
                    api_key=api_key,
                    center_lat=center_lat,
                    center_lng=center_lng,
                    markers=map_markers, # 모든 마커 (코스 장소 포함)
                    zoom=zoom_level,
                    height=500,
                    language=st.session_state.language,
                    route_points=map_markers, # 경로를 그릴 마커들
                    start_location=get_location_position() # 경로 시작 지점 (사용자 현재 위치)
                )
                
                # 일정 저장 버튼
                if st.button(current_lang_texts["save_course_button"], use_container_width=True):
                    if 'saved_courses' not in st.session_state:
                        st.session_state.saved_courses = []
                    
                    # 코스 정보 저장
                    course_info = {
                        "type": course_type,
                        "days": delta,
                        "date": start_date.strftime("%Y-%m-%d"),
                        "styles": selected_styles
                    }
                    
                    if daily_courses:
                        # 실제 데이터 기반 코스
                        course_info["daily_places"] = []
                        for day in daily_courses:
                            day_places = [place['title'] for place in day]
                            course_info["daily_places"].append(day_places)
                    else:
                        # 기본 코스
                        course_info["places"] = recommended_places
                    
                    st.session_state.saved_courses.append(course_info)
                    save_session_data()  # 세션 데이터 저장
                    
                    st.success(current_lang_texts["course_saved_success"])


def show_history_page():
    """관광 이력 페이지 표시"""
    # 현재 언어에 맞는 텍스트 가져오기
    current_lang_texts = st.session_state.texts[st.session_state.language]
    
    page_header(current_lang_texts["history_page_title"])
    
    # 뒤로가기 버튼
    if st.button(current_lang_texts["map_back_to_menu"]):
        change_page("menu")
        st.rerun()
    
    username = st.session_state.username
    
    # 사용자 레벨과 경험치 표시
    user_xp = st.session_state.user_xp.get(username, 0)
    user_level = calculate_level(user_xp)
    xp_percentage = calculate_xp_percentage(user_xp)
    remaining_xp = XP_PER_LEVEL - (user_xp % XP_PER_LEVEL)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        main_image_path = Path("asset") / "SeoulTripView.png"
        if main_image_path.exists():
            st.image(main_image_path, use_container_width=True)
        else:
            st.info("이미지를 찾을 수 없습니다: asset/SeoulTripView.png")
    
    with col2:
        st.markdown(f"## {current_lang_texts['level_text'].format(level=user_level)}")
        st.progress(xp_percentage / 100)
        st.markdown(f"**{current_lang_texts['total_xp_text'].format(xp=user_xp)}** ({current_lang_texts['next_level_xp_text'].format(remaining_xp=remaining_xp)})")
    
    with col3:
        st.write("")  # 빈 공간
    
    # 방문 통계
    if username in st.session_state.user_visits and st.session_state.user_visits[username]:
        visits = st.session_state.user_visits[username]
        
        total_visits = len(visits)
        unique_places = len(set([v['place_name'] for v in visits]))
        total_xp = sum([v.get('xp_gained', 0) for v in visits])
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(current_lang_texts["total_visits_metric"], current_lang_texts["visits_count"].format(count=total_visits))
        
        with col2:
            st.metric(current_lang_texts["visited_places_metric"], current_lang_texts["places_count"].format(count=unique_places))
        
        with col3:
            st.metric(current_lang_texts["earned_xp_metric"], current_lang_texts["xp_points"].format(xp=total_xp))
        
        # 방문 기록 목록 표시
        st.markdown("---")
        st.subheader(current_lang_texts["visit_history_tab"])
        
        # 정렬 옵션
        tab1, tab2, tab3 = st.tabs([
            current_lang_texts["all_tab"], 
            current_lang_texts["recent_tab"], 
            current_lang_texts["xp_tab"]
        ])
        
        with tab1:
            display_visits(visits, current_lang_texts)
        
        with tab2:
            recent_visits = sorted(visits, key=lambda x: x['timestamp'], reverse=True)
            display_visits(recent_visits, current_lang_texts)
        
        with tab3:
            xp_visits = sorted(visits, key=lambda x: x.get('xp_gained', 0), reverse=True)
            display_visits(xp_visits, current_lang_texts)
        
        # 방문한 장소를 지도에 표시
        st.markdown("---")
        st.subheader(current_lang_texts["visit_map_title"])
        
        # API 키 확인
        api_key = st.session_state.google_maps_api_key
        if not api_key or api_key == "YOUR_GOOGLE_MAPS_API_KEY":
            st.error(current_lang_texts["map_api_key_not_set"])
            api_key = st.text_input(current_lang_texts["map_enter_api_key"], type="password")
            if api_key:
                st.session_state.google_maps_api_key = api_key
                #st.success(current_lang_texts["map_api_key_set_success"])
            else:
                st.info(current_lang_texts["map_api_key_required_info"])
                return
        
        # 방문 장소 마커 생성
        visit_markers = []
        for visit in visits:
            marker = {
                'lat': visit["latitude"],
                'lng': visit["longitude"],
                'title': visit["place_name"],
                'color': 'purple',  # 방문한 장소는 보라색으로 표시
                'info': f"{current_lang_texts['visit_date']}: {visit['date']}<br>{current_lang_texts['map_xp_earned']}: +{visit.get('xp_gained', 0)}",
                'category': current_lang_texts["map_visit_history"]
            }
            visit_markers.append(marker)
        
        if visit_markers:
            # 지도 중심 좌표 계산 (마커들의 평균)
            center_lat = sum(m['lat'] for m in visit_markers) / len(visit_markers)
            center_lng = sum(m['lng'] for m in visit_markers) / len(visit_markers)
            
            # Google Maps 표시
            show_google_map(
                api_key=api_key,
                center_lat=center_lat,
                center_lng=center_lng,
                markers=visit_markers,
                zoom=12,
                height=500,
                language=st.session_state.language
            )
        else:
            st.info(current_lang_texts["no_map_visits"])
    else:
        st.info(current_lang_texts["no_visit_history"])
        
        # 예시 데이터 생성 버튼
        if st.button(current_lang_texts["generate_sample_data"]):
            # 샘플 방문 데이터
            sample_visits = [
                {
                    "place_name": "경복궁",
                    "latitude": 37.5796,
                    "longitude": 126.9770,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "xp_gained": 80
                },
                {
                    "place_name": "남산서울타워",
                    "latitude": 37.5511,
                    "longitude": 126.9882,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "xp_gained": 65
                },
                {
                    "place_name": "명동",
                    "latitude": 37.5635,
                    "longitude": 126.9877,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "xp_gained": 25
                }
            ]
            
            if username not in st.session_state.user_visits:
                st.session_state.user_visits[username] = []
            
            st.session_state.user_visits[username] = sample_visits
            
            # XP 부여
            total_xp = sum([v['xp_gained'] for v in sample_visits])
            if username not in st.session_state.user_xp:
                st.session_state.user_xp[username] = 0
            st.session_state.user_xp[username] += total_xp
            
            st.success(current_lang_texts["sample_data_success"].format(total_xp=total_xp))
            st.rerun()

#################################################
# 메인 앱 로직
#################################################

# 데이터 폴더 생성
data_folder = Path("data")
if not data_folder.exists():
    data_folder.mkdir(parents=True, exist_ok=True)

# asset 폴더 생성 (없는 경우)
asset_folder = Path("asset")
if not asset_folder.exists():
    asset_folder.mkdir(parents=True, exist_ok=True)

# CSS 스타일 적용
apply_custom_css()

# 세션 상태 초기화
init_session_state()

# 페이지 라우팅
def main():
    # 로그인 상태에 따른 페이지 제어
    if not st.session_state.logged_in and st.session_state.current_page != "login":
        st.session_state.current_page = "login"
    
    # 현재 페이지에 따라 해당 함수 호출
    if st.session_state.current_page == "login":
        show_login_page()
    elif st.session_state.current_page == "menu":
        show_menu_page()
    elif st.session_state.current_page == "map":
        show_map_page()
    elif st.session_state.current_page == "course":
        show_course_page()
    elif st.session_state.current_page == "history":
        show_history_page()
    else:
        show_menu_page()  # 기본값

if __name__ == "__main__":
    main()
