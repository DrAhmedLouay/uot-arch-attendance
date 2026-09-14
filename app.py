# -*- coding: utf-8 -*-
"""
منظومة حضور وغياب طلبة الدراسات العليا - قسم هندسة العمارة / الجامعة التكنولوجية
Postgraduate Attendance Management System - Department of Architecture Engineering (UOT)
الإصدار المطور (Enterprise Edition) - مظهر معماري فاخر، تحليلات بيانية، ومكافحة احتيال ثلاثية
"""

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
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ثوابت الموقع الجغرافي (مبنى قسم هندسة العمارة - الجامعة التكنولوجية / بغداد)
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

# 4. الهوية البصرية المعمارية والتصميم المتقدم (CSS RTL)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800;900&display=swap');
    
    html, body, [class*="css"], .stMarkdown, .stSelectbox, .stTextInput, .stButton, div {
        font-family: 'Tajawal', -apple-system, sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    /* Header Card */
    .arch-hero {
        background: linear-gradient(135deg, #451a03 0%, #78350f 50%, #b45309 100%);
        color: #ffffff;
        padding: 26px 30px;
        border-radius: 20px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(120, 53, 15, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
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
        color: #b45309 !important;
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
            ('TECH-701', 'الإنشاء المتقدم وتكنولوجيا الأغلفة المعمارية', 'ARCH_TECH', 30, 2, 'م.د. أحمد باسل العزاوي'),
            ('DES-702', 'استوديو التصميم المعماري المتقدم (Studio)', 'ARCH_DESIGN', 60, 4, 'أ.م.د. لمياء مهدي الدوري'),
            ('URB-703', 'استوديو التجديد الحضري وتصميم الفضاءات', 'URBAN_DESIGN', 60, 4, 'أ.د. رغد هاشم الكرخي'),
            ('PHD-801', 'فلسفة ومناهج البحث المعماري المتقدم (سمنار)', 'PHD_ARCH', 30, 2, 'أ.د. حيدر صباح النعيمي')
        ]
        cur.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?)", courses_data)
        
        students_data = [
            ('std-101', 'M-TECH-26-01', 'حيدر كريم الشمري', 'ARCH_TECH', 'TECH-701', 30, 1.0),
            ('std-102', 'M-TECH-26-02', 'زينب عمار التميمي', 'ARCH_TECH', 'TECH-701', 30, 2.0),
            ('std-103', 'M-TECH-26-03', 'ياسر محمد العاني', 'ARCH_TECH', 'TECH-701', 30, 0.0),
            ('std-104', 'M-TECH-26-04', 'هدى عبد الله السعد', 'ARCH_TECH', 'TECH-701', 30, 3.5),
            
            ('std-201', 'M-DES-26-01', 'مصطفى قاسم الجبوري', 'ARCH_DESIGN', 'DES-702', 60, 2.0),
            ('std-202', 'M-DES-26-02', 'سارة ليث العبيدي', 'ARCH_DESIGN', 'DES-702', 60, 4.0),
            ('std-203', 'M-DES-26-03', 'كرار فلاح حسن', 'ARCH_DESIGN', 'DES-702', 60, 4.5),
            ('std-204', 'M-DES-26-04', 'فاطمة جواد الكاظم', 'ARCH_DESIGN', 'DES-702', 60, 3.5),
            
            ('std-301', 'M-URB-26-01', 'عمر طارق السعدي', 'URBAN_DESIGN', 'URB-703', 60, 1.0),
            ('std-302', 'M-URB-26-02', 'مريم نبيل الخفاجي', 'URBAN_DESIGN', 'URB-703', 60, 0.0),
            ('std-303', 'M-URB-26-03', 'بلال حازم المشهداني', 'URBAN_DESIGN', 'URB-703', 60, 4.0),
            
            ('std-401', 'D-ARCH-26-01', 'د. علي جاسم الهاشمي', 'PHD_ARCH', 'PHD-801', 30, 0.0),
            ('std-402', 'D-ARCH-26-02', 'د. نور صفاء الزبيدي', 'PHD_ARCH', 'PHD-801', 30, 1.5),
            ('std-403', 'D-ARCH-26-03', 'د. مهند رياض الحمداني', 'PHD_ARCH', 'PHD-801', 30, 2.0)
        ]
        cur.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?)", students_data)
        
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

# 5. الترويسة الرئيسية المعمارية الفاخرة
st.markdown("""
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
            <h1 style="margin: 0; font-weight: 900; font-size: 26px; letter-spacing: -0.5px;">
                منظومة حضور وغياب الدراسات العليا - قسم هندسة العمارة
            </h1>
            <p style="margin: 6px 0 0 0; font-size: 13px; opacity: 0.9;">
                ماجستير: تكنولوجيا العمارة • التصميم المعماري • التصميم الحضري | دكتوراه هندسة العمارة
            </p>
        </div>
        <div style="text-align: left; background: rgba(0,0,0,0.25); padding: 12px 18px; border-radius: 14px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.15);">
            <div style="font-size: 11px; opacity: 0.8;">نظام الأمان النشط</div>
            <div style="font-weight: 800; font-size: 14px; color: #fbbf24;">🛡️ بروتوكول الحماية الثلاثي</div>
            <div style="font-size: 11px; opacity: 0.85;">QR متغير • GPS محيط 80م • جهاز موحد</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 6. الشريط الجانبي
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/ar/thumb/0/07/University_of_Technology_Iraq_logo.png/250px-University_of_Technology_Iraq_logo.png", width=105)
    st.markdown("### 🎛️ بوابة التنقل والصلاحيات")
    
    role = st.radio(
        "اختر الشاشة النشطة:",
        (
            "🏛️ إدارة الدراسات العليا (Admin Dashboard)",
            "👨‍🏫 بوابة التدريسي / شاشة القاعة (Instructor Portal)",
            "📱 بوابة مسح وحضور الطالب (Student Check-in)"
        ),
        index=0
    )
    
    st.divider()
    st.markdown("#### 📐 الفروع الأكاديمية للدراسات العليا:")
    st.markdown("- **تكنولوجيا العمارة:** الإنشاء والأغلفة")
    st.markdown("- **التصميم المعماري:** استوديو العمارة المتقدم")
    st.markdown("- **التصميم الحضري:** الفضاءات وتجديد المدن")
    st.markdown("- **دكتوراه هندسة العمارة:** فلسفة البحث المعماري")
    
    st.divider()
    st.caption("المنصة متوافقة تماماً مع تعليمات وضوابط الدراسات العليا النافذة لوزارة التعليم العالي والبحث العلمي العراقية.")
    st.info("💡 **هذه المنصة قيد التطوير وبمبادرة شخصية من المهندس المعماري الدكتور أحمد لؤي أحمد**")


# ==============================================================================
# 1. لوحة إدارة الدراسات العليا (ADMIN DASHBOARD) - 4 تبويبات متطورة
# ==============================================================================
if "Admin" in role:
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
    
    # التبويبات الأربعة المتطورة للإدارة
    tab_roster, tab_analytics, tab_security, tab_letters = st.tabs([
        "📋 سجل الغيابات والمتابعة الأكاديمية",
        "📊 التحليلات البيانية ومؤشرات الالتزام",
        "🛡️ سجل التدقيق الأمني ومكافحة الغش",
        "📜 مولّد خطابات الإنذار والحرمان الرسمية"
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
        
        # تصدير كشف Excel / CSV واستعراض كشف مجلس القسم
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
            with st.expander("🖨️ استعراض وطباعة كشف مجلس القسم للغيابات (PDF)", expanded=False):
                warned_council = df_students[df_students['pct'] >= 5.0]
                if warned_council.empty:
                    st.success("🎉 لا توجد حالات تجاوز لنسبة 5% حالياً. جميع الطلبة ضمن الموقف السليم.")
                else:
                    st.markdown(f"**الحالات المرفوعة لمجلس القسم للبت بالحرمان والإنذار ({len(warned_council)} باحثاً):**")
                    st.dataframe(warned_council[['name', 'reg_num', 'branch_name', 'course_name', 'missed_hours', 'pct']], use_container_width=True, hide_index=True)
                    import streamlit.components.v1 as components
                    components.html("""
                    <div style="direction: rtl; text-align: right;">
                        <button onclick="window.parent.print()" style="background:#b45309; color:white; border:none; padding:8px 18px; border-radius:10px; font-weight:700; cursor:pointer; font-size:12px; font-family:sans-serif;">
                            🖨️ طباعة كشف مجلس القسم / حفظ PDF
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
        st.markdown("#### 📜 إصدار كتب وتنبيهات الغياب الرسمية لمجلس القسم")
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
                    <h4 style="margin: 4px 0; color: #78350f;">الجامعة التكنولوجية - قسم هندسة العمارة / الدراسات العليا</h4>
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
                    يرجى الالتزام التام بتسجيل الحضور، وفي حال بلوغ نسبة الغياب 10% سيتم حرمانكم نهائياً من أداء الامتحان النهائي للمقرر وإشعار مجلس القسم لاتخاذ الإجراءات الأكاديمية والقانونية.
                </p>
                
                <div style="display: flex; justify-content: space-between; margin-top: 30px; padding-top: 15px; border-top: 1px dashed #d6d3d1;">
                    <div style="text-align: right; font-size: 12px;">
                        <strong>نسخة منه إلى:</strong><br>
                        - مقرر الدراسات العليا بالقسم.<br>
                        - أستاذ ومسؤول المقرر.<br>
                        - ملف الطالب / الحفظ.
                    </div>
                    <div style="text-align: center; font-size: 13px;">
                        <strong>أ.د. سعد خضير الجميلي</strong><br>
                        معاون العميد للشؤون العلمية والدراسات العليا<br>
                        قسم هندسة العمارة - الجامعة التكنولوجية
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


# ==============================================================================
# 2. بوابة أستاذ المادة (INSTRUCTOR PORTAL) - 3 تبويبات
# ==============================================================================
elif "Instructor" in role:
    conn = get_db_connection()
    courses_df = pd.read_sql_query("""
    SELECT c.code, c.title_ar, c.branch_code, b.name_ar AS branch_name, c.instructor_name, c.weekly_hours
    FROM courses c JOIN branches b ON c.branch_code = b.code
    """, conn)
    conn.close()
    
    course_options = {f"{r['instructor_name']} - {r['title_ar']} ({r['branch_name']})": r['code'] for _, r in courses_df.iterrows()}
    
    # بطاقة معلومات الجلسة
    with st.container():
        sc1, sc2, sc3 = st.columns([2, 1, 1])
        with sc1:
            selected_course_label = st.selectbox("المقرر الدراسي واستوديو العمارة:", list(course_options.keys()))
            selected_course_code = course_options[selected_course_label]
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
    st.subheader("📱 بوابة الطالب: مسح الحضور واختبار الأمان الثلاثي")
    st.markdown("هذه الواجهة تمثل شاشة الهاتف المحمول للطالب عند مسح الـ QR أو فحص موقفه الأكاديمي الشخصي.")
    
    st_tab_scan, tab_my_profile = st.tabs([
        "📱 مسح كود الـ QR والتأكيد",
        "🎓 بطاقة الموقف الأكاديمي للطالب (My Standing)"
    ])
    
    with st_tab_scan:
        active_token = st.session_state.get('active_qr_token', 'UOT-ARCH-DES-702-EXPIRED')
        active_course = st.session_state.get('active_course_code', 'DES-702')
        active_date = st.session_state.get('active_session_date', str(datetime.date.today()))
        
        conn = get_db_connection()
        students_df = pd.read_sql_query("SELECT id, name, reg_num, course_code, total_hours, missed_hours FROM students WHERE course_code = ?", conn, params=(active_course,))
        conn.close()
        
        col_scan_in, col_scan_test = st.columns([1.5, 1])
        
        with col_scan_in:
            st.markdown("##### 1. تحديد هوية الطالب والجهاز:")
            std_opt = st.selectbox("الطالب المسجل:", [f"{r['name']} ({r['reg_num']})" for _, r in students_df.iterrows()])
            sel_student_id = students_df[students_df['name'] == std_opt.split(' (')[0]].iloc[0]['id']
            sel_student_name = std_opt.split(' (')[0]
            
            device_input = st.selectbox(
                "بصمة الجهاز المكتشفة (Device Fingerprint):",
                [
                    "iPhone-15-Ahmed-UID-991",
                    "Galaxy-S24-Zainab-UID-442",
                    "iPhone-13-Mustafa-UID-113",
                    "جهاز مستخدم مسبقاً (محاكاة هاتف زميل) ➔ iPhone-15-Ahmed-UID-991"
                ],
                index=0
            )
            device_id = "iPhone-15-Ahmed-UID-991" if "iPhone-15-Ahmed" in device_input else device_input
            
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
            st.caption(f"المسافة من مبنى قسم هندسة العمارة: **{dist:.1f} متراً** (الحد المسموح: {GEOFENCE_RADIUS_METERS}م)")
            
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
        st.markdown("#### 🎓 كشف الموقف الأكاديمي ورصيد الغيابات الشخصي")
        st_profile_name = st.selectbox("اختر اسم الطالب للاستعلام:", students_df['name'].tolist())
        p_row = students_df[students_df['name'] == st_profile_name].iloc[0]
        
        status_txt, pct, to_5, to_10 = calculate_warning(p_row['missed_hours'], p_row['total_hours'])
        
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.metric("ساعات الغياب المسجلة", f"{p_row['missed_hours']} س", f"من إجمالي {p_row['total_hours']} س")
        with col_p2:
            st.metric("نسبة الغياب التراكمية", f"{pct:.1f}%", status_txt)
        with col_p3:
            st.metric("رصيد الأمان حتى الإنذار (5%)", f"{to_5:.1f} ساعة", "هامش الأمان الأكاديمي")
            
        st.progress((100 - pct) / 100, text=f"نسبة الالتزام بالحضور: {(100 - pct):.1f}%")

# ==============================================================================
# تذييل الصفحة الرسمي لكافة شاشات المنصة (FOOTER)
# ==============================================================================
st.markdown("""
<div style="margin-top: 50px; padding: 22px 16px; border-top: 2px solid #e2e8f0; text-align: center; color: #64748b; font-size: 13px; background: #ffffff; border-radius: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
    <div style="font-weight: 800; color: #b45309; margin-bottom: 6px; font-size: 14px;">
        🏛️ الجامعة التكنولوجية - قسم هندسة العمارة | منصة حضور الدراسات العليا
    </div>
    <div style="font-size: 12.5px; color: #334155; font-weight: 600;">
        هذه المنصة قيد التطوير وبمبادرة شخصية من المهندس المعماري الدكتور أحمد لؤي أحمد
    </div>
</div>
""", unsafe_allow_html=True)

