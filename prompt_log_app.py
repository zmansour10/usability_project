import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="Prompt Logbook Explorer",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Curated Custom CSS (Outfit font, glassmorphic cards, modern badges)
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');
        
        /* Global typography & background */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #1e293b;
        }
        
        .main {
            background-color: #f8fafc;
        }
        
        /* Premium Gradient Header Banner */
        .log-banner {
            background: linear-gradient(135deg, #4f46e5 0%, #1e1b4b 100%);
            padding: 2.5rem 2rem;
            border-radius: 16px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.15), 0 8px 10px -6px rgba(79, 70, 229, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.08);
            position: relative;
            overflow: hidden;
        }
        
        .log-banner::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, transparent 60%);
            pointer-events: none;
        }
        
        .log-title {
            font-size: 2.6rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.025em;
            background: linear-gradient(to right, #ffffff, #c7d2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .log-subtitle {
            font-size: 1.15rem;
            color: #cbd5e1;
            margin-top: 0.5rem;
            margin-bottom: 0;
            font-weight: 300;
        }
        
        /* Glassmorphic Metrics Card */
        .glass-card {
            background: white;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 1rem;
        }
        
        .glass-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.08);
            border-color: #cbd5e1;
        }
        
        .metric-title {
            font-size: 0.85rem;
            font-weight: 500;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.4rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #0f172a;
            line-height: 1;
            margin-bottom: 0.25rem;
            letter-spacing: -0.03em;
        }
        
        .metric-subtitle {
            font-size: 0.8rem;
            color: #94a3b8;
            margin: 0;
        }
        
        /* Entry Feed Card */
        .entry-card {
            background: white;
            border-radius: 14px;
            padding: 1.75rem;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
            margin-bottom: 1.75rem;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .entry-card:hover {
            box-shadow: 0 12px 20px -3px rgba(79, 70, 229, 0.06), 0 4px 6px -2px rgba(79, 70, 229, 0.04);
            border-color: #c7d2fe;
        }
        
        .entry-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 0.75rem;
            margin-bottom: 1rem;
        }
        
        .entry-id {
            font-size: 1.15rem;
            font-weight: 700;
            color: #4f46e5;
            background-color: #e0e7ff;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-family: 'Fira Code', monospace;
        }
        
        .entry-timestamp {
            font-size: 0.85rem;
            color: #94a3b8;
        }
        
        /* Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.65rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.5rem;
            margin-bottom: 0.4rem;
        }
        
        .badge-phase { background-color: #e0e7ff; color: #3730a3; border: 1px solid #c7d2fe; }
        .badge-model { background-color: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
        .badge-tool { background-color: #ecfeff; color: #155e75; border: 1px solid #cffafe; }
        .badge-tag { background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
        .badge-file { background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; font-family: 'Fira Code', monospace; font-size: 0.7rem; }
        
        /* Text blocks */
        .text-purpose {
            font-style: italic;
            color: #475569;
            border-left: 3.5px solid #4f46e5;
            padding-left: 0.75rem;
            margin: 1rem 0;
            font-size: 1rem;
            line-height: 1.6;
        }
        
        /* Custom Warning/Success Boxes */
        .problems-alert {
            padding: 0.75rem 1rem;
            border-radius: 8px;
            border-left: 4px solid #ef4444;
            background-color: #fef2f2;
            color: #991b1b;
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            margin-top: 0.75rem;
        }
        
        .clean-alert {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border-left: 4px solid #10b981;
            background-color: #ecfdf5;
            color: #065f46;
            font-size: 0.85rem;
            margin-top: 0.75rem;
        }
        
        /* Stars styling */
        .stars-container {
            display: inline-flex;
            gap: 2px;
            font-size: 1.15rem;
        }
        
        .star-active { color: #fbbf24; }
        .star-inactive { color: #cbd5e1; }
        
        /* Custom styling for Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0f172a;
            color: #cbd5e1;
        }
        
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: white !important;
        }
        
        /* Custom styling for Streamlit Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #f1f5f9;
            padding: 6px;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 42px;
            border-radius: 6px;
            padding: 0 24px;
            font-weight: 500;
            background-color: transparent;
            border: none !important;
            transition: all 0.2s ease;
            color: #475569;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            color: #0f172a;
            background-color: rgba(255, 255, 255, 0.5);
        }
        
        .stTabs [aria-selected="true"] {
            background-color: white !important;
            color: #4f46e5 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# 3. Load & Cache Data
@st.cache_data
def load_prompt_log(file_path: str):
    """Loads prompt log JSON file, caching the result."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return None

# Locate JSON file
current_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(current_dir, "prompt_log.json")

# Header Section
st.markdown("""
<div class="log-banner">
    <h1 class="log-title">📖 Prompt Logbook</h1>
    <p class="log-subtitle">A Premium Analytics Suite & Timeline Explorer for Agent Prompts, Outputs, and Iteration Performance</p>
</div>
""", unsafe_allow_html=True)

# Fetch data
log_data = load_prompt_log(json_path)

if log_data is None:
    st.error(f"Could not locate or parse `{json_path}`. Please ensure the file exists and is valid JSON.")
else:
    meta = log_data.get("meta", {})
    entries = log_data.get("entries", [])
    
    # Preprocess list into clean Pandas DataFrame for easy analysis/filtering
    processed_entries = []
    all_tags = set()
    all_files = set()
    
    for entry in entries:
        tags = entry.get("tags", [])
        files = entry.get("files_changed", [])
        
        for t in tags:
            all_tags.add(t)
        for f in files:
            all_files.add(f)
            
        processed_entries.append({
            "id": entry.get("id", "N/A"),
            "timestamp": entry.get("timestamp", ""),
            "phase": entry.get("phase", "General"),
            "model": entry.get("model", "Unknown"),
            "tool": entry.get("tool", "Unknown"),
            "purpose": entry.get("purpose", ""),
            "prompt": entry.get("prompt", ""),
            "output_summary": entry.get("output_summary", ""),
            "problems": entry.get("problems", ""),
            "rating": entry.get("rating", 0),
            "files_changed_count": len(files),
            "files_changed": files,
            "tags": tags,
            "has_problems": bool(entry.get("problems", ""))
        })
        
    df = pd.DataFrame(processed_entries)
    
    # Convert timestamp string to datetime objects
    df["datetime"] = pd.to_datetime(df["timestamp"], errors="coerce")
    
    # 4. Sidebar Filters & Navigation
    st.sidebar.markdown(
        '<div style="text-align: center; margin-bottom: 1.5rem;">'
        '<h1 style="color: white; font-size: 1.6rem; font-weight: 700; margin: 0; letter-spacing: -0.03em;">📖 Logbook Control</h1>'
        '<p style="color: #94a3b8; font-size: 0.8rem; margin: 0.2rem 0 0 0;">Metadata Explorer & Filters</p>'
        '</div>', 
        unsafe_allow_html=True
    )
    
    # Refresh Cache Button
    if st.sidebar.button("🔄 Refresh / Reload Logs", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    st.sidebar.markdown('<hr style="border-color: rgba(255,255,255,0.08); margin: 1rem 0;">', unsafe_allow_html=True)
    st.sidebar.markdown('<p style="color: #94a3b8; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5rem;">Global Filters</p>', unsafe_allow_html=True)
    
    # Filter 1: Text Search
    search_query = st.sidebar.text_input("🔍 Search Prompts/Outputs:", "", placeholder="Type keywords...")
    
    # Filter 2: Phase
    phases_list = ["All Phases"] + sorted(df["phase"].unique().tolist())
    selected_phase = st.sidebar.selectbox("Select Phase:", phases_list)
    
    # Filter 3: Model
    models_list = ["All Models"] + sorted(df["model"].unique().tolist())
    selected_model = st.sidebar.selectbox("Select Model:", models_list)
    
    # Filter 4: Rating
    ratings_list = ["All Ratings"] + [f"{i} Stars" for i in range(1, 6)]
    selected_rating = st.sidebar.selectbox("Minimum Rating:", ratings_list)
    
    # Filter 5: Tags
    tags_list = sorted(list(all_tags))
    selected_tags = st.sidebar.multiselect("Select Tags:", tags_list, placeholder="Filter by tags...")
    
    # Filter 6: Errors / Success State
    problem_filter = st.sidebar.selectbox("Execution Quality:", ["All Executions", "Clean Executions Only", "Errors/Problems Only"])
    
    # Applying filter logic to dataframe
    df_filtered = df.copy()
    
    # Search Query
    if search_query:
        query = search_query.lower()
        df_filtered = df_filtered[
            df_filtered["prompt"].str.lower().str.contains(query, na=False) |
            df_filtered["output_summary"].str.lower().str.contains(query, na=False) |
            df_filtered["purpose"].str.lower().str.contains(query, na=False) |
            df_filtered["problems"].str.lower().str.contains(query, na=False) |
            df_filtered["id"].str.lower().str.contains(query, na=False)
        ]
        
    # Phase
    if selected_phase != "All Phases":
        df_filtered = df_filtered[df_filtered["phase"] == selected_phase]
        
    # Model
    if selected_model != "All Models":
        df_filtered = df_filtered[df_filtered["model"] == selected_model]
        
    # Rating
    if selected_rating != "All Ratings":
        min_stars = int(selected_rating.split(" ")[0])
        df_filtered = df_filtered[df_filtered["rating"] >= min_stars]
        
    # Tags
    if selected_tags:
        # Check if entry has any of the selected tags
        df_filtered = df_filtered[df_filtered["tags"].apply(lambda t_list: any(t in t_list for t in selected_tags))]
        
    # Executions quality
    if problem_filter == "Clean Executions Only":
        df_filtered = df_filtered[~df_filtered["has_problems"]]
    elif problem_filter == "Errors/Problems Only":
        df_filtered = df_filtered[df_filtered["has_problems"]]
        
    # Sidebar footer info
    st.sidebar.markdown('<hr style="border-color: rgba(255,255,255,0.08); margin: 2rem 0 1rem 0;">', unsafe_allow_html=True)
    st.sidebar.markdown(
        f'<div style="color: #94a3b8; font-size: 0.75rem; line-height: 1.6;">'
        f'Project Name: <strong>{meta.get("project", "Usability Project")}</strong><br>'
        f'Logs Tracked: <strong>{len(df_filtered)}</strong> / {len(df)} entries<br>'
        f'Active View: <strong>Interactive Dashboard</strong><br>'
        f'App Version: <strong>{meta.get("version", "1.0")}</strong><br>'
        f'Last Loaded: <strong>{datetime.now().strftime("%H:%M:%S")}</strong>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    # 5. Core Interface Layout (3 Main Tabs)
    tab1, tab2, tab3 = st.tabs(["📋 Log Explorer", "📊 Analytics & Insights", "📁 Raw JSON Data"])
    
    # Dynamic Helper functions for badge HTML rendering
    def make_badge(text, badge_type):
        return f'<span class="badge badge-{badge_type}">{text}</span>'
        
    def make_star_rating_html(rating_val):
        active = '<span class="star-active">★</span>'
        inactive = '<span class="star-inactive">★</span>'
        return f'<div class="stars-container">{"".join([active if i < rating_val else inactive for i in range(5)])}</div>'

    # TAB 1: LOG EXPLORER
    with tab1:
        if df_filtered.empty:
            st.warning("⚠️ No logs matched the active filter combination. Adjust the Sidebar parameters.")
        else:
            # RENDER DYNAMIC KPI CARDS AT TOP OF EXPLORER
            kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
            
            with kpi_col1:
                total_filtered = len(df_filtered)
                st.markdown(f"""
                <div class="glass-card">
                    <div class="metric-title">Filtered Prompts</div>
                    <div class="metric-value">{total_filtered}</div>
                    <p class="metric-subtitle">Active matching records</p>
                </div>
                """, unsafe_allow_html=True)
                
            with kpi_col2:
                avg_rating = df_filtered["rating"].mean()
                stars_html = make_star_rating_html(round(avg_rating)) if not pd.isna(avg_rating) else "No Rating"
                st.markdown(f"""
                <div class="glass-card">
                    <div class="metric-title">Avg. Performance</div>
                    <div class="metric-value">{avg_rating:.2f} / 5</div>
                    <p class="metric-subtitle">{stars_html}</p>
                </div>
                """, unsafe_allow_html=True)
                
            with kpi_col3:
                clean_count = len(df_filtered[~df_filtered["has_problems"]])
                success_rate = (clean_count / total_filtered * 100) if total_filtered > 0 else 0
                st.markdown(f"""
                <div class="glass-card">
                    <div class="metric-title">Success Rate</div>
                    <div class="metric-value">{success_rate:.1f}%</div>
                    <p class="metric-subtitle">{clean_count} out of {total_filtered} clean</p>
                </div>
                """, unsafe_allow_html=True)
                
            with kpi_col4:
                # Count unique files modified in current scope
                unique_files_scope = set()
                for files_list in df_filtered["files_changed"]:
                    for f in files_list:
                        unique_files_scope.add(f)
                st.markdown(f"""
                <div class="glass-card">
                    <div class="metric-title">Files Affected</div>
                    <div class="metric-value">{len(unique_files_scope)}</div>
                    <p class="metric-subtitle">Across active prompts</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
            st.markdown("### 📋 Prompts Feed Timeline")
            
            # Feed of individual logs ordered by timestamp reverse chronological
            df_feed = df_filtered.sort_values(by="datetime", ascending=False)
            
            for index, row in df_feed.iterrows():
                # Extract details
                e_id = row["id"]
                timestamp_str = row["timestamp"]
                formatted_time = row["datetime"].strftime("%b %d, %Y - %H:%M:%S") if not pd.isna(row["datetime"]) else timestamp_str
                
                # Render the nice summary card header with HTML
                phase_badge = make_badge(row["phase"], "phase")
                model_badge = make_badge(row["model"], "model")
                tool_badge = make_badge(row["tool"], "tool")
                
                tags_badges = "".join([make_badge(t, "tag") for t in row["tags"]])
                files_badges = "".join([make_badge(f, "file") for f in row["files_changed"]])
                
                rating_stars = make_star_rating_html(row["rating"])
                
                st.markdown(f"""
                <div class="entry-card">
                    <div class="entry-header">
                        <div>
                            <span class="entry-id">{e_id}</span>
                            <span style="margin-left: 1rem;">{model_badge} {phase_badge} {tool_badge}</span>
                        </div>
                        <div style="text-align: right; display: flex; align-items: center; gap: 10px;">
                            {rating_stars}
                            <span class="entry-timestamp">{formatted_time}</span>
                        </div>
                    </div>
                    <strong style="font-size: 1.15rem; color: #1e293b; display: block; margin-bottom: 0.5rem;">🎯 Purpose:</strong>
                    <div class="text-purpose">{row["purpose"]}</div>
                    <div style="margin-top: 0.75rem;">
                        <strong>Tags:</strong> {tags_badges if row['tags'] else '<span style="color: #94a3b8; font-size: 0.8rem; font-style: italic;">None</span>'}
                    </div>
                    <div style="margin-top: 0.5rem; margin-bottom: 1rem;">
                        <strong>Files Modified:</strong> {files_badges if row['files_changed'] else '<span style="color: #94a3b8; font-size: 0.8rem; font-style: italic;">None</span>'}
                    </div>
                """, unsafe_allow_html=True)
                
                # Expanders for Prompt and Output summaries
                exp_prompt = st.expander("🔍 Show Prompt Content", expanded=False)
                with exp_prompt:
                    st.code(row["prompt"], language="text")
                    
                exp_output = st.expander("📝 Show Output Summary & Actions", expanded=False)
                with exp_output:
                    st.markdown(row["output_summary"])
                
                # Problems / Errors banner
                if row["has_problems"]:
                    st.markdown(f"""
                    <div class="problems-alert">
                        <strong>⚠️ Problem Logged:</strong><br>{row['problems']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="clean-alert">
                        <strong>✅ Smooth Execution:</strong> No errors, exceptions or regressions reported.
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Close feed-card div container
                st.markdown("</div>", unsafe_allow_html=True)

    # TAB 2: ANALYTICS & INSIGHTS
    with tab2:
        st.markdown("### 📊 Metrics, Success Rates and Statistics")
        st.markdown("Discover overall insights, performance metrics, and model execution distributions across all prompt entries.")
        
        # Check if df is empty
        if df.empty:
            st.info("No data available to display metrics.")
        else:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # 1. Ratings distribution
                rating_counts = df["rating"].value_counts().reset_index()
                rating_counts.columns = ["Rating", "Count"]
                rating_counts = rating_counts.sort_values(by="Rating")
                
                fig_ratings = px.bar(
                    rating_counts, 
                    x="Rating", 
                    y="Count", 
                    title="⭐ User Ratings Distribution",
                    labels={"Rating": "Rating (1 to 5 Stars)", "Count": "Number of Prompts"},
                    color="Count",
                    color_continuous_scale=px.colors.sequential.Blues,
                    template="plotly_white"
                )
                fig_ratings.update_layout(xaxis=dict(tickmode="linear", tick0=1, dtick=1))
                st.plotly_chart(fig_ratings, use_container_width=True)
                
            with col_chart2:
                # 2. Problems vs Success rate
                problems_summary = df["has_problems"].value_counts().reset_index()
                problems_summary.columns = ["Execution State", "Count"]
                problems_summary["Execution State"] = problems_summary["Execution State"].map({True: "⚠️ Errors/Problems", False: "✅ Clean Run"})
                
                fig_success = px.pie(
                    problems_summary,
                    names="Execution State",
                    values="Count",
                    title="🎯 Execution Quality & Success Ratio",
                    hole=0.4,
                    color="Execution State",
                    color_discrete_map={"✅ Clean Run": "#10b981", "⚠️ Errors/Problems": "#ef4444"},
                    template="plotly_white"
                )
                fig_success.update_traces(textinfo='percent+value')
                st.plotly_chart(fig_success, use_container_width=True)
                
            col_chart3, col_chart4 = st.columns(2)
            
            with col_chart3:
                # 3. Model Active Counts
                model_counts = df["model"].value_counts().reset_index()
                model_counts.columns = ["AI Model", "Usage Count"]
                
                fig_model = px.bar(
                    model_counts,
                    y="AI Model",
                    x="Usage Count",
                    orientation="h",
                    title="🤖 AI Models Usage Frequency",
                    labels={"AI Model": "Model Name", "Usage Count": "Times Prompted"},
                    color="Usage Count",
                    color_continuous_scale=px.colors.sequential.Purples,
                    template="plotly_white"
                )
                fig_model.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_model, use_container_width=True)
                
            with col_chart4:
                # 4. Most changed files list
                files_dist = {}
                for f_list in df["files_changed"]:
                    for f in f_list:
                        files_dist[f] = files_dist.get(f, 0) + 1
                        
                if files_dist:
                    files_df = pd.DataFrame(list(files_dist.items()), columns=["File", "Times Modified"]).sort_values(by="Times Modified", ascending=True)
                    
                    fig_files = px.bar(
                        files_df.tail(10),
                        y="File",
                        x="Times Modified",
                        orientation="h",
                        title="📁 Top 10 Most Modified Files",
                        labels={"File": "File Basename", "Times Modified": "Edit Frequency"},
                        color="Times Modified",
                        color_continuous_scale=px.colors.sequential.Reds,
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_files, use_container_width=True)
                else:
                    st.info("No files modified in prompt records yet.")
                    
            # 5. Tags Frequency
            st.markdown("#### 🏷️ Tag Popularity Explorer")
            tags_dist = {}
            for t_list in df["tags"]:
                for t in t_list:
                    tags_dist[t] = tags_dist.get(t, 0) + 1
                    
            if tags_dist:
                tags_df = pd.DataFrame(list(tags_dist.items()), columns=["Tag", "Occurrences"]).sort_values(by="Occurrences", ascending=False)
                
                # Show columns of tags for quick reading
                col_t1, col_t2 = st.columns([1, 2])
                with col_t1:
                    st.dataframe(tags_df, use_container_width=True, hide_index=True)
                with col_t2:
                    fig_tags = px.bar(
                        tags_df,
                        x="Tag",
                        y="Occurrences",
                        title="Tag Frequency Analytics",
                        labels={"Tag": "Tag Name", "Occurrences": "Prompt Counts"},
                        color="Occurrences",
                        color_continuous_scale=px.colors.sequential.Viridis,
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_tags, use_container_width=True)
            else:
                st.info("No tags assigned to prompt records yet.")

    # TAB 3: RAW JSON DATA
    with tab3:
        st.markdown("### 📁 JSON Tree Viewer & Data Export")
        st.markdown("Inspect the raw log values directly, search raw records, or download the active dataset for backup or further analysis.")
        
        # Download Active Filtered Data Buttons
        col_dl1, col_dl2 = st.columns(2)
        
        # Export logic
        filtered_entries_raw = df_filtered.drop(columns=["datetime", "has_problems"]).to_dict(orient="records")
        # Restructure to match original structure
        original_filtered_json = {
            "meta": meta,
            "entries": filtered_entries_raw
        }
        
        # Save as JSON / CSV strings
        json_str = json.dumps(original_filtered_json, indent=2, ensure_ascii=False)
        csv_str = df_filtered.drop(columns=["datetime", "has_problems"]).to_csv(index=False)
        
        with col_dl1:
            st.download_button(
                label="📥 Download Filtered Logs as JSON",
                data=json_str,
                file_name="filtered_prompt_log.json",
                mime="application/json",
                use_container_width=True
            )
            
        with col_dl2:
            st.download_button(
                label="📥 Download Filtered Logs as CSV",
                data=csv_str,
                file_name="filtered_prompt_log.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
        st.json(original_filtered_json)
