import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# --- تهيئة قاعدة البيانات ---
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

# --- دالة فحص اشتراكات الأعضاء تلقائياً وتنبيههم ---
async def check_subscriptions_job(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    c.execute("SELECT user_id FROM users WHERE sub_end_date = ?", (today_str,))
    expired_users = c.fetchall()
    conn.close()

    for user in expired_users:
        uid = user[0]
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text="⚠️ **عذراً، لقد انتهى اشتراكك الرياضي اليوم!**\n\nللاستمرار معنا وجدولة أنظمتك القادمة، يرجى التواصل مع الكوتش أو تجديد الاشتراك بأسعار التجديد الحالية.",
                parse_mode="Markdown"
            )
        except:
            pass

# --- محادثة تحديد وتعديل مدة اشتراك العضو ---
async def sub_date_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("⏳ أرسل **آيدي (ID) المشترك** المراد تحديد مدة اشتراكه:", parse_mode="Markdown")
    return SUB_UID

async def sub_date_get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sub_uid"] = update.message.text.strip()
    await update.message.reply_text("📅 أرسل **عدد الأيام** الباقية للاشتراك (مثلاً: اكتب 30 لاشتراك شهر):", parse_mode="Markdown")
    return SUB_DAYS

async def sub_date_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("sub_uid")
    try:
        days_count = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ يرجى إدخال رقم صحيح للأيام:")
        return SUB_DAYS
    
    end_date = (datetime.now() + timedelta(days=days_count)).strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE users SET sub_end_date = ? WHERE user_id = ?", (end_date, uid))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ **تم تحديث اشتراك العضو بنجاح!**\n👤 الآيدي: `{uid}`\n📅 تاريخ الانتهاء: `{end_date}`", parse_mode="Markdown")
    try:
        await context.bot.send_message(chat_id=int(uid), text=f"🔔 **تم تفعيل / تحديث اشتراكك بنجاح!**\nينتهي اشتراكك في تاريخ: `{end_date}`", parse_mode="Markdown")
    except:
        pass
    return ConversationHandler.END

# --- محادثة إضافة خطأ شائع جديد ---
async def mistake_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("⚠️ أكتب **عنوان الخطأ الشائع** (مثلاً: خطأ في رفع الوزن):", parse_mode="Markdown")
    return MISTAKE_TITLE

async def mistake_get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mistake_title"] = update.message.text.strip()
    await update.message.reply_text("📝 ممتاز! الآن أكتب **تفاصيل هذا الخطأ والشرح الصحيح** له للمتدربين:", parse_mode="Markdown")
    return MISTAKE_DESC

async def mistake_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = context.user_data.get("mistake_title")
    desc = update.message.text
    mistake_key = f"mistake_{int(datetime.now().timestamp())}"
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO common_mistakes (mistake_key, title, description) VALUES (?, ?, ?)", (mistake_key, title, desc))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ **تم إضافة الخطأ الشائع بنجاح!**\n📌 العنوان: `{title}`", parse_mode="Markdown")
    return ConversationHandler.END

async def set_contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("🔗 أرسل الآن **يوزر أو رابط تواصل الكوتش الجديد**:", parse_mode="Markdown")
    return SET_CONTACT_STEP

async def set_contact_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('coach_contact', ?)", (val,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ تم تحديث رابط التواصل بنجاح إلى:\n`{val}`", parse_mode="Markdown")
    return ConversationHandler.END

async def add_btn_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("🏷 أكتب **اسم الزرار** الجديد الذي سيظهر للمستخدمين:", parse_mode="Markdown")
    return ADD_BTN_NAME

async def add_btn_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_btn_name"] = update.message.text.strip()
    await update.message.reply_text("📝 ممتاز! الآن أرسل **الرد أو النص** الذي سيظهر للمستخدم عندما يضغط على هذا الزرار:", parse_mode="Markdown")
    return ADD_BTN_REPLY

async def add_btn_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btn_name = context.user_data.get("new_btn_name")
    btn_reply = update.message.text
    btn_key = f"custom_{int(datetime.now().timestamp())}"
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO custom_buttons (btn_key, btn_name, btn_reply) VALUES (?, ?, ?)", (btn_key, btn_name, btn_reply))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ **تم إضافة الزرار بنجاح!**\n📌 اسم الزرار: `{btn_name}`", parse_mode="Markdown")
    return ConversationHandler.END

