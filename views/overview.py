import streamlit as st
import plotly.express as px
import pandas as pd
from core.analytics import calculate_kpis
from components.ui import kpi_card

def render_overview(df: pd.DataFrame) -> None:
    """
    Renders the executive dashboard tab featuring high-level metrics,
    global geographical maps, dispatch health breakdowns, and busiest network nodes.
    """
    st.subheader("📊 Executive Operations & Booking Overview")
    st.markdown("A real-time administrative summary of the global flight dispatch network, passenger demographics, and scheduled pipelines.")
    
    # 1. Fetch KPI math
    kpis = calculate_kpis(df)
    
    # 2. Render Cards in a 5-column layout
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        kpi_card(
            title="Total Bookings", 
            value=f"{kpis['total_bookings']:,}", 
            subtitle="Passenger flight records"
        )
    with col2:
        kpi_card(
            title="Global Footprint", 
            value=f"{kpis['unique_countries']:,} Countries", 
            subtitle=f"{kpis['unique_airports']:,} Unique Airports"
        )
    with col3:
        kpi_card(
            title="Active Flight Crew", 
            value=f"{kpis['unique_pilots']:,} Pilots", 
            subtitle="Assigned scheduled duties"
        )
    with col4:
        status_cancel = "🚨 High Distress" if kpis['cancel_rate'] > 20 else ("⚠️ Normal Warning" if kpis['cancel_rate'] > 5 else "✅ Stable")
        kpi_card(
            title="Cancellation Rate", 
            value=f"{kpis['cancel_rate']:.1f}%", 
            subtitle=status_cancel
        )
    with col5:
        status_ontime = "🟢 Healthy Dispatch" if kpis['on_time_rate'] > 60 else "⚠️ Slow Dispatch"
        kpi_card(
            title="On-Time Rate", 
            value=f"{kpis['on_time_rate']:.1f}%", 
            subtitle=status_ontime
        )
        
    st.markdown('<div class="section-header">🌍 Global Network & Dispatch Breakdown</div>', unsafe_allow_html=True)
    
    # 3. Interactive map and status pie chart
    row1_col1, row1_col2 = st.columns([5, 3])
    
    with row1_col1:
        st.markdown("#### Global Booking Density by Country")
        # Precompute country frequencies
        country_counts = df['Country Name'].value_counts().reset_index()
        country_counts.columns = ['Country Name', 'Bookings']
        
        # Draw Plotly Choropleth Map
        fig_map = px.choropleth(
            country_counts,
            locations="Country Name",
            locationmode="country names",
            color="Bookings",
            hover_name="Country Name",
            color_continuous_scale=px.colors.sequential.Blues,
            height=420
        )
        
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_colorbar=dict(title="Bookings", thickness=15, len=0.8)
        )
        st.plotly_chart(fig_map, use_container_width=True)
        
    with row1_col2:
        st.markdown("#### Flight Operations Dispatch")
        # Precompute flight status frequencies
        status_counts = df['Flight Status'].value_counts().reset_index()
        status_counts.columns = ['Flight Status', 'Count']
        
        # Donut Chart
        fig_donut = px.pie(
            status_counts,
            values="Count",
            names="Flight Status",
            hole=0.45,
            color="Flight Status",
            color_discrete_map={
                'On Time': '#10b981',    # Emerald Green
                'Delayed': '#f59e0b',    # Amber Orange
                'Cancelled': '#ef4444'   # Rose Red
            }
        )
        
        fig_donut.update_layout(
            margin=dict(l=0, r=0, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        
    st.markdown('<div class="section-header">✈️ Network Hubs & Passenger Origins</div>', unsafe_allow_html=True)
    
    # 4. Top Hubs and Nationalities
    row2_col1, row2_col2 = st.columns(2)
    
    with row2_col1:
        st.markdown("#### Busiest Origin Airports (Top 10)")
        airport_counts = df['Airport Name'].value_counts().head(10).reset_index()
        airport_counts.columns = ['Airport Name', 'Departures']
        
        fig_airports = px.bar(
            airport_counts,
            x="Departures",
            y="Airport Name",
            orientation='h',
            color="Departures",
            color_continuous_scale=px.colors.sequential.Cividis
        )
        fig_airports.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_airports, use_container_width=True)
        
    with row2_col2:
        st.markdown("#### Top Passenger Nationalities (Top 10)")
        nationality_counts = df['Nationality'].value_counts().head(10).reset_index()
        nationality_counts.columns = ['Nationality', 'Bookings']
        
        fig_nat = px.bar(
            nationality_counts,
            x="Bookings",
            y="Nationality",
            orientation='h',
            color="Bookings",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig_nat.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_nat, use_container_width=True)
