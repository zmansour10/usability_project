
import pandas as pd
import numpy as np

# 1. wq_summary analysis
wq_summary = pd.read_csv('data/wq_summary.csv')
top_parameters = wq_summary.groupby('parameter')['n_observations'].sum().reset_index()
top_parameters = top_parameters[top_parameters['n_observations'] > 50].sort_values(by='n_observations', ascending=False)
print("--- TOP PARAMETERS (n > 50) ---")
print(top_parameters.head(10))

# 2. sites_leaf analysis
sites_leaf = pd.read_csv('data/sites_leaf.csv')
valid_coords = sites_leaf[sites_leaf['latitude'].notnull() & sites_leaf['longitude'].notnull()]
print(f"\n--- SITES WITH VALID COORDS: {len(valid_coords)} / {len(sites_leaf)} ---")

# Geographic Clustering based on km_start
# Elbe km: 0 (Czech border) to ~727 (Cuxhaven)
# Typical breakdown: 
# Oberlauf: 0 - 121 (until Schloss Hirschstein)
# Mittellauf: 121 - 585 (until Geesthacht)
# Unterlauf: 585 - 727 (Tidal Elbe)
def get_region(km):
    if pd.isnull(km): return "Unbekannt"
    if km < 121: return "Oberlauf"
    elif km < 585: return "Mittellauf"
    else: return "Unterlauf"

sites_leaf['region'] = sites_leaf['km_start'].apply(get_region)
print("\n--- REGIONAL CLUSTERS ---")
print(sites_leaf['region'].value_counts())

# 3. measurement_summary analysis (Activity)
m_summary = pd.read_csv('data/measurement_summary.csv')
m_summary['last_date'] = pd.to_datetime(m_summary['last_date'])
latest_year = m_summary['last_date'].dt.year.max()
active_threshold = 2015 # Arbitrary threshold for "Recent"
active_sites = m_summary[m_summary['last_date'].dt.year >= active_threshold]
print(f"\n--- ACTIVE SITES (>= {active_threshold}): {len(active_sites)} ---")

# 4. Data Quality Matrix (Simplified for insight)
# site_id x parameter
matrix = wq_summary.pivot(index='site_id', columns='parameter', values='n_observations').fillna(0)
print("\n--- DATA QUALITY MATRIX (First 5 sites, first 5 parameters) ---")
print(matrix.iloc[:5, :5])
