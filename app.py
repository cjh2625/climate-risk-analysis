import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# 1. GeoJSON 로드
geojson_url = 'https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_municipalities_geo_simple.json'
geojson_data = requests.get(geojson_url).json()

# 2. 데이터 로드 및 매핑 처리
# 엑셀 파일 로딩 (사용자 파일명 반영)
df = pd.read_csv('Final_Risk_Deploy.csv', encoding='utf-8-sig')

# 매핑 데이터 정제
mapping_info = df_vulner[['SGG_Code', '시도', '시군구']].drop_duplicates()
df = pd.merge(df_risk, mapping_info, on='SGG_Code', how='left')
df['지역명'] = df['시도'] + " " + df['시군구']

# 날짜 및 데이터 타입 전처리
df['Date'] = pd.to_datetime(df['Date'])
df = df[df['Date'].dt.month.isin([7, 8, 9])] # 하절기 필터링
df['SGG_Code'] = df['SGG_Code'].astype(str)

# 3. 사이드바 및 레이아웃 설정
st.set_page_config(layout="wide") # 화면 넓게 쓰기
st.title("🌍 하절기 복합 재난 분석 시스템")
st.markdown("### 2027-2050 미래 시나리오 기반")

# [변경 포인트] 연도 슬라이더 -> 선택 박스(selectbox)
available_years = sorted(df['Date'].dt.year.unique())
target_year = st.sidebar.selectbox("분석 연도 선택", options=available_years, index=0)

df_year = df[df['Date'].dt.year == target_year].copy()
df_year['Date_str'] = df_year['Date'].dt.strftime('%Y-%m-%d')

# 4. 분석 결과 표시 (탭 기반 대형 지도)
tab1, tab2, tab3 = st.tabs(["🔥 Hazard (위험)", "🏥 Vulnerability (취약성)", "⚠️ Final Risk (리스크)"])

maps_info = [
    {"tab": tab1, "title": "미래 위험 지수 (Hazard)", "col": "Future_Risk_Score", "color": "YlOrBr"},
    {"tab": tab2, "title": "최종 취약성 점수 (Vulnerability)", "col": "최종_취약성_점수", "color": "Purples"},
    {"tab": tab3, "title": "종합 리스크 지수 (Final Risk)", "col": "Final_Risk", "color": "Reds"}
]

for m in maps_info:
    with m['tab']:
        # 해당 지수의 연간 최고치 정보 추출
        max_row = df_year.loc[df_year[m['col']].idxmax()]
        
        # 상단 요약 지표 (메트릭)
        c1, c2, c3 = st.columns(3)
        c1.metric("연간 위험 정점 지역", max_row['지역명'])
        c2.metric("최고 위험 발생일", max_row['Date_str'])
        c3.metric("최대 위험 수치", f"{max_row[m['col']]:.4f}")

        # 지도 시각화 (크기 극대화)
        fig = px.choropleth(
            df_year, 
            geojson=geojson_data, 
            locations='SGG_Code',
            featureidkey="properties.code", 
            color=m['col'],
            animation_frame='Date_str', # 날짜별 변화 드래깅/재생 기능
            hover_name='지역명',
            hover_data={'SGG_Code': False, m['col']: ':.4f', 'Date_str': False},
            color_continuous_scale=m['color'],
            range_color=[0, df[m['col']].max()] # 전체 기간 대비 상대 비교를 위해 고정
        )
        
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            height=850, # 지도를 충분히 크게 설정
            margin={"r":0,"t":50,"l":0,"b":0},
            coloraxis_colorbar=dict(title="지수 값", thickness=20)
        )
        st.plotly_chart(fig, width='stretch')

st.info(f"💡 {target_year}년 데이터 분석 결과입니다. 하단의 재생 버튼을 누르면 하절기 일자별 변화를 볼 수 있습니다.")
