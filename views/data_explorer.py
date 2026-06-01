import streamlit as st
import pandas as pd
import random
import string
from core.data_service import add_booking

def render_data_explorer(df: pd.DataFrame) -> None:
    """
    Renders the data query, filtering, CSV exporter, and interactive
    Flight booking simulator. Includes automated relationship auto-filling.
    """
    st.subheader("🔍 Passenger Log Explorer & Booking Simulator")
    st.markdown("Search across bookings, export datasets, and simulate live passenger bookings with automatic relationship mapping.")
    
    tab_search, tab_simulator = st.tabs(["🔎 Passenger Log Explorer", "🎫 Live Booking Simulator"])
    
    # ──── TAB 1: PASSENGER SEARCH ──────────────────────────────────────────
    with tab_search:
        st.markdown("#### Dynamic Query Panel")
        
        # Search criteria
        col_search, col_status = st.columns([3, 1])
        with col_search:
            search_query = st.text_input(
                "Search Passenger Name, Pilot, Airport, or Nationality:", 
                placeholder="Type to filter bookings (e.g., 'Edithe', 'Japan', 'Grenoble')..."
            )
        with col_status:
            status_filter = st.selectbox(
                "Filter Status:", 
                ["All Statuses", "On Time", "Delayed", "Cancelled"]
            )
            
        # Filter dataframe
        filtered_df = df.copy()
        
        if status_filter != "All Statuses":
            filtered_df = filtered_df[filtered_df['Flight Status'] == status_filter]
            
        if search_query:
            q = search_query.lower()
            mask = (
                filtered_df['First Name'].str.lower().str.contains(q) |
                filtered_df['Last Name'].str.lower().str.contains(q) |
                filtered_df['Pilot Name'].str.lower().str.contains(q) |
                filtered_df['Airport Name'].str.lower().str.contains(q) |
                filtered_df['Nationality'].str.lower().str.contains(q) |
                filtered_df['Passenger ID'].str.lower().str.contains(q)
            )
            filtered_df = filtered_df[mask]
            
        st.markdown(f"**Found {len(filtered_df):,} bookings matching criteria**")
        
        # Custom Pagination for massive performance
        page_size = 15
        total_rows = len(filtered_df)
        
        if total_rows > 0:
            num_pages = max(1, (total_rows - 1) // page_size + 1)
            page_num = st.number_input(f"Page (1-{num_pages}):", min_value=1, max_value=num_pages, value=1, step=1)
            
            start_idx = (page_num - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
            
            # Format Departure Date for display
            display_df = filtered_df.iloc[start_idx:end_idx].copy()
            display_df['Departure Date'] = display_df['Departure Date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                display_df[[
                    'Passenger ID', 'First Name', 'Last Name', 'Gender', 'Age', 
                    'Nationality', 'Airport Name', 'Arrival Airport', 'Country Name', 
                    'Departure Date', 'Pilot Name', 'Flight Status'
                ]],
                use_container_width=True,
                hide_index=True
            )
            
            # Download filtered data
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Active Query to CSV",
                data=csv_data,
                file_name="aerosight_flight_query.csv",
                mime="text/csv"
            )
        else:
            st.info("ℹ️ No records found matching the specified query criteria.")
            
    # ──── TAB 2: LIVE BOOKING SIMULATOR ────────────────────────────────────
    with tab_simulator:
        st.markdown("#### Simulate New Passenger Booking")
        st.markdown(
            "Add a simulated reservation to the active environment. To preserve geographical and relational "
            "database integrity, **AeroSight automatically infers and populates** the destination, "
            "country code, country name, and continent boundaries based on the selected airport."
        )
        
        # Retrieve unique selections for drop-downs
        unique_airports = sorted(df['Airport Name'].dropna().unique().tolist())
        unique_nationalities = sorted(df['Nationality'].dropna().unique().tolist())
        
        # Form
        with st.form("booking_form", clear_on_submit=True):
            col_first, col_last = st.columns(2)
            with col_first:
                first_name = st.text_input("First Name (required):").strip()
            with col_last:
                last_name = st.text_input("Last Name (required):").strip()
                
            col_gender, col_age, col_nat = st.columns(3)
            with col_gender:
                gender = st.selectbox("Gender:", ["Female", "Male"])
            with col_age:
                age = st.slider("Age:", min_value=1, max_value=90, value=35)
            with col_nat:
                nationality = st.selectbox("Nationality:", unique_nationalities)
                
            col_airport, col_pilot = st.columns(2)
            with col_airport:
                selected_airport = st.selectbox("Departure Airport HUB:", unique_airports)
            with col_pilot:
                pilot_name = st.text_input("Assigned Pilot Name (required):", value="Capt. ").strip()
                
            col_date, col_status = st.columns(2)
            with col_date:
                departure_date = st.date_input("Departure Date:")
            with col_status:
                flight_status = st.selectbox("Flight Dispatch Status:", ["On Time", "Delayed", "Cancelled"])
                
            submit_btn = st.form_submit_button("🚀 Finalize Booking & Sync Dashboard")
            
            if submit_btn:
                # Basic validation
                if not first_name or not last_name:
                    st.error("❌ Submission failed: First Name and Last Name are required.")
                elif not pilot_name or pilot_name == "Capt.":
                    st.error("❌ Submission failed: A pilot must be assigned to the schedule.")
                else:
                    # 1. Generate unique string-hash ID
                    char_pool = string.ascii_letters + string.digits
                    generated_id = "".join(random.choices(char_pool, k=6))
                    
                    # 2. Relationship Auto-Inference: Search matching row in base data
                    matched_rows = df[df['Airport Name'] == selected_airport]
                    if not matched_rows.empty:
                        ref_row = matched_rows.iloc[0]
                        airport_country_code = ref_row['Airport Country Code']
                        country_name = ref_row['Country Name']
                        airport_continent = ref_row['Airport Continent']
                        continents = ref_row['Continents']
                        arrival_airport = ref_row['Arrival Airport']
                    else:
                        # Backup fallback if not matched
                        airport_country_code = "US"
                        country_name = "United States"
                        airport_continent = "NAM"
                        continents = "North America"
                        arrival_airport = "IATA"
                        
                    # 3. Construct booking dictionary
                    new_booking = {
                        'Passenger ID': generated_id,
                        'First Name': first_name,
                        'Last Name': last_name,
                        'Gender': gender,
                        'Age': int(age),
                        'Nationality': nationality,
                        'Airport Name': selected_airport,
                        'Airport Country Code': airport_country_code,
                        'Country Name': country_name,
                        'Airport Continent': airport_continent,
                        'Continents': continents,
                        'Departure Date': departure_date.strftime('%Y-%m-%d'),
                        'Arrival Airport': arrival_airport,
                        'Pilot Name': pilot_name,
                        'Flight Status': flight_status
                    }
                    
                    # 4. Save to session state
                    add_booking(new_booking)
                    st.success(f"🎉 Success! Passenger ID {generated_id} ({first_name} {last_name}) added successfully.")
                    st.info(f"📍 Relational Auto-Fill: Bound to {country_name} ({continents}), IATA code {arrival_airport}")
                    
                    # 5. Trigger st.rerun to update all dynamic KPIs and maps instantly!
                    st.rerun()
