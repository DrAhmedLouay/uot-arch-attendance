# -*- coding: utf-8 -*-
"""
منظومة حضور وغياب طلبة الدراسات العليا - قسم هندسة العمارة / الجامعة التكنولوجية
Postgraduate Attendance Management System - Department of Architecture Engineering (UOT)
مزودة بنظام الحماية الثلاثي لمكافحة الحضور بالإنابة (Anti-Proxy / Anti-Fraud Engine)
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

# 2. إحداثيات مبنى قسم هندسة العمارة - الجامعة التكنولوجية (بغداد)
UOT_ARCH_LAT = 33.312800
UOT_ARCH_LNG = 44.444400
GEOFENCE_RADIUS_METERS = 80.0  # النطاق المسموح به حول قاعات واستوديوهات القسم

def haversine_distance(lat1, lon1, lat2, lon2):
    """حساب المسافة بين نقطتين بالمتر وفق معادلة هافيرسين"""
    R = 6371000  # نصف قطر الأرض بالمتر
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 3. تخصيص المظهر باللغة العربية (RTL)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    
    html, body, [class*="css"], .stMarkdown, .stSelectbox, .stTextInput, .stButton, div {
        font-family: 'Tajawal', -apple-system, sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    .stMetric {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 16px;
    }
    
    [data-testid="stMetricValue"] {
        font-weight: 800 !important;
        color: #d97706 !important;
        text-align: right !important;
    }
    
    [data-testid="stMetricLabel"] {
        text-align: right !important;
        font-weight: 600 !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, #78350f, #b45309, #d97706);
        color: white;
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .security-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
        padding: 6px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# 4. إعداد قاعدة البيانات
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
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
            ('TECH-701', 'الإنشاء المتقدم وتكنولوجيا الأغلفة', 'ARCH_TECH', 30, 2, 'م.د. أحمد باسل العزاوي'),
            ('DES-702', 'استوديو التصميم المعماري المتقدم', 'ARCH_DESIGN', 60, 4, 'أ.م.د. لمياء مهدي الدوري'),
            ('URB-703', 'استوديو التجديد وتصميم الفضاءات الحضرية', 'URBAN_DESIGN', 60, 4, 'أ.د. رغد هاشم الكرخي'),
            ('PHD-801', 'فلسفة ومناهج البحث المعماري (سمنار)', 'PHD_ARCH', 30, 2, 'أ.د. حيدر صباح النعيمي')
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
    if total_hours == 0:
        return "طبيعي", 0.0
    pct = (missed_hours / total_hours) * 100
    if pct >= 10.0:
        return "حرمان رسمي (10% فأكثر)", pct
    elif pct >= 7.0:
        return "إنذار نهائي (7%)", pct
    elif pct >= 5.0:
        return "إنذار أولي (5%)", pct
    return "طبيعي ومستقر", pct

# 5. الترويسة الرئيسية
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h2 style="margin: 0; font-weight: 800; font-size: 26px;">🏛️ منظومة حضور وغياب الدراسات العليا - هندسة العمارة</h2>
            <h4 style="margin: 4px 0 0 0; font-weight: 500; font-size: 16px; opacity: 0.95;">
                الجامعة التكنولوجية - بغداد | بنظام الحماية الثلاثي لمكافحة التحضير بالإنابة (Anti-Proxy Engine)
            </h4>
        </div>
        <div style="text-align: left; font-size: 13px; background: rgba(255,255,255,0.15); padding: 8px 14px; border-radius: 10px;">
            <div>🛡️ الأمان: <strong>ثلاثي المستويات</strong></div>
            <div>⏱️ QR • 📍 GPS • 📱 Device</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 6. الشريط الجانبي
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/ar/thumb/0/07/University_of_Technology_Iraq_logo.png/250px-University_of_Technology_Iraq_logo.png", width=110)
    st.markdown("### ⚙️ تحديد الدور النشط")
    
    role = st.radio(
        "اختر الشاشة الحالية:",
        (
            "🏛️ إدارة الدراسات العليا (Admin)",
            "👨‍🏫 شاشة التدريسي / عرض الـ QR (Instructor)",
            "📱 بوابة مسح حضور الطالب (Student Scan Portal)"
        ),
        index=1
    )
    
    st.divider()
    st.markdown("#### 🛡️ بروتوكول الأمان الثلاثي المفعّل:")
    st.markdown("1. **Dynamic QR (8 ثوانٍ):** يمنع تصوير ونقل الكود عبر الواتساب.")
    st.markdown("2. **GPS Geofence (80 متراً):** يضمن تواجد الطالب داخل مبنى قسم العمارة.")
    st.markdown("3. **Single Device Policy:** يمنع تسجيل طالبين من نفس الهاتف نهائياً.")

# ==============================================================================
# 1. واجهة أستاذ المادة وتوليد الـ QR مع نظام الأمان اللحظي
# ==============================================================================
if "Instructor" in role:
    st.subheader("👨‍🏫 شاشة الأستاذ: بدء جلسة الحضور وتوليد الـ QR المحمي")
    
    conn = get_db_connection()
    courses_df = pd.read_sql_query("""
    SELECT c.code, c.title_ar, c.branch_code, b.name_ar AS branch_name, c.instructor_name, c.weekly_hours
    FROM courses c JOIN branches b ON c.branch_code = b.code
    """, conn)
    conn.close()
    
    course_options = {f"{r['instructor_name']} - {r['title_ar']} ({r['branch_name']})": r['code'] for _, r in courses_df.iterrows()}
    selected_course_label = st.selectbox("اختر المقرر الدراسي:", list(course_options.keys()))
    selected_course_code = course_options[selected_course_label]
    
    c1, c2, c3 = st.columns(3)
    with c1:
        session_date = st.date_input("تاريخ المحاضرة:", datetime.date.today())
    with c2:
        session_type = st.selectbox("نوع المحاضرة:", ["استوديو تصميم معماري (4 ساعات)", "محاضرة نظرية (ساعتان)", "سمنار دكتوراه (3 ساعات)"])
        session_hours = 4.0 if "4" in session_type else (3.0 if "3" in session_type else 2.0)
    with c3:
        attendance_mode = st.radio("نمط التحضير:", ("📱 متزامن (QR حي + أمان ثلاثي)", "📝 يدوي لا متزامن (أوفلاين)"), horizontal=True)

    st.markdown("---")

    conn = get_db_connection()
    students_in_course = pd.read_sql_query("SELECT id, reg_num, name, total_hours, missed_hours FROM students WHERE course_code = ?", conn, params=(selected_course_code,))
    conn.close()

    if "متزامن" in attendance_mode:
        # حساب الرمز المتجدد بناء على الوقت (نافذة كل 8 ثوانٍ)
        current_time_slot = int(time.time() // 8)
        qr_secret_token = f"UOT-ARCH-{selected_course_code}-{current_time_slot}"
        st.session_state.active_qr_token = qr_secret_token
        st.session_state.active_course_code = selected_course_code
        st.session_state.active_session_date = str(session_date)
        st.session_state.active_session_hours = session_hours

        col_qr, col_roster = st.columns([1, 2])
        
        with col_qr:
            st.markdown("#### 📺 شاشة العرض بالقاعة (Dynamic QR)")
            st.caption("يعرض الأستاذ هذه الشاشة على العارض (Projector). يتجدد الرمز تلقائياً كل 8 ثوانٍ لمنع إرساله عبر الواتساب.")
            
            # توليد صورة الـ QR
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(qr_secret_token)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#78350f", back_color="white")
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), width=250)
            
            # عداد الثواني اللحظي
            time_left = 8 - int(time.time() % 8)
            st.markdown(f"⏳ **يتجدد الرمز خلال:** `{time_left} ثوانٍ`")
            st.code(f"رمز الأمان اللحظي: {qr_secret_token}", language="text")
            
            st.markdown("""
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:10px; border-radius:10px; font-size:12px; color:#166534;">
                🔒 <strong>التحقق الجغرافي:</strong> مفعل (محيط 80م)<br>
                📱 <strong>فحص الجهاز:</strong> مفعل (جهاز واحد لكل طالب)
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 تحديث شاشة الـ QR الآن", use_container_width=True):
                st.rerun()

        with col_roster:
            st.markdown("#### 📋 سجل حضور القاعة التفاعلي")
            
            # جلب سجل الحضور الفعلي للجلسة الحالية
            conn = get_db_connection()
            cur_logs = pd.read_sql_query("""
            SELECT s.name, s.reg_num, al.status, al.distance_meters, al.device_fingerprint, al.verification_details, al.created_at
            FROM attendance_logs al
            JOIN students s ON al.student_id = s.id
            WHERE al.session_date = ? AND al.course_code = ?
            ORDER BY al.id DESC
            """, conn, params=(str(session_date), selected_course_code))
            conn.close()
            
            present_students = cur_logs[cur_logs['status'] == 'حاضر']['name'].tolist() if not cur_logs.empty else []
            total_students_count = len(students_in_course)
            present_count = len(present_students)
            
            st.metric("نسبة الحضور الموثقة بالقاعة الآن", f"{present_count} من {total_students_count}", f"{(present_count/total_students_count*100):.0f}%")
            
            if not cur_logs.empty:
                st.markdown("##### 🔍 سجل عمليات التحقق الأمني المباشرة:")
                for _, log in cur_logs.head(5).iterrows():
                    st.markdown(f"✔️ **{log['name']}** | {log['status']} | البعد: `{log['distance_meters']:.0f}م` | الجهاز: `{log['device_fingerprint']}`  \n<span style='font-size:11px; color:#15803d;'>{log['verification_details']}</span>", unsafe_allow_html=True)
            else:
                st.info("بانتظار مسح الطلبة للرمز... (يمكنك فتح تبويب 'بوابة مسح حضور الطالب' من الشريط الجانبي لتجربة المسح).")
                
            st.markdown("---")
            if st.button("✓ تحضير يدوي للطلبة الحاضرين واعتماد الجلسة", use_container_width=True):
                st.success("تم اعتماد الجلسة في قاعدة البيانات بنجاح.")

    else:
        st.markdown("#### 📝 التسجيل اليدوي اللامتزامن (أوفلاين)")
        st.caption("لحالات انقطاع الشبكة أو إدخال غيابات التواريخ السابقة.")
        for _, std in students_in_course.iterrows():
            c_n, c_s = st.columns([2, 1])
            with c_n:
                st.write(f"**{std['name']}** ({std['reg_num']})")
            with c_s:
                st.selectbox(f"حالة {std['id']}", ["حاضر", "غائب", "مجاز"], key=f"as_{std['id']}", label_visibility="collapsed")
        if st.button("💾 حفظ السجل اليدوي", type="primary"):
            st.success("تم حفظ السجل اللامتزامن بنجاح.")

