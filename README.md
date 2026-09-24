# GasStationDB - Data Warehouse & Business Intelligence Project

> **Repository:** Gasstation_KRK  
> **Group:** Project Group 1  
> **Course:** SC663402 Data Warehouse and Big Data Analytics  

โครงงานออกแบบและพัฒนาคลังข้อมูล (Data Warehouse) จากระบบ OLTP สู่ OLAP สำหรับธุรกิจสถานีบริการน้ำมัน (GasStationDB) เพื่อตอบคำถามทางธุรกิจและสร้าง Interactive Dashboard สื่อสารข้อมูลเพื่อการบริหารจัดการ

---
## Tech Stack Badges

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-0.9+-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)
![dbt](https://img.shields.io/badge/dbt-Core-FF694B?style=for-the-badge&logo=dbt&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

---

## สมาชิกในกลุ่ม

| รหัสนักศึกษา | ชื่อ-นามสกุล | บทบาทหน้าที่ |
| :---: | :--- | :--- |
| **673020045-9** | นายประภากร มีใส | Project Lead & Data Architect[cite: 1, 3] |
| **673020244-3** | นายกิตติพัศ ลาล้ำ | Data Engineer[cite: 1, 3] |
| **673020256-6** | นางสาวปภาวดี เหมาะดี | Data Analyst Lead[cite: 1, 3] |
| **673020264-7** | นางสาวสุกัญญา อุดมกัน | Data Modeler[cite: 1, 3] |
| **673020266-3** | นางสาวสุพิชญา ผ่องสนาม | Data Quality Engineer[cite: 1, 3] |
| **673020270-2** | นางสาวอาทิติญา ชาชัย | Business Intelligence Analyst[cite: 1, 3] |

---

## 1. Operational Database (OLTP)

* **ชุดข้อมูลต้นทาง:** GasStationDB (HCM City - PostgreSQL) จาก Kaggle[cite: 2]
* **ขอบเขตระบบ:** บันทึกธุรกรรมการขายน้ำมันประจำวัน การจัดการคลังน้ำมัน หัวจ่าย พนักงาน และลูกค้า รวม 24 วัน (15 มีนาคม – 7 เมษายน 2024)[cite: 2]
* **ER Diagram ต้นทาง:** [คลิกเปิดดู ER Diagram บน Google Drive](https://drive.google.com/file/d/1JGIX7BkISNF0DNA6mARoEywLSQCLhmJH/view)

![Operational ER Diagram](ER_Diagram.drawio.png)

แบบจำลองฐานข้อมูลเชิงสัมพันธ์นี้ ออกแบบเพื่อรองรับการดำเนินงานบริหารจัดการสถานีบริการน้ำมัน ครอบคลุมกระบวนการขาย บุคลากรประจำสาขา และปริมาณน้ำมันคงคลัง[cite: 2] แบ่งเป็น 3 กลุ่มหลัก:

1. **กลุ่มข้อมูลหลักและโครงสร้างสาขา (Master Data & Infrastructure):** `gasstation`, `employee`, `customer`, `product`[cite: 2]
2. **กลุ่มธุรกรรมงานขาย (Sales Transactions):** `invoice`, `invoicedetail`[cite: 2]
3. **กลุ่มคลังและการเคลื่อนไหวน้ำมันเชื้อเพลิง (Inventory Transactions):** `storagetank`, `inventorytransaction`[cite: 2]

---

## 2. โครงสร้างโปรเจกต์และกระบวนการ ELT (Project Structure)
โครงสร้างโปรเจกต์ทั้งหมด

```
Gasstation_KRK/
└── Gasstation_dw_duckdb/
    ├── dbt_project.yml
    ├── profiles.yml                    # หรืออยู่ที่ ~/.dbt/profiles.yml
    ├── dev.duckdb                      # ไฟล์ฐานข้อมูลจริง (สร้างอัตโนมัติตอนรันครั้งแรก)
    │
    ├── Datasets/                       # ไฟล์ CSV ต้นทาง 8 ไฟล์
    │   ├── Customer.csv
    │   ├── Employee.csv
    │   ├── GasStation.csv
    │   ├── Product.csv
    │   ├── Invoice.csv
    │   ├── InvoiceDetail.csv
    │   ├── StorageTank.csv
    │   └── InventoryTransaction.csv
    │
    ├── models/
    │   ├── staging/
    │   │   ├── src_gas.yml             # ประกาศ source (ชี้ไปที่ CSV)
    │   │   ├── stg_Customer.sql
    │   │   ├── stg_Employee.sql
    │   │   ├── stg_GasStation.sql
    │   │   ├── stg_Product.sql
    │   │   ├── stg_Invoice.sql
    │   │   ├── stg_InvoiceDetail.sql
    │   │   ├── stg_StorageTank.sql
    │   │   └── stg_InventoryTransaction.sql
    │   │
    │   └── datawarehouse/
    │       ├── schema.yml
    │       ├── dim_date.sql
    │       ├── dim_time.sql
    │       ├── dim_customer.sql
    │       ├── dim_employee.sql
    │       ├── dim_gasstation.sql
    │       ├── dim_product.sql
    │       ├── dim_paymentmethod.sql
    │       ├── dim_tank.sql
    │       ├── fact_sales.sql
    │       └── fact_inventory.sql
    │
    ├── app.py                          # Streamlit: Database Inspector (dev tool)
    └── dashboard_app.py                # Streamlit: Executive Dashboard (ตอบ 15 คำถามธุรกิจ)
```
---

