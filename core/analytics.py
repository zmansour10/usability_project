import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculates top-level operational and passenger metrics from the dataframe."""
    total_bookings = len(df)
    if total_bookings == 0:
        return {
            'total_bookings': 0, 'unique_passengers': 0, 'unique_airports': 0,
            'unique_countries': 0, 'unique_pilots': 0,
            'cancel_rate': 0.0, 'delay_rate': 0.0, 'on_time_rate': 0.0
        }
        
    unique_passengers = df['Passenger ID'].nunique()
    unique_airports = df['Airport Name'].nunique()
    unique_countries = df['Country Name'].nunique()
    unique_pilots = df['Pilot Name'].nunique()
    
    status_counts = df['Flight Status'].value_counts()
    cancel_count = status_counts.get('Cancelled', 0)
    delay_count = status_counts.get('Delayed', 0)
    on_time_count = status_counts.get('On Time', 0)
    
    cancel_rate = (cancel_count / total_bookings) * 100
    delay_rate = (delay_count / total_bookings) * 100
    on_time_rate = (on_time_count / total_bookings) * 100
    
    return {
        'total_bookings': total_bookings,
        'unique_passengers': unique_passengers,
        'unique_airports': unique_airports,
        'unique_countries': unique_countries,
        'unique_pilots': unique_pilots,
        'cancel_rate': cancel_rate,
        'delay_rate': delay_rate,
        'on_time_rate': on_time_rate
    }

def detect_anomalies(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Scans the dataset for statistical anomalies and operational outliers:
    1. Operational Spikes: Days with flight volumes > 2.5 standard deviations above mean.
    2. High-Distress Days: Days with cancellation rates above 45%.
    3. Overworked Pilots: Pilots with multiple assigned flights in the dataset.
    4. Demographic Outliers: Children aged <= 3 flying, or seniors aged >= 88.
    """
    anomalies = {}
    
    if df.empty or 'Departure Date' not in df.columns:
        return {'traffic_spikes': pd.DataFrame(), 'high_distress_days': pd.DataFrame(), 
                'busy_pilots': pd.DataFrame(), 'demographic_outliers': pd.DataFrame()}

    # 1. Traffic Spikes by Date
    daily_vol = df.groupby(df['Departure Date'].dt.date).size()
    if not daily_vol.empty:
        mean_vol = daily_vol.mean()
        std_vol = daily_vol.std()
        threshold = mean_vol + 2.5 * std_vol
        spikes = daily_vol[daily_vol > threshold].reset_index()
        spikes.columns = ['Date', 'Flight Count']
        spikes['Deviation (σ)'] = ((spikes['Flight Count'] - mean_vol) / std_vol).round(2)
        anomalies['traffic_spikes'] = spikes.sort_values(by='Flight Count', ascending=False)
    else:
        anomalies['traffic_spikes'] = pd.DataFrame()

    # 2. High-Distress Days (cancellation rate > 45% with at least 5 flights)
    daily_status = df.groupby([df['Departure Date'].dt.date, 'Flight Status']).size().unstack(fill_value=0)
    if not daily_status.empty:
        daily_status['Total'] = daily_status.sum(axis=1)
        # Filter for days with meaningful activity
        daily_status = daily_status[daily_status['Total'] >= 5]
        if 'Cancelled' in daily_status.columns:
            daily_status['Cancel Rate (%)'] = (daily_status['Cancelled'] / daily_status['Total'] * 100).round(1)
            distress = daily_status[daily_status['Cancel Rate (%)'] > 45.0].reset_index()
            distress.rename(columns={'Departure Date': 'Date'}, inplace=True)
            anomalies['high_distress_days'] = distress[['Date', 'Total', 'Cancelled', 'Cancel Rate (%)']].sort_values(by='Cancel Rate (%)', ascending=False)
        else:
            anomalies['high_distress_days'] = pd.DataFrame()
    else:
        anomalies['high_distress_days'] = pd.DataFrame()

    # 3. Busy Pilots (Pilots with more than 1 flight)
    pilot_counts = df['Pilot Name'].value_counts()
    busy = pilot_counts[pilot_counts > 1].reset_index()
    busy.columns = ['Pilot Name', 'Assigned Flights']
    anomalies['busy_pilots'] = busy
    
    # 4. Demographic Outliers (Ages <= 3 or >= 88)
    demo = df[(df['Age'] <= 3) | (df['Age'] >= 88)].copy()
    demo['Age Category'] = demo['Age'].apply(lambda x: 'Infant/Toddler (≤3)' if x <= 3 else 'Extreme Senior (≥88)')
    anomalies['demographic_outliers'] = demo[['Passenger ID', 'First Name', 'Last Name', 'Age', 'Nationality', 'Airport Name', 'Flight Status', 'Age Category']].head(100)

    return anomalies

