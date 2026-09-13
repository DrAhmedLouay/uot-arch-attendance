# -*- coding: utf-8 -*-
"""
منظومة حضور وغياب طلبة الدراسات العليا - قسم هندسة العمارة / الجامعة التكنولوجية
Postgraduate Attendance Management System - Department of Architecture Engineering (UOT)
"""

import streamlit as st
import pandas as pd
import sqlite3
import datetime
import qrcode
import io
import os
import random
from PIL import Image

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="منظومة حضور الدراسات العليا - هندسة العمارة | الجامعة التكنولوجية",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. تخصيص المظهر باللغة العربية (RTL) وثيم متناسق
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
    
    .branch-card {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 10px;
        background-color: #ffffff;
    }
    
    .badge-normal {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
    }
    .badge-warn5 {
        background-color: #fef3c7;
        color: #b45309;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
    }
    .badge-warn7 {
        background-color: #ffedd5;
        color: #c2410c;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
    }
    .badge-deprived {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# 3. إعداد وتهيئة قاعدة البيانات SQLite
DB_PATH = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # جداول النظام
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # فحص إذا كانت البيانات الأولية موجودة
    cur.execute("SELECT COUNT(*) FROM branches")
    if cur.fetchone()[0] == 0:
        # إضافة الفروع الأربعة
        branches_data = [
            ('ARCH_TECH', 'ماجستير: تكنولوجيا العمارة', 'MSC'),
            ('ARCH_DESIGN', 'ماجستير: التصميم المعماري', 'MSC'),
            ('URBAN_DESIGN', 'ماجستير: التصميم الحضري', 'MSC'),
            ('PHD_ARCH', 'دكتوراه: هندسة العمارة', 'PHD')
        ]
        cur.executemany("INSERT INTO branches VALUES (?, ?, ?)", branches_data)
        
        # المقررات والأساتذة
        courses_data = [
            ('TECH-701', 'الإنشاء المتقدم وتكنولوجيا الأغلفة', 'ARCH_TECH', 30, 2, 'م.د. أحمد باسل العزاوي'),
            ('DES-702', 'استوديو التصميم المعماري المتقدم', 'ARCH_DESIGN', 60, 4, 'أ.م.د. لمياء مهدي الدوري'),
            ('URB-703', 'استوديو التجديد وتصميم الفضاءات الحضرية', 'URBAN_DESIGN', 60, 4, 'أ.د. رغد هاشم الكرخي'),
            ('PHD-801', 'فلسفة ومناهج البحث المعماري (سمنار)', 'PHD_ARCH', 30, 2, 'أ.د. حيدر صباح النعيمي')
        ]
        cur.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?)", courses_data)
        
        # بيانات الطلبة الافتراضية
        students_data = [
            # تكنولوجيا العمارة
            ('std-101', 'M-TECH-26-01', 'حيدر كريم الشمري', 'ARCH_TECH', 'TECH-701', 30, 1.0),
            ('std-102', 'M-TECH-26-02', 'زينب عمار التميمي', 'ARCH_TECH', 'TECH-701', 30, 2.0),
            ('std-103', 'M-TECH-26-03', 'ياسر محمد العاني', 'ARCH_TECH', 'TECH-701', 30, 0.0),
            ('std-104', 'M-TECH-26-04', 'هدى عبد الله السعد', 'ARCH_TECH', 'TECH-701', 30, 3.5), # >10%
            
            # التصميم المعماري
            ('std-201', 'M-DES-26-01', 'مصطفى قاسم الجبوري', 'ARCH_DESIGN', 'DES-702', 60, 2.0),
            ('std-202', 'M-DES-26-02', 'سارة ليث العبيدي', 'ARCH_DESIGN', 'DES-702', 60, 4.0),
            ('std-203', 'M-DES-26-03', 'كرار فلاح حسن', 'ARCH_DESIGN', 'DES-702', 60, 4.5), # >=7%
            ('std-204', 'M-DES-26-04', 'فاطمة جواد الكاظم', 'ARCH_DESIGN', 'DES-702', 60, 3.5), # >=5%
            
            # التصميم الحضري
            ('std-301', 'M-URB-26-01', 'عمر طارق السعدي', 'URBAN_DESIGN', 'URB-703', 60, 1.0),
            ('std-302', 'M-URB-26-02', 'مريم نبيل الخفاجي', 'URBAN_DESIGN', 'URB-703', 60, 0.0),
            ('std-303', 'M-URB-26-03', 'بلال حازم المشهداني', 'URBAN_DESIGN', 'URB-703', 60, 4.0),
            
            # دكتوراه هندسة العمارة
            ('std-401', 'D-ARCH-26-01', 'د. علي جاسم الهاشمي', 'PHD_ARCH', 'PHD-801', 30, 0.0),
            ('std-402', 'D-ARCH-26-02', 'د. نور صفاء الزبيدي', 'PHD_ARCH', 'PHD-801', 30, 1.5),
            ('std-403', 'D-ARCH-26-03', 'د. مهند رياض الحمداني', 'PHD_ARCH', 'PHD-801', 30, 2.0)
        ]
        cur.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?)", students_data)
        
    conn.commit()
    conn.close()

