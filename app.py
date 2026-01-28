import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# 1. 페이지 설정
st.set_page_config(page_title="미래 복합 재난 리스크 분석", layout="wide")

# 2. GeoJSON 로드
@st.cache_data
def load_geojson():
    url = 'https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_municipalities_geo_simple.json'
    return requests.get(url).json()

geojson_data = load_geojson()

# 3. 데이터 로드 및 전처리
@st.cache_data
def load_data():
    df = pd.read_csv('Final_Risk_Deploy.csv', encoding='utf-8-sig')
    
    # [수정] 현재 파일에 '시도'가 없으므로 SGG_Code를 지역명 대용으로 사용합니다.
    df['지역명'] = "지역코드: " + df['SGG_Code'].astype(str)
    
    df['Date'] = pd.to_datetime(df['Date'])
    df['SGG_Code'] = df['SGG_Code'].astype(str)
    return df

df = load_data()

# 4. 사이드바 인터페이스
st.sidebar.header("🔍 분석 설정")
available_years = sorted(df['Date'].dt.year.unique())
target_year = st.sidebar.selectbox("📅 분석 연도 선택", options=available_years)

df_year = df[df['Date'].dt.year == target_year].copy()
df_year['Date_str'] = df_year['Date'].dt.strftime('%Y-%m-%d')

# 5. 메인 화면 구성
st.title(f"🌍 {target_year}년 하절기 복합 재난 분석 대시보드")

tab1, tab2, tab3 = st.tabs(["🔥 Hazard (위험)", "🏥 Vulnerability (취약성)", "⚠️ Final Risk (리스크)"])

maps_config = [
    {"tab": tab1, "col": "Future_Risk_Score", "name": "미래 위험 지수", "color": "YlOrBr"},
    {"tab": tab2, "col": "최종_취약성_점수", "name": "최종 취약성 점수", "color": "Purples"},
    {"tab": tab3, "col": "Final_Risk", "name": "종합 리스크 지수", "color": "Reds"}
]

for m in maps_config:
    with m['tab']:
        # 데이터가 비어있지 않은지 확인 후 처리
        if not df_year.empty:
            max_row = df_year.loc[df_year[m['col']].idxmax()]
            
            c1, c2, c3 = st.columns(3)
            c1.metric("최고 위험 지역", max_row['지역명'])
            c2.metric("최고 위험 발생일", max_row['Date_str'])
            c3.metric("최대 수치", f"{max_row[m['col']]:.4f}")
            
            fig = px.choropleth(
                df_year, 
                geojson=geojson_data, 
                locations='SGG_Code',
                featureidkey="properties.code",
                color=m['col'],
                animation_frame='Date_str',
                hover_name='지역명',
                hover_data={'SGG_Code': False, m['col']: ':.4f', 'Date_str': False},
                color_continuous_scale=m['color'],
                range_color=[0, df[m['col']].max()]
            )
            
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(height=800, margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("선택한 연도의 데이터가 없습니다.")