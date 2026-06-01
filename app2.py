import streamlit as st
import pandas as pd
from core.data_service import get_data
from components.ui import inject_custom_css, header_section, custom_alert
from views.overview import render_overview
from views.demographics import render_demographics
from views.operations import render_operations
from views.anomalies import render_anomalies
from views.data_explorer import render_data_explorer

# 1. Page Configuration
st.set_page_config(
    page_title="AeroSight: Aviation Analytics Hub",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Curated Styles
inject_custom_css()

# 3. Retrieve Active Dataset (Synced with Simulator)
df_raw = get_data()

# 4. SIDEBAR NAVIGATION & GLOBAL FILTERS
st.sidebar.markdown(
    '<div style="text-align: center; margin-bottom: 1.5rem;">'
    '<h1 style="color: white; font-size: 1.8rem; font-weight: 700; margin: 0; letter-spacing: -0.03em;">✈️ AeroSight</h1>'
    '<p style="color: #94a3b8; font-size: 0.8rem; margin: 0.2rem 0 0 0;">Corporate Analytics & Simulation</p>'
    '</div>', 
    unsafe_allow_html=True
)

st.sidebar.markdown('<p style="color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5rem;">Navigation</p>', unsafe_allow_html=True)
page = st.sidebar.radio(
    label="Go to Page:",
    options=[
        "📊 Executive Overview",
        "👥 Passenger Demographics",
        "✈️ Operations & Timeline",
        "🕵️ AI Insights & Anomalies",
        "🔍 Search & Bookings Simulator"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown('<hr style="border-color: rgba(255,255,255,0.08); margin: 1.5rem 0;">', unsafe_allow_html=True)
st.sidebar.markdown('<p style="color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5rem;">Global Filters</p>', unsafe_allow_html=True)

# Filter 1: Continent
continents_list = ["All Continents"] + sorted(df_raw['Continents'].dropna().unique().tolist())
selected_continent = st.sidebar.selectbox("Region/Continent:", continents_list)

# Filter 2: Flight Status
status_list = ["All Statuses", "On Time", "Delayed", "Cancelled"]
selected_status = st.sidebar.selectbox("Dispatch Status:", status_list)

# Filter 3: Age Range
min_age = int(df_raw['Age'].min())
max_age = int(df_raw['Age'].max())
selected_age_range = st.sidebar.slider(
    "Passenger Age Range:",
    min_value=min_age,
    max_value=max_age,
    value=(min_age, max_age)
)

# 5. DYNAMIC FILTERING LOGIC
df_filtered = df_raw.copy()

# Apply Continent Filter
if selected_continent != "All Continents":
    df_filtered = df_filtered[df_filtered['Continents'] == selected_continent]

# Apply Status Filter
if selected_status != "All Statuses":
    df_filtered = df_filtered[df_filtered['Flight Status'] == selected_status]

# Apply Age Range Filter
df_filtered = df_filtered[
    (df_filtered['Age'] >= selected_age_range[0]) & 
    (df_filtered['Age'] <= selected_age_range[1])
]

# Sidebar Footer Context
st.sidebar.markdown('<hr style="border-color: rgba(255,255,255,0.08); margin: 2rem 0 1rem 0;">', unsafe_allow_html=True)
st.sidebar.markdown(
    f'<div style="color: #64748b; font-size: 0.75rem;">'
    f'Active Scope: <strong>{len(df_filtered):,}</strong> / {len(df_raw):,} flights<br>'
    f'Version: <strong>2.1 (Production)</strong><br>'
    f'Local Time: <strong>2026-05-26</strong>'
    f'</div>',
    unsafe_allow_html=True
)

# 6. APP RENDER ORCHESTRATOR
# Top Banner
header_section(
    title="AeroSight Flight Operations Platform",
    subtitle="Interactive Corporate Intelligence, Demographic Profiling, and Real-Time Dispatch Simulations"
)

# Empty State Check
if df_filtered.empty:
    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)
    custom_alert(
        title="⚠️ Empty Data State Detected",
        text="The current combination of global filters (Continent, Dispatch Status, and Age Range) yields exactly zero matching flight records. Please adjust your sidebar settings to regain operational metrics.",
        alert_type="warning"
    )
else:
    # Router
    if page == "📊 Executive Overview":
        render_overview(df_filtered)
    elif page == "👥 Passenger Demographics":
        render_demographics(df_filtered)
    elif page == "✈️ Operations & Timeline":
        render_operations(df_filtered)
    elif page == "🕵️ AI Insights & Anomalies":
        render_anomalies(df_filtered)
    elif page == "🔍 Search & Bookings Simulator":
        render_data_explorer(df_filtered)
