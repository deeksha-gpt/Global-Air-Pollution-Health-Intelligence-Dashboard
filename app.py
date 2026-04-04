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
# TITLE
# -------------------------------
st.title("🌍 Global Air Pollution & Health Intelligence Dashboard")
st.markdown("Analyze the relationship between **air pollution (PM2.5)** and **health outcomes globally**.")

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

# Fix common mismatch
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
# KPI SECTION
# -------------------------------
st.subheader("📊 Key Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🌫️ PM2.5 Level", float(filtered['pm25'].values[0]))

with col2:
    st.metric("❤️ Mortality Rate", float(filtered['mortality_rate'].values[0]))

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
# SCATTER PLOT
# -------------------------------
with left:
    st.subheader("📈 Pollution vs Mortality")

    fig, ax = plt.subplots()
    sns.scatterplot(data=df, x='pm25', y='mortality_rate', ax=ax)

    # Highlight selected country
    sns.scatterplot(
        data=filtered,
        x='pm25',
        y='mortality_rate',
        color='red',
        s=120,
        ax=ax,
        label='Selected Country'
    )

    ax.set_xlabel("PM2.5")
    ax.set_ylabel("Mortality Rate")
    ax.legend()

    st.pyplot(fig)

# -------------------------------
# INTERACTIVE MAP (OPTIMIZED)
# -------------------------------
with right:
    st.subheader("🗺️ Interactive Global Pollution Map")
    st.markdown("##### 🌐 Hover over countries to explore pollution & health data")

    # Base map (light + fast)
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodbpositron")

    # Fit bounds (ensures full world visible)
    m.fit_bounds([[ -60, -180 ], [ 85, 180 ]])

    # Choropleth
    folium.Choropleth(
        geo_data=geo_df,
        data=geo_df,
        columns=['country', 'pm25'],
        key_on='feature.properties.name',
        fill_color='Reds',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='PM2.5 Levels'
    ).add_to(m)

    # Tooltip layer (lightweight)
    folium.GeoJson(
        geo_df[['geometry', 'country', 'pm25', 'mortality_rate']],
        tooltip=folium.GeoJsonTooltip(
            fields=['country', 'pm25', 'mortality_rate'],
            aliases=['Country:', 'PM2.5:', 'Mortality Rate:']
        )
    ).add_to(m)

    # Display map
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
# FOOTER
# -------------------------------
st.markdown("---")
st.markdown(
    "💡 **Insight:** Countries with higher PM2.5 levels tend to show increased mortality rates, "
    "highlighting the public health impact of air pollution."
)