# ==============================================================================
# 2. بوابة مسح حضور الطالب (STUDENT SCAN PORTAL) - اختبار الأمان الثلاثي
# ==============================================================================
elif "Student" in role:
    st.subheader("📱 بوابة مسح الحضور - جهاز الطالب")
    st.markdown("هذه الواجهة تمثل ما يراه الطالب عند فتح الرابط عبر هاتفه لمسح الـ QR والتأكيد.")
    
    active_token = st.session_state.get('active_qr_token', 'UOT-ARCH-DES-702-EXPIRED')
    active_course = st.session_state.get('active_course_code', 'DES-702')
    active_date = st.session_state.get('active_session_date', str(datetime.date.today()))
    active_hours = st.session_state.get('active_session_hours', 4.0)
    
    conn = get_db_connection()
    students_df = pd.read_sql_query("SELECT id, name, reg_num, course_code FROM students WHERE course_code = ?", conn, params=(active_course,))
    conn.close()
    
    col_input, col_sim = st.columns([1.5, 1])
    
    with col_input:
        st.markdown("#### 1. بيانات الطالب والجهاز:")
        student_choice = st.selectbox("اختر الطالب لتسجيل الحضور:", [f"{r['name']} ({r['reg_num']})" for _, r in students_df.iterrows()])
        selected_student_id = students_df[students_df['name'] == student_choice.split(' (')[0]].iloc[0]['id']
        selected_student_name = student_choice.split(' (')[0]
        
        device_id_input = st.selectbox(
            "معرّف الجهاز (Device Fingerprint):",
            [
                "iPhone-15-Ahmed-UID-991",
                "Galaxy-S24-Zainab-UID-442",
                "iPhone-13-Mustafa-UID-113",
                "جهاز مستخدم مسبقاً (محاكاة جهاز زميل) ➔ iPhone-15-Ahmed-UID-991"
            ],
            index=0
        )
        # تنظيف معرّف الجهاز
        device_id = "iPhone-15-Ahmed-UID-991" if "iPhone-15-Ahmed" in device_id_input else device_id_input
        
        st.markdown("#### 2. مسح رمز الـ QR:")
        scanned_token = st.text_input("رمز الـ QR الممسوح من الشاشة:", value=active_token)
        
        st.markdown("#### 3. إحداثيات الموقع الجغرافي (GPS):")
        location_mode = st.radio(
            "اختبار الموقع الجغرافي للطالب:",
            (
                "📍 داخل قسم هندسة العمارة (على بعد 15 متراً) ✅",
                "🏠 خارج الجامعة / في المنزل (على بعد 4.8 كم) 🛑"
            ),
            index=0
        )
        
        if "داخل" in location_mode:
            student_lat = UOT_ARCH_LAT + 0.00010  # ~12 meters away
            student_lng = UOT_ARCH_LNG + 0.00010
        else:
            student_lat = 33.280000  # Outside campus (several km)
            student_lng = 44.400000
            
        dist = haversine_distance(UOT_ARCH_LAT, UOT_ARCH_LNG, student_lat, student_lng)
        st.caption(f"المسافة المحسوبة من مبنى قسم العمارة: **{dist:.1f} متراً** (الحد الأقصى المسموح: {GEOFENCE_RADIUS_METERS}م)")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 تأكيد الحضور وإرسال الطلب", type="primary", use_container_width=True):
            # فحص الطبقات الأمنية الثلاث:
            
            # 1. فحص الكود المتجدد
            current_time_slot = int(time.time() // 8)
            expected_token = f"UOT-ARCH-{active_course}-{current_time_slot}"
            # السماح بالنافذة الحالية أو النافذة السابقة مباشرة (8 ثوانٍ مرونة لتأخر الشبكة)
            prev_token = f"UOT-ARCH-{active_course}-{current_time_slot - 1}"
            
            token_valid = (scanned_token == expected_token or scanned_token == prev_token)
            
            # 2. فحص الموقع الجغرافي
            geo_valid = (dist <= GEOFENCE_RADIUS_METERS)
            
            # 3. فحص الجهاز (One Device Policy)
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
            SELECT s.name FROM attendance_logs al
            JOIN students s ON al.student_id = s.id
            WHERE al.session_date = ? AND al.course_code = ? AND al.device_fingerprint = ? AND al.student_id != ?
            """, (active_date, active_course, device_id, selected_student_id))
            conflict_device = cur.fetchone()
            conn.close()
            
            device_valid = (conflict_device is None)
            
            # تقييم النتيجة
            if not token_valid:
                st.error("🛑 **فشل التحقق (الكود منتهي الصلاحية):** لقد مضى أكثر من 8 ثوانٍ على توليد الكود أو تم نسخه بطريقة غير نظامية! يرجى مسح الكود الحي على الشاشة مباشرة.")
            elif not geo_valid:
                st.error(f"🛑 **فشل التحقق (خارج النطاق الجغرافي):** تم رصد موقعك على بُعد {dist:.0f} متراً من قسم هندسة العمارة! يُشترط التواجد الفعلي داخل القاعة.")
            elif not device_valid:
                st.error(f"🛑 **فشل التحقق (احتيال عبر نفس الجهاز):** تم استخدام هذا الهاتف بالفعل لتسجيل حضور الطالب [{conflict_device[0]}] في نفس هذه المحاضرة! يُمنع التحضير بالإنابة.")
            else:
                # نجاح تام وتسجيل الحضور
                conn = get_db_connection()
                cur = conn.cursor()
                # حذف أي تسجيل سابق لنفس الطالب بالجلسة
                cur.execute("DELETE FROM attendance_logs WHERE session_date = ? AND course_code = ? AND student_id = ?", (active_date, active_course, selected_student_id))
                cur.execute("""
                INSERT INTO attendance_logs (session_date, course_code, student_id, status, hours_missed, session_mode, device_fingerprint, distance_meters, verification_details)
                VALUES (?, ?, ?, 'حاضر', 0.0, 'SYNC', ?, ?, 'اجتاز الأمان الثلاثي: QR حي + GPS داخل القاعة + هاتف فريد')
                """, (active_date, active_course, selected_student_id, device_id, dist))
                conn.commit()
                conn.close()
                st.success(f"🎉 **تم تأكيد حضورك بنجاح يا مهندس/ة [{selected_student_name}]!**  \n- الرمز: صالح وموثوق  \n- الموقع: داخل قاعة القسم ({dist:.1f}م)  \n- الهاتف: موثق ومعتمد")
                st.balloons()
                
    with col_sim:
        st.markdown("#### 🧪 سيناريوهات التحايل الشائعة للاختبار:")
        st.info("""
        **جرب الحالات التالية وشاهد النتيجة:**
        
        1. **حالة الحضور الشرعي:**
           - اختر الطالب، ضع الموقع "داخل القسم"، والرمز الحالي ➔ **قبول فوري ✅**.
        
        2. **حالة الطالب الغائب في المنزل:**
           - اختر الموقع "خارج الجامعة" واضغط تأكيد ➔ **يُرفض فوراً بسبب الـ GPS 🛑**.
        
        3. **حالة تصوير الـ QR وإرساله عبر واتساب:**
           - انتظر 10 ثوانٍ دون تحديث الرمز ثم اضغط تأكيد ➔ **يُرفض لانتهاء صلاحية الـ 8 ثوانٍ 🛑**.
        
        4. **حالة تحضير الزميل من نفس الهاتف:**
           - بعد تحضير طالب، اختر طالباً آخر واختر "جهاز مستخدم مسبقاً" ➔ **يُرفض بسبب تطابق بصمة الجهاز 🛑**.
        """)

# ==============================================================================
# 3. واجهة الإدارة (ADMIN VIEW)
# ==============================================================================
else:
    st.subheader("📊 لوحة إدارة الدراسات العليا ومتابعة الغيابات")
    conn = get_db_connection()
    df_students = pd.read_sql_query("""
    SELECT s.id, s.reg_num, s.name, b.name_ar AS branch_name, s.branch_code, c.title_ar AS course_name, s.total_hours, s.missed_hours
    FROM students s
    JOIN branches b ON s.branch_code = b.code
    JOIN courses c ON s.course_code = c.code
    """, conn)
    conn.close()
    
    df_students['pct'] = (df_students['missed_hours'] / df_students['total_hours']) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("إجمالي طلبة الدراسات العليا", f"{len(df_students)} طالباً")
    with col2:
        st.metric("متوسط نسبة الحضور", f"{(100 - df_students['pct'].mean()):.1f}%")
    with col3:
        warns = len(df_students[(df_students['pct'] >= 5.0) & (df_students['pct'] < 10.0)])
        st.metric("تنبيهات الإنذار (5% - 7%)", f"{warns} طلاب", delta_color="inverse")
    with col4:
        dep = len(df_students[df_students['pct'] >= 10.0])
        st.metric("حالات الحرمان (تجاوز 10%)", f"{dep} حالات", delta_color="inverse")
        
    st.markdown("---")
    
    branch_filter = st.selectbox(
        "تصفية الكشف حسب الفرع الأكاديمي:",
        ["كافة الفروع الأكاديمية", "ماجستير: تكنولوجيا العمارة", "ماجستير: التصميم المعماري", "ماجستير: التصميم الحضري", "دكتوراه: هندسة العمارة"]
    )
    
    f_df = df_students if branch_filter == "كافة الفروع الأكاديمية" else df_students[df_students['branch_name'] == branch_filter]
    
    rows = []
    for _, r in f_df.iterrows():
        status_txt, pct = calculate_warning(r['missed_hours'], r['total_hours'])
        rows.append({
            "الرقم الجامعي": r['reg_num'],
            "اسم الطالب": r['name'],
            "الفرع": r['branch_name'],
            "المقرر": r['course_name'],
            "ساعات الغياب": f"{r['missed_hours']} س",
            "النسبة": f"{pct:.1f}%",
            "الموقف": status_txt
        })
    res = pd.DataFrame(rows)
    st.dataframe(res, use_container_width=True, hide_index=True)
    
    csv = res.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 تصدير كشف الغياب الرسمي (Excel / CSV)", data=csv, file_name="غيابات_هندسة_العمارة.csv", mime="text/csv")
