import io
import csv
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from telegram import InputFile
import sqlite3
import random
from datetime import datetime, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

BOT_TOKEN = "8626691591:AAFGvecOFFTzD6TQejxaK0dZTH8SLjNDAsg"
DEFAULT_OWNER_ID = 6373995909 
DB_FILE = "bot_pro.db"

# --- مراحل المحادثة (Conversation States) ---
PROMO_CODE, PROMO_PRICE, PROMO_LIMIT = range(3)
PLAN_UID, PLAN_DAY, PLAN_CONTENT = range(3, 6)
SENDTO_UID, SENDTO_MSG = range(6, 8)
BROADCAST_MSG = range(8, 9)
ADD_ADMIN_STEP = range(9, 10)
REMOVE_ADMIN_STEP = range(10, 11)
SET_OWNER_STEP = range(11, 12)
SET_CONTACT_STEP = range(12, 13)
ADD_BTN_NAME, ADD_BTN_REPLY = range(13, 15)
MISTAKE_TITLE, MISTAKE_DESC = range(15, 17)
SUB_UID, SUB_DAYS = range(17, 19)
REMOVE_USER_STEP = range(19, 20)
ADD_VIP_UID, ADD_VIP_DAYS = range(20, 22)
VIP_AGE, VIP_HEIGHT, VIP_WEIGHT, VIP_GENDER, VIP_GOAL, VIP_TARGET_WEIGHT = range(22, 28)
NOTE_UID, NOTE_CONTENT = range(28, 30)
EXPORT_TARGET, EXPORT_FORMAT, EXPORT_INCLUDE_NOTES = range(30, 33)
WEEKLY_WEIGHT, WEEKLY_MEASUREMENTS = range(33, 35)
SCHED_TARGET, SCHED_MSG, SCHED_TIME = range(35, 38)
INJURY_PART, INJURY_DESC = range(38, 40)
EDIT_MEMBER_WEIGHT = range(40, 41)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS promo (code TEXT PRIMARY KEY, price TEXT, limit_count INTEGER, used_count INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS admins (user_id TEXT PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS owners (user_id TEXT PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, name TEXT, sub_end_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS requests (user_id TEXT PRIMARY KEY, deadline TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS user_plans (user_id TEXT, day TEXT, content TEXT, PRIMARY KEY(user_id, day))')
    c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS custom_buttons (btn_key TEXT PRIMARY KEY, btn_name TEXT, btn_reply TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS common_mistakes (mistake_key TEXT PRIMARY KEY, title TEXT, description TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS daily_reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS admin_client_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, note TEXT, date_added TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS scheduled_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, target_id TEXT, message TEXT, send_time TEXT)')

    c.execute('SELECT COUNT(*) FROM daily_reminders')
    if c.fetchone()[0] == 0:
        default_reminders = [
            "📖 قال الله تعالى: ﴿وَأَنْ لَيْسَ لِلإِنسَانِ إِلا مَا سَعَى ۝ وَأَنَّ سَعْيَهُ سَوْفَ يُرَى﴾\nتوكل على الله واجعل سعيك اليوم خطوة نحو هدفك يا بطل! 💪",
            "⚡ قال النبي صلى الله عليه وسلم: «المؤمن القوي خير وأحب إلى الله من المؤمن الضعيف وفي كل خير».\nحافظ على لياقتك وقوتك البدنية والروحية! 🏋️‍♂️",
            "💡 نصيحة اليوم: الالتزام الصغير المتكرر يصنع نتائج عظيمة. لا تفوت تمريرتك مهما كانت الظروف صعبة!",
            "🔥 تذكر دائماً: الألم الذي تشعر به اليوم هو القوة التي ستشعر بها غداً. استمر ولا تتراجع!",
            "📖 قال الله تعالى: ﴿وَاصْبِرْ فَإِنَّ اللَّهَ لا يُضِيعُ أُجْرَ الْمُحْسِنِينَ﴾\nاصبر على تمرينك ودايتك، والنتيجة قادمة لا محالة بإذن الله."
        ]
        c.executemany('INSERT INTO daily_reminders (content) VALUES (?)', [(r,) for r in default_reminders])

    conn.commit()
    conn.close()

init_db()

def is_owner(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM owners")
    owner = c.fetchone()
    conn.close()
    current_owner = owner[0] if owner else str(DEFAULT_OWNER_ID)
    return str(user_id) == str(current_owner)

def is_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id = ?", (str(user_id),))
    res = c.fetchone()
    conn.close()
    return res is not None or is_owner(user_id)

def is_subscribed(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT sub_end_date FROM users WHERE user_id = ?", (str(user_id),))
    row = c.fetchone()
    conn.close()
    
    if row and row[0]:
        try:
            sub_date = datetime.strptime(row[0], "%Y-%m-%d")
            if sub_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                return True
        except:
            pass
    return False

def get_contact_link():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'coach_contact'")
    res = c.fetchone()
    conn.close()
    if res:
        val = res[0]
        if val.startswith("http://") or val.startswith("https://"):
            return val
        else:
            clean_user = val.replace("@", "").strip()
            return f"https://t.me/{clean_user}"
    return "https://t.me/your_username"

def get_contact_display_name():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'coach_contact'")
    res = c.fetchone()
    conn.close()
    if res:
        val = res[0].replace("@", "").strip()
        return f"📩 تواصل مع الكوتش (@{val})"
    return "📩 تواصل مع الكوتش"

def calculate_macros(age, height, weight, gender, goal, target_weight):
    if gender.lower() in ['male', 'ولد', 'ذكر']:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    if goal.lower() in ['bulking', 'تضخيم']:
        calories = int(bmr * 1.35) + 400
        protein = int(weight * 2.0)
        fats = int(weight * 0.9)
        remaining_calories = calories - ((protein * 4) + (fats * 9))
        carbs = max(int(remaining_calories / 4), 50)
        advice = f"الهدف: تضخيم للوصول إلى {target_weight} كجم. التركيز على زيادة الأوزان تدريجياً وفائض سعرات نظيف."
    else:
        calories = int(bmr * 1.2) - 400
        protein = int(weight * 2.2)
        fats = int(weight * 0.7)
        remaining_calories = calories - ((protein * 4) + (fats * 9))
        carbs = max(int(remaining_calories / 4), 50)
        advice = f"الهدف: تنشيف للوصول إلى {target_weight} كجم. التزام بعجز السعرات والكارديو المنتظم."

    return {
        "calories": calories, "protein": protein, "carbs": carbs, "fats": fats, "advice": advice
    }

async def check_subscriptions_job(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, sub_end_date FROM users WHERE sub_end_date IS NOT NULL")
    users = c.fetchall()
    conn.close()

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for user in users:
        uid, end_date_str = user
        if not end_date_str:
            continue
        try:
            sub_end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            delta = (sub_end_date - today).days
            
            if delta == 7:
                await context.bot.send_message(chat_id=int(uid), text="⏳ **تنبيه بقرب انتهاء الاشتراك!**\n\nعزيزي البطل، فاضل **7 أيام** على انتهاء اشتراكك الرياضي. استعد لتجديد الاشتراك واصل إنجازاتك!", parse_mode="Markdown")
            elif delta == 3:
                await context.bot.send_message(chat_id=int(uid), text="⚠️ **انتبه، الوقت يمر بسرعة!**\n\nفاضل **3 أيام فقط** ويخلص اشتراكك. تواصل مع الكوتش لتجديد الاشتراك وضمان استمرار جدولك بدون توقف.", parse_mode="Markdown")
            elif delta == 1:
                await context.bot.send_message(chat_id=int(uid), text="🚨 **تحذير هامة - خلال 24 ساعة!**\n\nاشتراكك بينتهي بكرة تماماً! بادر بالتجديد الآن عشان تحافظ على تقدمك ونظامك التدريبي مع الكوتش.", parse_mode="Markdown")
            elif delta == 0:
                await context.bot.send_message(chat_id=int(uid), text="❌ **عذراً، لقد انتهى اشتراكك الرياضي اليوم!**\n\nللاستمرار معنا وجدولة أنظمتك القادمة، يرجى التواصل مع الكوتش أو تجديد الاشتراك فوراً.", parse_mode="Markdown")
        except Exception:
            pass

async def daily_motivation_job(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    c.execute("SELECT content FROM daily_reminders")
    reminders = c.fetchall()
    conn.close()

    if not reminders or not users:
        return

    selected_reminder = random.choice(reminders)[0]

    for user in users:
        uid = user[0]
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"☀️ **إشراقة يومية وتحفيز رياضي:**\n\n{selected_reminder}",
                parse_mode="Markdown"
            )
        except:
            pass

# --- نظام تسجيل الإصابات والألام البدنية ---
async def injury_report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_subscribed(query.from_user.id):
        await query.edit_message_text("⚠️ عذراً، هذه الميزة مخصصة للمشتركين النشطين فقط.")
        return ConversationHandler.END
        
    await query.edit_message_text(
        "🚨 **نظام الإبلاغ عن الإصابات والآلام:**\n\n"
        "سلامتك أولاً يا بطل! من فضلك، حدد واكتب **منطقة الإصابة أو مكان الألم بالتحديد** (مثلاً: الكتف الأيمن، أسفل الظهر، الركبة):",
        parse_mode="Markdown"
    )
    return INJURY_PART

async def injury_get_part(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["injury_part"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 ممتاز. الآن اشرح لنا تفاصيل الإصابة أو الألم (هل هي إصابة قديمة، متى تبدأ تشعر بها، وهل هي شديدة أم مجرد شك/إجهاد بسيط؟):",
        parse_mode="Markdown"
    )
    return INJURY_DESC

async def injury_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    injury_desc = update.message.text.strip()
    injury_part = context.user_data.get("injury_part")
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    note_content = f"🚨 [إصابة/ألم مسجل] المنطقة: {injury_part} | التفاصيل: {injury_desc}"
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO admin_client_notes (user_id, note, date_added) VALUES (?, ?, ?)", (str(user_id), note_content, current_date))
    conn.commit()
    
    c = conn.cursor()
    c.execute("SELECT user_id FROM owners")
    owner_row = c.fetchone()
    conn.close()
    admin_target = owner_row[0] if owner_row else str(DEFAULT_OWNER_ID)
    
    await update.message.reply_text(
        "✅ **تم إرسال تقرير الإصابة/الألم إلى الكوتش بنجاح!**\n"
        "تم حفظ البلاغ في ملفك وسيقوم الكوتش بمراجعته وتعديل التمارين المناسبة لك فوراً حفاظاً على سلامتك.",
        parse_mode="Markdown"
    )
    
    try:
        admin_alert = (
            f"🚨 **تنبيه إصابة أو ألم جديد من مشترك!**\n\n"
            f"👤 اسم المتدرب: {user_name}\n"
            f"🆔 الآيدي: `{user_id}`\n"
            f"🎯 المنطقة المتضررة: **{injury_part}**\n"
            f"📋 التفاصيل: {injury_desc}\n"
            f"📅 التاريخ: `{current_date}`"
        )
        await context.bot.send_message(chat_id=int(admin_target), text=admin_alert, parse_mode="Markdown")
    except:
        pass
    return ConversationHandler.END

# --- سجل ملاحظات الأدمن التراكمية ---
async def admin_note_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("📋 أرسل الآن **آيدي (ID) المتدرب** المراد إضافة ملاحظة أو سجل جديد لملفه:", parse_mode="Markdown")
    return NOTE_UID

async def admin_note_get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["note_target_uid"] = update.message.text.strip()
    await update.message.reply_text("✍️ أكتب **الملاحظة أو التحديث الجديد** (سيتم إضافته وسجله القديم محفوظ ولن يتم مسحه):", parse_mode="Markdown")
    return NOTE_CONTENT

async def admin_note_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("note_target_uid")
    note_text = update.message.text.strip()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO admin_client_notes (user_id, note, date_added) VALUES (?, ?, ?)", (uid, note_text, current_date))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ **تمت إضافة الملاحظة وسجل المتابعة بنجاح!**\n👤 المشترك: `{uid}`\n📅 التاريخ: `{current_date}`", parse_mode="Markdown")
    
    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text=f"🔔 **تحديث جديد في سجل المتابعة الخاص بك من الكوتش:**\n\n📌 {note_text}\n📅 التاريخ: `{current_date}`",
            parse_mode="Markdown"
        )
    except:
        pass
    return ConversationHandler.END

# --- إحصائيات المشتركين ونظام الإدارة مع أزرار التعديل والحذف المباشر ---
async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute("SELECT user_id, name, sub_end_date FROM users")
    all_users = c.fetchall()

    c.execute("SELECT COUNT(*), SUM(used_count) FROM promo")
    promo_data = c.fetchone()
    total_promos = promo_data[0] if promo_data[0] else 0
    total_uses = promo_data[1] if promo_data[1] else 0
    conn.close()

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    active_count = 0
    expired_count = 0

    stats_report = (
        f"📊 **لوحة إحصائيات المشتركين وإدارة البوت:**\n\n"
        f"👥 إجمالي المسجلين: **{total_users}**\n"
        f"🎟 أكواد الخصم النشطة: **{total_promos}** (إجمالي الاستخدام: {total_uses})\n\n"
        f"📋 **قائمة المشتركين والتحكم السريع:**\n"
    )

    keyboard = []
    for idx, (uid, name, end_date_str) in enumerate(all_users, 1):
        status_label = "❌ منتهي"
        if end_date_str:
            try:
                sub_end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                if sub_end_date >= today:
                    active_count += 1
                    status_label = "✅ ساري"
                else:
                    expired_count += 1
            except:
                expired_count += 1
        else:
            expired_count += 1

        keyboard.append([
            InlineKeyboardButton(f"👤 {name or 'متدرب'} ({status_label})", callback_data=f"noop_{uid}")
        ])
        keyboard.append([
            InlineKeyboardButton("✏️ تعديل بياناته", callback_data=f"adm_edit_{uid}"),
            InlineKeyboardButton("❌ حذف المشترك", callback_data=f"adm_del_{uid}")
        ])

    keyboard.append([InlineKeyboardButton("🔄 تحديث الإحصائيات", callback_data="btn_admin_stats")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home")])

    full_text = stats_report + f"🟢 ساري: {active_count} | 🔴 منتهي: {expired_count}"
    if len(full_text) > 4000:
        await query.message.reply_text(full_text[:4000], parse_mode="Markdown")
    else:
        await query.edit_message_text(full_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- تصدير تقارير البيانات (Excel أو PDF) ---
async def export_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("📊 ملف Excel (.xlsx)", callback_data="fmt_excel")],
        [InlineKeyboardButton("📄 ملف PDF (.pdf)", callback_data="fmt_pdf")]
    ]
    await query.edit_message_text("📤 **نظام تصدير وتقارير البيانات:**\n\nاختر صيغة الملف المطلوبة:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return EXPORT_FORMAT

async def export_get_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["exp_format"] = query.data
    
    keyboard = [
        [InlineKeyboardButton("👤 مشترك معين (بالآيدي)", callback_data="exp_single")],
        [InlineKeyboardButton("👥 جميع المشتركين", callback_data="exp_all")]
    ]
    await query.edit_message_text("🎯 حدد نطاق التصدير:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return EXPORT_TARGET

async def export_get_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data["exp_target"] = choice
    
    if choice == "exp_single":
        await query.edit_message_text("👤 أرسل الآن **آيدي (ID) المشترك** لاستخراج تقريره:", parse_mode="Markdown")
        return EXPORT_INCLUDE_NOTES
    else:
        keyboard = [
            [InlineKeyboardButton("📊 البيانات الأساسية فقط", callback_data="notes_no")],
            [InlineKeyboardButton("📋 البيانات الأساسية + سجل الملاحظات", callback_data="notes_yes")]
        ]
        await query.edit_message_text("📁 هل ترغب في تضمين سجل الملاحظات التراكمية في التقرير؟", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return EXPORT_INCLUDE_NOTES

async def export_get_uid_or_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.user_data.get("exp_target")
    if target == "exp_single" and "exp_uid" not in context.user_data:
        context.user_data["exp_uid"] = update.message.text.strip()
        keyboard = [
            [InlineKeyboardButton("📊 البيانات الأساسية فقط", callback_data="notes_no")],
            [InlineKeyboardButton("📋 البيانات الأساسية + سجل الملاحظات", callback_data="notes_yes")]
        ]
        await update.message.reply_text("📁 هل ترغب في تضمين سجل الملاحظات التراكمية لهذا المشترك؟", reply_markup=InlineKeyboardMarkup(keyboard))
        return EXPORT_INCLUDE_NOTES

async def export_generate_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    include_notes = (query.data == "notes_yes")
    target = context.user_data.get("exp_target")
    single_uid = context.user_data.get("exp_uid")
    file_format = context.user_data.get("exp_format")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if target == "exp_single":
        c.execute("SELECT user_id, name, sub_end_date FROM users WHERE user_id = ?", (single_uid,))
    else:
        c.execute("SELECT user_id, name, sub_end_date FROM users")
    users_rows = c.fetchall()
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if file_format == "fmt_excel":
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Gym_Report"
        
        headers = ["User ID", "Name", "Subscription End Date", "Status"]
        if include_notes:
            headers.append("Admin Notes & Progress Log")
        ws.append(headers)
        
        for row in users_rows:
            uid, name, end_date_str = row
            status = "Expired"
            if end_date_str:
                try:
                    if datetime.strptime(end_date_str, "%Y-%m-%d") >= today:
                        status = "Active"
                except:
                    pass
            
            row_data = [str(uid), str(name or "N/A"), str(end_date_str or "N/A"), status]
            if include_notes:
                c.execute("SELECT note, date_added FROM admin_client_notes WHERE user_id = ? ORDER BY id DESC", (str(uid),))
                notes_rows = c.fetchall()
                notes_str = " | ".join([f"[{d}] {n}" for n, d in notes_rows]) if notes_rows else "No Notes"
                row_data.append(notes_str)
            ws.append(row_data)
            
        conn.close()
        excel_io = io.BytesIO()
        wb.save(excel_io)
        excel_io.seek(0)
        
        filename = f"Gym_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        await query.message.reply_document(
            document=InputFile(excel_io, filename=filename),
            caption="✅ **تم تصدير تقرير الـ Excel بنجاح!**",
            parse_mode="Markdown"
        )
    else:
        # توليد ملف PDF
        pdf_io = io.BytesIO()
        c_pdf = canvas.Canvas(pdf_io, pagesize=letter)
        width, height = letter
        
        c_pdf.setFont("Helvetica-Bold", 16)
        c_pdf.drawString(50, height - 50, "Gym Management System - Report")
        c_pdf.setFont("Helvetica", 10)
        c_pdf.drawString(50, height - 70, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        y_offset = height - 100
        for row in users_rows:
            uid, name, end_date_str = row
            status = "Expired"
            if end_date_str:
                try:
                    if datetime.strptime(end_date_str, "%Y-%m-%d") >= today:
                        status = "Active"
                except:
                    pass
            
            if y_offset < 100:
                c_pdf.showPage()
                y_offset = height - 50
                
            c_pdf.setFont("Helvetica-Bold", 10)
            c_pdf.drawString(50, y_offset, f"ID: {uid} | Name: {name or 'N/A'} | Status: {status}")
            y_offset -= 15
            c_pdf.setFont("Helvetica", 9)
            c_pdf.drawString(50, y_offset, f"Sub End Date: {end_date_str or 'N/A'}")
            y_offset -= 15
            
            if include_notes:
                c.execute("SELECT note, date_added FROM admin_client_notes WHERE user_id = ? ORDER BY id DESC", (str(uid),))
                notes_rows = c.fetchall()
                for n, d in notes_rows:
                    if y_offset < 50:
                        c_pdf.showPage()
                        y_offset = height - 50
                    c_pdf.drawString(70, y_offset, f"[{d}] {n}")
                    y_offset -= 12
            y_offset -= 10
            
        conn.close()
        c_pdf.save()
        pdf_io.seek(0)
        
        filename = f"Gym_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        await query.message.reply_document(
            document=InputFile(pdf_io, filename=filename),
            caption="✅ **تم تصدير تقرير الـ PDF بنجاح!**",
            parse_mode="Markdown"
        )
        
    return ConversationHandler.END

# --- التحديث الأسبوعي للمتدرب ---
async def weekly_update_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_subscribed(query.from_user.id):
        await query.edit_message_text("⚠️ عذراً، هذه الميزة مخصصة للمشتركين النشطين فقط.")
        return ConversationHandler.END
        
    await query.edit_message_text(
        "🔄 **مرحباً بك في جلسة التحديث الأسبوعي!**\n\n"
        "من فضلك، أرسل **وزنك الحالي** هذا الأسبوع بالأرقام (مثلاً: 75.5):",
        parse_mode="Markdown"
    )
    return WEEKLY_WEIGHT

async def weekly_get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text.strip())
        context.user_data["weekly_weight"] = weight
        await update.message.reply_text(
            "📏 ممتاز يا وحش!\n"
            "الآن أرسل **قياساتك الجديدة أو ملاحظاتك عن أداء الأسبوع** (محيط الخصر، الملاحظات، إلخ):",
            parse_mode="Markdown"
        )
        return WEEKLY_MEASUREMENTS
    except ValueError:
        await update.message.reply_text("⚠️ من فضلك أدخل رقماً صحيحاً للوزن (مثال: 75 أو 74.5):")
        return WEEKLY_WEIGHT

async def weekly_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    measurements_text = update.message.text.strip()
    weight = context.user_data.get("weekly_weight")
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    note_content = f"📊 [تحديث أسبوعي] الوزن الحالي: {weight} كجم | القياسات والملاحظات: {measurements_text}"
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO admin_client_notes (user_id, note, date_added) VALUES (?, ?, ?)", (str(user_id), note_content, current_date))
    conn.commit()
    
    c = conn.cursor()
    c.execute("SELECT user_id FROM owners")
    owner_row = c.fetchone()
    conn.close()
    admin_target = owner_row[0] if owner_row else str(DEFAULT_OWNER_ID)
    
    await update.message.reply_text(
        "✅ **تم إرسال تحديثك الأسبوعي بنجاح إلى الكوتش!**\n"
        f"⚖️ الوزن المسجل: `{weight} كجم`",
        parse_mode="Markdown"
    )
    
    try:
        admin_report = (
            f"📈 **استلام تحديث أسبوعي جديد من مشترك:**\n\n"
            f"👤 اسم المتدرب: {user_name}\n"
            f"🆔 الآيدي: `{user_id}`\n"
            f"⚖️ الوزن الجديد: **{weight} كجم**\n"
            f"📏 الملاحظات: {measurements_text}\n"
            f"📅 التاريخ: `{current_date}`"
        )
        await context.bot.send_message(chat_id=int(admin_target), text=admin_report, parse_mode="Markdown")
    except:
        pass
    return ConversationHandler.END

# --- نظام الرسائل المجدولة الآلية ---
async def schedule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("📢 إرسال لجميع المشتركين", callback_data="sched_all")],
        [InlineKeyboardButton("👤 لمشترك معين (بالآيدي)", callback_data="sched_single")]
    ]
    await query.edit_message_text("⏰ **نظام الرسائل المجدولة:**\n\nاختر الفئة المستهدفة لهذه الرسالة:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return SCHED_TARGET

async def schedule_get_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data["sched_target"] = choice
    
    if choice == "sched_single":
        await query.edit_message_text("👤 أرسل الآن **آيدي (ID) المشترك** المراد جدولة الرسالة له:", parse_mode="Markdown")
    else:
        await query.edit_message_text("✍️ أرسل الآن **نص الرسالة** المراد جدولتها وإرسالها للجميع:", parse_mode="Markdown")
    return SCHED_MSG

async def schedule_get_msg_or_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.user_data.get("sched_target")
    if target == "sched_single" and "sched_uid" not in context.user_data:
        context.user_data["sched_uid"] = update.message.text.strip()
        await update.message.reply_text("✍️ ممتاز. الآن أرسل **نص الرسالة** المراد جدولتها لهذا المشترك:", parse_mode="Markdown")
        return SCHED_MSG
    else:
        context.user_data["sched_msg"] = update.message.text.strip()
        await update.message.reply_text(
            "⏳ أدخل **عدد الدقائق من الآن** لتنفيذ وإرسال هذه الرسالة (مثلاً: اكتب `60` لإرسالها بعد ساعة):",
            parse_mode="Markdown"
        )
        return SCHED_TIME

async def schedule_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        delay_minutes = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ يرجى إدخال رقم صحيح يمثل عدد الدقائق:")
        return SCHED_TIME
        
    target_type = context.user_data.get("sched_target")
    single_uid = context.user_data.get("sched_uid") if target_type == "sched_single" else "ALL"
    msg_text = context.user_data.get("sched_msg")
    
    context.job_queue.run_once(
        send_scheduled_message_job,
        when=delay_minutes * 60,
        data={"target": single_uid, "message": msg_text}
    )
    
    await update.message.reply_text(
        f"✅ **تمت جدولتها بنجاح!**\n"
        f"⏱️ ستُرسل الرسالة بعد **{delay_minutes} دقيقة**.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def send_scheduled_message_job(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    target = job_data["target"]
    msg = job_data["message"]
    
    conn = sqlite3.connect(DB_FILE)
    if target == "ALL":
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        rows = c.fetchall()
        conn.close()
        for r in rows:
            try:
                await context.bot.send_message(chat_id=int(r[0]), text=f"⏰ **رسالة مجدولة من الإدارة:**\n\n{msg}", parse_mode="Markdown")
            except:
                pass
    else:
        conn.close()
        try:
            await context.bot.send_message(chat_id=int(target), text=f"⏰ **رسالة مجدولة من الإدارة:**\n\n{msg}", parse_mode="Markdown")
        except:
            pass

# --- باقي الوظائف (VIP, Plans, Promos, إلخ) ---
async def add_vip_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("➕ أرسل الآن **آيدي (ID) المتدرب** المراد إضافته وتفعيله:", parse_mode="Markdown")
    return ADD_VIP_UID

async def add_vip_get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_vip_uid"] = update.message.text.strip()
    await update.message.reply_text("📅 أرسل **عدد أيام الاشتراك** للمتدرب:", parse_mode="Markdown")
    return ADD_VIP_DAYS

async def add_vip_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("add_vip_uid")
    try:
        days_count = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ يرجى إدخال رقم صحيح:")
        return ADD_VIP_DAYS
    
    end_date = (datetime.now() + timedelta(days=days_count)).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO users (user_id, name, sub_end_date) VALUES (?, ?, ?)", (uid, "متدرب VIP", end_date))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ **تمت إضافة وتفعيل المشترك بنجاح!**\n👤 الآيدي: `{uid}`", parse_mode="Markdown")
    try:
        keyboard = [[InlineKeyboardButton("📝 ابدأ تسجيل بياناتك البدنية", callback_data="start_vip_reg")]]
        await context.bot.send_message(chat_id=int(uid), text=f"🎉 **تم تفعيل اشتراكك حتى:** `{end_date}`", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except:
        pass
    return ConversationHandler.END

async def vip_reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("هيا بنا نبدأ! من فضلك أدخل **عمرك** بالأرقام:", parse_mode="Markdown")
    return VIP_AGE

async def vip_get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["vip_age"] = int(update.message.text.strip())
        await update.message.reply_text("ما هو **طولك** بالسنتيمتر:", parse_mode="Markdown")
        return VIP_HEIGHT
    except ValueError:
        await update.message.reply_text("⚠️ أدخل رقم صحيح:")
        return VIP_AGE

async def vip_get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["vip_height"] = float(update.message.text.strip())
        await update.message.reply_text("ما هو **وزنك الحالي** بالكيلوجرام:", parse_mode="Markdown")
        return VIP_WEIGHT
    except ValueError:
        await update.message.reply_text("⚠️ أدخل رقم صحيح:")
        return VIP_HEIGHT

async def vip_get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["vip_weight"] = float(update.message.text.strip())
        markup = ReplyKeyboardMarkup([["ولد", "بنت"]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("حدد النوع:", reply_markup=markup)
        return VIP_GENDER
    except ValueError:
        await update.message.reply_text("⚠️ أدخل وزناً صحيحاً:")
        return VIP_WEIGHT

async def vip_get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text.strip()
    context.user_data["vip_gender"] = gender
    markup = ReplyKeyboardMarkup([["تضخيم", "تنشيف"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("ما هو هدفك الحالي؟", reply_markup=markup)
    return VIP_GOAL

async def vip_get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["vip_goal"] = update.message.text.strip()
    await update.message.reply_text("ما هو **الوزن المستهدف** بالكيلوجرام؟", reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
    return VIP_TARGET_WEIGHT

async def vip_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_weight = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ أدخل رقماً صحيحاً:")
        return VIP_TARGET_WEIGHT
    
    chat_id = update.effective_user.id
    macros = calculate_macros(context.user_data["vip_age"], context.user_data["vip_height"], context.user_data["vip_weight"], context.user_data["vip_gender"], context.user_data["vip_goal"], target_weight)
    
    await update.message.reply_text(f"✅ تم تسجيل بياناتك بنجاح!\nالسعرات: {macros['calories']} kcal", parse_mode="Markdown")
    return ConversationHandler.END

async def service_feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("اكتب مقترحك أو فكرتك في رسالة واحدة للإدارة:", parse_mode="Markdown")
    return BROADCAST_MSG

async def service_feedback_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feedback_text = update.message.text
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM owners")
    owner_row = c.fetchone()
    conn.close()
    admin_target = owner_row[0] if owner_row else str(DEFAULT_OWNER_ID)
    try:
        await context.bot.send_message(chat_id=int(admin_target), text=f"💡 مقترح جديد:\n{feedback_text}", parse_mode="Markdown")
        await update.message.reply_text("✅ شكراً لك! تم إرسال مقترحك.")
    except:
        pass
    return ConversationHandler.END

async def remove_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("🗑 أرسل **آيدي المشترك** لحذفه:", parse_mode="Markdown")
    return REMOVE_USER_STEP

async def remove_user_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_uid = update.message.text.strip()
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM users WHERE user_id = ?", (target_uid,))
    conn.execute("DELETE FROM user_plans WHERE user_id = ?", (target_uid,))
    conn.execute("DELETE FROM admin_client_notes WHERE user_id = ?", (target_uid,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ تم حذف المشترك `{target_uid}` بنجاح.", parse_mode="Markdown")
    return ConversationHandler.END

async def sub_date_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("⏳ أرسل **آيدي المشترك** لتحديث مدة اشتراكه:", parse_mode="Markdown")
    return SUB_UID

async def sub_date_get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sub_uid"] = update.message.text.strip()
    await update.message.reply_text("📅 أرسل عدد الأيام الباقية للاشتراك:", parse_mode="Markdown")
    return SUB_DAYS

async def sub_date_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("sub_uid")
    days_count = int(update.message.text.strip())
    end_date = (datetime.now() + timedelta(days=days_count)).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE users SET sub_end_date = ? WHERE user_id = ?", (end_date, uid))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ تم تفعيل الاشتراك حتى: `{end_date}`", parse_mode="Markdown")
    return ConversationHandler.END

async def mistake_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("⚠️ أكتب عنوان الخطأ الشائع:", parse_mode="Markdown")
    return MISTAKE_TITLE

async def mistake_get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mistake_title"] = update.message.text.strip()
    await update.message.reply_text("📝 اكتب تفاصيل الخطأ الشائع:", parse_mode="Markdown")
    return MISTAKE_DESC

async def mistake_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO common_mistakes (mistake_key, title, description) VALUES (?, ?, ?)", 
                 (f"mistake_{int(datetime.now().timestamp())}", context.user_data.get("mistake_title"), update.message.text))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ تم إضافة الخطأ الشائع بنجاح.")
    return ConversationHandler.END

async def set_contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("🔗 أرسل رابط أو يوزر تواصل الكوتش:", parse_mode="Markdown")
    return SET_CONTACT_STEP

async def set_contact_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('coach_contact', ?)", (update.message.text.strip(),))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ تم تحديث رابط تواصل الكوتش بنجاح.")
    return ConversationHandler.END

async def add_btn_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("🏷 أكتب اسم الزرار الجديد:", parse_mode="Markdown")
    return ADD_BTN_NAME

async def add_btn_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_btn_name"] = update.message.text.strip()
    await update.message.reply_text("📝 أرسل الرد أو النص الخاص بهذا الزرار:", parse_mode="Markdown")
    return ADD_BTN_REPLY

async def add_btn_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO custom_buttons (btn_key, btn_name, btn_reply) VALUES (?, ?, ?)", 
                 (f"custom_{int(datetime.now().timestamp())}", context.user_data.get("new_btn_name"), update.message.text))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ تم إضافة الزرار بنجاح.")
    return ConversationHandler.END

async def promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("🎟 أرسل كود الخصم الجديد:", parse_mode="Markdown")
    return PROMO_CODE

async def promo_get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["p_code"] = update.message.text.strip()
    await update.message.reply_text("💵 أرسل السعر بعد الخصم:", parse_mode="Markdown")
    return PROMO_PRICE

async def promo_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["p_price"] = update.message.text.strip()
    await update.message.reply_text("👥 أرسل عدد المقاعد المتاحة:", parse_mode="Markdown")
    return PROMO_LIMIT

async def promo_get_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO promo VALUES (?, ?, ?, 0)", 
                 (context.user_data.get("p_code"), context.user_data.get("p_price"), int(update.message.text.strip())))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ تم إضافة كود الخصم بنجاح.")
    return ConversationHandler.END

async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("👤 أرسل آيدي المشترك لإضافة النظام له:", parse_mode="Markdown")
    return PLAN_UID

async def plan_get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["plan_uid"] = update.message.text.strip()
    days = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
    keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in days]
    await update.message.reply_text("📅 اختر اليوم:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return PLAN_DAY

async def plan_get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["plan_day"] = query.data
    await query.edit_message_text(f"📝 أرسل تفاصيل نظام يوم {query.data}:", parse_mode="Markdown")
    return PLAN_CONTENT

async def plan_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("plan_uid")
    day = context.user_data.get("plan_day")
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO user_plans (user_id, day, content) VALUES (?, ?, ?)", (uid, day, update.message.text))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ تم إضافة النظام بنجاح.", parse_mode="Markdown")
    return ConversationHandler.END

async def sendto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("📩 أرسل آيدي المستخدم للمراسة:", parse_mode="Markdown")
    return SENDTO_UID

async def sendto_get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["target_uid"] = update.message.text.strip()
    await update.message.reply_text("✍️ أرسل نص الرسالة:", parse_mode="Markdown")
    return SENDTO_MSG

async def sendto_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(chat_id=int(context.user_data.get("target_uid")), text=f"📬 رسالة من الإدارة:\n\n{update.message.text}", parse_mode="Markdown")
        await update.message.reply_text("✅ تم الإرسال بنجاح.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")
    return ConversationHandler.END

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("📢 أرسل نص الإعلان لجميع المشتركين:", parse_mode="Markdown")
    return BROADCAST_MSG

async def broadcast_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    rows = c.fetchall()
    conn.close()
    for r in rows:
        try:
            await context.bot.send_message(chat_id=int(r[0]), text=f"📢 إعلان عام:\n\n{msg}", parse_mode="Markdown")
        except:
            pass
    await update.message.reply_text("✅ تم إرسال الإعلان للجميع.")
    return ConversationHandler.END

async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_owner(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("➕ أرسل آيدي الشخص لتعيينه كأدمن:", parse_mode="Markdown")
    return ADD_ADMIN_STEP

async def add_admin_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO admins VALUES (?)", (update.message.text.strip(),))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ تم إضافة الأدمن بنجاح.")
    return ConversationHandler.END

async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_owner(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("🗑 أرسل آيدي الأدمن لإزالته:", parse_mode="Markdown")
    return REMOVE_ADMIN_STEP

async def remove_admin_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM admins WHERE user_id = ?", (update.message.text.strip(),))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ تم إزالة الأدمن بنجاح.")
    return ConversationHandler.END

async def set_owner_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_owner(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("👑 أرسل آيدي المالك الجديد:", parse_mode="Markdown")
    return SET_OWNER_STEP

async def set_owner_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_owner = update.message.text.strip()
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM owners")
    conn.execute("INSERT INTO owners VALUES (?)", (new_owner,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"👑 تم نقل الملكية بنجاح إلى: `{new_owner}`", parse_mode="Markdown")
    return ConversationHandler.END

async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)", (str(user_id), user.first_name))
    conn.commit()
    
    c = conn.cursor()
    c.execute("SELECT btn_key, btn_name FROM custom_buttons")
    custom_btns = c.fetchall()
    conn.close()

    if is_owner(user_id):
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مشترك جديد للـ VIP", callback_data="btn_add_vip")],
            [InlineKeyboardButton("📋 إضافة ملاحظة لسجل المتدرب", callback_data="btn_admin_note")],
            [InlineKeyboardButton("📊 إحصائيات المشتركين والنظام", callback_data="btn_admin_stats")],
            [InlineKeyboardButton("📤 تصدير تقارير البيانات (Excel/PDF)", callback_data="btn_export_data")],
            [InlineKeyboardButton("⏰ جداول الرسائل الآلية", callback_data="btn_scheduled_msg")],
            [InlineKeyboardButton("🎟 إضافة كود خصم", callback_data="btn_promo")],
            [InlineKeyboardButton("📋 إضافة نظام يومي لمشترك", callback_data="btn_plan")],
            [InlineKeyboardButton("⏳ تعيين مدة اشتراك للمتدرب", callback_data="btn_sub_date")],
            [InlineKeyboardButton("📩 أرسل رسالة لشخص معين", callback_data="btn_sendto")],
            [InlineKeyboardButton("📢 إرسال إعلان للجميع", callback_data="btn_broadcast")],
            [InlineKeyboardButton("🗑 حذف مشترك من البوت", callback_data="btn_remove_user")],
            [InlineKeyboardButton("⚙️ تعديل تواصل الكوتش", callback_data="btn_set_contact")],
            [InlineKeyboardButton("➕ إضافة زرار جديد", callback_data="btn_add_custom")],
            [InlineKeyboardButton("⚠️ إضافة خطأ شائع", callback_data="btn_add_mistake")],
            [InlineKeyboardButton("➕ إضافة أدمن جديد", callback_data="btn_add_admin")],
            [InlineKeyboardButton("🗑 إزالة أدمن", callback_data="btn_remove_admin")],
            [InlineKeyboardButton("👑 نقل أو تغيير المالك", callback_data="btn_set_owner")]
        ]
        await update.message.reply_text(f"👑 **أهلاً بك يا مالك البوت:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مشترك جديد للـ VIP", callback_data="btn_add_vip")],
            [InlineKeyboardButton("📋 إضافة ملاحظة لسجل المتدرب", callback_data="btn_admin_note")],
            [InlineKeyboardButton("📊 إحصائيات المشتركين والنظام", callback_data="btn_admin_stats")],
            [InlineKeyboardButton("📤 تصدير تقارير البيانات (Excel/PDF)", callback_data="btn_export_data")],
            [InlineKeyboardButton("⏰ جداول الرسائل الآلية", callback_data="btn_scheduled_msg")],
            [InlineKeyboardButton("🎟 إضافة كود خصم", callback_data="btn_promo")],
            [InlineKeyboardButton("📋 إضافة نظام يومي لمشترك", callback_data="btn_plan")],
            [InlineKeyboardButton("⏳ تعيين مدة اشتراك للمتدرب", callback_data="btn_sub_date")],
            [InlineKeyboardButton("📩 أرسل رسالة لشخص معين", callback_data="btn_sendto")],
            [InlineKeyboardButton("📢 إرسال إعلان للجميع", callback_data="btn_broadcast")],
            [InlineKeyboardButton("🗑 حذف مشترك من البوت", callback_data="btn_remove_user")],
            [InlineKeyboardButton("⚙️ تعديل تواصل الكوتش", callback_data="btn_set_contact")],
            [InlineKeyboardButton("➕ إضافة زرار جديد", callback_data="btn_add_custom")],
            [InlineKeyboardButton("⚠️ إضافة خطأ شائع", callback_data="btn_add_mistake")]
        ]
        await update.message.reply_text(f"🛠 **أهلاً بك يا كوتش في لوحة التحكم:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        coach_url = get_contact_link()
        coach_btn_text = get_contact_display_name()
        subscribed = is_subscribed(user_id)
        keyboard = []
        if not subscribed:
            keyboard.append([InlineKeyboardButton("💪 الانضمام لبرنامج التدريب الشخصي", callback_data="buy")])
        else:
            keyboard.append([InlineKeyboardButton("📋 عرض نظامي اليومي", callback_data="my_plan")])
            keyboard.append([InlineKeyboardButton("📖 سجل المتابعة والملاحظات", callback_data="my_admin_notes")])
            keyboard.append([InlineKeyboardButton("🔄 تسجيل التحديث الأسبوعي (الوزن والقياسات)", callback_data="weekly_update_btn")])
            keyboard.append([InlineKeyboardButton("🚨 تسجيل إصابة أو ألم بدني", callback_data="injury_report_btn")])
            keyboard.append([InlineKeyboardButton("⚠️ الأخطاء الشائعة", callback_data="list_mistakes")])
            keyboard.append([InlineKeyboardButton("💡 مقترحات تطوير الخدمة", callback_data="service_feedback_btn")])
            keyboard.append([InlineKeyboardButton(coach_btn_text, url=coach_url)])
            
        for b_key, b_name in custom_btns:
            keyboard.append([InlineKeyboardButton(b_name, callback_data=b_key)])

        status_text = "💎 **أنت مشترك ساري معنا!**" if subscribed else "🚀 أهلاً بك في البوت الرياضي:"
        await update.message.reply_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data.startswith("adm_del_"):
        if not is_admin(user_id): return
        target_uid = query.data.replace("adm_del_", "")
        conn = sqlite3.connect(DB_FILE)
        conn.execute("DELETE FROM users WHERE user_id = ?", (target_uid,))
        conn.execute("DELETE FROM user_plans WHERE user_id = ?", (target_uid,))
        conn.execute("DELETE FROM admin_client_notes WHERE user_id = ?", (target_uid,))
        conn.commit()
        conn.close()
        await query.answer("✅ تم حذف المشترك بنجاح!", show_alert=True)
        try:
            await query.edit_message_text(f"✅ تم حذف المشترك `{target_uid}` من قاعدة البيانات بنجاح.", parse_mode="Markdown")
        except:
            pass
        return

    elif query.data.startswith("adm_edit_"):
        if not is_admin(user_id): return
        target_uid = query.data.replace("adm_edit_", "")
        context.user_data["edit_target_uid"] = target_uid
        await query.message.reply_text(f"✏️ أرسل الآن **البيانات أو التعديل الجديد** للمشترك `{target_uid}` (سيتم حفظه في سجل ملاحظاته):", parse_mode="Markdown")
        return

    if query.data == "buy":
        await query.edit_message_text(
            "💪 لتفعيل اشتراكك وبدء رحلتك معنا، تواصل مع الكوتش مباشرة:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_contact_display_name(), url=get_contact_link())]]),
            parse_mode="Markdown"
        )
    elif query.data == "my_plan":
        if not is_subscribed(user_id):
            await query.edit_message_text("⚠️ عذراً، هذه الميزة للمشتركين فقط.")
            return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT day, content FROM user_plans WHERE user_id = ?", (str(user_id),))
        plans = c.fetchall()
        conn.close()
        if plans:
            text = "📋 **جدول أنظمتك:**\n\n" + "".join([f"🔹 **يوم {p[0]}:**\n{p[1]}\n\n" for p in plans])
            await query.edit_message_text(text, parse_mode="Markdown")
        else:
            await query.edit_message_text("⚠️ ليس لديك أي أنظمة مسجلة حالياً.")

    elif query.data == "my_admin_notes":
        if not is_subscribed(user_id):
            await query.edit_message_text("⚠️ للمشتركين فقط.")
            return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT note, date_added FROM admin_client_notes WHERE user_id = ? ORDER BY id DESC", (str(user_id),))
        notes = c.fetchall()
        conn.close()
        if notes:
            text = "📖 **سجل المتابعة والملاحظات المرسلة من الكوتش:**\n\n" + "".join([f"🔸 **[{d}]**\n{n}\n\n" for n, d in notes])
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_home")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await query.edit_message_text("⚠️ لا توجد ملاحظات مسجلة في ملفك حتى الآن.")

    elif query.data == "list_mistakes":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT mistake_key, title FROM common_mistakes")
        mistakes = c.fetchall()
        conn.close()
        if mistakes:
            keyboard = [[InlineKeyboardButton(f"⚠️ {m[1]}", callback_data=m[0])] for m in mistakes]
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_home")])
            await query.edit_message_text("⚠️ **الأخطاء الشائعة:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await query.edit_message_text("⚠️ لا توجد أخطاء شائعة مسجلة.")

    elif query.data.startswith("mistake_"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT title, description FROM common_mistakes WHERE mistake_key = ?", (query.data,))
        res = c.fetchone()
        conn.close()
        if res:
            keyboard = [[InlineKeyboardButton("🔙 عودة", callback_data="list_mistakes")]]
            await query.edit_message_text(f"⚠️ **{res[0]}**\n\n{res[1]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "back_home":
        coach_url = get_contact_link()
        coach_btn_text = get_contact_display_name()
        subscribed = is_subscribed(user_id)
        keyboard = []
        if not subscribed:
            keyboard.append([InlineKeyboardButton("💪 الانضمام لبرنامج التدريب الشخصي", callback_data="buy")])
        else:
            keyboard.append([InlineKeyboardButton("📋 عرض نظامي اليومي", callback_data="my_plan")])
            keyboard.append([InlineKeyboardButton("📖 سجل المتابعة والملاحظات", callback_data="my_admin_notes")])
            keyboard.append([InlineKeyboardButton("🔄 تسجيل التحديث الأسبوعي (الوزن والقياسات)", callback_data="weekly_update_btn")])
            keyboard.append([InlineKeyboardButton("🚨 تسجيل إصابة أو ألم بدني", callback_data="injury_report_btn")])
            keyboard.append([InlineKeyboardButton("⚠️ الأخطاء الشائعة", callback_data="list_mistakes")])
            keyboard.append([InlineKeyboardButton("💡 مقترحات تطوير الخدمة", callback_data="service_feedback_btn")])
            keyboard.append([InlineKeyboardButton(coach_btn_text, url=coach_url)])
            
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT btn_key, btn_name FROM custom_buttons")
        custom_btns = c.fetchall()
        conn.close()
        for b_key, b_name in custom_btns:
            keyboard.append([InlineKeyboardButton(b_name, callback_data=b_key)])
            
        await query.edit_message_text("🚀 **القائمة الرئيسية:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data.startswith("custom_"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT btn_name, btn_reply FROM custom_buttons WHERE btn_key = ?", (query.data,))
        res = c.fetchone()
        conn.close()
        if res:
            await query.edit_message_text(f"📌 **{res[0]}**:\n\n{res[1]}", parse_mode="Markdown")

async def handle_admin_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_uid = context.user_data.get("edit_target_uid")
    if not target_uid:
        return
    
    note_text = update.message.text.strip()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO admin_client_notes (user_id, note, date_added) VALUES (?, ?, ?)", (target_uid, f"✏️ [تعديل إداري] {note_text}", current_date))
    conn.commit()
    conn.close()
    
    context.user_data.pop("edit_target_uid", None)
    await update.message.reply_text(f"✅ **تم تحديث وحفظ بيانات وسجل المشترك `{target_uid}` بنجاح!**", parse_mode="Markdown")
    
    try:
        await context.bot.send_message(
            chat_id=int(target_uid),
            text=f"🔔 **تحديث وتعديل جديد في سجلك من الكوتش:**\n\n📌 {note_text}\n📅 التاريخ: `{current_date}`",
            parse_mode="Markdown"
        )
    except:
        pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.job_queue.run_repeating(check_subscriptions_job, interval=86400, first=10)
    # تم ضبط وقت إرسال النصيحة اليومية لتكون في الساعة 5:00 صباحاً يومياً
    app.job_queue.run_daily(daily_motivation_job, time=time(hour=5, minute=0, second=0))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(vip_reg_start, pattern="start_vip_reg")],
        states={
            VIP_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, vip_get_age)],
            VIP_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, vip_get_height)],
            VIP_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, vip_get_weight)],
            VIP_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, vip_get_gender)],
            VIP_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, vip_get_goal)],
            VIP_TARGET_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, vip_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_vip_start, pattern="btn_add_vip")],
        states={
            ADD_VIP_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_vip_get_uid)],
            ADD_VIP_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_vip_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_note_start, pattern="btn_admin_note")],
        states={
            NOTE_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_note_get_uid)],
            NOTE_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_note_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(service_feedback_start, pattern="service_feedback_btn")],
        states={BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, service_feedback_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(remove_user_start, pattern="btn_remove_user")],
        states={REMOVE_USER_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_user_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(promo_start, pattern="btn_promo")],
        states={
            PROMO_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_get_code)],
            PROMO_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_get_price)],
            PROMO_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_get_limit)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(plan_start, pattern="btn_plan")],
        states={
            PLAN_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_get_uid)],
            PLAN_DAY: [CallbackQueryHandler(plan_get_day)],
            PLAN_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(sub_date_start, pattern="btn_sub_date")],
        states={
            SUB_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_date_get_uid)],
            SUB_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_date_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(sendto_start, pattern="btn_sendto")],
        states={
            SENDTO_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, sendto_get_uid)],
            SENDTO_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, sendto_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_start, pattern="btn_broadcast")],
        states={BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_admin_start, pattern="btn_add_admin")],
        states={ADD_ADMIN_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(remove_admin_start, pattern="btn_remove_admin")],
        states={REMOVE_ADMIN_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_admin_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(set_owner_start, pattern="btn_set_owner")],
        states={SET_OWNER_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_owner_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(set_contact_start, pattern="btn_set_contact")],
        states={SET_CONTACT_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_contact_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_btn_start, pattern="btn_add_custom")],
        states={
            ADD_BTN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_btn_get_name)],
            ADD_BTN_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_btn_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(mistake_start, pattern="btn_add_mistake")],
        states={
            MISTAKE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mistake_get_title)],
            MISTAKE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, mistake_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(export_start, pattern="btn_export_data")],
        states={
            EXPORT_FORMAT: [CallbackQueryHandler(export_get_format, pattern="^fmt_")],
            EXPORT_TARGET: [CallbackQueryHandler(export_get_target, pattern="^exp_")],
            EXPORT_INCLUDE_NOTES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, export_get_uid_or_notes),
                CallbackQueryHandler(export_generate_file, pattern="^notes_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(weekly_update_start, pattern="weekly_update_btn")],
        states={
            WEEKLY_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weekly_get_weight)],
            WEEKLY_MEASUREMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, weekly_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(schedule_start, pattern="btn_scheduled_msg")],
        states={
            SCHED_TARGET: [CallbackQueryHandler(schedule_get_target, pattern="^sched_")],
            SCHED_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, schedule_get_msg_or_uid)],
            SCHED_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, schedule_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(injury_report_start, pattern="injury_report_btn")],
        states={
            INJURY_PART: [MessageHandler(filters.TEXT & ~filters.COMMAND, injury_get_part)],
            INJURY_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, injury_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    ))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(user_id=DEFAULT_OWNER_ID), handle_admin_edit_text))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(admin_stats_handler, pattern="btn_admin_stats"))

    print("🚀 البوت شغال بكامل التعديلات (توقيت 5 الصبح + زر تواصل الكوتش المتجدد) بنجاح!")
    app.run_polling()

if __name__ == "__main__":
    main()