async def promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("🎟 أرسل الآن **كود الخصم** الجديد:", parse_mode="Markdown")
    return PROMO_CODE

async def promo_get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["p_code"] = update.message.text.strip()
    await update.message.reply_text("💵 أرسل **السعر الجديد** بعد الخصم:", parse_mode="Markdown")
    return PROMO_PRICE

async def promo_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["p_price"] = update.message.text.strip()
    await update.message.reply_text("👥 أرسل **عدد المقاعد المتاحة** لهذا الكود:", parse_mode="Markdown")
    return PROMO_LIMIT

async def promo_get_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        limit = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ يرجى إدخال رقم صحيح لعدد المقاعد:")
        return PROMO_LIMIT
    
    code = context.user_data.get("p_code")
    price = context.user_data.get("p_price")
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO promo VALUES (?, ?, ?, 0)", (code, price, limit))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ **تم إضافة كود الخصم بنجاح!**\n🎟 الكود: `{code}`", parse_mode="Markdown")
    return ConversationHandler.END

async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("👤 أرسل الآن **آيدي (ID) المشترك** المُراد إضافة النظام له:", parse_mode="Markdown")
    return PLAN_UID

async def plan_get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["plan_uid"] = update.message.text.strip()
    days = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
    keyboard = [[InlineKeyboardButton(day, callback_data=day)] for day in days]
    await update.message.reply_text("📅 اختر **اليوم** المراد إضافته:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return PLAN_DAY

async def plan_get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["plan_day"] = query.data
    await query.edit_message_text(f"📝 ممتاز! اخترت يوم **{query.data}**.\nالآن أرسل تفاصيل النظام:", parse_mode="Markdown")
    return PLAN_CONTENT

async def plan_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("plan_uid")
    day = context.user_data.get("plan_day")
    content = update.message.text

    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO user_plans (user_id, day, content) VALUES (?, ?, ?)", (uid, day, content))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ **تم إضافة النظام بنجاح!**\n👤 المشترك: `{uid}`\n📅 اليوم: {day}", parse_mode="Markdown")
    try:
        await context.bot.send_message(chat_id=int(uid), text=f"🔔 **تم تحديث نظام يوم {day}:**\n\n{content}", parse_mode="Markdown")
    except:
        pass
    return ConversationHandler.END

async def sendto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("📩 أرسل **آيدي المستخدم** المراد مراسلته:", parse_mode="Markdown")
    return SENDTO_UID

async def sendto_get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["target_uid"] = update.message.text.strip()
    await update.message.reply_text("✍️ أرسل الآن **نص الرسالة**:", parse_mode="Markdown")
    return SENDTO_MSG

async def sendto_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("target_uid")
    msg = update.message.text
    try:
        await context.bot.send_message(chat_id=int(uid), text=f"📬 **رسالة من الإدارة:**\n\n{msg}", parse_mode="Markdown")
        await update.message.reply_text("✅ تم إرسال الرسالة للمستخدم بنجاح.")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء الإرسال: {e}")
    return ConversationHandler.END

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("📢 أرسل نص الإعلان أو الرسالة لجميع المشتركين:", parse_mode="Markdown")
    return BROADCAST_MSG

async def broadcast_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    rows = c.fetchall()
    conn.close()
    
    success = 0
    for r in rows:
        try:
            await context.bot.send_message(chat_id=int(r[0]), text=f"📢 **إعلان عام:**\n\n{msg}", parse_mode="Markdown")
            success += 1
        except:
            pass
            
    await update.message.reply_text(f"✅ تم إرسال الإعلان بنجاح إلى ({success}) مستخدم.")
    return ConversationHandler.END

async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_owner(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("➕ أرسل **آيدي (ID)** الشخص المراد تعيينه كـ **أدمن**:", parse_mode="Markdown")
    return ADD_ADMIN_STEP

async def add_admin_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_admin = update.message.text.strip()
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO admins VALUES (?)", (new_admin,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ تم إضافة المشرف `{new_admin}` بنجاح.", parse_mode="Markdown")
    return ConversationHandler.END

async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_owner(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("🗑 أرسل **آيدي (ID)** الأدمن المراد إزالته:", parse_mode="Markdown")
    return REMOVE_ADMIN_STEP

async def remove_admin_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_to_rm = update.message.text.strip()
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM admins WHERE user_id = ?", (admin_to_rm,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ تم إزالة الأدمن `{admin_to_rm}` بنجاح.", parse_mode="Markdown")
    return ConversationHandler.END

