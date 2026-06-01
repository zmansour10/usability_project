import streamlit as st
from typing import Optional

def inject_custom_css() -> None:
    """
    Injects custom global CSS into the Streamlit app to create a highly premium,
    modern aesthetic (Curated HSL color palettes, Outfit Google Font, subtle shadows,
    glassmorphism effects, and clean sidebar widgets).
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        /* Global typography & layout */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #1e293b;
        }
        
        .main {
            background-color: #f8fafc;
        }
        
        /* Premium Gradient Header Banner */
        .brand-banner {
            background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
            padding: 2.5rem 2rem;
            border-radius: 16px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.15), 0 8px 10px -6px rgba(30, 58, 138, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.08);
            position: relative;
            overflow: hidden;
        }
        
        .brand-banner::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 60%);
            pointer-events: none;
        }
        
        .brand-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.025em;
            background: linear-gradient(to right, #ffffff, #93c5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .brand-subtitle {
            font-size: 1.1rem;
            color: #94a3b8;
            margin-top: 0.5rem;
            margin-bottom: 0;
            font-weight: 300;
        }
        
        /* Glassmorphic Metrics Card */
        .glass-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 1rem;
        }
        
        .glass-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
            border-color: #cbd5e1;
        }
        
        .metric-title {
            font-size: 0.875rem;
            font-weight: 500;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2.25rem;
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
        
        /* Interactive Tabs styling */
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
            color: #1e3a8a !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        }
        
        /* Section Dividers */
        .section-header {
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #f1f5f9;
            color: #1e293b;
            font-weight: 600;
        }
        
        /* Dynamic badge indicators */
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .badge-ontime { background-color: #dcfce7; color: #166534; }
        .badge-delayed { background-color: #fef9c3; color: #854d0e; }
        .badge-cancelled { background-color: #fee2e2; color: #991b1b; }
        
        /* Sidebar styling overrides */
        .css-6qob1r, [data-testid="stSidebar"] {
            background-color: #0f172a;
            color: #cbd5e1;
        }
        
        .css-6qob1r h1, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: white;
        }
        
        /* Beautiful Custom Premium Cards */
        .custom-alert {
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
            background-color: #eff6ff;
            color: #1e40af;
            margin-bottom: 1rem;
        }
        
        .custom-alert-warning {
            border-left-color: #f59e0b;
            background-color: #fffbeb;
            color: #92400e;
        }
        
        .custom-alert-success {
            border-left-color: #10b981;
            background-color: #ecfdf5;
            color: #065f46;
        }
        
    </style>
    """, unsafe_allow_html=True)

def header_section(title: str, subtitle: str) -> None:
    """Renders a beautiful gradient top-banner header."""
    st.markdown(f"""
    <div class="brand-banner">
        <h1 class="brand-title">{title}</h1>
        <p class="brand-subtitle">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def kpi_card(title: str, value: str, subtitle: Optional[str] = None) -> None:
    """Renders a stunning glassmorphic KPI statistics card."""
    sub_html = f'<p class="metric-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

def custom_alert(title: str, text: str, alert_type: str = "info") -> None:
    """Renders a custom designed informative, warning, or success alert box."""
    css_class = "custom-alert"
    if alert_type == "warning":
        css_class = "custom-alert custom-alert-warning"
    elif alert_type == "success":
        css_class = "custom-alert custom-alert-success"
        
    st.markdown(f"""
    <div class="{css_class}">
        <strong style="font-size: 1.05rem; display: block; margin-bottom: 0.25rem;">{title}</strong>
        <span style="font-size: 0.95rem; line-height: 1.5;">{text}</span>
    </div>
    """, unsafe_allow_html=True)
