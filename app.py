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