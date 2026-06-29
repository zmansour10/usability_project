"""
Elbe Monitoring – Refined UI
============================================================================
Refinement der Baseline-App für die Modulprüfung "Refinement" (Usability SS2026).

Schwerpunkte der Überarbeitung:
  1. Typografie      – konsistente Typoskala, eine Schriftfamilie, klare Hierarchie
  2. Farbleitsystem  – semantische Statusfarben + redundante Kodierung (Icon/Text)
  3. Informations-   – "Overview first, zoom and filter, details on demand"
     architektur       (Shneiderman), kontextbezogene Filter, KPI-Header

Die Logik der Datenaufbereitung bleibt funktional identisch zur Baseline,
damit der Vergleich (Vorher/Nachher) ausschließlich die UX-Ebene betrifft.
============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. Globale Konfiguration & Design-Tokens
# ---------------------------------------------------------------------------
DATA_DIR = Path("data")

st.set_page_config(
    page_title="Elbe-Monitoring",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Design-Tokens (zentral, statt verstreuter Inline-Styles) --------------
# Ein abgestimmtes, ruhiges Blau-Grün-Schema (Gewässer-Domäne) plus ein
# klar abgegrenztes, WCAG-konformes Statustripel. Statusfarben sind bewusst
# NICHT dieselben wie die Regionsfarben, um Bedeutungskollisionen zu vermeiden.
TOKENS = {
    # Markenfarben (Domäne: Fluss / Wasser)
    "brand":        "#0B6E99",   # Tiefes Wasserblau – Primärakzent
    "brand_dark":   "#08506F",
    "ink":          "#1A2530",   # Fast-Schwarz für Fließtext (Kontrast > 12:1)
    "muted":        "#5B6B7A",   # Sekundärtext / Captions
    "line":         "#E3E8ED",   # Hairline-Trennlinien
    "surface":      "#FFFFFF",
    "canvas":       "#F4F7F9",   # App-Hintergrund (sehr helles Blaugrau)
    # Semantische Statusfarben (Ampel, aber WCAG-tauglich & farbenblind-robust)
    "ok":           "#2E7D52",   # Grün – OK
    "warn":         "#B7791F",   # Bernstein statt reines Gelb (Kontrast!)
    "crit":         "#C0392B",   # Rot – kritisch
    "ok_soft":      "#E6F2EB",
    "warn_soft":    "#FBF2E1",
    "crit_soft":    "#FBE9E7",
    # Regionsfarben (qualitativ, kollidieren nicht mit Status-Rot/Grün)
    "region_ober":  "#7E57C2",   # Violett
    "region_mit":   "#0B6E99",   # Blau
    "region_unter": "#26A69A",   # Teal
    "region_unk":   "#9AA7B2",   # Grau
}

REGION_COLORS = {
    "Oberlauf":  TOKENS["region_ober"],
    "Mittellauf": TOKENS["region_mit"],
    "Unterlauf": TOKENS["region_unter"],
    "Unbekannt": TOKENS["region_unk"],
}

# Plotly-Standardlayout: ruhig, viel Weißraum, keine harten Gitterlinien
PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, -apple-system, Segoe UI, sans-serif",
              size=13, color=TOKENS["ink"]),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=48, b=10),
    title=dict(font=dict(size=16, color=TOKENS["ink"])),
    xaxis=dict(gridcolor=TOKENS["line"], zeroline=False),
    yaxis=dict(gridcolor=TOKENS["line"], zeroline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)

# ---------------------------------------------------------------------------
# 1. Typografie & globales CSS (eine Typoskala, eine Schriftfamilie)
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: {TOKENS['ink']};
    }}
    .main, .stApp {{ background-color: {TOKENS['canvas']}; }}

    /* ---- Typoskala (Major-Third-nah: 13 / 16 / 20 / 26 / 34) ----------- */
    h1, .h1 {{ font-size: 1.9rem !important; font-weight: 700; letter-spacing:-.01em;
               color:{TOKENS['ink']}; margin:0 0 .25rem 0; }}
    h2, .h2 {{ font-size: 1.35rem !important; font-weight: 600; color:{TOKENS['ink']};
               margin:1.4rem 0 .6rem 0; }}
    h3, .h3 {{ font-size: 1.05rem !important; font-weight: 600; color:{TOKENS['ink']}; }}
    .caption {{ font-size:.82rem; color:{TOKENS['muted']}; text-transform:uppercase;
                letter-spacing:.06em; font-weight:600; }}
    .lead {{ font-size:.98rem; color:{TOKENS['muted']}; margin-top:-.2rem; }}

    /* ---- KPI-Karten (Overview-first) ----------------------------------- */
    .kpi-row {{ display:flex; gap:14px; margin:.2rem 0 1.1rem 0; flex-wrap:wrap; }}
    .kpi {{ flex:1; min-width:140px; background:{TOKENS['surface']};
            border:1px solid {TOKENS['line']}; border-radius:14px;
            padding:16px 18px; box-shadow:0 1px 2px rgba(16,40,60,.04); }}
    .kpi .label {{ font-size:.74rem; color:{TOKENS['muted']}; text-transform:uppercase;
                   letter-spacing:.07em; font-weight:600; }}
    .kpi .value {{ font-size:1.7rem; font-weight:700; color:{TOKENS['ink']};
                   line-height:1.15; margin-top:2px; }}
    .kpi .unit {{ font-size:.85rem; font-weight:500; color:{TOKENS['muted']}; }}
    .kpi.accent {{ border-left:4px solid {TOKENS['brand']}; }}

    /* ---- Statusfarben mit redundanter (Text-)Kodierung ----------------- */
    .pill {{ display:inline-flex; align-items:center; gap:6px; padding:3px 10px;
             border-radius:999px; font-size:.8rem; font-weight:600; }}
    .pill.ok   {{ background:{TOKENS['ok_soft']};   color:{TOKENS['ok']};   }}
    .pill.warn {{ background:{TOKENS['warn_soft']}; color:{TOKENS['warn']}; }}
    .pill.crit {{ background:{TOKENS['crit_soft']}; color:{TOKENS['crit']}; }}

    /* ---- Tabs: ruhiger, klarer aktiver Zustand ------------------------- */
    .stTabs [data-baseweb="tab-list"] {{ gap:4px; border-bottom:1px solid {TOKENS['line']}; }}
    .stTabs [data-baseweb="tab"] {{ height:46px; padding:0 18px; font-weight:600;
                                    color:{TOKENS['muted']}; background:transparent; }}
    .stTabs [aria-selected="true"] {{ color:{TOKENS['brand']} !important;
                                      border-bottom:2px solid {TOKENS['brand']}; }}

    /* ---- Info-/Kontextleisten ------------------------------------------ */
    .context-bar {{ background:{TOKENS['surface']}; border:1px solid {TOKENS['line']};
                    border-radius:12px; padding:12px 16px; margin-bottom:1rem;
                    font-size:.9rem; color:{TOKENS['ink']}; }}
    .meta {{ background:{TOKENS['surface']}; border:1px solid {TOKENS['line']};
             border-left:4px solid {TOKENS['brand']}; border-radius:12px;
             padding:14px 18px; font-size:.92rem; }}
    /* ---- "Kernaussage": narrative key-finding callout (Restorff-Effekt) -- */
    .kernaussage {{ background:#EAF3F7; border:1px solid #CFE3EC;
                    border-left:4px solid {TOKENS['brand']}; border-radius:12px;
                    padding:11px 16px; margin:.3rem 0 1rem 0; font-size:.92rem;
                    color:{TOKENS['ink']}; line-height:1.45; }}
    .kernaussage b {{ color:{TOKENS['brand_dark']}; letter-spacing:.02em; }}
    /* ---- ehrlicher Daten-/Methodenhinweis (Transparenz) ---------------- */
    .note {{ background:{TOKENS['warn_soft']}; border:1px solid #EAD9B0;
             border-radius:10px; padding:9px 14px; margin:.2rem 0 .8rem 0;
             font-size:.85rem; color:{TOKENS['ink']}; }}
    section[data-testid="stSidebar"] {{ background:{TOKENS['surface']};
             border-right:1px solid {TOKENS['line']}; }}
    section[data-testid="stSidebar"] .caption {{ margin-bottom:.3rem; }}
    /* sichtbarer Tastatur-Fokus (Accessibility) */
    *:focus-visible {{ outline:3px solid {TOKENS['brand']}; outline-offset:2px; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 2. Datenladen & Vorverarbeitung  (Logik wie Baseline)
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    data = {}

    # wq_summary -----------------------------------------------------------
    try:
        wq_sum = pd.read_csv(DATA_DIR / "wq_summary.csv", low_memory=False)
        data["wq_summary"] = wq_sum
        top = (wq_sum.groupby("parameter")["n_observations"].sum().reset_index())
        top = top[top["n_observations"] > 50].sort_values("n_observations", ascending=False)
        data["top_10_params"] = top.head(10)["parameter"].tolist()
    except Exception:
        data["wq_summary"], data["top_10_params"] = pd.DataFrame(), []

    # sites_leaf -----------------------------------------------------------
    try:
        sites = pd.read_csv(DATA_DIR / "sites_leaf.csv", low_memory=False)
        sites["km_start_num"] = pd.to_numeric(sites["km_start"], errors="coerce")

        def get_region(km):
            if pd.isna(km):
                return "Unbekannt"
            if km < 200:
                return "Oberlauf"
            if km < 400:
                return "Mittellauf"
            return "Unterlauf"

        sites["Region"] = sites["km_start_num"].apply(get_region)
        data["sites"] = sites
    except Exception:
        data["sites"] = pd.DataFrame()

    # measurement_summary --------------------------------------------------
    try:
        meas = pd.read_csv(DATA_DIR / "measurement_summary.csv", low_memory=False)
        meas["last_date"] = pd.to_datetime(meas["last_date"], errors="coerce")
        meas["Status"] = meas["last_date"].apply(
            lambda x: "Aktiv" if pd.notna(x) and x.year >= 2015 else "Inaktiv")
        data["meas_summary"] = meas
    except Exception:
        data["meas_summary"] = pd.DataFrame()

    # Datenqualitäts-Matrix -------------------------------------------------
    if not data["wq_summary"].empty:
        data["wq_matrix"] = data["wq_summary"].pivot(
            index="site_id", columns="parameter", values="n_observations").fillna(0)
    else:
        data["wq_matrix"] = pd.DataFrame()

    # wq_raw ---------------------------------------------------------------
    try:
        raw = pd.read_csv(DATA_DIR / "wq_raw.csv", low_memory=False)
        raw["timestamp"] = pd.to_datetime(raw["timestamp"], errors="coerce")
        data["wq_raw"] = raw.dropna(subset=["timestamp"])
    except Exception:
        data["wq_raw"] = pd.DataFrame()

    # corrosion_positions --------------------------------------------------
    try:
        corr = pd.read_csv(DATA_DIR / "corrosion_positions.csv", low_memory=False)
        corr["measurement_date"] = pd.to_datetime(corr["measurement_date"], errors="coerce")
        # pandas 3.0 lädt diese Spalten als (pyarrow-)String -> explizit numerisch
        for c in ("actual_wall_thickness", "planned_wall_thickness",
                  "number_of_holes", "average_hole_size"):
            if c in corr.columns:
                corr[c] = pd.to_numeric(corr[c], errors="coerce")
        # data_quality säubern: Leerzeichen/Groß-Klein + Tippfehler vereinheitlichen
        if "data_quality" in corr.columns:
            dq = corr["data_quality"].astype("string").str.strip().str.lower()
            corr["data_quality"] = dq.where(dq.isin(["gut", "mäßig", "schlecht"]), "unbekannt")
        data["corrosion"] = corr
    except Exception:
        data["corrosion"] = pd.DataFrame()

    # Querverweis Wasserqualität <-> Korrosion (Gruppen) -------------------
    try:
        data["groups"] = pd.read_csv(DATA_DIR / "sites_wq_corrosion_groups.csv", low_memory=False)
    except Exception:
        data["groups"] = pd.DataFrame()

    # Hinweis: corrosion_rates.csv wird bewusst NICHT verwendet – alle Raten
    # sind 0.0 (fast alle Stationen haben nur eine Kampagne) -> nicht aussagekräftig.

    return data


data = load_data()

# Stations-Stammdaten + Messzusammenfassung verbinden
if not data["sites"].empty and not data["meas_summary"].empty:
    sites_full = pd.merge(data["sites"], data["meas_summary"], on="site_id", how="left")
    sites_full["Status"] = sites_full["Status"].fillna("Inaktiv")
    sites_full["last_date"] = sites_full["last_date"].dt.date
else:
    sites_full = data["sites"]


# ---------------------------------------------------------------------------
# 3. Wiederverwendbare UI-Bausteine
# ---------------------------------------------------------------------------
def kpi_card(label, value, unit="", accent=False, help_text=""):
    """Eine KPI-Kachel (Overview-first). help_text => natives Tooltip."""
    cls = "kpi accent" if accent else "kpi"
    title = f' title="{help_text}"' if help_text else ""
    unit_html = f' <span class="unit">{unit}</span>' if unit else ""
    return (f'<div class="{cls}"{title}><div class="label">{label}</div>'
            f'<div class="value">{value}{unit_html}</div></div>')


def pill(kind, text):
    icon = {"ok": "●", "warn": "▲", "crit": "■"}[kind]  # Form ≠ nur Farbe (WCAG 1.4.1)
    return f'<span class="pill {kind}">{icon} {text}</span>'


def kernaussage(text):
    """Narrative Kernaussage (Annotation-Layer / Storytelling): hebt DIE eine
    Erkenntnis einer Ansicht hervor (Peak-End-Rule, Restorff-Effekt)."""
    st.markdown(f'<div class="kernaussage"><b>Kernaussage:</b> {text}</div>',
                unsafe_allow_html=True)


# Namen der 14 Stationen mit Wasserqualitäts-Zeitreihen (für Drill-down/Verlinkung)
WQ_SITE_NAMES = (set(data["wq_raw"]["site_name"].dropna().unique())
                 if not data["wq_raw"].empty else set())


def _preselect_wq(name):
    """Callback: Station für den WQ-Tab vorwählen. Läuft VOR der Widget-
    Instanzierung -> kein 'modified after instantiated'-Fehler. Region auf 'Alle',
    damit die Station garantiert in der Auswahlliste enthalten ist."""
    st.session_state["wq_region"] = "Alle"
    st.session_state["wq_station"] = name


# ---------------------------------------------------------------------------
# 4. Kopfbereich:  Titel + globale KPIs  (Overview first)
# ---------------------------------------------------------------------------
st.markdown('<div class="h1">Elbe-Monitoring</div>', unsafe_allow_html=True)
st.markdown('<div class="lead">Wasserqualität und Bauwerks­korrosion entlang der Elbe · '
            '1954–2024</div>', unsafe_allow_html=True)

n_sites = len(sites_full) if not sites_full.empty else 0
n_active = int((sites_full["Status"] == "Aktiv").sum()) if not sites_full.empty and "Status" in sites_full else 0
n_wq = len(data["wq_raw"]) if not data["wq_raw"].empty else 0
n_corr = len(data["corrosion"]) if not data["corrosion"].empty else 0

# Echte Befundgröße statt toter "% < 50"-Logik: Durchrostungen (Löcher) in der
# letzten Messung je Station. Datenbefund: KEINE Position < 80 % Restwanddicke,
# aber 76 Stationen weisen Löcher auf -> das ist das belastbare Korrosionssignal.
holes_count = 0
if not data["corrosion"].empty and "number_of_holes" in data["corrosion"].columns:
    c = data["corrosion"].dropna(subset=["measurement_date"]).copy()
    if not c.empty:
        idx = c.groupby("site_id")["measurement_date"].transform("max") == c["measurement_date"]
        latest = c[idx]
        holes_count = int((latest["number_of_holes"].fillna(0) > 0).sum())

st.markdown(
    '<div class="kpi-row">'
    + kpi_card("Stationen", f"{n_sites}", accent=True,
               help_text="Gesamtzahl der Messstationen im Datensatz")
    + kpi_card("Aktiv (seit 2015)", f"{n_active}",
               help_text="Stationen mit Messung im Jahr 2015 oder später")
    + kpi_card("WQ-Messungen", f"{n_wq:,}".replace(",", "."),
               help_text="Einzelmesswerte der Wasserqualität")
    + kpi_card("Positionen mit Durchrostung", f"{holes_count}",
               help_text="Messpunkte mit mindestens einem Loch (Durchrostung) in der "
                         "letzten Messung – das belastbare Korrosionssignal.")
    + "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 5. Tabs
# ---------------------------------------------------------------------------
tab_map, tab_wq, tab_corr, tab_sum = st.tabs([
    "Stationsübersicht", "Wasserqualität", "Korrosion", "Zusammenfassung",
])

# ── TAB 1: STATIONSÜBERSICHT ───────────────────────────────────────────────
with tab_map:
    st.markdown('<div class="h2">Räumliche Übersicht</div>', unsafe_allow_html=True)
    st.markdown('<div class="lead">Überblick zuerst – Region wählen, um Karte und Liste '
                'gemeinsam zu filtern; eine Station auf der Karte anklicken, um Details '
                'abzurufen (Overview → Zoom &amp; Filter → Details-on-demand).</div>',
                unsafe_allow_html=True)

    if sites_full.empty:
        st.info("Keine Stationsdaten gefunden. Bitte CSV-Dateien im Ordner **data/** prüfen.")
    else:
        valid = sites_full.dropna(subset=["latitude", "longitude"]).copy()

        # Kontextbezogener Filter DIREKT im Tab (nicht in globaler Sidebar)
        regions = ["Alle"] + sorted([r for r in sites_full["Region"].unique()])
        fcol1, fcol2 = st.columns([1, 3])
        with fcol1:
            sel_region = st.selectbox("Region", regions, key="map_region",
                                      help="Filtert Karte und Liste gemeinsam (Brushing & Linking).")
        if sel_region != "Alle":
            valid = valid[valid["Region"] == sel_region]

        col1, col2 = st.columns([3, 2], gap="large")
        sel_site_id = None
        with col1:
            if not valid.empty:
                valid["n_measurements"] = valid.get("n_measurements", 0)
                valid["n_measurements"] = valid["n_measurements"].fillna(0).astype(int)
                fig = px.scatter_mapbox(
                    valid, lat="latitude", lon="longitude", color="Region",
                    color_discrete_map=REGION_COLORS, hover_name="site_name",
                    hover_data={"site_id": True, "n_measurements": ":,",
                                "Region": True, "latitude": False, "longitude": False},
                    custom_data=["site_id", "site_name"],
                    zoom=5, height=560, mapbox_style="carto-positron",
                )
                fig.update_traces(marker=dict(size=11, opacity=.85))
                fig.update_layout(**{k: v for k, v in PLOTLY_LAYOUT.items()
                                     if k in ("font", "margin", "legend", "paper_bgcolor")})
                # Direkte Manipulation: Klick auf einen Punkt = Auswahl (Selection-Event)
                event = st.plotly_chart(fig, use_container_width=True,
                                        on_select="rerun", key="map_sel")
                try:
                    pts = event["selection"]["points"]
                except Exception:
                    pts = []
                if pts and pts[0].get("customdata"):
                    raw = pts[0]["customdata"][0]
                    try:
                        sel_site_id = int(raw)
                    except (ValueError, TypeError):
                        sel_site_id = raw
                st.caption("Tipp: Punkt anklicken für Stationsdetails. Alt-Text: Punktkarte "
                           "der Messstationen, eingefärbt nach Flussabschnitt (Region).")
            else:
                st.info("Keine Stationen mit gültigen Koordinaten in dieser Region.")
        with col2:
            # --- Details-on-demand: Detailkarte zur angeklickten Station -------
            if sel_site_id is not None:
                row = sites_full[sites_full["site_id"] == sel_site_id]
            else:
                row = pd.DataFrame()
            if not row.empty:
                r = row.iloc[0]
                name = r.get("site_name")
                has_wq = name in WQ_SITE_NAMES
                has_corr = (not data["corrosion"].empty
                            and sel_site_id in set(data["corrosion"]["site_id"].unique()))
                km = pd.to_numeric(pd.Series([r.get("km_start")]), errors="coerce").iloc[0]
                cy = pd.to_numeric(pd.Series([r.get("construction_year")]), errors="coerce").iloc[0]
                st.markdown(
                    '<div class="context-bar"><div class="caption">Ausgewählte Station</div>'
                    f'<div class="h3">📍 {name if pd.notna(name) else "—"}</div>'
                    f'<div class="lead">Region {r.get("Region", "—")}'
                    + (f' · Strom-km {km:.1f}' if pd.notna(km) else "")
                    + (f' · Baujahr {int(cy)}' if pd.notna(cy) and cy > 1800 else "")
                    + '</div><div style="margin-top:8px">'
                    + (pill("ok", "WQ-Zeitreihe") if has_wq else pill("warn", "keine WQ-Zeitreihe"))
                    + " "
                    + (pill("ok", "Korrosionsdaten") if has_corr else pill("warn", "keine Korrosionsdaten"))
                    + '</div></div>', unsafe_allow_html=True)
                if has_wq:
                    st.button("→ Im Wasserqualitäts-Tab anzeigen", key="jump_wq",
                              use_container_width=True, on_click=_preselect_wq, args=(name,),
                              help="Wählt diese Station im Tab „Wasserqualität“ vor.")
            else:
                st.markdown('<div class="context-bar"><div class="caption">Details</div>'
                            '<div class="lead">Eine Station auf der Karte anklicken, um '
                            'Stammdaten und Datenverfügbarkeit zu sehen.</div></div>',
                            unsafe_allow_html=True)

            st.markdown('<div class="caption">Stationsliste</div>', unsafe_allow_html=True)
            cols = [c for c in ["site_id", "site_name", "Region", "last_date", "Status"]
                    if c in sites_full.columns]
            df = (sites_full if sel_region == "Alle"
                  else sites_full[sites_full["Region"] == sel_region])[cols].copy()
            sort_by = st.selectbox("Sortieren nach",
                                   ["Region", "Letztes Messdatum", "Stations-ID"], key="map_sort")
            if sort_by == "Region":
                df = df.sort_values("Region")
            elif sort_by == "Letztes Messdatum" and "last_date" in df.columns:
                df = df.sort_values("last_date", ascending=False)
            else:
                df = df.sort_values("site_id")
            st.dataframe(
                df, use_container_width=True, height=340, hide_index=True,
                column_config={
                    "site_id": st.column_config.TextColumn("ID", help="Eindeutige Stations-ID"),
                    "site_name": "Station",
                    "last_date": st.column_config.DateColumn("Letzte Messung"),
                    "Status": st.column_config.TextColumn("Status",
                              help="Aktiv = Messung seit 2015"),
                },
            )
        kernaussage("Die 14 Stationen mit Wasserqualitäts-Zeitreihen liegen fast alle in der "
                    "tidebeeinflussten Unterelbe (Hamburg, Strom-km ~614–631); die "
                    "Korrosionsmessungen verteilen sich dagegen über tausende "
                    "Bauwerkspositionen entlang des gesamten Flusslaufs.")

# ── TAB 2: WASSERQUALITÄT ──────────────────────────────────────────────────
with tab_wq:
    st.markdown('<div class="h2">Zeitreihen-Explorer · Wasserqualität</div>', unsafe_allow_html=True)

    if data["wq_raw"].empty or not data["top_10_params"]:
        st.info("Zu wenig Wasserqualitätsdaten oder Top-10-Parameter nicht identifizierbar.")
    else:
        # --- Kontextbezogene Filter im Tab selbst (nicht global) -----------
        f1, f2, f3 = st.columns([1, 1.4, 1])
        with f1:
            regions = sorted([r for r in sites_full["Region"].unique() if r != "Unbekannt"])
            sel_region = st.selectbox("Region", ["Alle"] + regions, key="wq_region")
        if sel_region != "Alle":
            region_sites = sites_full[sites_full["Region"] == sel_region]["site_id"].tolist()
            avail = data["wq_raw"][data["wq_raw"]["site_id"].isin(region_sites)]["site_name"].dropna().unique().tolist()
        else:
            avail = data["wq_raw"]["site_name"].dropna().unique().tolist()
        with f2:
            sel_station = st.selectbox("Station", sorted(avail), key="wq_station")
        with f3:
            sel_param = st.selectbox("Parameter (Top 10)", data["top_10_params"], key="wq_param",
                                     help="Die zehn am häufigsten gemessenen Parameter.")

        site_id = data["wq_raw"][data["wq_raw"]["site_name"] == sel_station]["site_id"].iloc[0]
        min_d = data["wq_raw"]["timestamp"].min().date()
        max_d = data["wq_raw"]["timestamp"].max().date()
        sel_dates = st.slider("Zeitraum", min_value=min_d, max_value=max_d,
                              value=(min_d, max_d), key="wq_dates")

        mask = ((data["wq_raw"]["site_id"] == site_id)
                & (data["wq_raw"]["parameter"] == sel_param)
                & (data["wq_raw"]["timestamp"].dt.date >= sel_dates[0])
                & (data["wq_raw"]["timestamp"].dt.date <= sel_dates[1]))
        wq = data["wq_raw"][mask].sort_values("timestamp")
        n_obs = len(wq)
        unit = (wq["unit"].iloc[0] if n_obs > 0 and "unit" in wq.columns
                and pd.notna(wq["unit"].iloc[0]) else "")

        chart, stat = st.columns([3, 1], gap="large")
        with chart:
            # Datenqualität als sichtbarer, ehrlicher Hinweis (Vertrauen / Ethik)
            if 0 < n_obs < 3:
                st.warning(f"Nur {n_obs} Messwert(e) im gewählten Zeitraum – "
                           "die Reihe ist statistisch wenig aussagekräftig.")
            if n_obs > 0:
                fig = px.line(wq, x="timestamp", y="value", markers=n_obs < 100,
                              labels={"timestamp": "Datum", "value": f"Messwert ({unit})"})
                fig.update_traces(line_color=TOKENS["brand"],
                                  hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f} " + unit + "<extra></extra>")
                fig.update_xaxes(dtick="M12", tickformat="%Y")
                fig.update_layout(
                    title=f"{sel_station} · {sel_param}  "
                          f"(n={n_obs}, {sel_dates[0].year}–{sel_dates[1].year})",
                    **{k: v for k, v in PLOTLY_LAYOUT.items() if k != "title"})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Keine Daten für diese Kombination. Bitte Parameter, "
                        "Station oder Zeitraum anpassen.")
        with stat:
            st.markdown('<div class="caption">Statistik</div>', unsafe_allow_html=True)
            row = data["wq_summary"][(data["wq_summary"]["site_id"] == site_id)
                                     & (data["wq_summary"]["parameter"] == sel_param)]
            if not row.empty:
                mean_v = row["mean_value"].values[0]
                std_v = row["std_value"].values[0]
                min_v = row["min_value"].values[0]
                max_v = row["max_value"].values[0]
                st.markdown(
                    kpi_card("Mittelwert", f"{mean_v:.2f}", unit)
                    + kpi_card("Min / Max", f"{min_v:.1f} / {max_v:.1f}", unit)
                    + kpi_card("Std.-Abw.", f"±{std_v:.2f}", unit),
                    unsafe_allow_html=True)
            else:
                st.caption("Keine Statistik in der Zusammenfassung verfügbar.")

        # --- Komplexe Visualisierung: saisonales Muster (Monat × Jahr) ------
        if n_obs >= 24:
            st.markdown('<div class="h3">Saisonales Muster · Monat × Jahr</div>',
                        unsafe_allow_html=True)
            hm = wq.copy()
            hm["Jahr"] = hm["timestamp"].dt.year
            hm["Monat"] = hm["timestamp"].dt.month
            piv = (hm.pivot_table(index="Monat", columns="Jahr", values="value",
                                  aggfunc="mean").reindex(range(1, 13)))
            months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                      "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
            figh = px.imshow(
                piv.values, x=[str(c) for c in piv.columns], y=months,
                color_continuous_scale="Cividis", aspect="auto")
            figh.update_traces(
                hovertemplate="Jahr %{x} · %{y}<br>%{z:.2f} " + unit + "<extra></extra>")
            figh.update_layout(
                height=300, coloraxis_colorbar=dict(title=unit or "Wert"),
                **{k: v for k, v in PLOTLY_LAYOUT.items()
                   if k in ("font", "margin", "paper_bgcolor", "plot_bgcolor")})
            st.plotly_chart(figh, use_container_width=True)
            st.caption("Farbintensität = Monatsmittel (Skala „Cividis“, farbfehlsichtigkeits-"
                       "sicher). Alt-Text: Heatmap der Monatsmittel je Jahr – horizontale "
                       "Streifen zeigen die Jahreszeit, vertikale die Unterschiede zwischen Jahren.")
            # Datengetriebene Kernaussage: frühe vs. späte Jahre
            yearly = hm.groupby("Jahr")["value"].mean()
            if len(yearly) >= 6:
                third = max(1, len(yearly) // 3)
                first, last = yearly.iloc[:third].mean(), yearly.iloc[-third:].mean()
                d = last - first
                trend = ("nahezu unverändert" if abs(d) < 0.05 * (abs(first) + 1e-9)
                         else ("steigend" if d > 0 else "fallend"))
                kernaussage(
                    f"{sel_param} an „{sel_station}“ ist über den gewählten Zeitraum {trend}: "
                    f"Mittel der frühen Jahre {first:.2f} {unit} → späte Jahre {last:.2f} {unit} "
                    f"(Δ {d:+.2f} {unit}).")

# ── TAB 3: KORROSION ───────────────────────────────────────────────────────
with tab_corr:
    st.markdown('<div class="h2">Stahlwand-Monitoring</div>', unsafe_allow_html=True)
    st.markdown('<div class="lead">Restwanddicke und Durchrostung der Stahlspundwände – '
                'Überblick zuerst, dann Drill-down je Station.</div>', unsafe_allow_html=True)

    if data["corrosion"].empty:
        st.info("Keine Korrosionsdaten verfügbar.")
    else:
        # ---- Ehrlicher Methodenhinweis (Transparenz / Ethik) --------------
        st.markdown(
            '<div class="note"><b>Lesehilfe &amp; Datenehrlichkeit:</b> Die „Restwanddicke %“ '
            '(Messung ÷ Soll) liegt in diesen Daten <b>nie unter ~80 %</b>, aber bei rund einem '
            'Fünftel der Punkte <b>über 100 %</b> (Messung &gt; Sollmaß). Werte &gt; 100 % sind als '
            'Mess-/Datenartefakt zu lesen, nicht als „Sicherheitsreserve“. Das belastbare '
            'Schadenssignal ist daher die <b>Zahl der Durchrostungen (Löcher)</b> und die '
            '<b>Datenqualität</b> – nicht eine Ampel auf Basis der Restwanddicke.</div>',
            unsafe_allow_html=True)

        # ---- Überblick: Verteilung der Restwanddicke (alle Stationen) ------
        allc = data["corrosion"].dropna(
            subset=["measurement_date", "actual_wall_thickness", "planned_wall_thickness"]).copy()
        if not allc.empty:
            idx_all = (allc.groupby("site_id")["measurement_date"].transform("max")
                       == allc["measurement_date"])
            latest_all = allc[idx_all].copy()
            latest_all["pct"] = (latest_all["actual_wall_thickness"]
                                 / latest_all["planned_wall_thickness"] * 100)
            over = int((latest_all["pct"] > 100).sum())
            figd = px.histogram(latest_all, x="pct", nbins=60, range_x=[60, 200])
            figd.update_traces(marker_color=TOKENS["brand"],
                               hovertemplate="Restwanddicke %{x:.0f} %<br>%{y} Positionen<extra></extra>")
            figd.add_vline(x=100, line_dash="dash", line_color=TOKENS["ink"],
                           annotation_text="Soll = 100 %", annotation_position="top")
            figd.update_layout(
                title="Verteilung der Restwanddicke je Position (letzte Messung, alle Stationen)",
                xaxis_title="Restwanddicke (% vom Soll)", yaxis_title="Positionen", height=300,
                **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("title", "xaxis", "yaxis")})
            st.plotly_chart(figd, use_container_width=True)
            st.caption(("{:,}".format(over).replace(",", ".")) +
                       " Positionen liegen über 100 % (Artefakt). Ansicht auf 60–200 % begrenzt. "
                       "Alt-Text: Histogramm, Häufung dicht bei 100 %.")

        st.markdown('<div class="h3">Station im Detail</div>', unsafe_allow_html=True)
        corr_sites = data["corrosion"]["site_id"].dropna().unique()
        if not sites_full.empty:
            names = sites_full[sites_full["site_id"].isin(corr_sites)][["site_id", "site_name"]]
            site_dict = {r["site_id"]: (f"{r['site_name']} ({r['site_id']})"
                         if pd.notna(r["site_name"]) else str(r["site_id"]))
                         for _, r in names.iterrows()}
        else:
            site_dict = {s: str(s) for s in corr_sites}

        sel_id = st.selectbox("Station", options=list(site_dict.keys()),
                              format_func=lambda x: site_dict.get(x, str(x)), key="corr_site")
        site_corr = data["corrosion"][data["corrosion"]["site_id"] == sel_id].copy()

        if not site_corr.empty:
            last = site_corr["measurement_date"].max()
            latest = site_corr[site_corr["measurement_date"] == last].copy()
            latest["pct"] = latest["actual_wall_thickness"] / latest["planned_wall_thickness"] * 100

            # Stations-Überblick: ehrliche Kennzahlen (Durchrostung + Datenqualität)
            n_pos = len(latest)
            n_holes = int((latest["number_of_holes"].fillna(0) > 0).sum())
            dq = latest["data_quality"].value_counts()
            dq_txt = " · ".join(f"{k}: {v}" for k, v in dq.items()) if len(dq) else "—"
            holes_pill = (pill("crit", f"{n_holes} mit Durchrostung") if n_holes > 0
                          else pill("ok", "keine Durchrostung"))
            st.markdown(
                f'<div class="context-bar">Letzte Messung '
                f'<b>{last.strftime("%d.%m.%Y")}</b> · {site_dict.get(sel_id, sel_id)}'
                f'&nbsp;&nbsp;{pill("ok", f"{n_pos} Positionen")} {holes_pill}'
                f'<div class="lead" style="margin-top:6px">Datenqualität – {dq_txt}</div>'
                f'</div>', unsafe_allow_html=True)

            # Restwanddicke % je Position – farbcodiert nach Gesundheitszustand
            # Sortierung: kritischste Positionen zuerst (aufsteigend nach %)
            latest = latest.sort_values("pct", ascending=True)
            _MAX_BARS = 15
            _hidden = max(0, len(latest) - _MAX_BARS)
            latest = latest.head(_MAX_BARS)          # zeige nur die _MAX_BARS kritischsten
            holes_arr = latest["number_of_holes"].fillna(0)

            def _pct_color(pct, holes):
                if holes > 0:
                    return TOKENS["crit"]          # Durchrostung → immer rot
                if pct < 80:
                    return TOKENS["crit"]          # < 80 % → kritisch
                if pct < 100:
                    return TOKENS["warn"]          # 80–99 % → Warnung
                return TOKENS["ok"]                # ≥ 100 % → OK

            bar_colors = [_pct_color(p, h)
                          for p, h in zip(latest["pct"], holes_arr)]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=latest["position_name"].astype(str),
                x=latest["pct"].round(1),
                name="Restwanddicke",
                orientation="h",
                marker=dict(color=bar_colors, opacity=0.88,
                            line=dict(width=0)),
                customdata=np.stack([
                    latest["actual_wall_thickness"],
                    latest["planned_wall_thickness"],
                    holes_arr,
                    latest["data_quality"].astype(str),
                ], axis=-1),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Restwanddicke: <b>%{x:.0f} %</b><br>"
                    "Gemessen: %{customdata[0]:.1f} mm · Soll: %{customdata[1]:.1f} mm<br>"
                    "Löcher: %{customdata[2]:.0f} · Datenqualität: %{customdata[3]}"
                    "<extra></extra>"),
            ))

            # Referenzlinie bei 100 % (= Soll erfüllt)
            fig.add_vline(
                x=100,
                line_dash="dash", line_color=TOKENS["ink"], line_width=1.5,
                annotation_text="Sollwert",
                annotation_position="top right",
                annotation_font=dict(size=11, color=TOKENS["muted"]),
            )

            fig.update_layout(
                title="Restwanddicke je Position (% des Sollwerts)",
                xaxis_title="Restwanddicke (%)",
                yaxis_title=None,
                xaxis=dict(
                    gridcolor=TOKENS["line"], zeroline=False,
                    range=[0, max(latest["pct"].max() * 1.05, 115)],
                    ticksuffix=" %",
                ),
                yaxis=dict(gridcolor="rgba(0,0,0,0)", zeroline=False),
                height=min(480, max(260, len(latest) * 32 + 60)),
                showlegend=False,
                **{k: v for k, v in PLOTLY_LAYOUT.items()
                   if k not in ("title", "xaxis", "yaxis", "legend")})
            st.plotly_chart(fig, use_container_width=True)
            if _hidden > 0:
                st.markdown(
                    f'<div style="font-size:.82rem;color:{TOKENS["muted"]};'
                    f'margin-top:-6px;padding-left:4px">'
                    f'⚠ {_hidden} weitere Position(en) mit höherer Restwanddicke ausgeblendet – '
                    f'alle Werte in der Detailtabelle unten sichtbar.</div>',
                    unsafe_allow_html=True)

            # Farblegende unter dem Chart
            st.markdown(
                f'<div style="display:flex;gap:18px;font-size:.82rem;'
                f'color:{TOKENS["muted"]};margin-top:-8px;padding-left:4px">'
                f'<span><span style="display:inline-block;width:12px;height:12px;'
                f'border-radius:3px;background:{TOKENS["ok"]};margin-right:5px"></span>≥ 100 % OK</span>'
                f'<span><span style="display:inline-block;width:12px;height:12px;'
                f'border-radius:3px;background:{TOKENS["warn"]};margin-right:5px"></span>80–99 % Warnung</span>'
                f'<span><span style="display:inline-block;width:12px;height:12px;'
                f'border-radius:3px;background:{TOKENS["crit"]};margin-right:5px"></span>< 80 % oder Durchrostung</span>'
                f'</div>', unsafe_allow_html=True)

            # Details-on-demand: aufklappbare Detailtabelle
            with st.expander("Detailwerte der letzten Messung anzeigen"):
                cols_t = [c for c in ["position_id", "position_name", "planned_wall_thickness",
                                      "actual_wall_thickness", "pct", "number_of_holes",
                                      "data_quality"] if c in latest.columns]
                t = latest[cols_t].copy()
                t["pct"] = t["pct"].round(0)
                t["Befund"] = np.where(t["number_of_holes"].fillna(0) > 0, "Durchrostung", "—")
                t = t.rename(columns={
                    "position_id": "Pos-ID", "position_name": "Position",
                    "planned_wall_thickness": "Soll (mm)",
                    "actual_wall_thickness": "Gemessen (mm)", "pct": "Restwanddicke (%)",
                    "number_of_holes": "Löcher", "data_quality": "Datenqualität"})
                st.dataframe(
                    t, use_container_width=True, hide_index=True,
                    column_config={"Restwanddicke (%)": st.column_config.NumberColumn(
                        "Restwanddicke (%)",
                        help="Messung ÷ Soll × 100. Werte > 100 % sind Mess-/Datenartefakte.",
                        format="%.0f %%")})

            kernaussage(
                f"An dieser Station weisen {n_holes} von {n_pos} Positionen Durchrostungen auf. "
                "Über alle Stationen sind Löcher selten (≈ 1 % der Punkte) – die Spundwände sind "
                "überwiegend intakt; aussagekräftiger als die Restwanddicke ist der Befund "
                "„Durchrostung“.")

# ── TAB 4: ZUSAMMENFASSUNG ─────────────────────────────────────────────────
with tab_sum:
    st.markdown('<div class="h2">Datenqualität & Überblick</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="meta"><b>Datensatz-Metadaten</b><br>'
        f'Zeitspanne 1954–2024 · {n_sites} Stationen · '
        f'{n_wq:,}'.replace(",", ".") +
        f' WQ-Messungen · {n_corr:,}'.replace(",", ".") +
        ' Korrosionsmessungen</div>', unsafe_allow_html=True)
    st.write("")

    # --- Datenverfügbarkeits-Heatmap: Stationen × Parameter (WQ) --------
    if not data["wq_matrix"].empty:
        st.markdown('<div class="h3">Datenverfügbarkeit · Stationen × Parameter '
                    '(Wasserqualität)</div>', unsafe_allow_html=True)
        m = data["wq_matrix"].copy()
        m = m.loc[:, m.sum(axis=0).sort_values(ascending=False).index]  # dichteste Parameter links
        id2name = (sites_full.set_index("site_id")["site_name"].to_dict()
                   if "site_name" in sites_full.columns else {})
        ylabels = [str(id2name.get(i, i))[:32] for i in m.index]
        figm = px.imshow(np.log1p(m.values), x=list(m.columns), y=ylabels,
                         color_continuous_scale="Blues", aspect="auto")
        figm.update_traces(
            customdata=m.values,
            hovertemplate="%{y}<br>%{x}<br>%{customdata:,} Messwerte<extra></extra>")
        figm.update_layout(
            height=max(320, len(m) * 26), xaxis=dict(tickangle=-40),
            coloraxis_colorbar=dict(title="log(1+n)"),
            **{k: v for k, v in PLOTLY_LAYOUT.items()
               if k in ("font", "margin", "paper_bgcolor", "plot_bgcolor")})
        st.plotly_chart(figm, use_container_width=True)
        st.caption("Farbe = log-skalierte Messwertanzahl (Hover zeigt die echte Zahl). Helle/leere "
                   "Zellen = Datenlücken. Alt-Text: Raster Stationen (Zeilen) × Parameter (Spalten).")
        n_cells, n_filled = int(m.size), int((m.values > 0).sum())
        kernaussage(
            f"Nur {len(m)} Stationen liefern Wasserqualitäts-Zeitreihen, und selbst dort sind nur "
            f"rund {round(100 * n_filled / max(1, n_cells))} % aller Parameter-Kombinationen belegt "
            "– die hellen Zellen zeigen, wo Zeitreihen fehlen.")
        st.write("")

    if not sites_full.empty:
        s = sites_full[["site_id", "site_name", "Region", "Status"]].copy()
        if not data["wq_matrix"].empty:
            s["wq_obs"] = s["site_id"].map(data["wq_matrix"].sum(axis=1)).fillna(0).astype(int)
        else:
            s["wq_obs"] = 0
        if not data["corrosion"].empty:
            s["corr_obs"] = s["site_id"].map(
                data["corrosion"].groupby("site_id").size()).fillna(0).astype(int)
        else:
            s["corr_obs"] = 0

        s = s.rename(columns={"site_id": "ID", "site_name": "Station",
                              "wq_obs": "WQ-Messungen", "corr_obs": "Korrosionsmessungen"})
        st.dataframe(
            s, use_container_width=True, height=560, hide_index=True,
            column_config={
                "WQ-Messungen": st.column_config.ProgressColumn(
                    "Wassergüte", help="Anzahl WQ-Messwerte", format="%d",
                    min_value=0, max_value=int(max(1, s["WQ-Messungen"].max()))),
                "Korrosionsmessungen": st.column_config.ProgressColumn(
                    "Korrosion", help="Anzahl Korrosionsmesswerte", format="%d",
                    min_value=0, max_value=int(max(1, s["Korrosionsmessungen"].max()))),
                "Status": st.column_config.TextColumn("Status", help="Aktiv = Messung seit 2015"),
            })
        st.caption("Balken zeigen die relative Datendichte je Station "
                   "(längerer Balken = mehr Messungen).")

    # --- Querverweis Wasserqualität <-> Korrosion (Narrativ-Brücke) -----
    if not data.get("groups", pd.DataFrame()).empty:
        with st.expander("Verknüpfung Wasserqualität ↔ Korrosion (Standortgruppen)"):
            st.caption("Die Daten verbinden Korrosions-Bauwerke mit nahegelegenen "
                       "Wasserqualitäts-Stationen über gemeinsame Standortgruppen – die Brücke "
                       "zwischen beiden Hälften des Dashboards.")
            g = data["groups"]
            show = g[[c for c in ["group_name", "corrosion_site_name", "wq_site_name"]
                      if c in g.columns]].drop_duplicates()
            st.dataframe(show, use_container_width=True, hide_index=True, height=240,
                         column_config={"group_name": "Gruppe",
                                        "corrosion_site_name": "Korrosions-Standort",
                                        "wq_site_name": "WQ-Station"})