def generate_heuristic_insights(df: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Generates intelligent business observations and action-oriented airline recommendations
    based on the current filtered or total airline dataset.
    """
    if df.empty:
        return []
        
    kpis = calculate_kpis(df)
    insights = []
    
    # Insight 1: Global Footprint
    top_countries = df['Country Name'].value_counts().head(3)
    countries_str = ", ".join([f"{c} ({v} flights)" for c, v in top_countries.items()])
    insights.append({
        'category': 'Global Activity',
        'title': 'Operational Hotspots',
        'type': 'info',
        'description': f"AeroSight has identified that the airport network spans {kpis['unique_countries']} countries. "
                       f"The busiest aviation clusters are located in: **{countries_str}**."
    })
    
    # Insight 2: Operation Health & Cancellation Warnings
    cancel_pct = kpis['cancel_rate']
    if cancel_pct > 30:
        insights.append({
            'category': 'Operations Health',
            'title': 'Abnormal Distress Levels Detected',
            'type': 'warning',
            'description': f"The system detected a booking cancellation rate of **{cancel_pct:.2f}%**, which far exceeds industry benchmarks of 1-3%. "
                           f"This is an indicator of severe operational disruption or—statistically—a highly randomized synthetic dataset. "
                           f"Airlines should run structural stress tests on schedule buffer times."
        })
    else:
        insights.append({
            'category': 'Operations Health',
            'title': 'Operational Health Within Parameters',
            'type': 'success',
            'description': f"Cancellations are sitting stable at **{cancel_pct:.2f}%**. The flight dispatch pipeline is running efficiently."
        })
        
    # Insight 3: Demographics & Age Analysis
    df_kids = df[df['Age'] <= 12]
    df_seniors = df[df['Age'] >= 61]
    kids_pct = (len(df_kids) / len(df)) * 100
    seniors_pct = (len(df_seniors) / len(df)) * 100
    
    dominant_demographic = "Adults (19-60)"
    if kids_pct > 30:
        dominant_demographic = "Children (Family-centric)"
    elif seniors_pct > 30:
        dominant_demographic = "Seniors (Leisure-centric)"
        
    insights.append({
        'category': 'Passenger Profiling',
        'title': f"Market Segment: {dominant_demographic}",
        'type': 'info',
        'description': f"Ages cover 1 to 90 years. Children (0-12) make up **{kids_pct:.1f}%** and seniors (61-90) represent **{seniors_pct:.1f}%** of bookings. "
                       f"Airlines are advised to tailor in-flight amenities: increase family entertainment if children are high, and customize assistance/comfort if seniors are dominant."
    })
    
    # Insight 4: Peak Booking Seasonality
    df['MonthNum'] = df['Departure Date'].dt.month
    monthly_vols = df['MonthNum'].value_counts()
    if not monthly_vols.empty:
        peak_month_num = monthly_vols.idxmax()
        peak_month_name = pd.to_datetime(f"2022-{peak_month_num}-01").strftime('%B')
        peak_volume = monthly_vols.max()
        insights.append({
            'category': 'Seasonality Analysis',
            'title': f"Busiest Dispatch Cycle: {peak_month_name}",
            'type': 'info',
            'description': f"Flight dispatch volumes peaked in **{peak_month_name}** with **{peak_volume}** recorded passenger bookings. "
                           f"Dynamic pricing models should exploit this peak, while airport staff scheduling should increase by 10-15% during this month to prevent terminal queues."
        })
        
    return insights
