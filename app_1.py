
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import datetime as _dt

# ---------------------------------------------------------------------------
# Setup & Styling
# ---------------------------------------------------------------------------
DATA_DIR = Path("data")

st.set_page_config(
    page_title="Elbe Monitoring",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stat-box { background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 20px; }
    .stat-title { font-size: 14px; color: #6c757d; text-transform: uppercase; letter-spacing: 1px; }
    .stat-value { font-size: 28px; font-weight: bold; color: #212529; }
    .stat-trend { font-size: 14px; color: #28a745; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; border-radius: 4px 4px 0px 0px; padding: 0 20px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data Loading & Preprocessing
# ---------------------------------------------------------------------------

@st.cache_data
def load_data():
    data = {}
    
    # 1. wq_summary
    try:
        wq_sum = pd.read_csv(DATA_DIR / "wq_summary.csv", low_memory=False)
        data['wq_summary'] = wq_sum
        
        # Get Top 10 Parameters
        top_params = wq_sum.groupby('parameter')['n_observations'].sum().reset_index()
        top_params = top_params[top_params['n_observations'] > 50].sort_values('n_observations', ascending=False)
        data['top_10_params'] = top_params.head(10)['parameter'].tolist()
    except Exception:
        data['wq_summary'] = pd.DataFrame()
        data['top_10_params'] = []

    # 2. sites_leaf
    try:
        sites = pd.read_csv(DATA_DIR / "sites_leaf.csv", low_memory=False)
        sites['km_start_num'] = pd.to_numeric(sites['km_start'], errors='coerce')
        
        # Determine Clusters (Region)
        def get_region(km):
            if pd.isna(km): return "Unbekannt"
            if km < 200: return "Oberlauf"
            elif km < 400: return "Mittellauf"
            else: return "Unterlauf"
            
        sites['Region'] = sites['km_start_num'].apply(get_region)
        data['sites'] = sites
    except Exception:
        data['sites'] = pd.DataFrame()

    # 3. measurements_summary
    try:
        meas_sum = pd.read_csv(DATA_DIR / "measurement_summary.csv", low_memory=False)
        meas_sum['last_date'] = pd.to_datetime(meas_sum['last_date'], errors='coerce')
        
        # Status logic: Active if last measurement is >= 2015
        meas_sum['Status'] = meas_sum['last_date'].apply(
            lambda x: "Aktiv" if pd.notna(x) and x.year >= 2015 else "Inaktiv"
        )
        data['meas_summary'] = meas_sum
    except Exception:
        data['meas_summary'] = pd.DataFrame()

    # 4. Data Quality Matrix (internal)
    if not data['wq_summary'].empty:
        data['wq_matrix'] = data['wq_summary'].pivot(index='site_id', columns='parameter', values='n_observations').fillna(0)
    else:
        data['wq_matrix'] = pd.DataFrame()

    # wq_raw
    try:
        wq_raw = pd.read_csv(DATA_DIR / "wq_raw.csv", low_memory=False)
        wq_raw['timestamp'] = pd.to_datetime(wq_raw['timestamp'], errors='coerce')
        data['wq_raw'] = wq_raw.dropna(subset=['timestamp'])
    except Exception:
        data['wq_raw'] = pd.DataFrame()

    # corrosion_positions
    try:
        corr = pd.read_csv(DATA_DIR / "corrosion_positions.csv", low_memory=False)
        corr['measurement_date'] = pd.to_datetime(corr['measurement_date'], errors='coerce')
        corr['actual_wall_thickness'] = pd.to_numeric(corr['actual_wall_thickness'], errors='coerce')
        corr['planned_wall_thickness'] = pd.to_numeric(corr['planned_wall_thickness'], errors='coerce')
        data['corrosion'] = corr
    except Exception:
        data['corrosion'] = pd.DataFrame()

    return data

data = load_data()

# Helper to merge site info with meas_summary
if not data['sites'].empty and not data['meas_summary'].empty:
    sites_full = pd.merge(data['sites'], data['meas_summary'], on='site_id', how='left')
    sites_full['Status'] = sites_full['Status'].fillna("Inaktiv")
    sites_full['last_date'] = sites_full['last_date'].dt.date
else:
    sites_full = data['sites']

# ---------------------------------------------------------------------------
# App Layout & Tabs
# ---------------------------------------------------------------------------

tab_map, tab_wq, tab_corr, tab_sum = st.tabs([
    "🗺️ Stationsübersicht", 
    "📈 Wasserqualität", 
    "🔩 Korrosion", 
    "📊 Zusammenfassung"
])

# ── 🗺️ TAB 1: STATIONSÜBERSICHT ──────────────────────────────────────────────
with tab_map:
    st.header("Räumliche Übersicht der Messstationen")
    
    if sites_full.empty:
        st.warning("Keine Stationsdaten gefunden.")
    else:
        col1, col2 = st.columns([3, 2])
        
        valid_sites = sites_full.dropna(subset=['latitude', 'longitude']).copy()
        
        with col1:
            if not valid_sites.empty:
                # Add a column for hover info
                valid_sites['n_measurements'] = valid_sites['n_measurements'].fillna(0).astype(int)
                
                # Colors mapping
                color_map = {"Oberlauf": "#2ca02c", "Mittellauf": "#1f77b4", "Unterlauf": "#d62728", "Unbekannt": "#7f7f7f"}
                
                fig_map = px.scatter_mapbox(
                    valid_sites,
                    lat="latitude",
                    lon="longitude",
                    color="Region",
                    color_discrete_map=color_map,
                    hover_name="site_name",
                    hover_data={"site_id": True, "n_measurements": True, "Region": False, "latitude": False, "longitude": False},
                    zoom=5,
                    height=600,
                    mapbox_style="carto-positron",
                    title="Stationen nach Region"
                )
                fig_map.update_traces(marker=dict(size=12, opacity=0.8))
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("Keine Stationen mit gültigen Koordinaten.")
                
        with col2:
            st.subheader("Stationsliste")
            # Prepare table
            table_cols = ['site_id', 'site_name', 'Region', 'last_date', 'Status']
            available_cols = [c for c in table_cols if c in sites_full.columns]
            
            display_df = sites_full[available_cols].copy()
            
            # Allow sorting by Region or Date
            sort_by = st.selectbox("Sortieren nach:", ["Region", "Letztes Messdatum (last_date)", "site_id"])
            if sort_by == "Region":
                display_df = display_df.sort_values('Region')
            elif sort_by == "Letztes Messdatum (last_date)" and 'last_date' in display_df.columns:
                display_df = display_df.sort_values('last_date', ascending=False)
            else:
                display_df = display_df.sort_values('site_id')
                
            st.dataframe(display_df, use_container_width=True, height=500, hide_index=True)


# ── 📈 TAB 2: WASSERQUALITÄT ────────────────────────────────────────────────
with tab_wq:
    st.header("Time Series Explorer: Wasserqualität")
    
    if data['wq_raw'].empty or not data['top_10_params']:
        st.warning("Zu wenig Wasserqualitätsdaten oder Top-10-Parameter nicht identifizierbar.")
    else:
        # Sidebar WQ Filters
        st.sidebar.markdown("### 📈 WQ Filter")
        
        regions = sorted([r for r in sites_full['Region'].unique() if r != "Unbekannt"])
        selected_region = st.sidebar.selectbox("Region", ["Alle"] + regions)
        
        # Filter stations by region
        if selected_region != "Alle":
            region_sites = sites_full[sites_full['Region'] == selected_region]['site_id'].tolist()
            available_wq_sites = data['wq_raw'][data['wq_raw']['site_id'].isin(region_sites)]['site_name'].dropna().unique().tolist()
        else:
            available_wq_sites = data['wq_raw']['site_name'].dropna().unique().tolist()
            
        selected_station_name = st.sidebar.selectbox("Station", sorted(available_wq_sites))
        
        # Get site_id for the selected station name
        site_id_match = data['wq_raw'][data['wq_raw']['site_name'] == selected_station_name]['site_id'].iloc[0]
        
        # Parameter dropdown (Top 10 only)
        selected_param = st.sidebar.selectbox("Parameter (Top 10)", data['top_10_params'])
        
        # Date range
        min_d = data['wq_raw']['timestamp'].min().date()
        max_d = data['wq_raw']['timestamp'].max().date()
        selected_dates = st.sidebar.slider("Zeitraum", min_value=min_d, max_value=max_d, value=(min_d, max_d))
        
        # Data Filtering
        mask = (data['wq_raw']['site_id'] == site_id_match) & \
               (data['wq_raw']['parameter'] == selected_param) & \
               (data['wq_raw']['timestamp'].dt.date >= selected_dates[0]) & \
               (data['wq_raw']['timestamp'].dt.date <= selected_dates[1])
               
        wq_filtered = data['wq_raw'][mask].sort_values('timestamp')
        
        col_chart, col_stat = st.columns([3, 1])
        
        with col_chart:
            n_obs = len(wq_filtered)
            time_span = f"{selected_dates[0].year}–{selected_dates[1].year}"
            unit = wq_filtered['unit'].iloc[0] if n_obs > 0 and 'unit' in wq_filtered.columns and pd.notna(wq_filtered['unit'].iloc[0]) else ""
            
            title = f"{selected_station_name} – {selected_param} (n={n_obs} Messungen, {time_span})"
            
            if n_obs < 3:
                st.warning(f"⚠️ Nur {n_obs} Messungen im gewählten Zeitraum – wenig aussagekräftig.")
            
            if n_obs > 0:
                # Format X-Axis to YYYY-MM logic by resample or formatting in Plotly
                fig_line = px.line(
                    wq_filtered, 
                    x="timestamp", 
                    y="value", 
                    title=title,
                    labels={"timestamp": "Datum", "value": f"Messwert ({unit})"},
                    markers=n_obs < 100
                )
                fig_line.update_xaxes(dtick="M12", tickformat="%Y-%m")
                fig_line.update_traces(line_color="#1f77b4")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Keine Daten für diese Kombination.")
                
        with col_stat:
            st.markdown("### Statistik")
            # Fetch from wq_summary
            stat_row = data['wq_summary'][
                (data['wq_summary']['site_id'] == site_id_match) & 
                (data['wq_summary']['parameter'] == selected_param)
            ]
            
            if not stat_row.empty:
                mean_v = stat_row['mean_value'].values[0]
                std_v = stat_row['std_value'].values[0]
                min_v = stat_row['min_value'].values[0]
                max_v = stat_row['max_value'].values[0]
                
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-title">Mean</div>
                    <div class="stat-value">{mean_v:.2f} <span style="font-size:14px">{unit}</span></div>
                </div>
                <div class="stat-box">
                    <div class="stat-title">Min / Max</div>
                    <div class="stat-value" style="font-size:20px">{min_v:.2f} / {max_v:.2f}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-title">Std Dev</div>
                    <div class="stat-value" style="font-size:20px">±{std_v:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write("Keine Statistik in summary verfügbar.")


# ── 🔩 TAB 3: KORROSION ──────────────────────────────────────────────────────
with tab_corr:
    st.header("Steel Wall Monitoring")
    
    if data['corrosion'].empty:
        st.warning("Keine Korrosionsdaten verfügbar.")
    else:
        st.sidebar.markdown("### 🔩 Korrosion Filter")
        
        # Available stations in corrosion data
        corr_sites = data['corrosion']['site_id'].dropna().unique()
        
        # Try to map to names if possible
        if not sites_full.empty:
            corr_site_names = sites_full[sites_full['site_id'].isin(corr_sites)][['site_id', 'site_name']]
            # Create a mapping dictionary for the selectbox
            site_dict = {row['site_id']: f"{row['site_name']} ({row['site_id']})" if pd.notna(row['site_name']) else str(row['site_id']) 
                         for _, row in corr_site_names.iterrows()}
        else:
            site_dict = {s: str(s) for s in corr_sites}
            
        selected_corr_site_id = st.sidebar.selectbox(
            "Station (Korrosion)", 
            options=list(site_dict.keys()), 
            format_func=lambda x: site_dict.get(x, str(x))
        )
        
        # Filter data for site
        site_corr = data['corrosion'][data['corrosion']['site_id'] == selected_corr_site_id].copy()
        
        if not site_corr.empty:
            # Get latest measurement
            latest_meas_date = site_corr['measurement_date'].max()
            latest_data = site_corr[site_corr['measurement_date'] == latest_meas_date].copy()
            
            # Top text
            st.markdown(f"**Letzte Messung:** {latest_meas_date.strftime('%Y-%m-%d')} | **Station:** {site_dict.get(selected_corr_site_id, selected_corr_site_id)}")
            
            # Calculate % Remaining
            latest_data['pct_remaining'] = (latest_data['actual_wall_thickness'] / latest_data['planned_wall_thickness']) * 100
            
            # Setup Bar Chart Data
            # Melting the dataframe to have planned vs actual side by side
            plot_data = pd.melt(
                latest_data, 
                id_vars=['position_name', 'pct_remaining'], 
                value_vars=['planned_wall_thickness', 'actual_wall_thickness'],
                var_name='Thickness Type', 
                value_name='Thickness (mm)'
            )
            
            # Map names for legend
            plot_data['Thickness Type'] = plot_data['Thickness Type'].map({
                'planned_wall_thickness': 'Planned',
                'actual_wall_thickness': 'Actual'
            })

            # Custom colors for Actual based on % remaining
            colors = []
            for _, row in latest_data.iterrows():
                # Planned is gray
                # Actual is green if >= 80%, red if < 80%
                c = "green" if row['pct_remaining'] >= 80 else "red"
                colors.append(c)

            fig_bar = go.Figure()
            
            # Add Planned bars (Gray)
            planned = latest_data['planned_wall_thickness']
            fig_bar.add_trace(go.Bar(
                y=latest_data['position_name'].astype(str),
                x=planned,
                name='Planned (mm)',
                orientation='h',
                marker=dict(color='lightgray')
            ))
            
            # Add Actual bars (Colored)
            actual = latest_data['actual_wall_thickness']
            fig_bar.add_trace(go.Bar(
                y=latest_data['position_name'].astype(str),
                x=actual,
                name='Actual (mm)',
                orientation='h',
                marker=dict(color=[('green' if p >= 80 else 'red') for p in latest_data['pct_remaining']])
            ))
            
            fig_bar.update_layout(
                barmode='group',
                title="Wanddicke: Geplant vs. Aktuell",
                xaxis_title="Wanddicke (mm)",
                yaxis_title="Position",
                height=max(400, len(latest_data) * 30),
                yaxis={'categoryorder':'category descending'}
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Table Below
            st.subheader("Detailwerte der letzten Messung")
            table_data = latest_data[['position_id', 'position_name', 'planned_wall_thickness', 'actual_wall_thickness', 'pct_remaining']].copy()
            table_data = table_data.rename(columns={
                'planned_wall_thickness': 'Planned (mm)',
                'actual_wall_thickness': 'Actual (mm)',
                'pct_remaining': '% Remaining'
            })
            table_data['% Remaining'] = table_data['% Remaining'].round(1)
            table_data['⚠️ Alarm'] = table_data['% Remaining'].apply(lambda x: "🚨 KRITISCH" if x < 50 else ("⚠️ Warnung" if x < 80 else "✅ OK"))
            
            st.dataframe(table_data, use_container_width=True, hide_index=True)


# ── 📊 TAB 4: ZUSAMMENFASSUNG ────────────────────────────────────────────────
with tab_sum:
    st.header("Datenqualität & Überblick")
    
    # Infobox
    st.markdown(f"""
    <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; border-left: 5px solid #0056b3; margin-bottom: 20px;">
        <strong>Datensatz Metadaten:</strong><br>
        Zeitspanne: 1954–2023<br>
        Insgesamt: {len(sites_full)} Stationen | 
        {len(data['wq_raw']) if not data['wq_raw'].empty else 0} WQ-Messungen | 
        {len(data['corrosion']) if not data['corrosion'].empty else 0} Korrosionsmessungen
    </div>
    """, unsafe_allow_html=True)
    
    # Card-like table
    if not sites_full.empty:
        summary_table = sites_full[['site_id', 'site_name', 'Region', 'Status']].copy()
        
        # Add WQ and Corrosion info
        if not data['wq_matrix'].empty:
            # Count how many parameters have > 0 observations for each site
            wq_counts = (data['wq_matrix'] > 0).sum(axis=1)
            wq_obs_total = data['wq_matrix'].sum(axis=1)
            
            summary_table['Wassergüte'] = summary_table['site_id'].map(wq_obs_total).fillna(0).astype(int)
        else:
            summary_table['Wassergüte'] = 0
            
        if not data['corrosion'].empty:
            corr_counts = data['corrosion'].groupby('site_id').size()
            summary_table['Korrosion'] = summary_table['site_id'].map(corr_counts).fillna(0).astype(int)
        else:
            summary_table['Korrosion'] = 0
            
        # Format columns with icons
        def format_wq(val):
            if val > 1000: return f"🟢 Sehr gut ({val} Messungen)"
            elif val > 0: return f"🟡 Ausreichend ({val} Messungen)"
            else: return "⚪ Keine Daten"
            
        def format_corr(val):
            if val > 100: return f"🟢 Sehr gut ({val} Messungen)"
            elif val > 0: return f"🟡 Ausreichend ({val} Messungen)"
            else: return "⚪ Keine Daten"
            
        summary_table['Wassergüte Status'] = summary_table['Wassergüte'].apply(format_wq)
        summary_table['Korrosion Status'] = summary_table['Korrosion'].apply(format_corr)
        
        display_sum = summary_table[['site_id', 'site_name', 'Region', 'Wassergüte Status', 'Korrosion Status', 'Status']]
        
        st.dataframe(display_sum, use_container_width=True, height=600, hide_index=True)



