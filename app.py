"""
app.py — Fuel Station Analytics Report (v3 · ต่อกับ dbt warehouse ชุดใหม่)
==========================================================================
อ่านข้อมูลจาก dev.duckdb ที่สร้างโดย dbt เท่านั้น (dim_ / fact_ / int_ / mart_)

รัน:
    streamlit run app.py

ถ้าไฟล์ฐานข้อมูลอยู่ที่อื่น ตั้งค่าผ่าน environment variable ได้:
    GAS_DW_PATH=/path/to/dev.duckdb streamlit run app.py
"""

from __future__ import annotations

import os

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# 1) การตั้งค่าฐานข้อมูล
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.environ.get("GAS_DW_PATH"),
    os.path.join(os.getcwd(), "dev.duckdb"),
    os.path.join(HERE, "Gasstation_dw_duckdb", "dev.duckdb"),
    os.path.join(HERE, "dev.duckdb"),
]
DB_PATH = next((p for p in _CANDIDATES if p and os.path.exists(p)), _CANDIDATES[1])

# ---------------------------------------------------------------------------
# 2) ดีไซน์ระบบ — พาเลตสีที่ผ่านการตรวจสอบ (categorical order คงที่, ห้ามสลับ)
#    อ้างอิงจาก dataviz skill: sequential = blue เดียว, diverging = blue<->red,
#    status = fixed 4 สี, categorical = ลำดับ 8 สีที่ผ่าน CVD check แล้ว
# ---------------------------------------------------------------------------
SURFACE, PAGE = "#fcfcfb", "#f9f9f7"
INK, INK_SOFT, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, BORDER = "#e1e0d9", "#c3c2b7", "rgba(11,11,11,0.10)"

CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
               "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
BLUE, ORANGE, AQUA, YELLOW = CATEGORICAL[0], CATEGORICAL[1], CATEGORICAL[2], CATEGORICAL[3]
RED_HUE = CATEGORICAL[7]

SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#184f95"]
DIVERGING = [[0.0, "#e34948"], [0.5, "#f0efec"], [1.0, "#2a78d6"]]

STATUS_GOOD, STATUS_WARN, STATUS_SERIOUS, STATUS_CRIT = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"

WEEKDAY_TH = {"Monday": "จันทร์", "Tuesday": "อังคาร", "Wednesday": "พุธ",
              "Thursday": "พฤหัสบดี", "Friday": "ศุกร์", "Saturday": "เสาร์", "Sunday": "อาทิตย์"}
WEEKDAY_ORDER = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

