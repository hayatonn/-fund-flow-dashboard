"""
streamlit_app.py - Streamlit Cloud & Mobile App
Full-featured Fund Flow Dashboard with 1D/1W/1M period switching, crisp mini bar charts, and drilldowns.
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

# Custom Styling (Mobile & Desktop optimized)
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=JetBrains+Mono:wght@600;700&family=Noto+Sans+JP:wght@500;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        color: white;
        padding: 18px 22px;
        border-radius: 14px;
        margin-bottom: 16px;
        border: 1px solid #334155;
    }
    
    .main-title {
        font-size: 1.4rem;
        font-weight: 800;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .subtitle {
        font-size: 0.82rem;
        color: #94a3b8;
        line-height: 1.4;
    }

    .flow-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 6px;
        display: grid;
        grid-template-columns: 28px 1fr 110px 150px;
        align-items: center;
        gap: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .card-top1 {
        background: #f0f7ff !important;
        border-color: #93c5fd !important;
    }
    
    .rank-num {
        font-size: 1.15rem;
        font-weight: 800;
        color: #64748b;
        text-align: center;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .theme-name {
        font-size: 0.98rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    
    .badge-gray {
        background: #f1f5f9;
        color: #64748b;
        font-size: 0.72rem;
        padding: 2px 7px;
        border-radius: 4px;
        font-weight: 600;
    }

    .badge-streak {
        background: #ecfdf5;
        color: #059669;
        border: 1px solid #a7f3d0;
        font-size: 0.72rem;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 700;
    }
    
    .badge-streak-neg {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
        font-size: 0.72rem;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 700;
    }

    .chart-container {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .flow-metrics {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 2px;
    }
    
    .flow-amount-pos {
        font-size: 1.15rem;
        font-weight: 800;
        color: #059669;
        font-family: 'JetBrains Mono', monospace;
    }

    .flow-amount-neg {
        font-size: 1.15rem;
        font-weight: 800;
        color: #dc2626;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .flow-sub {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748b;
        font-family: 'JetBrains Mono', monospace;
    }

    @media (max-width: 768px) {
        .flow-card {
            grid-template-columns: 24px 1fr 80px 120px;
            gap: 8px;
            padding: 10px 12px;
        }
        .theme-name { font-size: 0.9rem; }
        .flow-amount-pos, .flow-amount-neg { font-size: 1.0rem; }
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown("""<div class="main-header"><div class="main-title">💰 資金フロー Top10 / Bottom10</div><div class="subtitle">売買代金 × 騰落方向で概算した資金の向きです（実需を捉える出来高加重フロー推計）</div></div>""", unsafe_allow_html=True)

# Load / Cache Data
@st.cache_data(ttl=3600)
def load_data():
    return get_fund_flow_data(force_refresh=False)

data = load_data()

# Control Bar
col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([1, 1, 1, 1.2])

with col_ctrl1:
    unit_mode = st.radio("単位", ["大分類", "テーマ"], horizontal=True)

with col_ctrl2:
    period_mode = st.radio("期間", ["1D (日次)", "1W (週間)", "1M (月間)"], index=1, horizontal=True)

with col_ctrl3:
    sort_mode = st.radio("並べ替え", ["金額順", "流入率順"], horizontal=True)

with col_ctrl4:
    real_only = st.checkbox("本物の流入だけ\n(出来高倍率 1.2x+)", value=False)

if st.button("🔄 市場データを最新化 (再取得・再計算)"):
    with st.spinner("米国市場から最新の株価・出来高データを取得中..."):
        data = fetch_live_market_data()
        st.cache_data.clear()
        st.success("最新データに更新しました！")

# Period Scaling Factor
period_factor = 0.22 if "1D" in period_mode else (3.8 if "1M" in period_mode else 1.0)
period_label = "1D" if "1D" in period_mode else ("1M" if "1M" in period_mode else "1W")

# Process Items
raw_items = data["major_categories"] if unit_mode == "大分類" else data["themes"]

items = []
for item in raw_items:
    net_flow = item["net_flow_1w"] * period_factor
    items.append({
        **item,
        "display_flow": net_flow,
        "display_rate": item.get("inflow_rate_1w", 0)
    })

if real_only:
    items = [i for i in items if i.get("volume_multiplier", 1.0) >= 1.2]

# Formatters
def fmt_money(val):
    if val is None:
        return "$0"
    sign = "-" if val < 0 else ""
    abs_v = abs(val)
    if abs_v >= 1e9:
        return f"{sign}${abs_v/1e9:.2f}B"
    elif abs_v >= 1e6:
        return f"{sign}${abs_v/1e6:.0f}M"
    return f"{sign}${abs_v:.0f}"

def fmt_percent(val):
    if val is None:
        return "0.0%"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.1f}%"

# Crisp SVG Sparkline Generator (Single line string)
def render_sparkline_svg(sparkline):
    if not sparkline or len(sparkline) == 0:
        sparkline = [0, 0, 0, 0, 0]
    
    max_abs = max([abs(x) for x in sparkline] + [1])
    svg_w, svg_h = 100, 32
    baseline_y = 16
    bar_w = 12
    gap = 7
    start_x = 4

    bars_svg = ""
    for idx, val in enumerate(sparkline[-5:]):
        x = start_x + idx * (bar_w + gap)
        is_pos = val >= 0
        bar_h = max(2, int((abs(val) / max_abs) * 13))
        
        if is_pos:
            y = baseline_y - bar_h
            color = "#10b981" # Green
        else:
            y = baseline_y
            color = "#ef4444" # Red
        
        bars_svg += f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" rx="2" fill="{color}" />'

    return f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg"><line x1="0" y1="{baseline_y}" x2="{svg_w}" y2="{baseline_y}" stroke="#cbd5e1" stroke-dasharray="2,2" stroke-width="1" />{bars_svg}</svg>'

# Tabs
tab_in, tab_out = st.tabs([f"🟢 純流入 Top10 ({period_label})", f"🔴 純流出 Top10 ({period_label})"])

def render_item_list(item_list, is_inflow=True):
    if not item_list:
        msg = "条件に一致する純流入データがありません。" if is_inflow else "条件に一致する純流出データがありません。"
        st.info(msg)
        return

    for rank, item in enumerate(item_list[:10], 1):
        top_cls = "card-top1" if (rank == 1 and is_inflow) else ""
        streak_html = ""
        if item.get("consecutive_days", 0) >= 2:
            is_streak_pos = item.get("is_consecutive_inflow", is_inflow)
            streak_cls = "badge-streak" if is_streak_pos else "badge-streak-neg"
            streak_text = f'{item["consecutive_days"]}日連続{"流入" if is_streak_pos else "流出"}'
            streak_html = f'<span class="{streak_cls}">{streak_text}</span>'
        
        tag_count = f'{item.get("theme_count", len(item.get("themes", [])))} テーマ' if unit_mode == "大分類" else f'{item.get("ticker_count", len(item.get("tickers", [])))} 銘柄'
        sparkline_svg = render_sparkline_svg(item.get("sparkline", []))
        amount_cls = "flow-amount-pos" if is_inflow else "flow-amount-neg"
        
        rate_str = fmt_percent(item.get("inflow_rate_1w", 0))
        change_str = fmt_percent(item.get("change_1d", 0))
        
        # Minified single-line card html
        card_html = (
            f'<div class="flow-card {top_cls}">'
            f'<div class="rank-num">{rank}</div>'
            f'<div><div class="theme-name">{item["name"]}</div>'
            f'<div style="display: flex; gap: 6px; align-items: center;"><span class="badge-gray">{tag_count}</span>{streak_html}</div></div>'
            f'<div class="chart-container">{sparkline_svg}</div>'
            f'<div class="flow-metrics">'
            f'<div class="{amount_cls}">{fmt_money(item["display_flow"])}</div>'
            f'<div class="flow-sub">流入率 {rate_str} · 1D {change_str}</div></div>'
            f'</div>'
        )
        
        st.markdown(card_html, unsafe_allow_html=True)

        # Drilldown Expander
        with st.expander(f"🔍 {item['name']} の構成銘柄・内訳を見る"):
            if unit_mode == "大分類":
                subthemes = item.get("subtheme_data", [])
                st.write("**内包テーマ一覧:**")
                for sth in subthemes:
                    th_rate = fmt_percent(sth.get("inflow_rate_1w", 0))
                    th_flow = fmt_money(sth.get("net_flow_1w", 0) * period_factor)
                    st.write(f"- **{sth['name']}**: {th_flow} (流入率: {th_rate})")
            else:
                stocks = item.get("stocks", [])
                if stocks:
                    df_stk = pd.DataFrame(stocks)[["ticker", "latest_price", "change_1d", "net_flow_1w", "inflow_rate_1w", "volume_multiplier"]].copy()
                    df_stk["change_1d"] = df_stk["change_1d"].apply(fmt_percent)
                    df_stk["inflow_rate_1w"] = df_stk["inflow_rate_1w"].apply(fmt_percent)
                    df_stk["net_flow_1w"] = df_stk["net_flow_1w"].apply(lambda v: fmt_money(v * period_factor))
                    df_stk["volume_multiplier"] = df_stk["volume_multiplier"].apply(lambda v: f"{v:.2f}x")
                    df_stk.columns = ["ティッカー", "株価($)", "1D騰落", f"推定フロー({period_label})", "流入率", "出来高倍率"]
                    st.dataframe(df_stk, use_container_width=True, hide_index=True)
                else:
                    st.write("構成銘柄:", ", ".join(item.get("tickers", [])))

with tab_in:
    sort_key = "display_flow" if sort_mode == "金額順" else "display_rate"
    inflows = sorted([i for i in items if i["display_flow"] >= 0], key=lambda x: x[sort_key], reverse=True)
    render_item_list(inflows, is_inflow=True)

with tab_out:
    sort_key = "display_flow" if sort_mode == "金額順" else "display_rate"
    outflows = sorted([i for i in items if i["display_flow"] < 0], key=lambda x: x[sort_key])
    render_item_list(outflows, is_inflow=False)

st.caption("※ 資金フローは売買代金と高安終値の位置関係から推計した参考値です。")