init_db()

# دوال مساعدة لحساب الغيابات والإنذارات
def get_db_connection():
    return sqlite3.connect(DB_PATH)

def calculate_warning(missed_hours, total_hours):
    if total_hours == 0:
        return "طبيعي", "badge-normal", 0.0
    pct = (missed_hours / total_hours) * 100
    if pct >= 10.0:
        return "حرمان رسمي (10% فأكثر)", "badge-deprived", pct
    elif pct >= 7.0:
        return "إنذار نهائي (7%)", "badge-warn7", pct
    elif pct >= 5.0:
        return "إنذار أولي (5%)", "badge-warn5", pct
    return "طبيعي ومستقر", "badge-normal", pct

# 4. ترويسة النظام والشعار
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h2 style="margin: 0; font-weight: 800; font-size: 26px;">🏛️ منظومة حضور وغياب طلبة الدراسات العليا</h2>
            <h4 style="margin: 4px 0 0 0; font-weight: 500; font-size: 16px; opacity: 0.95;">
                الجامعة التكنولوجية - قسم هندسة العمارة | العام الدراسي 2026-2027
            </h4>
            <p style="margin: 6px 0 0 0; font-size: 13px; opacity: 0.85;">
                ماجستير (تكنولوجيا العمارة، التصميم المعماري، التصميم الحضري) • دكتوراه هندسة العمارة
            </p>
        </div>
        <div style="text-align: left; font-size: 13px; background: rgba(255,255,255,0.15); padding: 8px 14px; border-radius: 10px;">
            <div>🕒 الفصل الدراسي الأول</div>
            <div style="font-weight: bold;">نظام الساعات المعتمدة</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 5. الشريط الجانبي (Sidebar)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/ar/thumb/0/07/University_of_Technology_Iraq_logo.png/250px-University_of_Technology_Iraq_logo.png", width=120)
    st.markdown("### ⚙️ لوحة التحكم والصلاحيات")
    
    role = st.radio(
        "اختر نوع الحساب النشط:",
        ("🏛️ إدارة الدراسات العليا (Admin)", "👨‍🏫 أستاذ المادة (Instructor)"),
        index=0
    )
    
    st.divider()
    st.markdown("#### 📚 الفروع الأكاديمية للدراسات العليا:")
    st.markdown("- **ماجستير:** فرع تكنولوجيا العمارة")
    st.markdown("- **ماجستير:** فرع التصميم المعماري")
    st.markdown("- **ماجستير:** فرع التصميم الحضري")
    st.markdown("- **دكتوراه:** هندسة العمارة")
    
    st.divider()
    st.info("💡 **ضوابط الغياب المعتمدة:**\n- 5%: إنذار أولي\n- 7%: إنذار نهائي\n- 10%: حرمان رسمي من الامتحان")