st.set_page_config(page_title="Fuel Station Analytics Report", page_icon="⛽",
                    layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  html, body, [class*="css"] {{ font-family: "IBM Plex Sans Thai", "IBM Plex Sans", sans-serif; }}
  .stApp {{ background: {PAGE}; color: {INK}; }}
  [data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
  [data-testid="stHeader"] {{ background: transparent; }}
  .block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1440px; }}
  h1, h2, h3, h4 {{ color: {INK}; font-weight: 700; letter-spacing: .1px; }}
  .report-header {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; padding: 22px 28px; margin-bottom: 20px; border-left: 4px solid {BLUE}; }}
  .report-header h1 {{ margin: 0; font-size: 1.5rem; }}
  .report-header p {{ margin: 6px 0 0; color: {INK_SOFT}; font-size: .92rem; }}
  .report-header .meta {{ color: {MUTED}; font-size: .8rem; margin-top: 10px; }}
  .kpi {{ background: {SURFACE}; border: 1px solid {BORDER}; border-top: 3px solid {BLUE}; border-radius: 8px; padding: 14px 16px; height: 100%; }}
  .kpi .label {{ color: {MUTED}; font-size: .74rem; font-weight: 600; letter-spacing: .3px; text-transform: uppercase; }}
  .kpi .value {{ color: {INK}; font-size: 1.5rem; font-weight: 700; margin-top: 4px; line-height: 1.2; }}
  .kpi .unit {{ font-size: .8rem; color: {MUTED}; font-weight: 500; margin-left: 3px; }}
  .kpi .sub {{ font-size: .76rem; color: {INK_SOFT}; margin-top: 4px; }}
  .panel {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; padding: 18px 20px 8px; margin-bottom: 18px; }}
  .panel h4 {{ margin: 0 0 4px; font-size: 1.02rem; font-weight: 700; }}
  .panel .why {{ color: {MUTED}; font-size: .80rem; margin: 4px 0 12px; line-height: 1.5; }}
  [data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 8px; }}
  .stAlert {{ border-radius: 8px; }}
  footer, #MainMenu {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 3) Data access
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_con() -> duckdb.DuckDBPyConnection:
    if not os.path.exists(DB_PATH):
        st.error(f"ไม่พบไฟล์ฐานข้อมูล: `{DB_PATH}`\n\n"
                 "รัน `dbt run` ในโฟลเดอร์ `Gasstation_dw_duckdb` ก่อน หรือกำหนด "
                 "environment variable `GAS_DW_PATH` ให้ชี้ไปที่ `dev.duckdb`")
        st.stop()
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data(show_spinner=False)
def q(sql: str, params: tuple | list | None = None) -> pd.DataFrame:
    return get_con().execute(sql, list(params) if params else []).df()


def panel(title: str, why: str = "") -> None:
    st.markdown(f'<div class="panel"><h4>{title}</h4>'
                f'<p class="why">{why}</p></div>', unsafe_allow_html=True)


def style(fig: go.Figure, height: int = 360, legend_top: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=28, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans Thai, IBM Plex Sans, sans-serif", color=INK, size=12.5),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BLUE, font_color=INK),
        colorway=CATEGORICAL)
    if legend_top:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                                       bgcolor="rgba(0,0,0,0)", title_text=""))
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=BASELINE, linecolor=BASELINE,
                      tickfont_color=MUTED, title_font_color=INK_SOFT)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=BASELINE, linecolor=BASELINE,
                      tickfont_color=MUTED, title_font_color=INK_SOFT)
    return fig


