# 🏛️ منظومة حضور وغياب طلبة الدراسات العليا - كلية هندسة العمارة | الجامعة التكنولوجية
### Postgraduate Attendance Management System - Department of Architecture Engineering (UOT)

منصة متكاملة ومصممة خصيصاً لمتابعة حضور وغياب طلبة الدراسات العليا (ماجستير ودكتوراه) في كلية هندسة العمارة بالجامعة التكنولوجية في بغداد، متوافقة مع الضوابط والتعليمات الامتحانية لوزارة التعليم العالي العراقية.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 الميزات الرئيسية

1. **تغطية شاملة لفروع الدراسات العليا الأربعة:**
   - 📐 **ماجستير تكنولوجيا العمارة** (Architectural Technology)
   - 🏛️ **ماجستير التصميم المعماري** (Architectural Design)
   - 🏙️ **ماجستير التصميم الحضري** (Urban Design)
   - 🎖️ **دكتوراه هندسة العمارة** (Ph.D. Architecture)

2. **نظام صلاحيات متعدد الأدوار (RBAC):**
   - **لوحة إدارة الدراسات العليا (Admin):** مؤشرات لحظية (KPIs)، متابعة نسب الغياب، تنبيهات الإنذار والحرمان، وتصدير كشوفات Excel بضغطة زر.
   - **بوابة أستاذ المادة (Instructor Portal):** استعراض المقررات واستوديوهات العمارة وإدخال الحضور.

3. **آليات التحضير:**
   - **آني متزامن (Synchronous):** توليد رمز QR ديناميكي حي يتجدد دورياً لمنع التزوير مع قائمة نداء فورية.
   - **يدوي / لا متزامن (Asynchronous & Offline):** إدخال الغيابات بأثر رجعي أو في حالات انقطاع الإنترنت داخل استوديوهات التصميم.

4. **احتساب نسب الحرمان التلقائي:**
   - إنذار أولي عند بلوغ **5%**.
   - إنذار نهائي عند بلوغ **7%**.
   - حرمان رسمي من الامتحان عند بلوغ **10%**.

---

## 🚀 طريقة النشر السريع على GitHub و Streamlit Cloud

### الخطوة 1: إنشاء مستودع جديد على GitHub
افتح الرابط التالي لإنشاء المستودع مباشرة:
👉 **[إنشاء مستودع جديد على GitHub](https://github.com/new?name=uot-arch-attendance&description=Postgraduate+Attendance+Platform+-+Architecture+Engineering+UOT)**

### الخطوة 2: رفع الكود من جهازك إلى GitHub
افتح موجه الأوامر (Terminal) ونفّذ التالي (استبدل `YOUR_USERNAME` باسم حسابك على GitHub):

```bash
cd /Users/ahmedlouay/.gemini/antigravity/scratch/uot_arch_attendance
git remote add origin https://github.com/YOUR_USERNAME/uot-arch-attendance.git
git branch -M main
git push -u origin main
```

### الخطوة 3: النشر المجاني على Streamlit Community Cloud
1. ادخل إلى: **[share.streamlit.io/deploy](https://share.streamlit.io/deploy)**
2. اختر المستودع: `YOUR_USERNAME/uot-arch-attendance`
3. اختر الفرع: `main`
4. حدد الملف الرئيسي: `app.py`
5. اضغط **Deploy!**

خلال دقائق، سيكون تطبيقك متاحاً برابط عام مجاني:
🌐 `https://YOUR_USERNAME-uot-arch-attendance.streamlit.app`

---

## 💻 التشغيل المحلي (Local Development)

لتشغيل المنظومة محلياً على جهازك:

```bash
# 1. تثبيت المكتبات المطلوبة
pip install -r requirements.txt

# 2. تشغيل التطبيق
streamlit run app.py
```

سيفتح التطبيق تلقائياً على المتصفح على العنوان: `http://localhost:8501`.
