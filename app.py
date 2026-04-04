import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="GEOINT Dashboard", layout="wide")

# -------------------------------
# TITLE + CONTEXT (IMPROVEMENT 1 + 5)
# -------------------------------
st.title("🌍 Global Air Pollution & Health Intelligence Dashboard")

st.markdown(
    "This dashboard supports **geospatial intelligence (GEOINT)** analysis by identifying environmental risk hotspots."
)

st.markdown(
    "Built using global datasets (WHO & World Bank) to analyze the relationship between **air pollution (PM2.5)** and **health outcomes**."
)

# -------------------------------
# LOAD DATA
# -------------------------------
pm25 = pd.read_csv("data/pm25_global.csv")
health = pd.read_csv("data/health_data.csv")
world = gpd.read_file("data/world.geojson")

# -------------------------------
# CLEAN DATA
# -------------------------------
pm25['country'] = pm25['country'].str.lower().str.strip()
health['country'] = health['country'].str.lower().str.strip()
world['name'] = world['name'].str.lower().str.strip()

pm25['country'] = pm25['country'].replace({
    'united states': 'united states of america'
})

# -------------------------------
# MERGE
# -------------------------------
df = pm25.merge(health, on='country')
geo_df = world.merge(df, left_on='name', right_on='country')

# -------------------------------
# SIDEBAR
# -------------------------------
st.sidebar.header("🌐 Filters")
country = st.sidebar.selectbox("Select Country", sorted(df['country'].unique()))
filtered = df[df['country'] == country]

# -------------------------------
# KPI SECTION (IMPROVEMENT 2 - UNITS)
# -------------------------------
st.subheader("📊 Key Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🌫️ PM2.5 Level (µg/m³)", float(filtered['pm25'].values[0]))

with col2:
    st.metric("❤️ Mortality Rate (%)", float(filtered['mortality_rate'].values[0]))

with col3:
    risk = "High Risk ⚠️" if (
        float(filtered['pm25'].values[0]) > df['pm25'].mean() and
        float(filtered['mortality_rate'].values[0]) > df['mortality_rate'].mean()
    ) else "Moderate / Low Risk"
    st.metric("🚨 Risk Level", risk)

# -------------------------------
# LAYOUT
# -------------------------------
left, right = st.columns(2)

# -------------------------------
# SCATTER PLOT (IMPROVEMENT 3)
# -------------------------------
with left:
    st.subheader("📈 Pollution vs Mortality")

    fig, ax = plt.subplots()
    sns.scatterplot(data=df, x='pm25', y='mortality_rate', ax=ax)

    sns.scatterplot(
        data=filtered,
        x='pm25',
        y='mortality_rate',
        color='red',
        s=120,
        ax=ax,
        label='Selected Country'
    )

    ax.set_xlabel("PM2.5 (µg/m³)")
    ax.set_ylabel("Mortality Rate (%)")
    ax.set_title("Higher Pollution → Higher Mortality Trend")
    ax.legend()

    st.pyplot(fig)

# -------------------------------
# MAP
# -------------------------------
with right:
    st.subheader("🗺️ Interactive Global Pollution Map")
    st.markdown("##### 🌐 Hover over countries to explore pollution & health data")

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodbpositron")

    m.fit_bounds([[ -60, -180 ], [ 85, 180 ]])

    folium.Choropleth(
        geo_data=geo_df,
        data=geo_df,
        columns=['country', 'pm25'],
        key_on='feature.properties.name',
        fill_color='Reds',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='PM2.5 Levels (µg/m³)'
    ).add_to(m)

    folium.GeoJson(
        geo_df[['geometry', 'country', 'pm25', 'mortality_rate']],
        tooltip=folium.GeoJsonTooltip(
            fields=['country', 'pm25', 'mortality_rate'],
            aliases=['Country:', 'PM2.5 (µg/m³):', 'Mortality Rate (%):']
        )
    ).add_to(m)

    st_folium(m, use_container_width=True, height=500)

# -------------------------------
# HOTSPOTS
# -------------------------------
st.subheader("🔥 High Risk Regions")

geo_df['high_risk'] = (
    (geo_df['pm25'] > geo_df['pm25'].mean()) &
    (geo_df['mortality_rate'] > geo_df['mortality_rate'].mean())
)

high_risk = geo_df[geo_df['high_risk']][['country', 'pm25', 'mortality_rate']]

st.dataframe(high_risk)

# -------------------------------
# INSIGHT BOX (IMPROVEMENT 4)
# -------------------------------
st.info(
    "⚠️ Insight: Regions with higher PM2.5 levels tend to show increased mortality rates, "
    "highlighting the global health burden of air pollution."
)

# -------------------------------
# FOOTER
# -------------------------------
st.markdown("---")
st.markdown(
    "💡 This dashboard demonstrates how geospatial intelligence can support environmental risk analysis and decision-making."
)
