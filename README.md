# 🍃 MongoDB Dump GUI (Portable)

โปรแกรมเดสก์ท็อป GUI แบบ **Portable** สำหรับสั่งสำรองข้อมูล MongoDB โดยเชื่อมต่อและสั่งการผ่าน `mongodump` (MongoDB Database Tools CLI) รองรับการใช้งานข้ามแพลตฟอร์มทั้ง **Windows (โฟกัสหลัก x86_64)**, **macOS** และ **Linux**

---

## ✨ คุณสมบัติเด่น (Key Features)

- **100% Portable Application:**
  - รันได้ทันทีโดยไม่ต้องติดตั้ง ไม่ต้องใช้สิทธิ์ Admin
  - บันทึกการตั้งค่าลงไฟล์ `config.jsonc` ในโฟลเดอร์เดียวกับตัวโปรแกรม สามารถย้ายโฟลเดอร์หรือใส่ Flash Drive ไปรันเครื่องอื่นได้ทันที
- **Auto-Detection & Cross-Platform Tools:**
  - รองรับทั้ง `mongodump.exe` (Windows) และ `mongodump` (macOS/Linux)
  - มีระบบค้นหา binary อัตโนมัติใน System `PATH` และโฟลเดอร์มาตรฐาน
  - สามารถ Browse เลือก path ของ binary ได้เองผ่าน GUI พร้อมไฟสถานะและแสดงเวอร์ชัน
- **🔒 Zero-Secrets Security Guarantee (ความปลอดภัยระดับสูงสุด):**
  - **ห้ามบันทึก** Connection URI หรือ Password ลงในไฟล์ config หรือ disk เด็ดขาด
  - ข้อมูล Connection URI จะอยู่ในหน่วยความจำ (RAM) ชั่วคราวระหว่างเปิดใช้งานเท่านั้น
  - หน้าต่าง Log Console มีระบบ **Masking** กรองรหัสผ่าน (`***`) อัตโนมัติ ป้องกันข้อมูลหลุดบนหน้าจอ
- **Preset Management:**
  - บันทึกและโหลด Preset การ Dump (เช่น Dev DB, Staging DB, Sales Archive) ได้อย่างสะดวกรวดเร็ว
  - Preset จะเก็บเฉพาะค่า Options เช่น DB, Collection, Output, Flags (ไม่เก็บข้อมูลลับ)
- **JSONC Configuration Support:**
  - รองรับไฟล์คอนฟิกทั้ง `config.jsonc` และ `config.json`
  - รองรับคอมเมนต์รูปแบบ `// ...`, `/* ... */`, `# ...` และ trailing commas สามารถเขียนโน้ตในไฟล์คอนฟิกได้
- **Real-Time Streaming Console & Collapsible Log:**
  - ดักจับ stdout/stderr จาก `mongodump` แสดงผลสดแบบ Real-time
  - มีปุ่ม **Show Log / Hide Log** สามารถซ่อนหรือเปิดดูกล่อง Log ได้ตลอดเวลาโดยไม่รบกวนการทำงาน
  - มีปุ่ม **Cancel** ยกเลิกกระบวนการ dump ได้อย่างปลอดภัย และปุ่ม Clear / Copy Log

---

## 🚀 การติดตั้งและเริ่มใช้งาน (Quick Start)

### 1. รันจาก Source Code (Python 3.10+)

```bash
# โคลนโปรเจกต์
git clone <repo-url>
cd mongo-tools

# สร้าง Virtual Environment
python3 -m venv .venv

# บน Windows:
.venv\Scripts\activate
# บน macOS/Linux:
source .venv/bin/activate

# ติดตั้ง Dependencies
pip install -r requirements.txt

# รันโปรแกรม
python app.py
```

### 2. รันชุดทดสอบ (Unit & Integration Tests)

```bash
pytest -v
```

---

## 📦 การ Build เป็นโปรแกรม Portable Executable

### สำหรับ Windows x86_64 (Single `.exe` File)

ดับเบิ้ลคลิกไฟล์ `packaging\build_windows.bat` หรือรันผ่าน Command Prompt:

```cmd
packaging\build_windows.bat
```

เมื่อเสร็จสิ้น จะได้ไฟล์ **`dist\MongoDumpGUI.exe`** เพียงไฟล์เดียว สามารถนำไปวางใช้งานที่ใดก็ได้บนเครื่อง Windows x86_64

### สำหรับ macOS

```bash
./packaging/build_macos.sh
```
จะได้ `dist/MongoDumpGUI.app`

### สำหรับ Linux

```bash
./packaging/build_linux.sh
```
จะได้ `dist/MongoDumpGUI` (Standalone ELF executable)

---

## ⚙️ โครงสร้างไฟล์ Config (`config.jsonc`)

เมื่อเปิดโปรแกรม ตัวโปรแกรมจะสร้างไฟล์ `config.jsonc` อยู่ข้างตัวโปรแกรมโดยอัตโนมัติ:

```jsonc
// MongoDB Dump GUI Portable Configuration (JSONC supported)
// Note: Connection strings and credentials are NEVER saved here.
{
  "tool_path": "C:\\Tools\\mongodb-database-tools\\bin\\mongodump.exe",
  "last_used_preset": "Sales Monthly Backup",
  "presets": {
    "Sales Monthly Backup": {
      "db": "sales_db",
      "collection": "",
      "output_mode": "archive",
      "output_path": "./backups/sales_monthly.dump",
      "gzip": true,
      "num_parallel_collections": 4,
      "read_preference": "secondaryPreferred",
      "exclude_collections": "temp_logs,audit"
    }
  }
}
```

---

## 🛠️ รายละเอียดตัวเลือกการ Dump ในโปรแกรม

| ฟิลด์ | คำอธิบาย | พารามิเตอร์ของ `mongodump` |
|---|---|---|
| **mongodump Path** | ตำแหน่งไฟล์ executable ของ mongodump | เรียกใช้งาน executable |
| **Preset** | สลับ/บันทึกการตั้งค่าการ dump แต่ละระบบ | - |
| **Connection URI** | MongoDB Connection String (เช่น `mongodb+srv://...`) | `--uri="<URI>"` *(In-Memory Only)* |
| **Database** | ชื่อฐานข้อมูลที่ต้องการ dump (เว้นว่าง = ทั้งหมด) | `--db=<db>` |
| **Collection** | ชื่อ collection เฉพาะ (เว้นว่าง = ทั้งหมด) | `--collection=<col>` |
| **Exclude Collections** | ข้าม collection ที่ระบุ (คั่นด้วยจุลภาค `,`) | `--excludeCollection=<col>` |
| **Output Format** | เลือกระหว่าง Directory หรือ Single Archive File | `--out=<path>` หรือ `--archive=<path>` |
| **Compress with Gzip** | บีบอัดข้อมูลด้วย Gzip ลดขนาดไฟล์ | `--gzip` |
| **Parallel Jobs (-j)** | จำนวน collection ที่ประมวลผลพร้อมกัน | `--numParallelCollections=<N>` |
| **Read Preference** | เลือกอ่านจาก node สำรองใน Replica Set | `--readPreference=<pref>` |

---

## 🧪 การทดสอบระบบ (Automated CI/CD)

โปรเจกต์มี **GitHub Actions Workflow** (`.github/workflows/build.yml`) ซึ่งจะรันการทดสอบและ build executable ครอบคลุมทั้ง 3 ระบบปฏิบัติการ (`windows-latest`, `macos-latest`, `ubuntu-latest`) โดยอัตโนมัติเมื่อ push ขึ้น repository
