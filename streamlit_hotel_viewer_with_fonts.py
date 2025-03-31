import streamlit as st
import pandas as pd
import altair as alt

# CSV 파일 경로
data_path = "final_all_loc_all_fin_2.csv"
df = pd.read_csv(data_path, encoding='euc-kr')

st.set_page_config(page_title="호텔 리뷰 감성 요약", layout="wide")
st.title("🏨 호텔 리뷰 요약 및 항목별 분석")

# 지역 선택 (radio 버튼 스타일)
df = df.dropna(subset=['Hotel', 'Location'])  # NaN 제거
locations = df['Location'].unique()
selected_location = st.radio("지역을 선택하세요", sorted(locations), horizontal=True)

# 지역 기반 호텔 리스트
hotels = df[df['Location'] == selected_location]['Hotel'].unique()
selected_hotel = st.selectbox("호텔을 선택하세요", sorted(hotels))

# 선택한 호텔 정보 필터링
hotel_data = df[(df['Hotel'] == selected_hotel) & (df['Location'] == selected_location)].iloc[0]

# 컬럼 나누기
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

aspect_columns = ['소음', '가격', '위치', '서비스', '청결', '편의시설']
aspect_scores = hotel_data[aspect_columns]

plot_df = pd.DataFrame({
    "항목": aspect_columns,
    "점수": aspect_scores.values,
    "색상": ['#FF6B6B' if v < 0 else '#4EA8DE' for v in aspect_scores.values]
})

chart = alt.Chart(plot_df).mark_bar().encode(
    x=alt.X('항목:N', sort=None),
    y=alt.Y('점수:Q'),
    color=alt.Color('색상:N', scale=None)
).properties(width=600, height=400)

st.altair_chart(chart, use_container_width=True)

# Raw 데이터 보기
with st.expander("📄 원본 데이터 보기"):
    st.dataframe(df[df['Hotel'] == selected_hotel].reset_index(drop=True))


