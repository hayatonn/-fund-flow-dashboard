"""
streamlit_app.py - Streamlit Cloud Deployment Version
Mobile-first, responsive US Stock Fund Flow Dashboard for Streamlit Community Cloud.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from fetcher import get_fund_flow_data, fetch_live_market_data, SECTOR_THEME_DEFINITIONS

# Page Config
st.set_page_config(
    page_title="米国株 資金フロー Top10",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling (Mobile optimized)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=JetBrains+Mono:wght@600;700&family=Noto+Sans+JP:wght@500;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        color: white;
        padding: 20px 24px;
        border-radius: 14px;
        margin-bottom: 20px;
        border: 1px solid #334155;
    }
    
    .main-title {
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .subtitle {
        font-size: 0.85rem;
        color: #94a3b8;
    }

    .flow-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .card-top1 {
        background: #f0f7ff;
        border-color: #93c5fd;
    }
    
    .rank-num {
        font-size: 1.1rem;
        font-weight: 800;
        color: #64748b;
        width: 28px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .theme-name {
        font-size: 1.0rem;
        font-weight: 700;
        color: #0f172a;
    }
    
    .badge-gray {
        background: #f1f5f9;
        color: #64748b;
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
    }

    .badge-streak {
        background: #ecfdf5;
        color: #059669;
        border: 1px solid #a7f3d0;
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 700;
    }
    
    .badge-streak-neg {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 700;
    }
    
    .flow-amount-pos {
        font-size: 1.15rem;
        font-weight: 800;
        color: #059669;
        font-family: 'JetBrains Mono', monospace;
        text-align: right;
    }

    .flow-amount-neg {
        font-size: 1.15rem;
        font-weight: 800;
        color: #dc2626;
        font-family: 'JetBrains Mono', monospace;
        text-align: right;
    }
    
    .flow-sub {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748b;
        text-align: right;
        font-family: 'JetBrains Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown("""
<div class="main-header">
    <div class="main-title">💰 資金フロー Top10 / Bottom10</div>
    <div class="subtitle">売買代金 × 騰落方向で概算した資金の向きです（実需を捉える出来高加重フロー推計）</div>
</div>
""", unsafe_allow_html=True)

# Load / Cache Data
@st.cache_data(ttl=3600)
def load_data():
    return get_fund_flow_data(force_refresh=False)

data = load_data()

# Refresh trigger
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 1])

with col_ctrl1:
    unit_mode = st.radio("集計単位", ["大分類", "テーマ"], horizontal=True)

with col_ctrl2:
    sort_mode = st.radio("並べ替え", ["金額順", "流入率順"], horizontal=True)

with col_ctrl3:
    real_only = st.checkbox("本物の流入だけ (出来高倍率 1.2x+)", value=False)

if st.button("🔄 市場データを最新化 (再計算)"):
    with st.spinner("米国市場から最新の株価・出来高データを取得中..."):
        data = fetch_live_market_data()
        st.cache_data.clear()
        st.success("最新データに更新しました！")

# Process Items
items = data["major_categories"] if unit_mode == "大分類" else data["themes"]

if real_only:
    items = [i for i in items if i.get("volume_multiplier", 1.0) >= 1.2]

# Formatters
def fmt_money(val):
    sign = "-" if val < 0 else ""
    abs_v = abs(val)
    if abs_v >= 1e9:
        return f"{sign}${abs_v/1e9:.2f}B"
    elif abs_v >= 1e6:
        return f"{sign}${abs_v/1e6:.0f}M"
    return f"{sign}${abs_v:.0f}"

# Tabs
tab_in, tab_out = st.tabs(["🟢 純流入 Top10 (1W)", "🔴 純流出 Top10 (1W)"])

with tab_in:
    sort_key = "net_flow_1w" if sort_mode == "金額順" else "inflow_rate_1w"
    inflows = sorted([i for i in items if i["net_flow_1w"] >= 0], key=lambda x: x[sort_key], reverse=True)
    
    for rank, item in enumerate(inflows[:10], 1):
        top_cls = "card-top1" if rank == 1 else ""
        streak_html = ""
        if item.get("consecutive_days", 0) >= 2:
            streak_html = f'<span class="badge-streak">{item["consecutive_days"]}日連続流入</span>'
        
        tag_count = f'{item.get("theme_count", len(item.get("themes", [])))} テーマ' if unit_mode == "大分類" else f'{item.get("ticker_count", len(item.get("tickers", [])))} 銘柄'
        
        with st.container():
            st.markdown(f"""
            <div class="flow-card {top_cls}">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="rank-num">{rank}</div>
                    <div>
                        <div class="theme-name">{item['name']}</div>
                        <div style="display: flex; gap: 6px; margin-top: 4px;">
                            <span class="badge-gray">{tag_count}</span>
                            {streak_html}
                        </div>
                    </div>
                </div>
                <div>
                    <div class="flow-amount-pos">{fmt_money(item['net_flow_1w'])}</div>
                    <div class="flow-sub">流入率 +{item['inflow_rate_1w']}% · 1D {'+' if item['change_1d']>=0 else ''}{item['change_1d']}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Drilldown Expander
            with st.expander(f"🔍 {item['name']} の構成銘柄・内訳を見る"):
                if unit_mode == "大分類":
                    subthemes = item.get("subtheme_data", [])
                    st.write("**内包テーマ一覧:**")
                    for sth in subthemes:
                        st.write(f"- **{sth['name']}**: {fmt_money(sth['net_flow_1w'])} (流入率: +{sth['inflow_rate_1w']}%)")
                else:
                    stocks = item.get("stocks", [])
                    if stocks:
                        df_stk = pd.DataFrame(stocks)[["ticker", "latest_price", "change_1d", "net_flow_1w", "inflow_rate_1w", "volume_multiplier"]]
                        df_stk.columns = ["ティッカー", "株価($)", "1D騰落(%)", "推定フロー($)", "流入率(%)", "出来高倍率"]
                        st.dataframe(df_stk, use_container_width=True)
                    else:
                        st.write("構成銘柄:", ", ".join(item.get("tickers", [])))

with tab_out:
    sort_key = "net_flow_1w" if sort_mode == "金額順" else "inflow_rate_1w"
    outflows = sorted([i for i in items if i["net_flow_1w"] < 0], key=lambda x: x[sort_key])
    
    for rank, item in enumerate(outflows[:10], 1):
        streak_html = ""
        if item.get("consecutive_days", 0) >= 2:
            streak_html = f'<span class="badge-streak-neg">{item["consecutive_days"]}日連続流出</span>'
        
        tag_count = f'{item.get("theme_count", len(item.get("themes", [])))} テーマ' if unit_mode == "大分類" else f'{item.get("ticker_count", len(item.get("tickers", [])))} 銘柄'
        
        with st.container():
            st.markdown(f"""
            <div class="flow-card">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="rank-num">{rank}</div>
                    <div>
                        <div class="theme-name">{item['name']}</div>
                        <div style="display: flex; gap: 6px; margin-top: 4px;">
                            <span class="badge-gray">{tag_count}</span>
                            {streak_html}
                        </div>
                    </div>
                </div>
                <div>
                    <div class="flow-amount-neg">{fmt_money(item['net_flow_1w'])}</div>
                    <div class="flow-sub">流入率 {item['inflow_rate_1w']}% · 1D {'+' if item['change_1d']>=0 else ''}{item['change_1d']}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.caption("※ 資金フローは売買代金と高安終値の位置関係から推計した参考値です。")