def kpi(col, label: str, value: str, unit: str = "", sub: str = "") -> None:
    col.markdown(f'<div class="kpi"><div class="label">{label}</div>'
                 f'<div class="value">{value}<span class="unit">{unit}</span></div>'
                 f'<div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def guard(df: pd.DataFrame, msg: str = "ไม่มีข้อมูลในเงื่อนไขที่เลือก") -> bool:
    if df is None or df.empty:
        st.info(msg)
        return False
    return True


# ---------------------------------------------------------------------------
# 4) Sidebar filters
# ---------------------------------------------------------------------------
dim_station = q("select gasstation_id, gasstation_name, address from dim_gasstation "
                "order by gasstation_id")
dim_prod = q("select product_id, product_name, product_type, is_fuel from dim_product "
             "order by is_fuel desc, product_id")
bounds = q("select min(date_day) d0, max(date_day) d1 from dim_date")
D0, D1 = bounds.iloc[0, 0], bounds.iloc[0, 1]

with st.sidebar:
    st.markdown(f'<div style="font-size:1.1rem;font-weight:700;color:{INK}">⛽ Fuel Analytics</div>'
                f'<div style="color:{MUTED};font-size:.76rem;margin-bottom:14px">'
                f'Star Schema · DuckDB · dbt</div>', unsafe_allow_html=True)

    st.markdown("##### ช่วงวันที่")
    dr = st.date_input("ช่วงวันที่", value=(D0, D1), min_value=D0, max_value=D1,
                        label_visibility="collapsed")
    start_d, end_d = dr if isinstance(dr, (tuple, list)) and len(dr) == 2 else (D0, D1)

    rank_st = q("""
        select gasstation_id, sum(total_amount) as sales_amount
        from fact_invoice group by 1 order by 2 desc
    """)
    rank_st = rank_st.merge(dim_station, on="gasstation_id")

    st.markdown("##### สถานีบริการ")
    st.caption(f"คลังข้อมูลมี {len(dim_station):,} สถานี")
    scope = st.radio("ขอบเขต", ["Top 10 ตามยอดขาย", "Top 25 ตามยอดขาย", "ทั้งหมด", "เลือกเอง"],
                      label_visibility="collapsed")

    if scope == "ทั้งหมด":
        S = dim_station["gasstation_id"].tolist()
    elif scope.startswith("Top"):
        n = int(scope.split()[1])
        S = rank_st.head(n)["gasstation_id"].tolist()
    else:
        picked = st.multiselect("เลือกสถานี", dim_station["gasstation_name"].tolist(),
                                 default=rank_st.head(5)["gasstation_name"].tolist())
        S = dim_station.loc[dim_station["gasstation_name"].isin(picked), "gasstation_id"].tolist()

    st.markdown("##### สินค้า")
    fuel_only = st.toggle("เฉพาะน้ำมันเชื้อเพลิง", value=True)
    pool = dim_prod[dim_prod["is_fuel"]] if fuel_only else dim_prod
    prod_names = st.multiselect("สินค้า", pool["product_name"].tolist(),
                                 default=pool["product_name"].tolist(),
                                 label_visibility="collapsed")

    st.divider()
    st.caption("ข้อมูลอ้างอิงจากตาราง dim_ / fact_ / int_ ใน dbt warehouse โดยตรง "
               "กราฟตอบสนองตามช่วงวันที่และสถานีที่เลือกด้านบน")

if not S:
    st.warning("กรุณาเลือกอย่างน้อย 1 สถานี")
    st.stop()
if not prod_names:
    st.warning("กรุณาเลือกอย่างน้อย 1 สินค้า")
    st.stop()

P = dim_prod.loc[dim_prod["product_name"].isin(prod_names), "product_id"].tolist()
k0 = int(pd.Timestamp(start_d).strftime("%Y%m%d"))
k1 = int(pd.Timestamp(end_d).strftime("%Y%m%d"))
span_days = (pd.Timestamp(end_d) - pd.Timestamp(start_d)).days + 1

# ---------------------------------------------------------------------------
# 5) Header + KPI row
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="report-header">
  <h1>รายงานวิเคราะห์เครือข่ายสถานีบริการน้ำมัน</h1>
  <p>สรุปยอดขาย พฤติกรรมการซื้อ ประสิทธิภาพบุคลากร และการบริหารคลังน้ำมัน
     สำหรับ {len(S)} สถานี · {len(P)} สินค้า · {start_d:%d %b %Y} – {end_d:%d %b %Y}
     ({span_days} วัน)</p>
  <div class="meta">แหล่งข้อมูล: dim_ / fact_ / int_ tables · dbt + DuckDB</div>
</div>
""", unsafe_allow_html=True)

kpi_sql = """
select coalesce(sum(f.total_amount), 0) as sales_amount,
       count(*) as bill_count,
       count(distinct f.customer_id) as customer_count
from fact_invoice f
where f.gasstation_id = any(?) and f.date_key between ? and ?
"""
cur_k = q(kpi_sql, (S, k0, k1)).iloc[0]

fuel_sql = """
select coalesce(sum(s.quantity_sold), 0) as fuel_liters
from fact_sales s join dim_product p on s.product_id = p.product_id
where p.is_fuel and s.gasstation_id = any(?) and s.product_id = any(?)
  and s.date_key between ? and ?
"""
fuel_liters = q(fuel_sql, (S, P, k0, k1)).iloc[0].fuel_liters

top_station = q("""
    select g.gasstation_name, sum(f.total_amount) as s
    from fact_invoice f join dim_gasstation g on f.gasstation_id = g.gasstation_id
    where f.gasstation_id = any(?) and f.date_key between ? and ?
    group by 1 order by 2 desc limit 1
""", (S, k0, k1))

spread = q("""
    select avg(sales_multiple) as m
    from mart_09_daily_station_ranking
    where date_key between ? and ? and sales_multiple is not null
""", (k0, k1)).iloc[0].m

c = st.columns(5)
kpi(c[0], "ยอดขายรวม", f"{cur_k.sales_amount:,.0f}", " ₫")
kpi(c[1], "ปริมาณน้ำมันที่ขาย", f"{fuel_liters:,.0f}", " ลิตร")
kpi(c[2], "จำนวนบิล", f"{cur_k.bill_count:,.0f}", " บิล",
    f"เฉลี่ย {cur_k.sales_amount / cur_k.bill_count:,.0f} ₫/บิล" if cur_k.bill_count else "")
kpi(c[3], "สถานีขายดีสุด", top_station.iloc[0].gasstation_name if not top_station.empty else "—",
    sub=f"{top_station.iloc[0].s:,.0f} ₫" if not top_station.empty else "")
kpi(c[4], "ส่วนต่างยอดขายสูงสุด/ต่ำสุดต่อวัน", f"{spread:,.1f}" if pd.notna(spread) else "—", " เท่า",
    "เฉลี่ยทั้งระบบ")
st.write("")

# ===========================================================================
# ส่วนที่ 1 — ผลการดำเนินงานตามสถานี
# ===========================================================================
panel("ผลการดำเนินงานตามสถานี",
      "แท่งแนวนอนเรียงตามยอดขายเฉลี่ยต่อวันของสถานีในขอบเขตที่เลือก สีไล่ระดับตามกลุ่มยอดขาย "
      "(สูง/กลาง/ต่ำ) ช่วยอ่านกลุ่มได้เร็วโดยไม่ต้องกดตัวเลข ชื่อถนนของแต่ละสถานีแสดงในป้ายเมื่อชี้เมาส์")

perf = q("""
    with daily as (
        select gasstation_id, date_key, sum(total_amount) as daily_sales
        from fact_invoice
        where gasstation_id = any(?) and date_key between ? and ?
        group by 1, 2
    ),
    station_avg as (
        select gasstation_id, avg(daily_sales) as avg_daily_sales
        from daily group by 1
    )
    select s.gasstation_id, g.gasstation_name,
           trim(split_part(g.address, ',', 1)) as road_name,
           s.avg_daily_sales,
           ntile(3) over (order by s.avg_daily_sales desc) as tier_rank
    from station_avg s join dim_gasstation g on s.gasstation_id = g.gasstation_id
    order by s.avg_daily_sales desc
""", (S, k0, k1))

if guard(perf):
    TIER_LABEL = {1: "กลุ่มสูง", 2: "กลุ่มกลาง", 3: "กลุ่มต่ำ"}
    TIER_COLOR = {1: SEQ_BLUE[4], 2: SEQ_BLUE[3], 3: SEQ_BLUE[1]}
    top_n = perf.head(20).sort_values("avg_daily_sales")
    fig = go.Figure()
    for tier in [3, 2, 1]:
        sub = top_n[top_n["tier_rank"] == tier]
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            x=sub.avg_daily_sales, y=sub.gasstation_name, orientation="h",
            name=TIER_LABEL[tier], marker_color=TIER_COLOR[tier],
            customdata=sub[["road_name"]].values,
            hovertemplate="%{y}<br>ถนน %{customdata[0]}<br>%{x:,.0f} ₫/วัน<extra></extra>"))
    fig.update_layout(barmode="overlay", legend_title_text="ระดับยอดขาย")
    fig.update_xaxes(title_text="ยอดขายเฉลี่ยต่อวัน (₫)")
    fig.update_yaxes(title_text="")
    st.plotly_chart(style(fig, 420, True), width="stretch")
