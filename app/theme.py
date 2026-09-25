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
    [data-testid="stSidebar"] .stRadio label {{
      color: #E5E7EB !important;
    }}
    [data-testid="stSidebar"] .stRadio > div {{
      gap: 2px;
    }}
    [data-testid="stSidebar"] .stRadio label > div:first-child {{
      background-color: #1F2937 !important;
      border-color: #334155 !important;
    }}
    [data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {{
      padding: 10px 12px;
      border-radius: 12px;
      border-left: 3px solid transparent;
      margin: 0 0 4px 0;
      transition: background 0.15s ease, border-color 0.15s ease;
    }}
    [data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {{
      background: #162033;
    }}
    [data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked) {{
      background: #1F2937;
      border-left-color: var(--blue);
    }}
    [data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked) p {{
      color: #FFFFFF !important;
      font-weight: 600;
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
      padding: 14px 16px;
      min-height: 98px;
    }}
    .metric-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
    }}
    .metric-value {{
      font-size: 28px;
      line-height: 1;
      font-weight: 700;
      color: var(--text);
    }}
    .metric-label {{
      font-size: 14px;
      font-weight: 600;
      color: var(--text);
    }}
    .metric-note {{
      font-size: 12px;
      color: var(--muted);
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
    .compact-card {{
      padding: 14px 16px;
      max-width: 100%;
      margin: 0;
    }}
    .compact-top {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }}
    .compact-asset {{
      font-size: 18px;
      font-weight: 700;
      color: var(--text);
    }}
    .compact-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      margin: 10px 0;
    }}
    .compact-kv {{
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 8px 10px;
      background: #FCFDFE;
    }}
    .compact-kv b {{
      display: block;
      font-size: 11px;
      line-height: 1.2;
      color: var(--muted);
      font-weight: 600;
      margin-bottom: 2px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .compact-kv span {{
      display: block;
      font-size: 13px;
      line-height: 1.35;
      color: var(--text);
      font-weight: 500;
    }}
    .compact-summary {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin-top: 2px;
    }}
    .compact-actions {{
      margin-top: 8px;
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
    .info-row {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .info-box {{
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: #FFFFFF;
    }}
    .info-box b {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 3px;
    }}
    .info-box span {{
      color: var(--text);
      font-size: 14px;
      font-weight: 600;
    }}
    .status-strip {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .status-item {{
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: #FFFFFF;
    }}
    .status-item b {{
      display: block;
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 3px;
    }}
    .status-item span {{
      color: var(--text);
      font-size: 14px;
      font-weight: 600;
    }}
    .detail-box,
    .compact-line {{
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: #FCFDFE;
    }}
    .detail-box b,
    .compact-line b {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 3px;
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
      gap: 10px;
      margin-top: 10px;
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
      width: 100%;
      border-radius: 10px;
      min-height: 38px;
      border: 1px solid var(--border);
      background: #FFFFFF;
      color: var(--text);
      font-size: 14px;
      font-weight: 600;
      box-shadow: none;
    }}
    div.stButton > button:hover {{
      border-color: #CBD5E1;
      background: #F8FAFC;
      color: var(--text);
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
      .compact-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
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
      .compact-grid,
      .info-row {{
        grid-template-columns: 1fr;
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
