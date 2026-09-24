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