async def set_owner_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_owner(query.from_user.id): return ConversationHandler.END
    await query.edit_message_text("👑 أرسل **آيدي (ID)** المالك الجديد:", parse_mode="Markdown")
    return SET_OWNER_STEP

async def set_owner_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_owner = update.message.text.strip()
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM owners")
    conn.execute("INSERT INTO owners VALUES (?)", (new_owner,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"👑 تم نقل الملكية بنجاح إلى المالك الجديد: `{new_owner}`", parse_mode="Markdown")
    return ConversationHandler.END

async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية الحالية.")
    return ConversationHandler.END

# --- واجهة البداية واللوحات الذكية ---
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
            [InlineKeyboardButton("🎟 إضافة كود خصم", callback_data="btn_promo")],
            [InlineKeyboardButton("📋 إضافة نظام يومي لمشترك", callback_data="btn_plan")],
            [InlineKeyboardButton("⏳ تعيين مدة اشتراك للمتدرب", callback_data="btn_sub_date")],
            [InlineKeyboardButton("📩 أرسل رسالة لشخص معين", callback_data="btn_sendto")],
            [InlineKeyboardButton("📢 إرسال إعلان للجميع", callback_data="btn_broadcast")],
            [InlineKeyboardButton("⚙️ تعديل تواصل الكوتش", callback_data="btn_set_contact")],
            [InlineKeyboardButton("➕ إضافة زرار جديد", callback_data="btn_add_custom")],
            [InlineKeyboardButton("⚠️ إضافة خطأ شائع", callback_data="btn_add_mistake")],
            [InlineKeyboardButton("➕ إضافة أدمن جديد", callback_data="btn_add_admin")],
            [InlineKeyboardButton("🗑 إزالة أدمن", callback_data="btn_remove_admin")],
            [InlineKeyboardButton("👑 نقل أو تغيير المالك", callback_data="btn_set_owner")]
        ]
        await update.message.reply_text(
            f"👑 **أهلاً بك يا مالك البوت {user.first_name}:**\nاختر العملية المطلوبة من لوحة التحكم:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("🎟 إضافة كود خصم", callback_data="btn_promo")],
            [InlineKeyboardButton("📋 إضافة نظام يومي لمشترك", callback_data="btn_plan")],
            [InlineKeyboardButton("⏳ تعيين مدة اشتراك للمتدرب", callback_data="btn_sub_date")],
            [InlineKeyboardButton("📩 أرسل رسالة لشخص معين", callback_data="btn_sendto")],
            [InlineKeyboardButton("📢 إرسال إعلان للجميع", callback_data="btn_broadcast")],
            [InlineKeyboardButton("⚙️ تعديل تواصل الكوتش", callback_data="btn_set_contact")],
            [InlineKeyboardButton("➕ إضافة زرار جديد", callback_data="btn_add_custom")],
            [InlineKeyboardButton("⚠️ إضافة خطأ شائع", callback_data="btn_add_mistake")]
        ]
        await update.message.reply_text(
            f"🛠 **أهلاً بك يا كوتش {user.first_name} في لوحة التحكم:**\nاختر العملية المطلوبة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        coach_url = get_contact_link()
        keyboard = [
            [InlineKeyboardButton("💳 طلب اشتراك VIP", callback_data="buy")],
            [InlineKeyboardButton("📋 عرض نظامي اليومي", callback_data="my_plan")],
            [InlineKeyboardButton("⚠️ الأخطاء الشائعة", callback_data="list_mistakes")],
            [InlineKeyboardButton("📩 تواصل مع الكوتش", url=coach_url)]
        ]
        
        for b_key, b_name in custom_btns:
            keyboard.append([InlineKeyboardButton(b_name, callback_data=b_key)])

        await update.message.reply_text(
            f"أهلاً بك يا {user.first_name} في البوت الرياضي 🚀\nاختر من الأزرار أدناه:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "my_plan":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT day, content FROM user_plans WHERE user_id = ?", (str(user_id),))
        plans = c.fetchall()
        conn.close()
        
        if plans:
            text = "📋 **جدول أنظمتك المخصصة:**\n\n"
            for p in plans:
                text += f"🔹 **يوم {p[0]}:**\n{p[1]}\n\n------------------\n"
            await query.edit_message_text(text, parse_mode="Markdown")
        else:
            await query.edit_message_text("⚠️ ليس لديك أي أنظمة مسجلة حالياً. تواصل مع الكوتش لإضافتها!")
            
    elif query.data == "list_mistakes":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT mistake_key, title FROM common_mistakes")
        mistakes = c.fetchall()
        conn.close()
        
        if mistakes:
            keyboard = [[InlineKeyboardButton(f"⚠️ {m[1]}", callback_data=m[0])] for m in mistakes]
            keyboard.append([InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home")])
            await query.edit_message_text("⚠️ **قائمة الأخطاء الشائعة:**\nاختر الخطأ لمعرفة تفاصيله والصحيح منه:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await query.edit_message_text("⚠️ لا توجد أخطاء شائعة مسجلة حالياً.")

    elif query.data.startswith("mistake_"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT title, description FROM common_mistakes WHERE mistake_key = ?", (query.data,))
        res = c.fetchone()
        conn.close()
        
        if res:
            title, desc = res
            keyboard = [[InlineKeyboardButton("🔙 عودة لقائمة الأخطاء", callback_data="list_mistakes")]]
            await query.edit_message_text(f"⚠️ **{title}**\n\n{desc}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await query.edit_message_text("⚠️ عذراً، هذا الخطأ غير موجود.")

    elif query.data == "back_home":
        coach_url = get_contact_link()
        keyboard = [
            [InlineKeyboardButton("💳 طلب اشتراك VIP", callback_data="buy")],
            [InlineKeyboardButton("📋 عرض نظامي اليومي", callback_data="my_plan")],
            [InlineKeyboardButton("⚠️ الأخطاء الشائعة", callback_data="list_mistakes")],
            [InlineKeyboardButton("📩 تواصل مع الكوتش", url=coach_url)]
        ]
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
            b_name, b_reply = res
            await query.edit_message_text(f"📌 **{b_name}**:\n\n{b_reply}", parse_mode="Markdown")
        else:
            await query.edit_message_text("⚠️ عذراً، هذا الزرار لم يعد موجوداً.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # التعديل الصحيح للـ JobQueue بدون أي أخطاء
    app.job_queue.run_repeating(check_subscriptions_job, interval=86400, first=10)

    promo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(promo_start, pattern="btn_promo")],
        states={
            PROMO_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_get_code)],
            PROMO_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_get_price)],
            PROMO_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_get_limit)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    plan_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(plan_start, pattern="btn_plan")],
        states={
            PLAN_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_get_uid)],
            PLAN_DAY: [CallbackQueryHandler(plan_get_day)],
            PLAN_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    sub_date_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(sub_date_start, pattern="btn_sub_date")],
        states={
            SUB_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_date_get_uid)],
            SUB_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_date_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    sendto_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(sendto_start, pattern="btn_sendto")],
        states={
            SENDTO_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, sendto_get_uid)],
            SENDTO_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, sendto_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_start, pattern="btn_broadcast")],
        states={
            BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    add_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_admin_start, pattern="btn_add_admin")],
        states={ADD_ADMIN_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    remove_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(remove_admin_start, pattern="btn_remove_admin")],
        states={REMOVE_ADMIN_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_admin_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    set_owner_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_owner_start, pattern="btn_set_owner")],
        states={SET_OWNER_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_owner_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    set_contact_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_contact_start, pattern="btn_set_contact")],
        states={SET_CONTACT_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_contact_finish)]},
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    add_custom_btn_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_btn_start, pattern="btn_add_custom")],
        states={
            ADD_BTN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_btn_get_name)],
            ADD_BTN_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_btn_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    mistake_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(mistake_start, pattern="btn_add_mistake")],
        states={
            MISTAKE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mistake_get_title)],
            MISTAKE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, mistake_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    app.add_handler(promo_conv)
    app.add_handler(plan_conv)
    app.add_handler(sub_date_conv)
    app.add_handler(sendto_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(add_admin_conv)
    app.add_handler(remove_admin_conv)
    app.add_handler(set_owner_conv)
    app.add_handler(set_contact_conv)
    app.add_handler(add_custom_btn_conv)
    app.add_handler(mistake_conv)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 البوت شغال بالكامل وبأفضل شكل!")
    app.run_polling()

if __name__ == "__main__":
    main()