# 6. واجهة مدير الدراسات العليا (ADMIN VIEW)
if "Admin" in role:
    st.subheader("📊 لوحة المؤشرات الشاملة - إدارة الدراسات العليا")
    
    conn = get_db_connection()
    df_students = pd.read_sql_query("""
    SELECT s.id, s.reg_num, s.name, b.name_ar AS branch_name, s.branch_code, c.title_ar AS course_name, s.total_hours, s.missed_hours
    FROM students s
    JOIN branches b ON s.branch_code = b.code
    JOIN courses c ON s.course_code = c.code
    """, conn)
    conn.close()
    
    # حساب الإحصائيات
    df_students['pct'] = (df_students['missed_hours'] / df_students['total_hours']) * 100
    total_students = len(df_students)
    warn_5_count = len(df_students[(df_students['pct'] >= 5.0) & (df_students['pct'] < 10.0)])
    deprived_count = len(df_students[df_students['pct'] >= 10.0])
    avg_attendance = 100 - df_students['pct'].mean()
    
    # بطاقات المؤشرات الرقمية
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("إجمالي طلبة الدراسات العليا", f"{total_students} طالباً", "4 فروع تخصصية")
    with col2:
        st.metric("متوسط نسبة الحضور", f"{avg_attendance:.1f}%", "مستوى التزام مرتفع")
    with col3:
        st.metric("تنبيهات الإنذار (5% - 7%)", f"{warn_5_count} طلاب", "تنبيه إداري", delta_color="inverse")
    with col4:
        st.metric("حالات الحرمان (تجاوز 10%)", f"{deprived_count} حالات", "يُعرض على مجلس القسم", delta_color="inverse")
        
    st.markdown("---")
    
    # فلترة الفروع
    col_filter, col_export = st.columns([3, 1])
    with col_filter:
        branch_filter = st.selectbox(
            "تصفية الكشف حسب الفرع الأكاديمي:",
            ["كافة الفروع الأكاديمية", "ماجستير: تكنولوجيا العمارة", "ماجستير: التصميم المعماري", "ماجستير: التصميم الحضري", "دكتوراه: هندسة العمارة"]
        )
        
    filtered_df = df_students.copy()
    if branch_filter != "كافة الفروع الأكاديمية":
        filtered_df = filtered_df[filtered_df['branch_name'] == branch_filter]
        
    # تنسيق جدول العرض
    display_rows = []
    for _, row in filtered_df.iterrows():
        status_text, badge_class, pct = calculate_warning(row['missed_hours'], row['total_hours'])
        display_rows.append({
            "الرقم الجامعي": row['reg_num'],
            "اسم الطالب": row['name'],
            "الفرع الأكاديمي": row['branch_name'],
            "المقرر الدراسي": row['course_name'],
            "إجمالي الساعات": f"{row['total_hours']} س",
            "ساعات الغياب": f"{row['missed_hours']} س",
            "نسبة الغياب": f"{pct:.1f}%",
            "الموقف الأكاديمي": status_text
        })
        
    res_df = pd.DataFrame(display_rows)
    
    with col_export:
        st.markdown("<br>", unsafe_allow_html=True)
        csv = res_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 تصدير الكشف إلى Excel (CSV)",
            data=csv,
            file_name=f"كشف_غيابات_هندسة_العمارة_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    st.dataframe(res_df, use_container_width=True, hide_index=True)
    
    # تفاصيل الحالات الحرجة
    critical_cases = filtered_df[filtered_df['pct'] >= 5.0]
    if not critical_cases.empty:
        st.warning("⚠️ **تنبيه الحالات التي تستوجب إصدار كتب إنذار أو إحالة لمجلس قسم هندسة العمارة:**")
        for _, c_row in critical_cases.iterrows():
            status_text, _, pct = calculate_warning(c_row['missed_hours'], c_row['total_hours'])
            st.markdown(f"- **{c_row['name']}** ({c_row['branch_name']}) | المقرر: {c_row['course_name']} | الساعات المفقودة: {c_row['missed_hours']} من {c_row['total_hours']} س (**{pct:.1f}%**) ➔ `{status_text}`")

