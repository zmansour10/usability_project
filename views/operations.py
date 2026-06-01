import streamlit as st
import plotly.express as px
import pandas as pd
from components.ui import kpi_card

def render_operations(df: pd.DataFrame) -> None:
    """
    Renders the operational and schedule management dashboard,
    displaying volume timelines, regional performance, and flight crew metrics.
    """
    st.subheader("✈️ Flight Dispatch & Operations Management")
    st.markdown("Administrative metrics on schedules, timeline distributions, continental performance, and flight crew assignments.")
    
    # Pre-parse dates to be absolutely sure
    df['MonthName'] = df['Departure Date'].dt.strftime('%B')
    df['MonthNum'] = df['Departure Date'].dt.month
    
    # 1. Operational KPIs
    busiest_month_num = df['MonthNum'].value_counts().idxmax()
    busiest_month_name = pd.to_datetime(f"2022-{busiest_month_num}-01").strftime('%B')
    busiest_month_count = df['MonthNum'].value_counts().max()
    
    pilot_count = df['Pilot Name'].nunique()
    multi_flight_pilots = (df['Pilot Name'].value_counts() > 1).sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Busiest Month", f"{busiest_month_name}", f"{busiest_month_count:,} bookings recorded")
    with col2:
        kpi_card("Scheduled Pilots", f"{pilot_count:,} Crew", "Unique active flight dispatchers")
    with col3:
        kpi_card("Busiest Continents", "North America", f"{len(df[df['Continents'] == 'North America']):,} flights dispatched")
    with col4:
        kpi_card("Crew Double-Duty", f"{multi_flight_pilots} Pilots", "Crew assigned to >1 flights")

    st.markdown('<div class="section-header">📅 Timeline Dispatch Activity (2022)</div>', unsafe_allow_html=True)

    # 2. Monthly Timeline
    monthly_data = df.groupby(['MonthNum', 'MonthName', 'Flight Status']).size().reset_index(name='Flights')
    monthly_data = monthly_data.sort_values(by='MonthNum')
    
    fig_line = px.bar(
        monthly_data,
        x="MonthName",
        y="Flights",
        color="Flight Status",
        barmode="group",
        color_discrete_map={
            'On Time': '#10b981',
            'Delayed': '#f59e0b',
            'Cancelled': '#ef4444'
        },
        title="Monthly Dispatch Volume by Operations Outcome"
    )
    
    fig_line.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Month (2022)",
        yaxis_title="Dispatched Flights"
    )
    st.plotly_chart(fig_line, use_container_width=True)

    st.markdown('<div class="section-header">🗺️ Regional & Crew Operations</div>', unsafe_allow_html=True)
    
    # 3. Regional and Crew Analysis Row
    row2_col1, row2_col2 = st.columns([4, 3])
    
    with row2_col1:
        st.markdown("#### Continental Operations Breakdown")
        st.markdown("Compares flight volume and operations outcomes across all world regions.")
        
        continent_counts = df.groupby(['Continents', 'Flight Status']).size().reset_index(name='Volume')
        
        fig_continent = px.bar(
            continent_counts,
            x="Continents",
            y="Volume",
            color="Flight Status",
            color_discrete_map={
                'On Time': '#10b981',
                'Delayed': '#f59e0b',
                'Cancelled': '#ef4444'
            },
            title="Flight Dispatch Status by Continent"
        )
        
        fig_continent.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            barmode="stack",
            xaxis_title="Continent",
            yaxis_title="Total Flights"
        )
        st.plotly_chart(fig_continent, use_container_width=True)
        
    with row2_col2:
        st.markdown("#### Crew Duty Assignments (Busiest Pilots)")
        st.markdown("Lists pilots with double duty (assigned multiple flights in 2022) and their dispatch results.")
        
        # Busiest pilots in data
        pilot_workloads = df['Pilot Name'].value_counts()
        busiest_pilots = pilot_workloads[pilot_workloads > 1].index.tolist()
        
        if busiest_pilots:
            busy_df = df[df['Pilot Name'].isin(busiest_pilots)].copy()
            # Summary of pilot and status
            pilot_summary = busy_df.groupby(['Pilot Name', 'Flight Status']).size().unstack(fill_value=0).reset_index()
            # Rename columns
            for col in ['Cancelled', 'Delayed', 'On Time']:
                if col not in pilot_summary.columns:
                    pilot_summary[col] = 0
            pilot_summary['Total Flights'] = pilot_summary['Cancelled'] + pilot_summary['Delayed'] + pilot_summary['On Time']
            pilot_summary = pilot_summary.sort_values(by='Total Flights', ascending=False)
            
            # Display custom table
            st.dataframe(
                pilot_summary[['Pilot Name', 'Total Flights', 'On Time', 'Delayed', 'Cancelled']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ All active flight crew members are scheduled for exactly one flight in the filtered dataset.")
