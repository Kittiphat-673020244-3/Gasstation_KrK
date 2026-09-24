import os
import glob
import subprocess
import duckdb

def build_data_warehouse():
    print("🚀 [1/3] เริ่มต้นกระบวนการสร้าง Data Warehouse อัตโนมัติ...")

    # ค้นหาตำแหน่งโฟลเดอร์ datasets
    possible_dirs = ['Datasets', 'datasets', '../Datasets', '../datasets']
    target_dir = next((d for d in possible_dirs if os.path.exists(d) and os.path.isdir(d)), None)

    if not target_dir:
        print("❌ ไม่พบโฟลเดอร์ datasets กรุณาตรวจสอบตำแหน่งไฟล์ CSV")
        return

    print(f"📁 ดึงข้อมูลจากโฟลเดอร์: {target_dir}")
    
    # โหลดไฟล์ CSV เข้า DuckDB
    conn = duckdb.connect('dev.duckdb')
    csv_files = glob.glob(os.path.join(target_dir, '*.csv'))
    for csv_file in csv_files:
        table_name = os.path.splitext(os.path.basename(csv_file))[0]
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_csv_auto('{csv_file}')")
        print(f"  ✓ โหลดตาราง {table_name} สำเร็จ")
    conn.close()

    print("\n🌱 [2/3] สั่งรัน dbt seed...")
    subprocess.run(["dbt", "seed", "--profiles-dir", "."], check=True)

    print("\n⚡ [3/3] สั่งรัน dbt run...")
    subprocess.run(["dbt", "run", "--profiles-dir", "."], check=True)

    print("\n✅ เสร็จสมบูรณ์! คลังข้อมูล DuckDB พร้อมใช้งานเรียบร้อยแล้ว")

if __name__ == "__main__":
    build_data_warehouse()
