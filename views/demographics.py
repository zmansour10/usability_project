import streamlit as st
import plotly.express as px
import pandas as pd
from components.ui import kpi_card

def render_demographics(df: pd.DataFrame) -> None:
    """
    Renders the passenger demographics and marketing profiling tab,
    providing in-depth segmentation on age cohorts, genders, and nationalities.
    """
    st.subheader("👥 Passenger Demographics & Market Segments")
    st.markdown("Detailed intelligence on target consumer groups, age distributions, gender balance, and geographical travel patterns.")
    
    # 1. Demographics Overview Stats
    mean_age = df['Age'].mean()
    median_age = df['Age'].median()
    female_pct = (len(df[df['Gender'] == 'Female']) / len(df)) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Mean Passenger Age", f"{mean_age:.1f} Yrs", "Average age across bookings")
    with col2:
        kpi_card("Median Age", f"{int(median_age)} Yrs", "50th percentile of passengers")
    with col3:
        kpi_card("Gender Diversity", f"{female_pct:.1f}% Female", f"{100-female_pct:.1f}% Male passenger split")
    with col4:
        international_count = (df['Nationality'].str.lower() != df['Country Name'].str.lower()).sum()
        intl_pct = (international_count / len(df)) * 100
        kpi_card("Int'l Bookings", f"{intl_pct:.1f}% Cross-Border", f"{international_count:,} out-of-country departures")

    st.markdown('<div class="section-header">🎂 Age Profile & Consumer Cohorts</div>', unsafe_allow_html=True)

    # 2. Age Histogram & Cohorts Row
    row1_col1, row1_col2 = st.columns([5, 3])
    
    with row1_col1:
        st.markdown("#### Passenger Age Density")
        bin_size = st.slider("Select Histogram Bin Size:", min_value=1, max_value=10, value=5, step=1)
        
        fig_hist = px.histogram(
            df,
            x="Age",
            color="Gender",
            nbins=int(90 / bin_size),
            color_discrete_sequence=['#3b82f6', '#ec4899'], # Blue and Pink
            marginal="box",
            opacity=0.8,
            title="Age Frequency Distribution by Gender"
        )
        fig_hist.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Passenger Age",
            yaxis_title="Count"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with row1_col2:
        st.markdown("#### Consumer Age Segmentations")
        # Define age cohorts
        df['Age Cohort'] = pd.cut(
            df['Age'], 
            bins=[0, 12, 18, 60, 90], 
            labels=['Child (0-12)', 'Youth (13-18)', 'Adult (19-60)', 'Senior (61-90)']
        )
        cohort_counts = df['Age Cohort'].value_counts().reset_index()
        cohort_counts.columns = ['Age Cohort', 'Count']
        
        fig_cohort = px.bar(
            cohort_counts,
            x="Age Cohort",
            y="Count",
            color="Age Cohort",
            color_discrete_sequence=px.colors.qualitative.Prism,
            title="Bookings by Target Cohort"
        )
        fig_cohort.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        st.plotly_chart(fig_cohort, use_container_width=True)

    st.markdown('<div class="section-header">🔀 Demographic Correlations & Travel Flow</div>', unsafe_allow_html=True)
    
    # 3. Correlations and flows
    row2_col1, row2_col2 = st.columns(2)
    
    with row2_col1:
        st.markdown("#### Are Older Passengers Correlated with Delays?")
        fig_box = px.box(
            df,
            x="Flight Status",
            y="Age",
            color="Flight Status",
            color_discrete_map={
                'On Time': '#10b981',
                'Delayed': '#f59e0b',
                'Cancelled': '#ef4444'
            },
            title="Passenger Age Distribution vs. Flight Status"
        )
        fig_box.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
    with row2_col2:
        st.markdown("#### Cross-Border Booking Matrix")
        st.markdown("Examines the flow of passenger nationality against airport country location to map cross-border flights.")
        
        # Calculate cross tab of top 10 nationalities vs top 10 country names
        top_nats = df['Nationality'].value_counts().head(8).index
        top_countries = df['Country Name'].value_counts().head(8).index
        
        matrix_df = df[df['Nationality'].isin(top_nats) & df['Country Name'].isin(top_countries)].copy()
        
        crosstab = pd.crosstab(
            matrix_df['Nationality'], 
            matrix_df['Country Name']
        )
        
        fig_heat = px.imshow(
            crosstab,
            labels=dict(x="Airport Country", y="Passenger Nationality", color="Bookings"),
            color_continuous_scale="Purples",
            title="Demographic Departure Matrix (Top 8 Countries)"
        )
        fig_heat.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_heat, use_container_width=True)
