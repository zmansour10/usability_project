import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Page configuration
st.set_page_config(page_title="Elbe Monitoring Dashboard", page_icon="🌊", layout="wide")

# --- DATA LOADING ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"Datei nicht gefunden: {file_path}")
        return None
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden von {file_path}: {e}")
        return None

# Base path for data
DATA_DIR = "data"

# Load all required files
sites_all = load_data(os.path.join(DATA_DIR, "sites_all.csv"))
wq_summary = load_data(os.path.join(DATA_DIR, "wq_summary.csv"))
wq_raw = load_data(os.path.join(DATA_DIR, "wq_raw.csv"))
corrosion_positions = load_data(os.path.join(DATA_DIR, "corrosion_positions.csv"))
corrosion_rates = load_data(os.path.join(DATA_DIR, "corrosion_rates.csv"))
# Using the correct filename found in 'ls data'
measurement_summary = load_data(os.path.join(DATA_DIR, "measurement_summary.csv"))

# Ensure critical data is loaded
if sites_all is None:
    st.error("Stationen konnten nicht geladen werden. Bitte prüfen Sie den 'data' Ordner.")
    st.stop()

# Preprocess dates
if wq_raw is not None and "timestamp" in wq_raw.columns:
    wq_raw["timestamp"] = pd.to_datetime(wq_raw["timestamp"], format='mixed')

if corrosion_positions is not None and "measurement_date" in corrosion_positions.columns:
    corrosion_positions["measurement_date"] = pd.to_datetime(corrosion_positions["measurement_date"], format='mixed')

if wq_summary is not None:
    if "first_timestamp" in wq_summary.columns:
        wq_summary["first_timestamp"] = pd.to_datetime(wq_summary["first_timestamp"], format='mixed')
    if "last_timestamp" in wq_summary.columns:
        wq_summary["last_timestamp"] = pd.to_datetime(wq_summary["last_timestamp"], format='mixed')

if measurement_summary is not None:
    if "first_date" in measurement_summary.columns:
        measurement_summary["first_date"] = pd.to_datetime(measurement_summary["first_date"], format='mixed')
    if "last_date" in measurement_summary.columns:
        measurement_summary["last_date"] = pd.to_datetime(measurement_summary["last_date"], format='mixed')

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter & Navigation")

# Site selection
site_options = sites_all[['site_id', 'site_name']].drop_duplicates()
site_dict = dict(zip(site_options['site_id'], site_options['site_name']))
selected_site_id = st.sidebar.selectbox(
    "Station auswählen",
    options=site_options['site_id'].tolist(),
    format_func=lambda x: f"{site_dict.get(x, 'Unbekannt')} (ID: {x})"
)

# Parameter selection (based on wq_raw)
if wq_raw is not None and "parameter" in wq_raw.columns:
    available_params = wq_raw['parameter'].unique().tolist()
    selected_parameter = st.sidebar.selectbox("Wasserqualität Parameter", options=available_params)
else:
    selected_parameter = None

# Date range selection
if wq_raw is not None and "timestamp" in wq_raw.columns:
    min_date = wq_raw["timestamp"].min().date()
    max_date = wq_raw["timestamp"].max().date()
    date_range = st.sidebar.date_input(
        "Zeitraum (Wasserqualität)",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = (None, None)

# --- MAIN UI ---
st.title("🌊 Elbe Monitoring Dashboard")
st.markdown("### Wasserqualität und Stahlkorrosion an Flussbauwerken")

tabs = st.tabs(["📊 Übersicht", "💧 Wasserqualität", "🏗️ Korrosion", "📋 Zusammenfassung"])

# 1. Tab: Übersicht
with tabs[0]:
    st.header("Messstationen")
    st.dataframe(sites_all, use_container_width=True, hide_index=True)

# 2. Tab: Wasserqualität
with tabs[1]:
    st.header(f"Zeitreihe: {selected_parameter}")
    
    if wq_raw is not None and selected_parameter:
        # Filter data
        mask = (
            (wq_raw["site_id"] == selected_site_id) &
            (wq_raw["parameter"] == selected_parameter)
        )
        
        # Apply date filter if valid
        if isinstance(date_range, tuple) and len(date_range) == 2:
            mask &= (wq_raw["timestamp"].dt.date >= date_range[0]) & (wq_raw["timestamp"].dt.date <= date_range[1])
            
        df_filtered = wq_raw.loc[mask].sort_values("timestamp")
        
        if not df_filtered.empty:
            unit = df_filtered['unit'].iloc[0] if 'unit' in df_filtered.columns else "Wert"
            fig = px.line(
                df_filtered, 
                x="timestamp", 
                y="value", 
                title=f"{selected_parameter} - Verlauf",
                labels={"value": f"{selected_parameter} ({unit})", "timestamp": "Zeitpunkt"},
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Rohdaten anzeigen"):
                st.dataframe(df_filtered, use_container_width=True)
        else:
            st.warning("Keine Daten für die gewählte Kombination aus Station, Parameter und Zeitraum gefunden.")
    else:
        st.info("Bitte wählen Sie eine Station und einen Parameter in der Sidebar aus.")

# 3. Tab: Korrosion
with tabs[2]:
    st.header("Wanddicken-Messungen")
    
    if corrosion_positions is not None:
        df_corr = corrosion_positions[corrosion_positions["site_id"] == selected_site_id]
        
        if not df_corr.empty:
            # Latest measurements
            latest_date = df_corr["measurement_date"].max()
            df_corr_latest = df_corr[df_corr["measurement_date"] == latest_date]
            
            st.subheader(f"Aktuelle Messung vom {latest_date.date()}")
            
            fig_corr = px.bar(
                df_corr_latest,
                x="position_name",
                y="actual_wall_thickness",
                title="Wanddicke pro Messposition",
                labels={"actual_wall_thickness": "Wanddicke (mm)", "position_name": "Position"},
                color="actual_wall_thickness",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            
            with st.expander("Alle Messungen an dieser Station"):
                st.dataframe(df_corr, use_container_width=True)
        else:
            st.warning(f"Keine Korrosionsdaten für Station ID {selected_site_id} ({site_dict.get(selected_site_id)}) gefunden.")
    else:
        st.error("Korrosionsdaten konnten nicht geladen werden.")

# 4. Tab: Zusammenfassung
with tabs[3]:
    st.header("Wasserqualität: Statistiken")
    if wq_summary is not None:
        st.dataframe(wq_summary, use_container_width=True, hide_index=True)
    else:
        st.error("Zusammenfassungsdaten konnten nicht geladen werden.")
