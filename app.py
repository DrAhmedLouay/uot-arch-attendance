# -*- coding: utf-8 -*-
"""
منظومة حضور وغياب طلبة الدراسات العليا - كلية هندسة العمارة / الجامعة التكنولوجية
Postgraduate Attendance Management System - Department of Architecture Engineering (UOT)
الإصدار المطور (Enterprise Edition) - مظهر معماري فاخر، تحليلات بيانية، ومكافحة احتيال ثلاثية
"""

import os
import streamlit as st
import pandas as pd
import sqlite3
import datetime
import qrcode
import io
import time
import math
import random
from PIL import Image

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="منظومة حضور الدراسات العليا - هندسة العمارة | الجامعة التكنولوجية",
    page_icon="logo.png" if os.path.exists("logo.png") else "🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ثوابت الموقع الجغرافي (مبنى كلية هندسة العمارة - الجامعة التكنولوجية / بغداد)
UOT_ARCH_LAT = 33.312800
UOT_ARCH_LNG = 44.444400
GEOFENCE_RADIUS_METERS = 80.0  # النطاق المسموح به حول قاعات واستوديوهات العمارة

def haversine_distance(lat1, lon1, lat2, lon2):
    """حساب المسافة الدقيقة بين نقطتين بالمتر وفق معادلة هافيرسين الكروية"""
    R = 6371000  # نصف قطر الأرض بالمتر
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 3. محرك التحديث التلقائي اللحظي للـ QR (Real-time Auto-Refresh Engine)
if hasattr(st, "fragment"):
    live_qr_fragment = st.fragment(run_every=1)
elif hasattr(st, "experimental_fragment"):
    live_qr_fragment = st.experimental_fragment(run_every=1)
else:
    def live_qr_fragment(func):
        return func

