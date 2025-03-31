import streamlit as st
import pandas as pd
import altair as alt
# 수정된 CSV 파일 경로 (Streamlit Cloud용 상대 경로)
data_path = "hotel_fin_0331_1.csv"
df = pd.read_csv(data_path, encoding='euc-kr')
st.set_page_config(page_title="호텔 리뷰 감성 요약", layout="wide")
st.title("🏨 호텔 리뷰 요약 및 항목별 분석")
# 지역 선택
regions = df['Location'].unique()
selected_region = st.radio("📍 지역을 선택하세요", regions, horizontal=True)
# 지역 필터링
region_df = df[df['Location'] == selected_region]
region_hotels = region_df['Hotel'].unique()
# 호텔 선택
selected_hotel = st.selectbox("🏨 호텔을 선택하세요", ["전체 보기"] + list(region_hotels))
# 지도 데이터 준비
if selected_hotel == "전체 보기":
    # 지역 내 모든 호텔 위치 표시
    st.subheader(f"🗺️ {selected_region} 지역 호텔 지도")
    map_df = region_df[['Latitude', 'Longitude']].dropna()
    map_df.columns = ['lat', 'lon']
    st.map(map_df)
else:
    # 선택된 호텔 정보만 표시
    hotel_data = region_df[region_df['Hotel'] == selected_hotel].iloc[0]
    
    # 실제 위경도 데이터 사용
    st.subheader(f"🗺️ '{selected_hotel}' 위치")
    lat = hotel_data['Latitude']
    lon = hotel_data['Longitude']
    st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
    
    # 요약 출력
    st.markdown("### ✨ 선택한 호텔 요약")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ 긍정 요약")
        st.write(hotel_data['Refined_Positive'])
    with col2:
        st.subheader("🚫 부정 요약")
        st.write(hotel_data['Refined_Negative'])
    
    # 감성 점수 시각화
    st.markdown("---")
    st.subheader("📊 항목별 평균 점수")
    
    # 점수 데이터 추출
    aspect_columns = ['소음', '가격', '위치', '서비스', '청결', '편의시설']
    aspect_scores = hotel_data[aspect_columns]
    
    # DataFrame으로 변환
    score_df = pd.DataFrame({
        '항목': aspect_columns,
        '점수': [hotel_data[col] for col in aspect_columns]
    })
    
    # Altair 차트 - X축 레이블만 수정
    chart = alt.Chart(score_df).mark_bar().encode(
        x=alt.X('항목', sort=None, axis=alt.Axis(labelAngle=0)),  # X축 레이블 각도 0도(수평)로 설정
        y=alt.Y('점수', axis=alt.Axis(titleAngle=90)),  # Y축은 각도 90도
        color=alt.condition(
            alt.datum.점수 < 0,
            alt.value('crimson'),  # 음수면 빨간색
            alt.value('steelblue') # 양수면 파란색
        )
    ).properties(
        width=600,
        height=400
    )
    
    st.altair_chart(chart, use_container_width=True)
    
# Raw 데이터 보기
with st.expander("📄 원본 데이터 보기"):
    if selected_hotel == "전체 보기":
        st.dataframe(region_df.reset_index(drop=True))
    else:
        st.dataframe(region_df[region_df['Hotel'] == selected_hotel].reset_index(drop=True))
