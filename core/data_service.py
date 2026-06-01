import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Dict, Any

DATA_PATH = Path("data2/Airline Dataset Updated - v2.csv")

@st.cache_data
def _load_base_data() -> pd.DataFrame:
    """
    Loads the baseline airline dataset and handles mixed date parsing.
    Exploratory analysis found mixed date formats, so format='mixed' is critical.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Aviation dataset not found at {DATA_PATH.resolve()}")
    
    # Load dataset
    df = pd.read_csv(DATA_PATH)
    
    # Parse dates with the 'mixed' format as identified during initial profiling
    df['Departure Date'] = pd.to_datetime(df['Departure Date'], format='mixed')
    
    # Clean up whitespace in string columns
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            
    return df

def get_data() -> pd.DataFrame:
    """
    Retrieves the active dataframe from Streamlit's Session State.
    If the session state is empty, loads the base CSV data and initializes it.
    """
    if 'airline_data' not in st.session_state:
        try:
            st.session_state['airline_data'] = _load_base_data()
        except Exception as e:
            st.error(f"⚠️ Critical error loading dataset: {e}")
            st.session_state['airline_data'] = pd.DataFrame()
            
    return st.session_state['airline_data']

def add_booking(booking_dict: Dict[str, Any]) -> None:
    """
    Appends a new passenger booking record to the active dataset in Session State.
    Validates types and ensures date formats are standard before merging.
    """
    df = get_data()
    
    # Convert inputs to appropriate types
    new_row = pd.DataFrame([{
        'Passenger ID': str(booking_dict['Passenger ID']),
        'First Name': str(booking_dict['First Name']),
        'Last Name': str(booking_dict['Last Name']),
        'Gender': str(booking_dict['Gender']),
        'Age': int(booking_dict['Age']),
        'Nationality': str(booking_dict['Nationality']),
        'Airport Name': str(booking_dict['Airport Name']),
        'Airport Country Code': str(booking_dict['Airport Country Code']),
        'Country Name': str(booking_dict['Country Name']),
        'Airport Continent': str(booking_dict['Airport Continent']),
        'Continents': str(booking_dict['Continents']),
        'Departure Date': pd.to_datetime(booking_dict['Departure Date']),
        'Arrival Airport': str(booking_dict['Arrival Airport']),
        'Pilot Name': str(booking_dict['Pilot Name']),
        'Flight Status': str(booking_dict['Flight Status'])
    }])
    
    # Append and update state
    updated_df = pd.concat([df, new_row], ignore_index=True)
    st.session_state['airline_data'] = updated_df