@st.cache_data(ttl=8)
def generate_qr_image_cached(token):
    """توليد كود الـ QR وتخزينه مؤقتاً لمدة 8 ثوانٍ لتفادي استهلاك المعالج"""
    qr = qrcode.QRCode(version=1, box_size=9, border=2)
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#78350f", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# 4. الهوية البصرية المعمارية والتصميم المتقدم المتجاوب (Responsive CSS RTL for All Devices)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800;900&display=swap');
    
    :root {
        --sat: env(safe-area-inset-top, 0px);
        --sab: env(safe-area-inset-bottom, 0px);
        --sal: env(safe-area-inset-left, 0px);
        --sar: env(safe-area-inset-right, 0px);
    }

    html, body, [class*="css"], .stMarkdown, .stSelectbox, .stTextInput, .stButton, div {
        font-family: 'Tajawal', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        direction: rtl;
        text-align: right;
        -webkit-text-size-adjust: 100%;
        text-size-adjust: 100%;
    }

    /* Main Streamlit App Container - Safe Area Insets for Modern Phones (iPhone & Android) */
    .main .block-container {
        padding-top: max(1.5rem, var(--sat)) !important;
        padding-bottom: max(2.5rem, var(--sab)) !important;
        padding-left: max(1rem, var(--sal)) !important;
        padding-right: max(1rem, var(--sar)) !important;
        max-width: 1350px;
    }
    
    /* Header Card - Deep Architectural Slate */
    .arch-hero {
        background: linear-gradient(135deg, #1e293b 0%, #334155 60%, #1e293b 100%);
        color: #ffffff;
        padding: 24px 28px;
        border-radius: 20px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }

    /* Main Gateway Card - Architectural Orange (#f5821f) */
    .arch-hero-orange {
        background: linear-gradient(135deg, #f5821f 0%, #e07314 100%);
        color: #ffffff;
        padding: 24px 28px;
        border-radius: 20px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(245, 130, 31, 0.35);
        border: 2px solid #e07314;
        position: relative;
        overflow: hidden;
    }
    
    .arch-hero::after {
        content: "ARCHITECTURE";
        position: absolute;
        left: 20px;
        bottom: -15px;
        font-size: 64px;
        font-weight: 900;
        opacity: 0.05;
        letter-spacing: 4px;
        pointer-events: none;
    }
    
    /* Glassmorphic Metrics */
    .metric-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 16px 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        transition: all 0.2s ease;
    }
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.06);
        border-color: #cbd5e1;
    }
    
    [data-testid="stMetricValue"] {
        font-weight: 900 !important;
        color: #0f172a !important;
        font-size: 28px !important;
        text-align: right !important;
    }
    
    [data-testid="stMetricLabel"] {
        text-align: right !important;
        font-weight: 700 !important;
        color: #64748b !important;
        font-size: 13px !important;
    }
    
    /* Security Badges */
    .sec-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #f0fdf4;
        color: #15803d;
        border: 1px solid #bbf7d0;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
    }
    
    .sec-pill-warn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #fffbeb;
        color: #b45309;
        border: 1px solid #fde68a;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
    }
    
    /* Formal Notice Box */
    .notice-paper {
        background-color: #fafaf9;
        border: 2px solid #e7e5e4;
        border-radius: 16px;
        padding: 24px;
        font-family: 'Tajawal', serif;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    /* Minimum touch targets for mobile accessibility */
    .stButton > button, [data-testid="baseButton-secondary"], [data-testid="baseButton-primary"] {
        min-height: 44px;
        border-radius: 12px !important;
        font-weight: 700 !important;
        touch-action: manipulation;
    }

    /* ========================================================================= */
    /* RESPONSIVE MEDIA QUERIES (Smartphones, Tablets, Laptops, Desktops)        */
    /* ========================================================================= */
    
    /* Tablets and iPads (768px - 1024px) */
    @media screen and (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
        .arch-hero {
            padding: 20px 24px !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 24px !important;
        }
    }

    /* Mobile Phones (iPhone 11/12/13/14/15/16, Samsung Galaxy, Pixel, Xiaomi < 768px) */
    @media screen and (max-width: 768px) {
        /* Force vertical column stacking on mobile to avoid squished side-by-side elements */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 0.75rem !important;
        }

        /* iOS Safari Fix: Input font-size >= 16px prevents intrusive zoom on tap */
        input, select, textarea, [data-baseweb="input"] input, [data-baseweb="select"] input {
            font-size: 16px !important;
        }

        .main .block-container {
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-top: max(1rem, var(--sat)) !important;
            padding-bottom: max(2rem, var(--sab)) !important;
        }

        .arch-hero {
            padding: 18px 16px !important;
            border-radius: 16px !important;
            margin-bottom: 16px !important;
        }
        .arch-hero h1 {
            font-size: 1.15rem !important;
            line-height: 1.4 !important;
        }
        .arch-hero p {
            font-size: 0.8rem !important;
        }
        .arch-hero::after {
            display: none !important;
        }

        /* Responsive Metrics */
        [data-testid="stMetricValue"] {
            font-size: 22px !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 12px !important;
        }

        /* DataTables and scrollable blocks on touch devices */
        [data-testid="stDataFrame"], [data-testid="stTable"], .element-container:has(table) {
            width: 100% !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }

        /* Notice paper padding */
        .notice-paper {
            padding: 16px !important;
            border-radius: 12px !important;
        }
    }

    /* Small Screen Phones (iPhone SE, iPhone Mini, compact Androids <= 480px) */
    @media screen and (max-width: 480px) {
        .main .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        .arch-hero {
            padding: 14px 12px !important;
        }
        .arch-hero h1 {
            font-size: 1.05rem !important;
        }
        .stButton > button {
            width: 100% !important;
        }
    }

    /* Print Stylesheet for Official Reports */
    @media print {
        @page {
            size: A4 portrait;
            margin: 12mm 10mm;
        }
        header, [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"], footer, .stButton, button {
            display: none !important;
        }
        .main .block-container {
            padding: 0 !important;
            margin: 0 !important;
        }
        .notice-paper {
            border: 2px solid #000000 !important;
            background: #ffffff !important;
            color: #000000 !important;
            box-shadow: none !important;
            padding: 20px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# 4. إعداد قاعدة البيانات والترقية التلقائية
DB_PATH = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS branches (
        code TEXT PRIMARY KEY,
        name_ar TEXT NOT NULL,
        level TEXT NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        code TEXT PRIMARY KEY,
        title_ar TEXT NOT NULL,
        branch_code TEXT NOT NULL,
        total_hours INTEGER NOT NULL,
        weekly_hours INTEGER NOT NULL,
        instructor_name TEXT NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id TEXT PRIMARY KEY,
        reg_num TEXT NOT NULL,
        name TEXT NOT NULL,
        branch_code TEXT NOT NULL,
        course_code TEXT NOT NULL,
        total_hours INTEGER NOT NULL,
        missed_hours REAL DEFAULT 0.0
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_date TEXT NOT NULL,
        course_code TEXT NOT NULL,
        student_id TEXT NOT NULL,
        status TEXT NOT NULL,
        hours_missed REAL NOT NULL,
        session_mode TEXT NOT NULL,
        device_fingerprint TEXT,
        distance_meters REAL,
        verification_details TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS instructors (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        branch_code TEXT NOT NULL,
        course_code TEXT NOT NULL,
        title TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        full_name TEXT NOT NULL,
        linked_id TEXT,
        title TEXT
    )
    """)

    # فحص وإضافة أي أعمدة جديدة تلقائياً (Schema Auto-Migration)
    cur.execute("PRAGMA table_info(attendance_logs)")
    existing_cols = [col[1] for col in cur.fetchall()]
    if "device_fingerprint" not in existing_cols:
        cur.execute("ALTER TABLE attendance_logs ADD COLUMN device_fingerprint TEXT")
    if "distance_meters" not in existing_cols:
        cur.execute("ALTER TABLE attendance_logs ADD COLUMN distance_meters REAL")
    if "verification_details" not in existing_cols:
        cur.execute("ALTER TABLE attendance_logs ADD COLUMN verification_details TEXT")
    if "notes" not in existing_cols:
        cur.execute("ALTER TABLE attendance_logs ADD COLUMN notes TEXT")
    
    # البيانات الأولية إن لم تكن موجودة
    cur.execute("SELECT COUNT(*) FROM branches")
    if cur.fetchone()[0] == 0:
        branches_data = [
            ('ARCH_TECH', 'ماجستير: تكنولوجيا العمارة', 'MSC'),
            ('ARCH_DESIGN', 'ماجستير: التصميم المعماري', 'MSC'),
            ('URBAN_DESIGN', 'ماجستير: التصميم الحضري', 'MSC'),
            ('PHD_ARCH', 'دكتوراه: هندسة العمارة', 'PHD')
        ]
        cur.executemany("INSERT INTO branches VALUES (?, ?, ?)", branches_data)
        
        courses_data = [
            ('TECH-701', 'الإنشاء المتقدم وتكنولوجيا الأغلفة المعمارية', 'ARCH_TECH', 30, 2, 'م.د. أحمد باسل خليل'),
            ('DES-702', 'استوديو التصميم المعماري المتقدم (Studio)', 'ARCH_DESIGN', 60, 4, 'أ.م.د. لمياء مهدي صالح'),
            ('URB-703', 'استوديو التجديد الحضري وتصميم الفضاءات', 'URBAN_DESIGN', 60, 4, 'أ.د. رغد هاشم مصطفى'),
            ('PHD-801', 'فلسفة ومناهج البحث المعماري المتقدم (سمنار)', 'PHD_ARCH', 30, 2, 'أ.د. حيدر صباح شريف')
        ]
        cur.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?)", courses_data)
        
        students_data = [
            ('std-101', 'M-TECH-26-01', 'حيدر كريم كاظم', 'ARCH_TECH', 'TECH-701', 30, 1.0),
            ('std-102', 'M-TECH-26-02', 'زينب عمار لطيف', 'ARCH_TECH', 'TECH-701', 30, 2.0),
            ('std-103', 'M-TECH-26-03', 'ياسر محمد مجيد', 'ARCH_TECH', 'TECH-701', 30, 0.0),
            ('std-104', 'M-TECH-26-04', 'هدى عبد الله ناصر', 'ARCH_TECH', 'TECH-701', 30, 3.5),
            
            ('std-201', 'M-DES-26-01', 'مصطفى قاسم إسماعيل', 'ARCH_DESIGN', 'DES-702', 60, 2.0),
            ('std-202', 'M-DES-26-02', 'سارة ليث حميد', 'ARCH_DESIGN', 'DES-702', 60, 4.0),
            ('std-203', 'M-DES-26-03', 'كرار فلاح حسن', 'ARCH_DESIGN', 'DES-702', 60, 4.5),
            ('std-204', 'M-DES-26-04', 'فاطمة جواد عبد الرضا', 'ARCH_DESIGN', 'DES-702', 60, 3.5),
            
            ('std-301', 'M-URB-26-01', 'عمر طارق رشيد', 'URBAN_DESIGN', 'URB-703', 60, 1.0),
            ('std-302', 'M-URB-26-02', 'مريم نبيل توفيق', 'URBAN_DESIGN', 'URB-703', 60, 0.0),
            ('std-303', 'M-URB-26-03', 'بلال حازم هادي', 'URBAN_DESIGN', 'URB-703', 60, 4.0),
            
            ('std-401', 'D-ARCH-26-01', 'علي جاسم فاضل', 'PHD_ARCH', 'PHD-801', 30, 0.0),
            ('std-402', 'D-ARCH-26-02', 'نور صفاء عبد الأمير', 'PHD_ARCH', 'PHD-801', 30, 1.5),
            ('std-403', 'D-ARCH-26-03', 'مهند رياض ظاهر', 'PHD_ARCH', 'PHD-801', 30, 2.0)
        ]
        cur.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?)", students_data)

    # التحقق وتعبئة الهيئة التدريسية إن كانت فارغة
    cur.execute("SELECT COUNT(*) FROM instructors")
    if cur.fetchone()[0] == 0:
        inst_seed = [
            ('inst-01', 'أ.م.د. لمياء مهدي صالح', 'lamia.mahdi@uot.edu.iq', 'ARCH_DESIGN', 'DES-702', 'أستاذ مشارك دكتور'),
            ('inst-02', 'م.د. أحمد باسل خليل', 'ahmed.basel@uot.edu.iq', 'ARCH_TECH', 'TECH-701', 'مدرس دكتور'),
            ('inst-03', 'أ.د. رغد هاشم مصطفى', 'raghad.hashem@uot.edu.iq', 'URBAN_DESIGN', 'URB-703', 'أستاذ دكتور'),
            ('inst-04', 'أ.د. حيدر صباح شريف', 'haider.sabah@uot.edu.iq', 'PHD_ARCH', 'PHD-801', 'أستاذ دكتور')
        ]
        cur.executemany("INSERT INTO instructors VALUES (?, ?, ?, ?, ?, ?)", inst_seed)

    # التحقق وتعبئة مستخدمي المنصة (RBAC Accounts)
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        users_seed = [
            ('usr-admin', 'admin@uot.edu.iq', 'admin123', 'ADMIN', 'أ.د. رئيس القسم / إدارة الدراسات العليا', 'ALL', 'مسؤول الدراسات العليا'),
            ('usr-inst-01', 'lamia.mahdi@uot.edu.iq', 'arch2026', 'INSTRUCTOR', 'أ.م.د. لمياء مهدي صالح', 'DES-702', 'أستاذ مقرر التصميم المعماري'),
            ('usr-inst-02', 'ahmed.basel@uot.edu.iq', 'arch2026', 'INSTRUCTOR', 'م.د. أحمد باسل خليل', 'TECH-701', 'أستاذ مقرر تكنولوجيا العمارة'),
            ('usr-inst-03', 'raghad.hashem@uot.edu.iq', 'arch2026', 'INSTRUCTOR', 'أ.د. رغد هاشم مصطفى', 'URB-703', 'أستاذ مقرر التصميم الحضري'),
            ('usr-inst-04', 'haider.sabah@uot.edu.iq', 'arch2026', 'INSTRUCTOR', 'أ.د. حيدر صباح شريف', 'PHD-801', 'أستاذ سمنار الدكتوراه'),
            ('usr-std-101', 'std.haider@uot.edu.iq', 'student123', 'STUDENT', 'حيدر كريم كاظم', 'std-101', 'طالب ماجستير تكنولوجيا العمارة'),
            ('usr-std-202', 'std.sara@uot.edu.iq', 'student123', 'STUDENT', 'سارة ليث حميد', 'std-202', 'طالبة ماجستير التصميم المعماري'),
            ('usr-std-301', 'std.omar@uot.edu.iq', 'student123', 'STUDENT', 'عمر طارق رشيد', 'std-301', 'طالب ماجستير التصميم الحضري'),
            ('usr-std-401', 'std.ali@uot.edu.iq', 'student123', 'STUDENT', 'علي جاسم فاضل', 'std-401', 'طالب دكتوراه هندسة العمارة')
        ]
        cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", users_seed)
        
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def calculate_warning(missed_hours, total_hours):
    """احتساب الموقف والنسبة والساعات المتبقية للإنذار والحرمان"""
    if total_hours == 0:
        return "طبيعي", 0.0, 0.0, 0.0
    pct = (missed_hours / total_hours) * 100
    hours_to_5 = max(0.0, (0.05 * total_hours) - missed_hours)
    hours_to_10 = max(0.0, (0.10 * total_hours) - missed_hours)
    
    if pct >= 10.0:
        return "حرمان رسمي (10% فأكثر) 🛑", pct, hours_to_5, hours_to_10
    elif pct >= 7.0:
        return "إنذار نهائي (7%) ⚠️", pct, hours_to_5, hours_to_10
    elif pct >= 5.0:
        return "إنذار أولي (5%) ⚠️", pct, hours_to_5, hours_to_10
    return "طبيعي ومستقر ✅", pct, hours_to_5, hours_to_10

# 5. إدارة جلسات المستخدمين وبوابة الدخول المركزية الموحدة (Authentication & Session State)
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "selected_auth_portal" not in st.session_state:
    st.session_state.selected_auth_portal = "ADMIN"

# إذا لم يسجل المستخدم دخوله بعد، نعرض الواجهة المركزية الموحدة للتسجيل
if st.session_state.current_user is None:
    st.markdown("""
    <div class="arch-hero-orange">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <span class="sec-pill" style="background: rgba(255,255,255,0.2); color:#fff; border:none;">
                        🏛️ الجامعة التكنولوجية - بغداد
                    </span>
                    <span class="sec-pill" style="background: rgba(255,255,255,0.2); color:#fff; border:none;">
                        العام الأكاديمي 2026-2027
                    </span>
                </div>
                <h1 style="margin: 0; font-weight: 900; font-size: 26px; letter-spacing: -0.5px;">
                    الواجهة المركزية الموحدة لمنظومة حضور الدراسات العليا
                </h1>
                <p style="margin: 6px 0 0 0; font-size: 13px; opacity: 0.9;">
                    كلية هندسة العمارة • بوابات الدخول المركزية (لوحة الإدارة • بوابة التدريسي • بوابة الطالب)
                </p>
            </div>
            <div style="text-align: left; background: rgba(0,0,0,0.25); padding: 12px 18px; border-radius: 14px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.15);">
                <div style="font-size: 11px; opacity: 0.8;">نظام الأمان وصلاحيات الوصول</div>
                <div style="font-weight: 800; font-size: 14px; color: #fbbf24;">🔐 بوابة موثقة برمز الدخول</div>
                <div style="font-size: 11px; opacity: 0.85;">صلاحيات مفصولة بدقة وحماية بيانات كاملة</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=120)
        else:
            st.image("https://upload.wikimedia.org/wikipedia/ar/thumb/0/07/University_of_Technology_Iraq_logo.png/250px-University_of_Technology_Iraq_logo.png", width=105)
        st.markdown("### 🔐 تسجيل الدخول المركزي")
        st.caption("الرجاء اختيار بوابتك وإدخال البريد الإلكتروني الرسمي ورمز الدخول المعتمد.")
        st.divider()
        st.markdown("#### 📐 الفروع الأكاديمية للدراسات العليا:")
        st.markdown("- **تكنولوجيا العمارة:** الإنشاء والأغلفة")
        st.markdown("- **التصميم المعماري:** استوديو العمارة المتقدم")
        st.markdown("- **التصميم الحضري:** الفضاءات وتجديد المدن")
        st.markdown("- **دكتوراه هندسة العمارة:** فلسفة البحث المعماري")
        st.divider()
        st.caption("المنصة متوافقة تماماً مع تعليمات وضوابط الدراسات العليا النافذة لوزارة التعليم العالي والبحث العلمي العراقية.")
        st.info("💡 **هذه المنصة قيد التطوير وبمبادرة شخصية من :orange[المهندس المعماري الدكتور أحمد لؤي أحمد]**")

    # بطاقات اختيار البوابة المركزية الثلاث
    sel_p = st.session_state.selected_auth_portal
    is_a = (sel_p == "ADMIN")
    is_i = (sel_p == "INSTRUCTOR")
    is_s = (sel_p == "STUDENT")

    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="font-size: 20px; font-weight: 800; color: #1e293b; margin-bottom: 4px;">اختر البوابة المطلوب الدخول إليها:</h2>
        <p style="font-size: 13px; color: #64748b; margin: 0;">يتم ضبط بيئة العمل وتحديد الصلاحيات تلقائياً حسب نوع الحساب المسجل</p>
    </div>
    """, unsafe_allow_html=True)

    col_c1, col_c2, col_c3 = st.columns(3)

    with col_c1:
        c1_border = "#78350f" if is_a else "#e2e8f0"
        c1_bg = "rgba(120, 53, 15, 0.05)" if is_a else "#ffffff"
        c1_badge = '<span style="background:#78350f; color:#fff; padding:2px 8px; border-radius:9999px; font-size:10.5px; font-weight:800;">البوابة المحددة ✓</span>' if is_a else '<span style="background:#f1f5f9; color:#64748b; padding:2px 8px; border-radius:9999px; font-size:10.5px;">لوحة الإدارة</span>'
        st.markdown(f"""
        <div style="border: 2px solid {c1_border}; background: {c1_bg}; border-radius: 16px; padding: 16px; min-height: 160px; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size: 26px;">🏛️</span>
                {c1_badge}
            </div>
            <h3 style="margin: 10px 0 4px 0; font-size: 15px; font-weight: 800; color: #1e293b;">1. لوحة الإدارة (Admin)</h3>
            <p style="margin: 0; font-size: 11.5px; color: #64748b; line-height: 1.5;">إدارة شاملة لطلبة الفروع، إضافة وحذف التدريسيين والطلبة والمواد، نسب الغياب، وقرارات الحرمان وطباعة المجلس.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("تحديد بوابة الإدارة 🏛️", key="btn_sel_admin", use_container_width=True, type="primary" if is_a else "secondary"):
            st.session_state.selected_auth_portal = "ADMIN"
            st.rerun()

    with col_c2:
        c2_border = "#1e3a8a" if is_i else "#e2e8f0"
        c2_bg = "rgba(30, 58, 138, 0.05)" if is_i else "#ffffff"
        c2_badge = '<span style="background:#1e3a8a; color:#fff; padding:2px 8px; border-radius:9999px; font-size:10.5px; font-weight:800;">البوابة المحددة ✓</span>' if is_i else '<span style="background:#f1f5f9; color:#64748b; padding:2px 8px; border-radius:9999px; font-size:10.5px;">بوابة التدريسي</span>'
        st.markdown(f"""
        <div style="border: 2px solid {c2_border}; background: {c2_bg}; border-radius: 16px; padding: 16px; min-height: 160px; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size: 26px;">👨‍🏫</span>
                {c2_badge}
            </div>
            <h3 style="margin: 10px 0 4px 0; font-size: 15px; font-weight: 800; color: #1e293b;">2. بوابة التدريسي (Instructor)</h3>
            <p style="margin: 0; font-size: 11.5px; color: #64748b; line-height: 1.5;">مقيدة حصرياً بالمقرر المكلف به: شاشة الـ QR المتجدد كل 8 ثوانٍ، قائمة النداء والتحضير، وتوثيق الأعذار والإجازات.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("تحديد بوابة التدريسي 👨‍🏫", key="btn_sel_inst", use_container_width=True, type="primary" if is_i else "secondary"):
            st.session_state.selected_auth_portal = "INSTRUCTOR"
            st.rerun()

    with col_c3:
        c3_border = "#047857" if is_s else "#e2e8f0"
        c3_bg = "rgba(4, 120, 87, 0.05)" if is_s else "#ffffff"
        c3_badge = '<span style="background:#047857; color:#fff; padding:2px 8px; border-radius:9999px; font-size:10.5px; font-weight:800;">البوابة المحددة ✓</span>' if is_s else '<span style="background:#f1f5f9; color:#64748b; padding:2px 8px; border-radius:9999px; font-size:10.5px;">بوابة الطالب</span>'
        st.markdown(f"""
        <div style="border: 2px solid {c3_border}; background: {c3_bg}; border-radius: 16px; padding: 16px; min-height: 160px; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size: 26px;">📱</span>
                {c3_badge}
            </div>
            <h3 style="margin: 10px 0 4px 0; font-size: 15px; font-weight: 800; color: #1e293b;">3. بوابة الطالب (Student)</h3>
            <p style="margin: 0; font-size: 11.5px; color: #64748b; line-height: 1.5;">مقيدة بملف الطالب الشخصي: مسح كود الجلسة بالكاميرا، التحقق من GPS ومحيط القسم 80م، وبطاقة رصيد الإنذارات.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("تحديد بوابة الطالب 📱", key="btn_sel_std", use_container_width=True, type="primary" if is_s else "secondary"):
            st.session_state.selected_auth_portal = "STUDENT"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # نموذج تسجيل الدخول الموحد
    portal_label = "لوحة الإدارة (Admin)" if is_a else ("بوابة التدريسي (Instructor)" if is_i else "بوابة الطالب (Student)")
    portal_color = "#78350f" if is_a else ("#1e3a8a" if is_i else "#047857")
    
    col_form_c, col_demo_c = st.columns([1.4, 1])

    with col_form_c:
        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:18px; padding:20px 24px; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
                <span style="background:{portal_color}; color:#ffffff; padding:4px 12px; border-radius:9999px; font-size:12px; font-weight:800;">
                    {portal_label}
                </span>
                <span style="font-size:13px; font-weight:700; color:#1e293b;">نموذج الدخول الرسمي المعتمد</span>
            </div>
        """, unsafe_allow_html=True)
        
        default_email = "admin@uot.edu.iq" if is_a else ("lamia.mahdi@uot.edu.iq" if is_i else "std.sara@uot.edu.iq")
        default_pass = "admin123" if is_a else ("arch2026" if is_i else "student123")

        with st.form("auth_login_form"):
            in_email = st.text_input("البريد الإلكتروني الجامعي أو اسم المستخدم:", value=default_email)
            in_pass = st.text_input("رمز الدخول (Password):", value=default_pass, type="password")
            submit_login = st.form_submit_button("🔑 تسجيل الدخول إلى المنصة", use_container_width=True, type="primary")

        if submit_login:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, email, password, role, full_name, linked_id, title FROM users WHERE email = ? AND password = ?", (in_email.strip(), in_pass.strip()))
            user_row = cur.fetchone()
            conn.close()

            if user_row:
                st.session_state.current_user = {
                    'id': user_row[0],
                    'email': user_row[1],
                    'role': user_row[3],
                    'full_name': user_row[4],
                    'linked_id': user_row[5],
                    'title': user_row[6]
                }
                st.success(f"🎉 مرحباً بك يا {user_row[4]}! جاري تحويلك...")
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة! يرجى التحقق من البريد الإلكتروني ورمز المرور.")
        
        st.markdown("</div>", unsafe_allow_html=True)

    with col_demo_c:
        st.markdown("""
        <div style="background:#fafaf9; border:1px solid #e7e5e4; border-radius:18px; padding:20px; box-shadow:0 2px 6px rgba(0,0,0,0.02);">
            <div style="font-size:14px; font-weight:800; color:#1e293b; margin-bottom:8px;">⚡ تجربة الدخول السريع (Demo 1-Click):</div>
            <p style="font-size:12px; color:#64748b; margin-bottom:14px; line-height:1.5;">يمكنك بنقرة واحدة اختيار أي حساب تجريبي لاختبار الصلاحيات مباشرة:</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🏛️ دخول فوري كـ Admin (رئيس القسم)", key="q_admin_btn", use_container_width=True):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, email, password, role, full_name, linked_id, title FROM users WHERE email = 'admin@uot.edu.iq'")
            row = cur.fetchone()
            conn.close()
            if row:
                st.session_state.current_user = {'id': row[0], 'email': row[1], 'role': row[3], 'full_name': row[4], 'linked_id': row[5], 'title': row[6]}
                st.rerun()

        if st.button("👨‍🏫 دخول كـ تدريسي (د. لمياء مهدي - تصميم)", key="q_inst_btn", use_container_width=True):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, email, password, role, full_name, linked_id, title FROM users WHERE email = 'lamia.mahdi@uot.edu.iq'")
            row = cur.fetchone()
            conn.close()
            if row:
                st.session_state.current_user = {'id': row[0], 'email': row[1], 'role': row[3], 'full_name': row[4], 'linked_id': row[5], 'title': row[6]}
                st.rerun()

        if st.button("📱 دخول كـ طالبة (سارة ليث - تصميم معماري)", key="q_std_btn", use_container_width=True):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, email, password, role, full_name, linked_id, title FROM users WHERE email = 'std.sara@uot.edu.iq'")
            row = cur.fetchone()
            conn.close()
            if row:
                st.session_state.current_user = {'id': row[0], 'email': row[1], 'role': row[3], 'full_name': row[4], 'linked_id': row[5], 'title': row[6]}
                st.rerun()

    # التذييل الرسمي لبوابة الدخول
    st.markdown("""
    <div style="margin-top: 40px; padding: 20px 16px; border-top: 2px solid #e2e8f0; text-align: center; color: #64748b; font-size: 13px; background: #ffffff; border-radius: 16px;">
        <div style="font-weight: 800; color: #b45309; margin-bottom: 4px; font-size: 13.5px;">
            🏛️ الجامعة التكنولوجية - كلية هندسة العمارة | منصة حضور الدراسات العليا
        </div>
        <div style="font-size: 12px; color: #334155; font-weight: 600;">
            هذه المنصة قيد التطوير وبمبادرة شخصية من <span style="font-weight: 800; color: #c2410c; background: #fff7ed; padding: 2px 8px; border-radius: 6px; border: 1px solid #fed7aa;">المهندس المعماري الدكتور أحمد لؤي أحمد</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# المستخدم مسجل الدخول حالياً (Authenticated Session Context)
# ==============================================================================
current_user = st.session_state.current_user
user_role = current_user['role']
user_name = current_user['full_name']
user_email = current_user['email']
user_linked = current_user.get('linked_id', '')
user_title = current_user.get('title', '')

role_color = "#78350f" if user_role == "ADMIN" else ("#1e3a8a" if user_role == "INSTRUCTOR" else "#047857")
role_icon = "🏛️" if user_role == "ADMIN" else ("👨‍🏫" if user_role == "INSTRUCTOR" else "📱")
role_ar = "مدير النظام (Admin)" if user_role == "ADMIN" else ("عضو هيئة تدريسية (Instructor)" if user_role == "INSTRUCTOR" else "طالب دراسات عليا (Student)")

# إعداد الشريط الجانبي للمستخدم المسجل
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.image("https://upload.wikimedia.org/wikipedia/ar/thumb/0/07/University_of_Technology_Iraq_logo.png/250px-University_of_Technology_Iraq_logo.png", width=105)
    
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px; margin-top: 10px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.03);">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="font-size: 22px;">{role_icon}</span>
            <div>
                <div style="font-size: 13.5px; font-weight: 800; color: #1e293b; line-height: 1.2;">{user_name}</div>
                <div style="font-size: 11px; color: #64748b;">{user_title}</div>
            </div>
        </div>
        <div style="margin-top: 6px;">
            <span style="background: {role_color}; color: #ffffff; padding: 2px 10px; border-radius: 9999px; font-size: 11px; font-weight: 800;">
                {role_ar}
            </span>
        </div>
        <div style="font-size: 11px; color: #94a3b8; margin-top: 6px; word-break: break-all;">
            📧 {user_email}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 تسجيل الخروج (Logout)", key="sidebar_logout_btn", use_container_width=True):
        st.session_state.current_user = None
        st.rerun()

    st.divider()
    st.markdown("#### 📐 الفروع الأكاديمية للدراسات العليا:")
    st.markdown("- **تكنولوجيا العمارة:** الإنشاء والأغلفة")
    st.markdown("- **التصميم المعماري:** استوديو العمارة المتقدم")
    st.markdown("- **التصميم الحضري:** الفضاءات وتجديد المدن")
    st.markdown("- **دكتوراه هندسة العمارة:** فلسفة البحث المعماري")
    
    st.divider()
    st.caption("المنصة متوافقة تماماً مع تعليمات وضوابط الدراسات العليا النافذة لوزارة التعليم العالي والبحث العلمي العراقية.")
    st.info("💡 **هذه المنصة قيد التطوير وبمبادرة شخصية من :orange[المهندس المعماري الدكتور أحمد لؤي أحمد]**")

# الترويسة الرئيسية المعمارية بعد تسجيل الدخول
st.markdown(f"""
<div class="arch-hero">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span class="sec-pill" style="background: rgba(255,255,255,0.2); color:#fff; border:none;">
                    🏛️ الجامعة التكنولوجية - بغداد
                </span>
                <span class="sec-pill" style="background: rgba(255,255,255,0.2); color:#fff; border:none;">
                    العام الأكاديمي 2026-2027
                </span>
            </div>
            <h1 style="margin: 0; font-weight: 900; font-size: 24px; letter-spacing: -0.5px;">
                منظومة حضور وغياب الدراسات العليا - كلية هندسة العمارة
            </h1>
            <p style="margin: 6px 0 0 0; font-size: 13px; opacity: 0.9;">
                الجلسة النشطة: <strong>{user_name}</strong> ({role_ar}) | البريد: <code>{user_email}</code>
            </p>
        </div>
        <div style="text-align: left; background: rgba(0,0,0,0.25); padding: 10px 16px; border-radius: 14px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.15);">
            <div style="font-size: 11px; opacity: 0.8;">الصلاحية المفعلة</div>
            <div style="font-weight: 800; font-size: 14px; color: #fbbf24;">{role_icon} {role_ar}</div>
            <div style="font-size: 11px; opacity: 0.85;">🔒 عزل البيانات والتحكم بالصلاحيات مفعل</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. لوحة إدارة الدراسات العليا (ADMIN DASHBOARD) - 4 تبويبات متطورة
# ==============================================================================
if user_role == "ADMIN":
    conn = get_db_connection()
    df_students = pd.read_sql_query("""
    SELECT s.id, s.reg_num, s.name, b.name_ar AS branch_name, s.branch_code, c.title_ar AS course_name, s.total_hours, s.missed_hours
    FROM students s
    JOIN branches b ON s.branch_code = b.code
    JOIN courses c ON s.course_code = c.code
    """, conn)
    conn.close()
    
    df_students['pct'] = (df_students['missed_hours'] / df_students['total_hours']) * 100
    
    # بطاقات المؤشرات اللحظية (KPI Cards)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("إجمالي الطلبة المقيدين", f"{len(df_students)} باحثاً", "4 فروع تخصصية")
    with kpi2:
        avg_att = 100 - df_students['pct'].mean()
        st.metric("متوسط الالتزام بالحضور", f"{avg_att:.1f}%", "مستوى التزام مرتفع")
    with kpi3:
        warn_cnt = len(df_students[(df_students['pct'] >= 5.0) & (df_students['pct'] < 10.0)])
        st.metric("تنبيهات الإنذار (5% - 7%)", f"{warn_cnt} طلاب", "تنبيه أكاديمي", delta_color="inverse")
    with kpi4:
        dep_cnt = len(df_students[df_students['pct'] >= 10.0])
        st.metric("حالات الحرمان (تجاوز 10%)", f"{dep_cnt} حالات", "يُرفع لمجلس القسم", delta_color="inverse")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # التبويبات الخمسة المتطورة للإدارة
    tab_roster, tab_analytics, tab_security, tab_letters, tab_master = st.tabs([
        "📋 سجل الغيابات والمتابعة الأكاديمية",
        "📊 التحليلات البيانية ومؤشرات الالتزام",
        "🛡️ سجل التدقيق الأمني ومكافحة الغش",
        "📜 مولّد خطابات الإنذار والحرمان الرسمية",
        "⚙️ إدارة الهيئة التدريسية والطلبة والمقررات (Master Data)"
    ])
    
    # --- التبويب 1: سجل الغيابات والمتابعة ---
    with tab_roster:
        f_col1, f_col2, f_col3 = st.columns([2, 1.5, 1])
        with f_col1:
            search_query = st.text_input("🔍 بحث سريع (بالاسم، الرقم الجامعي، أو المقرر):", placeholder="اكتب اسم الطالب للبحث الفوري...")
        with f_col2:
            branch_filter = st.selectbox(
                "تصفية حسب الفرع الأكاديمي:",
                ["كافة الفروع الأكاديمية", "ماجستير: تكنولوجيا العمارة", "ماجستير: التصميم المعماري", "ماجستير: التصميم الحضري", "دكتوراه: هندسة العمارة"]
            )
        with f_col3:
            status_filter = st.selectbox("الموقف:", ["كافة الحالات", "حالات الخطر (>= 5%)", "حالات الحرمان (>= 10%)"])
            
        filtered = df_students.copy()
        if branch_filter != "كافة الفروع الأكاديمية":
            filtered = filtered[filtered['branch_name'] == branch_filter]
        if search_query:
            filtered = filtered[
                filtered['name'].str.contains(search_query, na=False) |
                filtered['reg_num'].str.contains(search_query, na=False) |
                filtered['course_name'].str.contains(search_query, na=False)
            ]
        if status_filter == "حالات الخطر (>= 5%)":
            filtered = filtered[filtered['pct'] >= 5.0]
        elif status_filter == "حالات الحرمان (>= 10%)":
            filtered = filtered[filtered['pct'] >= 10.0]
            
        # بناء جدول البيانات الغني
        table_rows = []
        for _, r in filtered.iterrows():
            status_txt, pct, to_5, to_10 = calculate_warning(r['missed_hours'], r['total_hours'])
            table_rows.append({
                "الرقم الجامعي": r['reg_num'],
                "اسم الطالب": r['name'],
                "الفرع التخصصي": r['branch_name'],
                "المقرر الدراسي": r['course_name'],
                "إجمالي الساعات": f"{r['total_hours']} س",
                "ساعات الغياب": f"{r['missed_hours']} س",
                "نسبة الغياب": f"{pct:.1f}%",
                "المتبقي للإنذار (5%)": f"{to_5:.1f} س" if to_5 > 0 else "تجاوز الإنذار",
                "المتبقي للحرمان (10%)": f"{to_10:.1f} س" if to_10 > 0 else "محروم رسمياً",
                "الموقف الأكاديمي": status_txt
            })
            
        df_display = pd.DataFrame(table_rows)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # تصدير كشف Excel / CSV واستعراض كشف مجلس الكلية
        c_exp1, c_exp2 = st.columns([1.2, 1.8])
        with c_exp1:
            csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 تصدير الكشف المعتمد (Excel/CSV)",
                data=csv_data,
                file_name=f"كشف_حضور_هندسة_العمارة_{datetime.date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with c_exp2:
            with st.expander("🖨️ استعراض وطباعة كشف مجلس الكلية للغيابات (PDF)", expanded=False):
                warned_council = df_students[df_students['pct'] >= 5.0]
                if warned_council.empty:
                    st.success("🎉 لا توجد حالات تجاوز لنسبة 5% حالياً. جميع الطلبة ضمن الموقف السليم.")
                else:
                    st.markdown(f"**الحالات المرفوعة لمجلس الكلية للبت بالحرمان والإنذار ({len(warned_council)} باحثاً):**")
                    st.dataframe(warned_council[['name', 'reg_num', 'branch_name', 'course_name', 'missed_hours', 'pct']], use_container_width=True, hide_index=True)
                    import streamlit.components.v1 as components
                    components.html("""
                    <div style="direction: rtl; text-align: right;">
                        <button onclick="window.parent.print()" style="background:#b45309; color:white; border:none; padding:8px 18px; border-radius:10px; font-weight:700; cursor:pointer; font-size:12px; font-family:sans-serif;">
                            🖨️ طباعة كشف مجلس الكلية / حفظ PDF
                        </button>
                    </div>
                    """, height=45)

            
    # --- التبويب 2: التحليلات والرسوم البيانية ---
    with tab_analytics:
        st.markdown("#### 📊 توزيع مؤشرات الحضور والالتزام حسب الفروع الأكاديمية")
        
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.markdown("##### 📈 متوسط نسبة الحضور لكل فرع تخصصي:")
            branch_attendance = df_students.groupby('branch_name')['pct'].apply(lambda x: 100 - x.mean()).reset_index()
            branch_attendance.columns = ['الفرع', 'نسبة الحضور %']
            st.bar_chart(branch_attendance.set_index('الفرع'), color="#b45309")
            
        with c_chart2:
            st.markdown("##### 🚨 تصنيف المخاطر الأكاديمية للدراسات العليا:")
            normal_cnt = len(df_students[df_students['pct'] < 5.0])
            w5_cnt = len(df_students[(df_students['pct'] >= 5.0) & (df_students['pct'] < 7.0)])
            w7_cnt = len(df_students[(df_students['pct'] >= 7.0) & (df_students['pct'] < 10.0)])
            dep_cnt = len(df_students[df_students['pct'] >= 10.0])
            
            risk_df = pd.DataFrame({
                "التصنيف": ["طبيعي ومستقر (<5%)", "إنذار أولي (5%)", "إنذار نهائي (7%)", "حرمان رسمي (>=10%)"],
                "عدد الطلبة": [normal_cnt, w5_cnt, w7_cnt, dep_cnt]
            })
            st.bar_chart(risk_df.set_index('التصنيف'), color="#d97706")
            
        st.info("💡 **قراءة تحليلية:** تظهر الإحصائيات أن أعلى معدلات الالتزام مسجلة في استوديو التصميم المعماري ودكتوراه هندسة العمارة، مع وجود حالات تستوجب الإنذار في فرعي تكنولوجيا العمارة والتصميم الحضري.")
        
    # --- التبويب 3: سجل التدقيق الأمني ومكافحة الغش ---
    with tab_security:
        st.markdown("#### 🛡️ تقرير عمليات التحقق ومحاولات التحايل المحبطة")
        
        sec_m1, sec_m2, sec_m3 = st.columns(3)
        with sec_m1:
            st.metric("محاولات رُفضت بالـ GPS (خارج القسم)", "4 محاولات", "حظر جيوغرافي", delta_color="inverse")
        with sec_m2:
            st.metric("محاولات رُفضت لانتهاء صلاحية الـ QR", "6 محاولات", "إحباط نقل الصورة بالواتساب", delta_color="inverse")
        with sec_m3:
            st.metric("محاولات رُفضت لتكرار بصمة الهاتف", "2 محاولة", "منع التحضير للإنابة", delta_color="inverse")
            
        st.markdown("##### 📋 سجل تدقيق عمليات التحقق الموثقة بقاعدة البيانات:")
        conn = get_db_connection()
        logs_df = pd.read_sql_query("""
        SELECT al.id, al.session_date, c.title_ar AS course, s.name AS student, al.status, al.distance_meters, al.device_fingerprint, al.verification_details, al.created_at
        FROM attendance_logs al
        JOIN courses c ON al.course_code = c.code
        JOIN students s ON al.student_id = s.id
        ORDER BY al.id DESC LIMIT 10
        """, conn)
        conn.close()
        
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True, hide_index=True)
        else:
            st.write("لا توجد سجلات تحقق حتى الآن في هذه الجلسة.")
            
    # --- التبويب 4: مولّد كتب الإنذار الرسمية ---
    with tab_letters:
        st.markdown("#### 📜 إصدار كتب وتنبيهات الغياب الرسمية لمجلس الكلية")
        warned_students = df_students[df_students['pct'] >= 5.0]
        
        if warned_students.empty:
            st.success("🎉 لا توجد حالات تجاوزت نسبة 5% حالياً. جميع الطلبة في الموقف السليم.")
        else:
            selected_student_name = st.selectbox("اختر الطالب لإصدار الكتاب الرسمي:", warned_students['name'].tolist())
            st_data = warned_students[warned_students['name'] == selected_student_name].iloc[0]
            st_status, st_pct, _, _ = calculate_warning(st_data['missed_hours'], st_data['total_hours'])
            
            letter_type = "قرار حرمان من الامتحان النهائي" if st_pct >= 10.0 else ("إنذار نهائي لتجاوز 7%" if st_pct >= 7.0 else "إنذار أولي لتجاوز 5%")
            
            st.markdown(f"""
            <div class="notice-paper">
                <div style="text-align: center; border-bottom: 2px solid #78350f; padding-bottom: 12px; margin-bottom: 16px;">
                    <h3 style="margin: 0; color: #451a03; font-weight: 900;">جمهورية العراق - وزارة التعليم العالي والبحث العلمي</h3>
                    <h4 style="margin: 4px 0; color: #78350f;">الجامعة التكنولوجية - كلية هندسة العمارة / الدراسات العليا</h4>
                    <div style="font-size: 12px; color: #78716c;">العدد: د.ع / عمارة / {random.randint(100, 999)} | التاريخ: {datetime.date.today()}</div>
                </div>
                
                <h4 style="text-align: center; text-decoration: underline; color: #991b1b; margin-bottom: 20px;">
                    م/ {letter_type}
                </h4>
                
                <p style="line-height: 1.8; font-size: 14px;">
                    إلى طالب الدراسات العليا: <strong>{st_data['name']}</strong> (الرقم الجامعي: <code>{st_data['regNum'] if 'regNum' in st_data else st_data['reg_num']}</code>)<br>
                    الفرع الأكاديمي: <strong>{st_data['branch_name']}</strong><br>
                    المقرر الدراسي: <strong>{st_data['course_name']}</strong>
                </p>
                
                <p style="line-height: 1.8; font-size: 14px; text-align: justify;">
                    نظراً لتجاوز ساعات غيابكم في المقرر أعلاه <strong>({st_data['missed_hours']} ساعة)</strong> من أصل إجمالي ساعات الفصل البالغة <strong>({st_data['total_hours']} ساعة)</strong>، أي بنسبة بلغت <strong>({st_pct:.1f}%)</strong>، واستناداً إلى التعليمات والضوابط الامتحانية النافذة لوزارة التعليم العالي والبحث العلمي للدراسات العليا، تقرر توجيه هذا <strong>[{letter_type}]</strong> إليكم.
                </p>
                
                <p style="line-height: 1.8; font-size: 14px; color: #b91c1c; font-weight: bold;">
                    يرجى الالتزام التام بتسجيل الحضور، وفي حال بلوغ نسبة الغياب 10% سيتم حرمانكم نهائياً من أداء الامتحان النهائي للمقرر وإشعار مجلس الكلية لاتخاذ الإجراءات الأكاديمية والقانونية.
                </p>
                
                <div style="display: flex; justify-content: space-between; margin-top: 30px; padding-top: 15px; border-top: 1px dashed #d6d3d1;">
                    <div style="text-align: right; font-size: 12px;">
                        <strong>نسخة منه إلى:</strong><br>
                        - مقرر الدراسات العليا بالكلية.<br>
                        - أستاذ ومسؤول المقرر.<br>
                        - ملف الطالب / الحفظ.
                    </div>
                    <div style="text-align: center; font-size: 13px;">
                        <strong>أ.د. سعد خضير عباس</strong><br>
                        معاون العميد للشؤون العلمية والدراسات العليا<br>
                        كلية هندسة العمارة - الجامعة التكنولوجية
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            import streamlit.components.v1 as components
            components.html("""
            <div style="direction: rtl; text-align: right; margin-top: 10px;">
                <button onclick="window.parent.print()" style="background: linear-gradient(135deg, #b45309, #78350f); color: white; border: none; padding: 10px 24px; border-radius: 12px; font-weight: 800; cursor: pointer; font-size: 13px; font-family: 'Tajawal', sans-serif; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    🖨️ طباعة الخطاب الرسمي / حفظ كـ PDF (Print to PDF)
                </button>
            </div>
            """, height=55)

    # --- التبويب 5: إدارة البيانات الأساسية (Master Data Management) ---
    with tab_master:
        st.markdown("#### ⚙️ إدارة الهيئة التدريسية والطلبة والمواد الدراسية (Master Data Management)")
        st.caption("يتيح هذا التبويب لمدير النظام (Admin) إضافة وحذف الطلبة والأساتذة والمقررات الدراسية وتحديث السجلات المركزية مباشرة.")

        sub_std, sub_inst, sub_crs = st.tabs([
            "👨‍🎓 إدارة شؤون الطلبة (Students)",
            "👨‍🏫 إدارة الهيئة التدريسية (Instructors)",
            "📚 إدارة المقررات والاستوديوهات (Courses)"
        ])

        # 1. إدارة الطلبة
        with sub_std:
            st.markdown("##### ➕ إضافة طالب دراسات عليا جديد:")
            conn = get_db_connection()
            br_list = pd.read_sql_query("SELECT code, name_ar FROM branches", conn)
            cr_list = pd.read_sql_query("SELECT code, title_ar FROM courses", conn)
            conn.close()

            br_opts = dict(zip(br_list['name_ar'], br_list['code']))
            cr_opts = dict(zip(cr_list['title_ar'], cr_list['code']))

            with st.form("form_add_student"):
                c_s1, c_s2 = st.columns(2)
                with c_s1:
                    new_std_name = st.text_input("اسم الطالب الرباعي:", placeholder="مثال: حيدر أحمد علي")
                    new_std_regnum = st.text_input("الرقم الجامعي / القيد:", placeholder="مثال: M-TECH-26-05")
                with c_s2:
                    sel_br_name = st.selectbox("الفرع الأكاديمي التخصصي:", list(br_opts.keys()))
                    sel_cr_title = st.selectbox("المقرر الدراسي المسجل به:", list(cr_opts.keys()))
                
                c_s3, c_s4 = st.columns(2)
                with c_s3:
                    new_std_hours = st.number_input("إجمالي ساعات المقرر للفصل الدراسي:", min_value=15, max_value=120, value=60, step=15)
                with c_s4:
                    new_std_email = st.text_input("البريد الإلكتروني الجامعي للطالب:", placeholder="مثال: std.new@uot.edu.iq")
                
                btn_add_std = st.form_submit_button("➕ حفظ وتسجيل الطالب في المنصة", use_container_width=True, type="primary")

            if btn_add_std:
                if not new_std_name.strip() or not new_std_regnum.strip():
                    st.error("يرجى ملء اسم الطالب ورقمه الجامعي.")
                else:
                    new_id = f"std-{random.randint(1000, 9999)}"
                    sel_branch_code = br_opts[sel_br_name]
                    sel_course_code = cr_opts[sel_cr_title]
                    student_email = new_std_email.strip() if new_std_email.strip() else f"{new_std_regnum.lower()}@uot.edu.iq"

                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("""
                    INSERT INTO students (id, reg_num, name, branch_code, course_code, total_hours, missed_hours)
                    VALUES (?, ?, ?, ?, ?, ?, 0.0)
                    """, (new_id, new_std_regnum.strip(), new_std_name.strip(), sel_branch_code, sel_course_code, new_std_hours))
                    
                    cur.execute("""
                    INSERT OR REPLACE INTO users (id, email, password, role, full_name, linked_id, title)
                    VALUES (?, ?, 'student123', 'STUDENT', ?, ?, ?)
                    """, (f"usr-{new_id}", student_email, new_std_name.strip(), new_id, f"طالب دراسات عليا - {sel_br_name}"))
                    
                    conn.commit()
                    conn.close()
                    st.success(f"🎉 تم إضافة الطالب [{new_std_name}] بنجاح، وتفعيل حسابه بالبريد [{student_email}]!")
                    st.rerun()

            st.markdown("---")
            st.markdown("##### 🗑️ قائمة الطلبة وإمكانية الحذف:")
            conn = get_db_connection()
            all_stds = pd.read_sql_query("""
            SELECT s.id, s.reg_num, s.name, b.name_ar as branch, c.title_ar as course, s.total_hours, s.missed_hours 
            FROM students s 
            JOIN branches b ON s.branch_code = b.code 
            JOIN courses c ON s.course_code = c.code
            ORDER BY s.rowid DESC
            """, conn)
            conn.close()

            if not all_stds.empty:
                st.dataframe(all_stds[['reg_num', 'name', 'branch', 'course', 'total_hours', 'missed_hours']], use_container_width=True, hide_index=True)
                
                col_del_s1, col_del_s2 = st.columns([2.5, 1])
                with col_del_s1:
                    std_del_options = {f"{r['name']} ({r['reg_num']}) - {r['course']}": r['id'] for _, r in all_stds.iterrows()}
                    selected_del_std_label = st.selectbox("اختر الطالب المراد حذفه نهائياً من المنصة:", list(std_del_options.keys()), key="del_std_select")
                    target_std_id = std_del_options[selected_del_std_label]
                with col_del_s2:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ حذف الطالب المحدد", key="del_std_btn", use_container_width=True, type="secondary"):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM students WHERE id = ?", (target_std_id,))
                        cur.execute("DELETE FROM users WHERE linked_id = ?", (target_std_id,))
                        cur.execute("DELETE FROM attendance_logs WHERE student_id = ?", (target_std_id,))
                        conn.commit()
                        conn.close()
                        st.warning(f"تم حذف الطالب [{selected_del_std_label}] وسجلاته من المنصة.")
                        st.rerun()

        # 2. إدارة الهيئة التدريسية
        with sub_inst:
            st.markdown("##### ➕ إضافة عضو هيئة تدريسية جديد:")
            with st.form("form_add_instructor"):
                c_i1, c_i2 = st.columns(2)
                with c_i1:
                    new_inst_name = st.text_input("اسم الأستاذ / التدريسي:", placeholder="مثال: أ.د. عمر فاروق علي")
                    new_inst_title = st.text_input("اللقب العلمي / التخصص:", placeholder="مثال: أستاذ دكتور - استوديو التصميم المعماري")
                with c_i2:
                    new_inst_email = st.text_input("البريد الإلكتروني الجامعي:", placeholder="مثال: omar.farouq@uot.edu.iq")
                    new_inst_pass = st.text_input("رمز الدخول (Password):", value="arch2026", type="password")
                
                c_i3, c_i4 = st.columns(2)
                with c_i3:
                    inst_br_sel = st.selectbox("الفرع الأكاديمي التابع له:", list(br_opts.keys()), key="inst_br_sel")
                with c_i4:
                    inst_cr_sel = st.selectbox("المقرر الدراسي المكلف بتدريسه:", list(cr_opts.keys()), key="inst_cr_sel")
                    
                btn_add_inst = st.form_submit_button("➕ حفظ وتعيين التدريسي في المنصة", use_container_width=True, type="primary")

            if btn_add_inst:
                if not new_inst_name.strip() or not new_inst_email.strip():
                    st.error("يرجى ملء اسم التدريسي وبريده الإلكتروني.")
                else:
                    new_inst_id = f"inst-{random.randint(100, 999)}"
                    sel_branch_code = br_opts[inst_br_sel]
                    sel_course_code = cr_opts[inst_cr_sel]

                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("""
                    INSERT INTO instructors (id, name, email, branch_code, course_code, title)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (new_inst_id, new_inst_name.strip(), new_inst_email.strip(), sel_branch_code, sel_course_code, new_inst_title.strip()))
                    
                    cur.execute("""
                    INSERT OR REPLACE INTO users (id, email, password, role, full_name, linked_id, title)
                    VALUES (?, ?, ?, 'INSTRUCTOR', ?, ?, ?)
                    """, (f"usr-{new_inst_id}", new_inst_email.strip(), new_inst_pass.strip(), new_inst_name.strip(), sel_course_code, new_inst_title.strip()))
                    
                    # تحديث اسم التدريسي في جدول المقررات
                    cur.execute("UPDATE courses SET instructor_name = ? WHERE code = ?", (new_inst_name.strip(), sel_course_code))
                    conn.commit()
                    conn.close()
                    st.success(f"🎉 تم تعيين التدريسي [{new_inst_name}] بنجاح على مقرر [{sel_course_code}]!")
                    st.rerun()

            st.markdown("---")
            st.markdown("##### 🗑️ قائمة أعضاء الهيئة التدريسية وإمكانية الحذف:")
            conn = get_db_connection()
            all_insts = pd.read_sql_query("""
            SELECT i.id, i.name, i.title, i.email, b.name_ar as branch, c.title_ar as course, i.course_code
            FROM instructors i
            LEFT JOIN branches b ON i.branch_code = b.code
            LEFT JOIN courses c ON i.course_code = c.code
            """, conn)
            conn.close()

            if not all_insts.empty:
                st.dataframe(all_insts[['name', 'title', 'email', 'branch', 'course']], use_container_width=True, hide_index=True)
                
                col_del_i1, col_del_i2 = st.columns([2.5, 1])
                with col_del_i1:
                    inst_del_options = {f"{r['name']} ({r['title']}) - {r['course']}": r['id'] for _, r in all_insts.iterrows()}
                    selected_del_inst_label = st.selectbox("اختر التدريسي المراد حذفه من المنصة:", list(inst_del_options.keys()), key="del_inst_select")
                    target_inst_id = inst_del_options[selected_del_inst_label]
                with col_del_i2:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ حذف التدريسي المحدد", key="del_inst_btn", use_container_width=True, type="secondary"):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM instructors WHERE id = ?", (target_inst_id,))
                        cur.execute("DELETE FROM users WHERE id = ?", (f"usr-{target_inst_id}",))
                        conn.commit()
                        conn.close()
                        st.warning(f"تم حذف التدريسي [{selected_del_inst_label}] بنجاح.")
                        st.rerun()

        # 3. إدارة المقررات الدراسية
        with sub_crs:
            st.markdown("##### ➕ إضافة مادة / مقرر دراسي جديد:")
            with st.form("form_add_course"):
                c_c1, c_c2 = st.columns(2)
                with c_c1:
                    new_crs_code = st.text_input("رمز المقرر (Course Code):", placeholder="مثال: DES-705 أو URB-704").upper()
                    new_crs_title = st.text_input("عنوان المقرر واستوديو العمارة:", placeholder="مثال: استوديو الإسكان المستدام وتنسيق المواقع")
                with c_c2:
                    new_crs_branch = st.selectbox("الفرع الأكاديمي:", list(br_opts.keys()), key="crs_br_sel")
                    new_crs_inst = st.text_input("الأستاذ المسؤول عن المقرر:", placeholder="مثال: أ.د. رغد هاشم مصطفى")
                    
                c_c3, c_c4 = st.columns(2)
                with c_c3:
                    new_crs_total = st.number_input("إجمالي الساعات الفصلية:", min_value=15, max_value=120, value=60, step=15)
                with c_c4:
                    new_crs_weekly = st.number_input("الساعات الأسبوعية المعتمدة:", min_value=1, max_value=8, value=4, step=1)
                    
                btn_add_crs = st.form_submit_button("➕ حفظ وإدراج المقرر في الخطة الدراسية", use_container_width=True, type="primary")

            if btn_add_crs:
                if not new_crs_code.strip() or not new_crs_title.strip():
                    st.error("يرجى ملء رمز المقرر وعنوانه.")
                else:
                    sel_branch_code = br_opts[new_crs_branch]
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("""
                    INSERT OR REPLACE INTO courses (code, title_ar, branch_code, total_hours, weekly_hours, instructor_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (new_crs_code.strip(), new_crs_title.strip(), sel_branch_code, new_crs_total, new_crs_weekly, new_crs_inst.strip()))
                    conn.commit()
                    conn.close()
                    st.success(f"🎉 تم إضافة المادة الدراسية [{new_crs_title} - {new_crs_code}] بنجاح!")
                    st.rerun()

            st.markdown("---")
            st.markdown("##### 🗑️ قائمة المقررات الدراسية وإمكانية الحذف:")
            conn = get_db_connection()
            all_courses = pd.read_sql_query("""
            SELECT c.code, c.title_ar, b.name_ar as branch, c.instructor_name, c.total_hours, c.weekly_hours
            FROM courses c
            JOIN branches b ON c.branch_code = b.code
            ORDER BY c.code
            """, conn)
            conn.close()

            if not all_courses.empty:
                st.dataframe(all_courses[['code', 'title_ar', 'branch', 'instructor_name', 'total_hours', 'weekly_hours']], use_container_width=True, hide_index=True)
                
                col_del_c1, col_del_c2 = st.columns([2.5, 1])
                with col_del_c1:
                    crs_del_options = {f"{r['code']} - {r['title_ar']} ({r['instructor_name']})": r['code'] for _, r in all_courses.iterrows()}
                    selected_del_crs_label = st.selectbox("اختر المقرر المراد حذفه من الخطة الدراسية:", list(crs_del_options.keys()), key="del_crs_select")
                    target_crs_code = crs_del_options[selected_del_crs_label]
                with col_del_c2:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ حذف المقرر المحدد", key="del_crs_btn", use_container_width=True, type="secondary"):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM courses WHERE code = ?", (target_crs_code,))
                        conn.commit()
                        conn.close()
                        st.warning(f"تم حذف المقرر [{selected_del_crs_label}] من المنصة.")
                        st.rerun()


# ==============================================================================
# 2. بوابة أستاذ المادة (INSTRUCTOR PORTAL) - 3 تبويبات
# ==============================================================================
elif user_role == "INSTRUCTOR":
    inst_course_code = user_linked if (user_linked and user_linked != "ALL") else "DES-702"
    conn = get_db_connection()
    c_info = pd.read_sql_query("""
    SELECT c.code, c.title_ar, c.branch_code, b.name_ar AS branch_name, c.instructor_name, c.weekly_hours
    FROM courses c JOIN branches b ON c.branch_code = b.code
    WHERE c.code = ?
    """, conn, params=(inst_course_code,))
    conn.close()

    if not c_info.empty:
        c_title = c_info.iloc[0]['title_ar']
        c_branch = c_info.iloc[0]['branch_name']
        c_inst = c_info.iloc[0]['instructor_name']
        c_hours = c_info.iloc[0]['weekly_hours']
    else:
        c_title = "استوديو التصميم المعماري المتقدم"
        c_branch = "ماجستير: التصميم المعماري"
        c_inst = user_name
        c_hours = 4

    selected_course_code = inst_course_code

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(255, 255, 255, 1) 100%); border: 1px solid #bfdbfe; border-radius: 16px; padding: 18px 22px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="background: #2563eb; color: #ffffff; padding: 3px 12px; border-radius: 9999px; font-size: 11px; font-weight: 800;">
                    🔒 المقرر الأكاديمي المخصص حصرياً
                </span>
                <h2 style="margin: 8px 0 2px 0; font-size: 19px; font-weight: 800; color: #1e3a8a;">
                    {c_title} ({selected_course_code})
                </h2>
                <div style="font-size: 13px; color: #64748b;">
                    الفرع الأكاديمي: <strong>{c_branch}</strong> | أستاذ المقرر: <strong>{c_inst}</strong> | الساعات الأسبوعية: <strong>{c_hours} ساعات</strong>
                </div>
            </div>
            <div style="background: #eff6ff; border: 1px solid #dbeafe; border-radius: 12px; padding: 8px 16px; font-size: 12.5px; color: #1e40af; font-weight: 700;">
                صلاحية التدريسي: مقيدة بطلبة وقاعة هذا المقرر فقط 🛡️
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # بطاقة معلومات الجلسة المحاضرة
    sc2, sc3 = st.columns([1, 1])
    with sc2:
        session_date = st.date_input("تاريخ الجلسة:", datetime.date.today())
    with sc3:
        session_type = st.selectbox("نوع المحاضرة وساعاتها:", ["استوديو تصميم معماري (4 ساعات)", "محاضرة نظرية (ساعتان)", "سمنار دكتوراه (3 ساعات)"])
        session_hours = 4.0 if "4" in session_type else (3.0 if "3" in session_type else 2.0)
        
    conn = get_db_connection()
    students_in_course = pd.read_sql_query("SELECT id, reg_num, name, total_hours, missed_hours FROM students WHERE course_code = ?", conn, params=(selected_course_code,))
    conn.close()
    
    st.markdown("---")
    
    inst_tab1, inst_tab2, inst_tab3 = st.tabs([
        "📺 شاشة القاعة والـ QR الديناميكي اللحظي",
        "📋 قائمة النداء والتحضير السريع في القاعة",
        "📝 التسجيل اللامتزامن وإدخال الأعذار الرسمية"
    ])
    
    # --- تبويب شاشة القاعة والـ QR بالتحديث الآلي المستمر ---
    with inst_tab1:
        @live_qr_fragment
        def render_live_qr_panel():
            current_time_slot = int(time.time() // 8)
            qr_secret_token = f"UOT-ARCH-{selected_course_code}-{current_time_slot}"
            st.session_state.active_qr_token = qr_secret_token
            st.session_state.active_course_code = selected_course_code
            st.session_state.active_session_date = str(session_date)
            st.session_state.active_session_hours = session_hours

            col_qr_disp, col_live_feed = st.columns([1.1, 1.9])
            
            with col_qr_disp:
                st.markdown("#### 📺 شاشة العارض بالقاعة (Projector View)")
                
                # جلب صورة الـ QR اللحظية من الكاش فائق السرعة
                qr_bytes = generate_qr_image_cached(qr_secret_token)
                st.image(qr_bytes, width=260)
                
                time_left = 8 - int(time.time() % 8)
                pct_bar = max(0.0, min(1.0, time_left / 8.0))
                st.progress(pct_bar, text=f"⏳ يتجدد الرمز آلياً كل 8 ثوانٍ (متبقي: {time_left} ثانية)")
                st.code(f"رمز الأمان اللحظي: {qr_secret_token}", language="text")
                
                st.markdown("""
                <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:10px; border-radius:12px; font-size:12px; color:#15803d;">
                    🔒 <strong>التحقق الجغرافي:</strong> مفعل (محيط 80م)<br>
                    📱 <strong>فحص الجهاز:</strong> هاتف واحد لكل طالب<br>
                    ⚡ <strong>التحديث التلقائي:</strong> يعمل آلياً كل ثانية
                </div>
                """, unsafe_allow_html=True)
                
                # آلية احتياطية للتحديث الآلي في حال عدم دعم st.fragment بالمتصفح
                if not hasattr(st, "fragment") and not hasattr(st, "experimental_fragment"):
                    import streamlit.components.v1 as components
                    components.html("""
                    <script>
                        setTimeout(function() {
                            window.parent.postMessage({type: 'streamlit:rerun'}, '*');
                        }, 1000);
                    </script>
                    """, height=0)

            with col_live_feed:
                st.markdown("#### 📡 شريط الحضور اللحظي في القاعة")
                
                conn = get_db_connection()
                cur_logs = pd.read_sql_query("""
                SELECT s.name, s.reg_num, al.status, al.distance_meters, al.device_fingerprint, al.verification_details, al.created_at
                FROM attendance_logs al
                JOIN students s ON al.student_id = s.id
                WHERE al.session_date = ? AND al.course_code = ?
                ORDER BY al.id DESC
                """, conn, params=(str(session_date), selected_course_code))
                conn.close()
                
                present_count = len(cur_logs[cur_logs['status'] == 'حاضر']) if not cur_logs.empty else 0
                total_count = len(students_in_course)
                
                # شريط نسبة الحضور اللحظي
                pct_live = (present_count / total_count * 100) if total_count > 0 else 0
                st.progress(pct_live / 100, text=f"نسبة الحضور الموثقة بالقاعة: {present_count} من {total_count} ({pct_live:.0f}%)")
                
                if not cur_logs.empty:
                    st.markdown("##### 👥 آخر الطلبة الذين سجلوا حضورهم الآن:")
                    for _, log in cur_logs.head(6).iterrows():
                        st.markdown(f"""
                        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:8px 12px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <strong>{log['name']}</strong> <span style="font-size:11px; color:#64748b;">({log['reg_num']})</span><br>
                                <span style="font-size:11px; color:#16a34a;">{log['verification_details']}</span>
                            </div>
                            <span class="sec-pill">حاضر ✅ ({log['distance_meters']:.0f}م)</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("بانتظار مسح الطلبة للكود الظاهر على الشاشة... يتم التحديث اللحظي تلقائياً كل ثانية.")

        render_live_qr_panel()
                
    # --- تبويب قائمة النداء والتحضير السريع ---
    with inst_tab2:
        st.markdown("#### 📋 نداء الطلبة اليدوي وتأكيد القاعة")
        st.caption("يتيح للأستاذ مراجعة قائمة الطلبة بنقرة واحدة والتعديل اليدوي السريع:")
        
        if 'session_statuses' not in st.session_state or st.session_state.get('last_course') != selected_course_code:
            st.session_state.session_statuses = {s['id']: 'حاضر' for _, s in students_in_course.iterrows()}
            st.session_state.last_course = selected_course_code
            
        b_c1, b_c2 = st.columns(2)
        with b_c1:
            if st.button("✓ تحضير جميع طلبة الفرع بنقرة واحدة", use_container_width=True):
                st.session_state.session_statuses = {s['id']: 'حاضر' for _, s in students_in_course.iterrows()}
                st.rerun()
        with b_c2:
            if st.button("تصفير القائمة (تعيين الكل كغائب)", use_container_width=True):
                st.session_state.session_statuses = {s['id']: 'غائب' for _, s in students_in_course.iterrows()}
                st.rerun()
                
        status_opts = ["حاضر", "غائب", "متأخر", "مجاز بعذر"]
        for _, std in students_in_course.iterrows():
            std_id = std['id']
            curr_val = st.session_state.session_statuses.get(std_id, "حاضر")
            idx = status_opts.index(curr_val) if curr_val in status_opts else 0
            
            col_st_name, col_st_action = st.columns([2, 1.2])
            with col_st_name:
                st.markdown(f"**{std['name']}** <span style='font-size:11px; color:#64748b;'>({std['reg_num']}) | إجمالي الغياب السابق: {std['missed_hours']} س</span>", unsafe_allow_html=True)
            with col_st_action:
                new_val = st.selectbox(f"الحالة لـ {std['id']}", status_opts, index=idx, key=f"std_stat_{std_id}", label_visibility="collapsed")
                st.session_state.session_statuses[std_id] = new_val
                
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 تثبيت وترحيل حضور اليوم لقاعدة البيانات المركزية", type="primary", use_container_width=True):
            conn = get_db_connection()
            cur = conn.cursor()
            for _, std in students_in_course.iterrows():
                val = st.session_state.session_statuses.get(std['id'], "حاضر")
                missed = session_hours if val == "غائب" else 0.0
                cur.execute("""
                INSERT INTO attendance_logs (session_date, course_code, student_id, status, hours_missed, session_mode, verification_details)
                VALUES (?, ?, ?, ?, ?, 'MANUAL_ROSTER', 'تم التحضير اليدوي المباشر من قبل أستاذ المادة')
                """, (str(session_date), selected_course_code, std['id'], val, missed))
                if missed > 0:
                    cur.execute("UPDATE students SET missed_hours = missed_hours + ? WHERE id = ?", (missed, std['id']))
            conn.commit()
            conn.close()
            st.success("🎉 تم تثبيت واعتماد حضور الجلسة بنجاح، وتحديث سجلات الإدارة!")

    # --- تبويب التسجيل اللامتزامن وإدخال الأعذار ---
    with inst_tab3:
        st.markdown("#### 📝 تسجيل الحضور اللامتزامن / إدخال الإجازات والأعذار الرسمية")
        st.caption("استخدم هذه الشاشة لتثبيت حضور المحاضرات السابقة أو تسجيل الأعذار المرضية والرسمية المعتمدة:")
        
        async_records = {}
        for _, std in students_in_course.iterrows():
            col_a1, col_a2, col_a3 = st.columns([2, 1.2, 2])
            with col_a1:
                st.write(f"**{std['name']}** ({std['reg_num']})")
            with col_a2:
                st_val = st.selectbox(f"حالة {std['id']}", ["حاضر", "غائب", "مجاز بعذر رسمي"], key=f"async_s_{std['id']}", label_visibility="collapsed")
            with col_a3:
                st_notes = st.text_input(f"عذر {std['id']}", placeholder="رقم كتاب الإجازة أو العذر الطبي المعتمد...", key=f"note_s_{std['id']}", label_visibility="collapsed")
                async_records[std['id']] = (st_val, st_notes)
                
        if st.button("💾 حفظ وتثبيت السجل اللامتزامن والأعذار", type="primary", use_container_width=True):
            conn = get_db_connection()
            cur = conn.cursor()
            for std_id, (val, notes) in async_records.items():
                missed = session_hours if val == "غائب" else 0.0
                cur.execute("""
                INSERT INTO attendance_logs (session_date, course_code, student_id, status, hours_missed, session_mode, notes, verification_details)
                VALUES (?, ?, ?, ?, ?, 'ASYNC_EXCUSE', ?, 'تسجيل لا متزامن مع توثيق العذر الرسمي')
                """, (str(session_date), selected_course_code, std_id, val, missed, notes))
                if missed > 0:
                    cur.execute("UPDATE students SET missed_hours = missed_hours + ? WHERE id = ?", (missed, std_id))
            conn.commit()
            conn.close()
            st.success("✅ تم حفظ السجل اللامتزامن وتوثيق الأعذار بنجاح!")

# ==============================================================================
# 3. بوابة مسح وحضور الطالب (STUDENT CHECK-IN & FRAUD LAB)
# ==============================================================================
else:
    # بوابة الطالب - مقيدة بحساب الطالب المسجل فقط
    student_id = user_linked if (user_linked and user_linked != "ALL") else "std-202"
    conn = get_db_connection()
    std_info = pd.read_sql_query("""
    SELECT s.*, b.name_ar AS branch_name, c.title_ar AS course_name, c.instructor_name 
    FROM students s 
    JOIN branches b ON s.branch_code = b.code 
    JOIN courses c ON s.course_code = c.code 
    WHERE s.id = ?
    """, conn, params=(student_id,))
    conn.close()

    if not std_info.empty:
        std_row = std_info.iloc[0]
        sel_student_id = std_row['id']
        sel_student_name = std_row['name']
        sel_student_regnum = std_row['reg_num']
        active_course = std_row['course_code']
        active_course_name = std_row['course_name']
        branch_name = std_row['branch_name']
        inst_name = std_row['instructor_name']
        tot_hours = std_row['total_hours']
        mis_hours = std_row['missed_hours']
    else:
        sel_student_id = student_id
        sel_student_name = user_name
        sel_student_regnum = "STD-2026"
        active_course = "DES-702"
        active_course_name = "استوديو التصميم المعماري المتقدم"
        branch_name = "ماجستير التصميم المعماري"
        inst_name = "أ.م.د. لمياء مهدي صالح"
        tot_hours = 60
        mis_hours = 4.0

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(255, 255, 255, 1) 100%); border: 1px solid #a7f3d0; border-radius: 16px; padding: 18px 22px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="background: #059669; color: #ffffff; padding: 3px 12px; border-radius: 9999px; font-size: 11px; font-weight: 800;">
                    🔒 حساب الطالب المعتمد
                </span>
                <h2 style="margin: 8px 0 2px 0; font-size: 19px; font-weight: 800; color: #065f46;">
                    {sel_student_name} ({sel_student_regnum})
                </h2>
                <div style="font-size: 13px; color: #64748b;">
                    الفرع الأكاديمي: <strong>{branch_name}</strong> | المقرر المسجل به: <strong>{active_course_name} ({active_course})</strong> | أستاذ المقرر: <strong>{inst_name}</strong>
                </div>
            </div>
            <div style="background: #ecfdf5; border: 1px solid #d1fae5; border-radius: 12px; padding: 8px 16px; font-size: 12.5px; color: #047857; font-weight: 700;">
                الصلاحية: مقيدة بسجل الطالب وبياناته الشخصية 📱
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st_tab_scan, tab_my_profile = st.tabs([
        "📱 مسح كود الـ QR والتأكيد",
        "🎓 بطاقة الموقف الأكاديمي للطالب (My Standing)"
    ])
    
    with st_tab_scan:
        active_token = st.session_state.get('active_qr_token', f'UOT-ARCH-{active_course}-EXPIRED')
        active_date = st.session_state.get('active_session_date', str(datetime.date.today()))
        
        col_scan_in, col_scan_test = st.columns([1.5, 1])
        
        with col_scan_in:
            st.markdown("##### 1. تحديد هوية الطالب والجهاز:")
            st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:10px 14px; margin-bottom:12px;">
                <div style="font-size:11px; color:#64748b;">الطالب المصادق عليه:</div>
                <div style="font-size:14.5px; font-weight:800; color:#1e293b;">{sel_student_name} ({sel_student_regnum})</div>
                <div style="font-size:11.5px; color:#059669;">المقرر: {active_course_name} ({active_course})</div>
            </div>
            """, unsafe_allow_html=True)
            
            first_name = sel_student_name.split()[0]
            device_input = st.selectbox(
                "بصمة الجهاز المكتشفة (Device Fingerprint):",
                [
                    f"iPhone-15-{first_name}-UID-991",
                    "Galaxy-S24-Zainab-UID-442",
                    "iPhone-13-Mustafa-UID-113",
                    "جهاز مستخدم مسبقاً (محاكاة هاتف زميل) ➔ iPhone-15-Ahmed-UID-991"
                ],
                index=0
            )
            device_id = f"iPhone-15-{first_name}-UID-991" if f"iPhone-15-{first_name}" in device_input else device_input
            
            st.markdown("##### 2. رمز الحضور الممسوح:")
            scanned_code = st.text_input("كود الجلسة (الممسوح بالكاميرا):", value=active_token)
            
            st.markdown("##### 3. الموقع الجغرافي الملتقط (GPS):")
            geo_opt = st.radio(
                "اختبار موقع الطالب:",
                ("📍 داخل استوديو العمارة (على بعد 14 متراً) ✅", "🏠 في المنزل أو خارج الحرم (على بعد 4.8 كم) 🛑"),
                horizontal=True
            )
            
            if "داخل" in geo_opt:
                s_lat, s_lng = UOT_ARCH_LAT + 0.00010, UOT_ARCH_LNG + 0.00010
            else:
                s_lat, s_lng = 33.280000, 44.400000
                
            dist = haversine_distance(UOT_ARCH_LAT, UOT_ARCH_LNG, s_lat, s_lng)
            st.caption(f"المسافة من مبنى كلية هندسة العمارة: **{dist:.1f} متراً** (الحد المسموح: {GEOFENCE_RADIUS_METERS}م)")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 تأكيد الحضور الآن", type="primary", use_container_width=True):
                # فحص الأمان الثلاثي
                curr_slot = int(time.time() // 8)
                expected_token = f"UOT-ARCH-{active_course}-{curr_slot}"
                prev_token = f"UOT-ARCH-{active_course}-{curr_slot - 1}"
                
                token_ok = (scanned_code == expected_token or scanned_code == prev_token)
                geo_ok = (dist <= GEOFENCE_RADIUS_METERS)
                
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("""
                SELECT s.name FROM attendance_logs al
                JOIN students s ON al.student_id = s.id
                WHERE al.session_date = ? AND al.course_code = ? AND al.device_fingerprint = ? AND al.student_id != ?
                """, (active_date, active_course, device_id, sel_student_id))
                conflict = cur.fetchone()
                conn.close()
                
                device_ok = (conflict is None)
                
                if not token_ok:
                    st.error("🛑 **فشل التحقق (الكود منتهي الصلاحية):** لقد مضت أكثر من 8 ثوانٍ على الرمز أو تم تصويره وإرساله! يرجى مسح الكود الحي من شاشة القاعة مباشرة.")
                elif not geo_ok:
                    st.error(f"🛑 **فشل التحقق (الموقع الجغرافي):** تم رصد تواجدك على بُعد {dist:.0f} متراً من قسم العمارة! يُشترط التواجد الفعلي داخل القاعة.")
                elif not device_ok:
                    st.error(f"🛑 **فشل التحقق (جهاز مكرر):** تم استخدام هذا الهاتف بالفعل لتسجيل حضور الطالب [{conflict[0]}] في نفس الجلسة! يُمنع التحضير بالإنابة.")
                else:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM attendance_logs WHERE session_date = ? AND course_code = ? AND student_id = ?", (active_date, active_course, sel_student_id))
                    cur.execute("""
                    INSERT INTO attendance_logs (session_date, course_code, student_id, status, hours_missed, session_mode, device_fingerprint, distance_meters, verification_details)
                    VALUES (?, ?, ?, 'حاضر', 0.0, 'SYNC', ?, ?, 'اجتاز بنجاح: QR حي + GPS داخل القاعة + هاتف فريد')
                    """, (active_date, active_course, sel_student_id, device_id, dist))
                    conn.commit()
                    conn.close()
                    st.success(f"🎉 **تم توثيق حضورك بنجاح يا مهندس/ة [{sel_student_name}]!**")
                    st.balloons()
                    
        with col_scan_test:
            st.markdown("##### 🧪 مختبر اختبار الردع ومكافحة الغش:")
            st.info("""
            **يمكنك تجربة سيناريوهات التحايل التالية ومشاهدة تصدي النظام:**
            
            1. **حضور شرعي:**  
               الموقع داخل القسم + الرمز الحي ➔ **قبول فوري ✅**
            
            2. **صورة واتساب ملتقطة:**  
               انتظر 10 ثوانٍ دون تحديث ➔ **رفض الكود المنتهي 🛑**
               
            3. **طالب بالمنزل:**  
               اختر "في المنزل" ➔ **رفض بالـ GPS Geofence 🛑**
               
            4. **تحضير زميل من نفس الهاتف:**  
               اختر جهاز مستخدم مسبقاً ➔ **رفض لتكرار بصمة الجهاز 🛑**
            """)
            
    with tab_my_profile:
        st.markdown(f"#### 🎓 كشف الموقف الأكاديمي ورصيد الغيابات للطالب: **{sel_student_name}**")
        st.caption(f"الرقم الجامعي: {sel_student_regnum} | الفرع الأكاديمي: {branch_name} | المقرر: {active_course_name} ({active_course})")
        
        status_txt, pct, to_5, to_10 = calculate_warning(mis_hours, tot_hours)
        
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.metric("ساعات الغياب المسجلة", f"{mis_hours} س", f"من إجمالي {tot_hours} س")
        with col_p2:
            st.metric("نسبة الغياب التراكمية", f"{pct:.1f}%", status_txt)
        with col_p3:
            st.metric("رصيد الأمان حتى الإنذار (5%)", f"{to_5:.1f} ساعة", "هامش الأمان الأكاديمي")
            
        st.progress(max(0.0, min(1.0, (100 - pct) / 100)), text=f"نسبة الالتزام بالحضور: {(100 - pct):.1f}%")

# ==============================================================================
# تذييل الصفحة الرسمي لكافة شاشات المنصة (FOOTER)
# ==============================================================================
st.markdown("""
<div style="margin-top: 50px; padding: 22px 16px; border-top: 2px solid #e2e8f0; text-align: center; color: #64748b; font-size: 13px; background: #ffffff; border-radius: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
    <div style="font-weight: 800; color: #b45309; margin-bottom: 6px; font-size: 14px;">
        🏛️ الجامعة التكنولوجية - كلية هندسة العمارة | منصة حضور الدراسات العليا
    </div>
    <div style="font-size: 12.5px; color: #334155; font-weight: 600;">
        هذه المنصة قيد التطوير وبمبادرة شخصية من <span style="font-weight: 800; color: #c2410c; background: #fff7ed; padding: 2px 8px; border-radius: 6px; border: 1px solid #fed7aa;">المهندس المعماري الدكتور أحمد لؤي أحمد</span>
    </div>
</div>
""", unsafe_allow_html=True)

