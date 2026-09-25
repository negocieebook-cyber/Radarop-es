"""Tema visual centralizado do Radar de Opcoes Brasil."""

from __future__ import annotations

import streamlit as st


COLORS = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "sidebar": "#0F172A",
    "text": "#111827",
    "muted": "#64748B",
    "border": "#E2E8F0",
    "green": "#15803D",
    "yellow": "#D97706",
    "red": "#DC2626",
    "blue": "#2563EB",
}


def get_theme_css() -> str:
    return f"""
    <style>
    :root {{
      --bg: {COLORS["bg"]};
      --surface: {COLORS["surface"]};
      --sidebar: {COLORS["sidebar"]};
      --text: {COLORS["text"]};
      --muted: {COLORS["muted"]};
      --border: {COLORS["border"]};
      --green: {COLORS["green"]};
      --yellow: {COLORS["yellow"]};
      --red: {COLORS["red"]};
      --blue: {COLORS["blue"]};
    }}
    #MainMenu, footer, [data-testid="stHeader"] {{
      visibility: hidden;
    }}
    .stApp {{
      background: var(--bg);
      color: var(--text);
      font-family: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
    }}
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {{
      color: var(--text);
    }}
    .block-container {{
      max-width: 1200px;
      padding-top: 22px;
      padding-bottom: 36px;
      padding-left: 28px;
      padding-right: 28px;
    }}
    h1, h2, h3 {{
      color: var(--text) !important;
      letter-spacing: -0.02em;
    }}
    h1 {{
      font-size: 32px !important;
      line-height: 1.15 !important;
      font-weight: 700 !important;
      margin-bottom: 4px !important;
    }}
    h2 {{
      font-size: 22px !important;
      line-height: 1.2 !important;
      font-weight: 700 !important;
    }}
    h3 {{
      font-size: 17px !important;
      line-height: 1.25 !important;
      font-weight: 600 !important;
    }}
    p, li, label, [data-testid="stMarkdownContainer"] {{
      font-size: 14px;
    }}
    .stCaption, .muted-copy {{
      color: var(--muted) !important;
      font-size: 13px !important;
    }}
    [data-baseweb="input"] input,
    [data-baseweb="select"] input,
    textarea,
    input {{
      color: var(--text) !important;
    }}
    [data-testid="stSidebar"] {{
      background: var(--sidebar);
      border-right: 1px solid #1F2937;
      min-width: 240px;
      max-width: 250px;
    }}
    [data-testid="stSidebar"] .block-container {{
      padding-top: 20px;
      padding-left: 16px;
      padding-right: 16px;
    }}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {{
      color: #E5E7EB;
    }}
    [data-testid="stSidebarNav"] {{
      padding: 0;
    }}
    [data-testid="stSidebarNav"] > div {{
      gap: 2px;
    }}
    [data-testid="stSidebarNav"] .stSidebarNavSection {{
      color: #94A3B8;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 0 10px;
    }}
    [data-testid="stSidebarNav"] a {{
      background: transparent;
      border-radius: 12px;
      border-left: 3px solid transparent;
      padding: 10px 12px;
      margin: 2px 0;
      transition: background 0.15s ease, border-color 0.15s ease;
    }}
    [data-testid="stSidebarNav"] a:hover {{
      background: #162033;
    }}
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
      background: #1F2937;
      border-left-color: var(--blue);
    }}
    [data-testid="stSidebarNav"] a span {{
      color: #E5E7EB !important;
      font-size: 14px;
    }}
    [data-testid="stSidebarNav"] a[aria-current="page"] span {{
      color: #FFFFFF !important;
      font-weight: 600;
    }}
    [data-testid="stSidebarNav"] a svg {{
      color: #94A3B8;
    }}
    .sidebar-title {{
      color: #FFFFFF;
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 20px;
    }}
    .sidebar-group {{
      color: #94A3B8;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin: 18px 0 10px;
    }}
    .small-label {{
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .header-row {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 8px;
    }}
    .header-meta {{
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: flex-end;
      flex-wrap: wrap;
    }}
    .eyebrow {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 6px;
    }}
    .page-header {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin: 4px 0 14px;
    }}
    .page-header h1.page-title {{
      margin: 0 !important;
      font-size: 30px !important;
      line-height: 1.15 !important;
    }}
    .page-header-badge {{
      margin-top: 4px;
    }}
    .page-desc {{
      margin: 6px 0 0;
      font-size: 13.5px;
      color: var(--muted);
      max-width: 720px;
      line-height: 1.5;
    }}
    .howto-box {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px 10px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 8px 14px;
      margin: -4px 0 14px;
      font-size: 12.5px;
      color: var(--muted);
    }}
    .howto-label {{
      font-weight: 700;
      font-size: 10.5px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--blue);
    }}
    .howto-step {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      color: var(--text);
    }}
    .howto-num {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: rgba(37, 99, 235, 0.12);
      color: var(--blue);
      font-size: 10.5px;
      font-weight: 700;
      flex-shrink: 0;
    }}
    .howto-sep {{
      color: var(--border);
      font-weight: 700;
    }}
    .section-title {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 12px;
      margin: 22px 0 10px;
    }}
    .section-title p {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .surface-card,
    .metric-card,
    .compact-card,
    .section-card,
    .sidebar-inline,
    .empty-state {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }}
    .surface-card {{
      padding: 14px 16px;
    }}
    .section-card {{
      padding: 14px 16px;
      margin: 10px 0;
    }}
    .metric-card {{
      padding: 14px 16px 12px;
      min-height: 104px;
    }}
    .metric-label {{
      font-size: 12.5px;
      font-weight: 600;
      color: var(--muted);
    }}
    .metric-value {{
      font-size: 30px;
      line-height: 1.1;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-top: 4px;
    }}
    .metric-value.v-neutral {{ color: var(--text); }}
    .metric-value.v-approved {{ color: var(--green); }}
    .metric-value.v-warning {{ color: #B45309; }}
    .metric-value.v-rejected {{ color: var(--red); }}
    .metric-value.v-info {{ color: var(--blue); }}
    .metric-note {{
      font-size: 12px;
      color: #94A3B8;
      margin-top: 4px;
    }}
    .badge,
    .status-badge,
    .mock-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 9px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      border: 1px solid transparent;
      white-space: nowrap;
    }}
    .status-approved {{
      background: #ECFDF3;
      border-color: #BBF7D0;
      color: var(--green);
    }}
    .status-warning {{
      background: #FEF7E7;
      border-color: #FDE68A;
      color: var(--yellow);
    }}
    .status-rejected {{
      background: #FEF2F2;
      border-color: #FECACA;
      color: var(--red);
    }}
    .status-info {{
      background: #EFF6FF;
      border-color: #BFDBFE;
      color: var(--blue);
    }}
    .status-neutral {{
      background: #F8FAFC;
      border-color: #E2E8F0;
      color: var(--muted);
    }}
    .mock-badge {{
      background: #F8FAFC;
      border-color: #E2E8F0;
      color: var(--muted);
    }}
    .compact-banner {{
      margin: 10px 0 16px;
      padding: 10px 12px;
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 12px;
      color: var(--text);
      font-size: 13px;
    }}
    .summary {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin-top: 8px;
    }}
    .decision-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.9fr) minmax(300px, 1fr);
      gap: 18px;
      align-items: start;
      margin-top: 18px;
    }}
    .integrated-panel {{
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding: 6px 0 2px;
    }}
    .stack {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .empty-state {{
      padding: 28px 24px;
      text-align: center;
    }}
    .empty-title {{
      font-size: 20px;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 6px;
    }}
    .empty-copy {{
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 16px;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 3px 10px 3px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }}
    .pill::before {{
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: currentColor;
      opacity: 0.85;
    }}
    .pill-approved {{ background: #ECFDF3; color: #15803D; }}
    .pill-warning {{ background: #FEF6E7; color: #B45309; }}
    .pill-rejected {{ background: #FEF2F2; color: #B91C1C; }}
    .pill-info {{ background: #EFF6FF; color: #1D4ED8; }}
    .pill-neutral {{ background: #F1F5F9; color: #64748B; }}
    .pill-ghost {{
      background: transparent;
      border: 1px dashed #CBD5E1;
      color: #94A3B8;
      font-weight: 600;
    }}
    .pill-ghost::before {{ display: none; }}
    .op-card {{
      position: relative;
      background: var(--surface);
      border: 1px solid #E6EAF2;
      border-radius: 14px;
      padding: 14px 16px 13px 20px;
      margin: 0 0 4px;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    }}
    .op-card::before {{
      content: "";
      position: absolute;
      left: 8px;
      top: 14px;
      bottom: 14px;
      width: 3px;
      border-radius: 3px;
      background: #CBD5E1;
    }}
    .op-card.c-approved::before {{ background: #22C55E; }}
    .op-card.c-warning::before {{ background: #F59E0B; }}
    .op-card.c-rejected::before {{ background: #EF4444; }}
    .op-card.c-info::before {{ background: #3B82F6; }}
    .op-card:hover {{
      border-color: #D7DEEA;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
    }}
    .op-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }}
    .op-badges {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }}
    .op-eyebrow {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #94A3B8;
    }}
    .op-ticker {{
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.01em;
      color: var(--text);
      line-height: 1.2;
    }}
    .op-line {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 3px 0 9px;
    }}
    .op-strategy {{
      font-size: 13.5px;
      font-weight: 600;
      color: #334155;
    }}
    .op-score {{
      font-size: 12px;
      font-weight: 700;
      color: #1D4ED8;
      background: #EFF6FF;
      border-radius: 999px;
      padding: 2px 9px;
    }}
    .op-fields {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin: 0;
      border-top: 1px dashed #EEF2F7;
    }}
    .op-field {{
      padding: 7px 14px 7px 0;
      border-top: 1px dashed #EEF2F7;
      min-width: 0;
    }}
    .op-fields .op-field:nth-child(-n + 2) {{ border-top: none; }}
    .op-field:nth-child(even) {{
      border-left: 1px dashed #EEF2F7;
      padding-left: 14px;
    }}
    .op-field dt {{
      font-size: 10.5px;
      font-weight: 700;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      color: #94A3B8;
      margin-bottom: 2px;
    }}
    .op-field dd {{
      margin: 0;
      font-size: 13.5px;
      font-weight: 500;
      color: var(--text);
      line-height: 1.35;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .op-reason {{
      margin-top: 8px;
      font-size: 12.5px;
      color: var(--muted);
      line-height: 1.45;
    }}
    .mkt-card {{
      position: relative;
      background: var(--surface);
      border: 1px solid #E6EAF2;
      border-radius: 14px;
      padding: 14px 16px 12px 20px;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    }}
    .mkt-card::before {{
      content: "";
      position: absolute;
      left: 8px;
      top: 14px;
      bottom: 14px;
      width: 3px;
      border-radius: 3px;
      background: #CBD5E1;
    }}
    .mkt-card.c-approved::before {{ background: #22C55E; }}
    .mkt-card.c-warning::before {{ background: #F59E0B; }}
    .mkt-card.c-rejected::before {{ background: #EF4444; }}
    .mkt-card.c-info::before {{ background: #3B82F6; }}
    .mkt-price {{
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: var(--text);
      margin: 4px 0 10px;
      display: flex;
      align-items: baseline;
      gap: 10px;
    }}
    .chg {{ font-size: 13px; font-weight: 700; }}
    .chg.up {{ color: #15803D; }}
    .chg.down {{ color: #DC2626; }}
    .chg.flat {{ color: var(--muted); }}
    .mkt-stats {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin: 0;
      border-top: 1px dashed #EEF2F7;
    }}
    .mkt-stat {{
      padding: 7px 10px 7px 0;
      border-top: 1px dashed #EEF2F7;
    }}
    .mkt-stats .mkt-stat:nth-child(-n + 2) {{ border-top: none; }}
    .mkt-stat:nth-child(even) {{
      border-left: 1px dashed #EEF2F7;
      padding-left: 12px;
    }}
    .mkt-stat dt {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #94A3B8;
      margin-bottom: 2px;
      white-space: nowrap;
    }}
    .mkt-stat dd {{
      margin: 0;
      font-size: 14px;
      font-weight: 600;
      color: var(--text);
    }}
    .mkt-foot {{
      margin-top: 9px;
      padding-top: 8px;
      border-top: 1px solid #F1F5F9;
      font-size: 11.5px;
      color: #94A3B8;
    }}
    .info-row {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0 18px;
    }}
    .info-box {{
      padding: 8px 0;
      border: 0;
      border-bottom: 1px dashed #EEF2F7;
      border-radius: 0;
      background: transparent;
    }}
    .info-box b {{
      display: block;
      color: #94A3B8;
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      margin-bottom: 2px;
    }}
    .info-box span {{
      color: var(--text);
      font-size: 14px;
      font-weight: 600;
    }}
    .status-strip {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 0 18px;
    }}
    .status-item {{
      padding: 8px 0;
      border: 0;
      border-bottom: 1px dashed #EEF2F7;
      border-radius: 0;
      background: transparent;
    }}
    .status-item b {{
      display: block;
      font-size: 10.5px;
      color: #94A3B8;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      margin-bottom: 2px;
    }}
    .status-item span {{
      color: var(--text);
      font-size: 14px;
      font-weight: 600;
    }}
    .detail-box,
    .compact-line {{
      padding: 8px 0;
      border: 0;
      border-bottom: 1px dashed #EEF2F7;
      border-radius: 0;
      background: transparent;
    }}
    .detail-box b,
    .compact-line b {{
      display: block;
      color: #94A3B8;
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      margin-bottom: 2px;
    }}
    .detail-box span,
    .compact-line span {{
      color: var(--text);
      font-size: 14px;
      font-weight: 600;
    }}
    .compact-row,
    .detail-list {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0 18px;
      margin-top: 8px;
    }}
    .asset {{
      font-size: 20px;
      font-weight: 700;
      color: var(--text);
      line-height: 1.2;
    }}
    .top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 10px;
    }}
    .alert-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-left: 4px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
      margin: 8px 0;
    }}
    .alert-card.red {{
      border-left-color: var(--red);
    }}
    .alert-card.yellow {{
      border-left-color: var(--yellow);
    }}
    .alert-card.green {{
      border-left-color: var(--green);
    }}
    .alert-card.gray {{
      border-left-color: #94A3B8;
    }}
    .alert-card b,
    .alert-card span,
    .alert-card small {{
      color: var(--text);
    }}
    .alert-card small {{
      display: inline-block;
      margin-top: 4px;
      color: var(--muted);
    }}
    [data-testid="stDataFrame"] {{
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      background: #FFFFFF;
    }}
    [data-testid="stExpander"] {{
      border: 1px solid var(--border);
      border-radius: 12px;
      background: #FFFFFF;
    }}
    [data-testid="stForm"] {{
      border: 1px solid var(--border);
      border-radius: 12px;
      background: #FFFFFF;
      padding: 14px;
    }}
    div.stButton > button {{
      width: auto;
      border-radius: 10px;
      min-height: 34px;
      padding: 0 14px;
      border: 1px solid var(--border);
      background: #FFFFFF;
      color: var(--text);
      font-size: 13px;
      font-weight: 600;
      box-shadow: none;
      white-space: nowrap;
    }}
    div.stButton > button:hover {{
      border-color: #CBD5E1;
      background: #F8FAFC;
      color: var(--text);
    }}
    div.stButton > button[kind="primary"] {{
      background: var(--blue);
      border-color: var(--blue);
      color: #FFFFFF;
    }}
    div.stButton > button[kind="primary"]:hover {{
      background: #1D4ED8;
      border-color: #1D4ED8;
      color: #FFFFFF;
    }}
    [data-testid="stSidebar"] div.stButton > button {{
      width: 100%;
      background: transparent;
      border: none;
      border-left: 3px solid transparent;
      color: #E5E7EB;
      justify-content: flex-start;
      min-height: 36px;
      padding: 8px 12px;
      text-align: left;
    }}
    [data-testid="stSidebar"] div.stButton > button:hover {{
      background: #162033;
      border: none;
      border-left: 3px solid transparent;
      color: #E5E7EB;
    }}
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {{
      background: #1F2937;
      border-left-color: var(--blue);
      color: #FFFFFF;
      font-weight: 600;
    }}
    [data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover {{
      background: #334155;
      border-left-color: var(--blue);
      color: #FFFFFF;
    }}
    .secondary-note {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 8px;
    }}
    @media (max-width: 1100px) {{
      .decision-layout {{
        grid-template-columns: 1fr;
      }}
      .op-fields {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .mkt-stats {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .mkt-stats .mkt-stat:nth-child(n + 3) {{
        border-top: 1px dashed #EEF2F7;
      }}
      .mkt-stats .mkt-stat:nth-child(even) {{
        border-left: 1px dashed #EEF2F7;
        padding-left: 12px;
      }}
      .compact-row,
      .detail-list,
      .status-strip {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 760px) {{
      .block-container {{
        padding-left: 16px;
        padding-right: 16px;
      }}
      .header-row {{
        flex-direction: column;
      }}
      .header-meta {{
        justify-content: flex-start;
      }}
      .op-fields,
      .mkt-stats,
      .info-row {{
        grid-template-columns: 1fr;
      }}
      .op-field:nth-child(even),
      .mkt-stats .mkt-stat:nth-child(even) {{
        border-left: none;
        padding-left: 0;
      }}
    }}
    </style>
    """


def apply_theme() -> None:
    try:
        st.set_page_config(page_title="Radar de Opções Brasil", page_icon="📡", layout="wide")
    except Exception:
        # Streamlit raises if page config was already set in this run.
        pass
    st.markdown(get_theme_css(), unsafe_allow_html=True)