# 7. واجهة أستاذ المادة (INSTRUCTOR VIEW)
else:
    st.subheader("👨‍🏫 بوابة تدريسيي الدراسات العليا - تسجيل الحضور")
    
    conn = get_db_connection()
    courses_df = pd.read_sql_query("""
    SELECT c.code, c.title_ar, c.branch_code, b.name_ar AS branch_name, c.instructor_name, c.weekly_hours
    FROM courses c
    JOIN branches b ON c.branch_code = b.code
    """, conn)
    conn.close()
    
    # اختيار التدريسي والمقرر
    course_options = {f"{r['instructor_name']} - {r['title_ar']} ({r['branch_name']})": r['code'] for _, r in courses_df.iterrows()}
    selected_course_label = st.selectbox("المقرر والأستاذ المشرف:", list(course_options.keys()))
    selected_course_code = course_options[selected_course_label]
    
    selected_course_data = courses_df[courses_df['code'] == selected_course_code].iloc[0]
    
    # اختيار معايير المحاضرة
    c1, c2, c3 = st.columns(3)
    with c1:
        session_date = st.date_input("تاريخ المحاضرة / الاستوديو:", datetime.date.today())
    with c2:
        session_type = st.selectbox("نوع المحاضرة وعدد ساعاتها:", [
            "استوديو تصميم معماري (4 ساعات)",
            "محاضرة نظرية (ساعتان)",
            "سمنار / حلقة نقاشية (3 ساعات)"
        ])
        hours_per_session = 4.0 if "4" in session_type else (3.0 if "3" in session_type else 2.0)
    with c3:
        attendance_mode = st.radio("آلية إدخال الحضور:", ("📱 تسجيل متزامن آني (Dynamic QR)", "📝 تسجيل يدوي / لا متزامن (أوفلاين)"), horizontal=True)
        
    st.markdown("---")
    
    # جلب طلبة هذا المقرر
    conn = get_db_connection()
    students_in_course = pd.read_sql_query("""
    SELECT id, reg_num, name, total_hours, missed_hours 
    FROM students 
    WHERE course_code = ?
    """, conn, params=(selected_course_code,))
    conn.close()
    
    # أ. النمط المتزامن (Dynamic QR Code)
    if "متزامن" in attendance_mode:
        col_qr, col_roster = st.columns([1, 2])
        
        with col_qr:
            st.markdown("#### 📲 كود الحضور التفاعلي بالقاعة")
            st.caption("يُعرض هذا الرمز على شاشة العرض (Projector) في استوديو العمارة ليقوم الطلبة بمسحه بهواتفهم.")
            
            # توليد كود QR آمن
            token = f"UOT-ARCH-{selected_course_code}-{session_date}-{random.randint(1000, 9999)}"
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(token)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#78350f", back_color="white")
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), width=240)
            st.code(f"رمز الجلسة المؤقت: {token}", language="text")
            
            if st.button("📱 محاكاة مسح طالب للكود بهاتفه", use_container_width=True):
                random_std = students_in_course.sample(1).iloc[0]
                st.success(f"✅ تم تأكيد حضور الطالب: [{random_std['name']}] عبر الهاتف بنجاح!")
                
        with col_roster:
            st.markdown("#### 📋 قائمة النداء المباشر في القاعة")
            st.caption("يمكن للأستاذ تعديل حالة أي طالب مباشرة قبل اعتماد الجلسة:")
            
            # تجهيز حالة الطلبة
            if 'session_statuses' not in st.session_state or st.session_state.get('last_course') != selected_course_code:
                st.session_state.session_statuses = {s['id']: 'حاضر' for _, s in students_in_course.iterrows()}
                st.session_state.last_course = selected_course_code
                
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("✓ تحضير الكل كحاضرين", use_container_width=True):
                    st.session_state.session_statuses = {s['id']: 'حاضر' for _, s in students_in_course.iterrows()}
                    st.rerun()
            with col_b2:
                if st.button("إعادة ضبط القائمة", use_container_width=True):
                    st.session_state.session_statuses = {s['id']: 'غائب' for _, s in students_in_course.iterrows()}
                    st.rerun()
                    
            status_choices = ["حاضر", "غائب", "متأخر", "مجاز بعذر"]
            for _, std in students_in_course.iterrows():
                std_id = std['id']
                current_val = st.session_state.session_statuses.get(std_id, "حاضر")
                idx = status_choices.index(current_val) if current_val in status_choices else 0
                
                c_name, c_stat = st.columns([2, 1.5])
                with c_name:
                    st.markdown(f"**{std['name']}**  \n<span style='font-size:11px; color:#64748b;'>{std['reg_num']} | غيابات سابقة: {std['missed_hours']} س</span>", unsafe_allow_html=True)
                with c_stat:
                    new_stat = st.selectbox(
                        f"الحالة لـ {std['id']}", 
                        status_choices, 
                        index=idx, 
                        key=f"status_{std_id}",
                        label_visibility="collapsed"
                    )
                    st.session_state.session_statuses[std_id] = new_stat
                    
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 تثبيت واعتماد حضور جلسة اليوم", type="primary", use_container_width=True):
                conn = get_db_connection()
                cur = conn.cursor()
                for _, std in students_in_course.iterrows():
                    stat = st.session_state.session_statuses.get(std['id'], "حاضر")
                    missed = hours_per_session if stat == "غائب" else 0.0
                    
                    cur.execute("""
                    INSERT INTO attendance_logs (session_date, course_code, student_id, status, hours_missed, session_mode)
                    VALUES (?, ?, ?, ?, ?, 'SYNC')
                    """, (str(session_date), selected_course_code, std['id'], stat, missed))
                    
                    if missed > 0:
                        cur.execute("""
                        UPDATE students SET missed_hours = missed_hours + ? WHERE id = ?
                        """, (missed, std['id']))
                        
                conn.commit()
                conn.close()
                st.success("🎉 تم تثبيت حضور جلسة اليوم بنجاح وتحديث كشوفات الغياب المركزية لدى الإدارة!")
                
    # ب. النمط اللامتزامن / إدخال يدوي (Async / Offline)
    else:
        st.markdown("#### 📝 إدخال الحضور بأثر رجعي أو بدون اتصال")
        st.caption("استخدم هذا الخيار لإدخال غيابات التواريخ السابقة أو عند انقطاع شبكة الإنترنت داخل القاعة.")
        
        async_records = {}
        for _, std in students_in_course.iterrows():
            col_s1, col_s2, col_s3 = st.columns([2, 1.5, 2])
            with col_s1:
                st.write(f"**{std['name']}** ({std['reg_num']})")
            with col_s2:
                status = st.selectbox(f"حالة {std['id']}", ["حاضر", "غائب", "متأخر", "مجاز بعذر"], key=f"async_{std['id']}", label_visibility="collapsed")
                async_records[std['id']] = status
            with col_s3:
                notes = st.text_input(f"عذر {std['id']}", placeholder="ملاحظات العذر إن وجد", key=f"note_{std['id']}", label_visibility="collapsed")
                
        if st.button("💾 حفظ السجل اللامتزامن الآن", type="primary", use_container_width=True):
            conn = get_db_connection()
            cur = conn.cursor()
            for std_id, stat in async_records.items():
                missed = hours_per_session if stat == "غائب" else 0.0
                cur.execute("""
                INSERT INTO attendance_logs (session_date, course_code, student_id, status, hours_missed, session_mode)
                VALUES (?, ?, ?, ?, ?, 'ASYNC')
                """, (str(session_date), selected_course_code, std_id, stat, missed))
                
                if missed > 0:
                    cur.execute("UPDATE students SET missed_hours = missed_hours + ? WHERE id = ?", (missed, std_id))
                    
            conn.commit()
            conn.close()
            st.success("✅ تم حفظ السجل اللامتزامن بنجاح وتم ترحيل التعديلات لقاعدة البيانات!")
