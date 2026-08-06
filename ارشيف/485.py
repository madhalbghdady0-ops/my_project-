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

# --- مراحل المحادثة التفاعلية (Conversation States) ---
PROMO_CODE, PROMO_PRICE, PROMO_LIMIT = range(3)
PLAN_UID, PLAN_DAY, PLAN_CONTENT = range(3, 6)
SENDTO_UID, SENDTO_MSG = range(6, 8)
BROADCAST_MSG = range(8, 9)
ADD_ADMIN_STEP = range(9, 10)
REMOVE_ADMIN_STEP = range(10, 11)
SET_OWNER_STEP = range(11, 12)

# --- تهيئة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS promo (code TEXT PRIMARY KEY, price TEXT, limit_count INTEGER, used_count INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS admins (user_id TEXT PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS owners (user_id TEXT PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, name TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS requests (user_id TEXT PRIMARY KEY, deadline TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS user_plans (user_id TEXT, day TEXT, content TEXT, PRIMARY KEY(user_id, day))')
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

# --- محادثة إضافة كود الخصم بالأزرار ---
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
    
    await update.message.reply_text(f"✅ **تم إضافة كود الخصم بنجاح!**\n🎟 الكود: `{code}`\n💰 السعر: {price}\n👥 المقاعد: {limit}", parse_mode="Markdown")
    return ConversationHandler.END

# --- محادثة النظام اليومي (تفاعلية بأزرار أيام الأسبوع) ---
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
    await query.edit_message_text(f"📝 ممتاز! اخترت يوم **{query.data}**.\nالآن أرسل تفاصيل النظام (تمرين اليوم أو الأكل المخصص):", parse_mode="Markdown")
    return PLAN_CONTENT

async def plan_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("plan_uid")
    day = context.user_data.get("plan_day")
    content = update.message.text

    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO user_plans (user_id, day, content) VALUES (?, ?, ?)", (uid, day, content))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ **تم إضافة النظام بنجاح!**\n👤 المشترك: `{uid}`\n📅 اليوم: {day}\n📝 المحتوى:\n{content}", parse_mode="Markdown")
    try:
        await context.bot.send_message(chat_id=int(uid), text=f"🔔 **تم تحديث نظام يوم {day}:**\n\n{content}", parse_mode="Markdown")
    except:
        pass
    return ConversationHandler.END

# --- محادثة إرسال رسالة لشخص معين ---
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

# --- محادثة الإذاعة العامة ---
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

# --- محادثات إدارة الأدمن والمالك (تفاعلية بالكامل) ---
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
    conn.close()

    # لو الشخص مالك (Owner): تظهر له لوحة الإدارة الكاملة + أزرار الملكية الخاصة بالمالك فقط
    if is_owner(user_id):
        keyboard = [
            [InlineKeyboardButton("🎟 إضافة كود خصم", callback_data="btn_promo")],
            [InlineKeyboardButton("📋 إضافة نظام يومي لمشترك", callback_data="btn_plan")],
            [InlineKeyboardButton("📩 أرسل رسالة لشخص معين", callback_data="btn_sendto")],
            [InlineKeyboardButton("📢 إرسال إعلان للجميع", callback_data="btn_broadcast")],
            [InlineKeyboardButton("➕ إضافة أدمن جديد", callback_data="btn_add_admin")],
            [InlineKeyboardButton("🗑 إزالة أدمن", callback_data="btn_remove_admin")],
            [InlineKeyboardButton("👑 نقل أو تغيير المالك", callback_data="btn_set_owner")]
        ]
        await update.message.reply_text(
            f"👑 **أهلاً بك يا مالك البوت {user.first_name}:**\nاختر العملية المطلوبة من الأزرار أدناه:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif is_admin(user_id):
        # لو الشخص أدمن عادي (بدون صلاحيات المالك المطلقة)
        keyboard = [
            [InlineKeyboardButton("🎟 إضافة كود خصم", callback_data="btn_promo")],
            [InlineKeyboardButton("📋 إضافة نظام يومي لمشترك", callback_data="btn_plan")],
            [InlineKeyboardButton("📩 أرسل رسالة لشخص معين", callback_data="btn_sendto")],
            [InlineKeyboardButton("📢 إرسال إعلان للجميع", callback_data="btn_broadcast")]
        ]
        await update.message.reply_text(
            f"🛠 **أهلاً بك يا كوتش {user.first_name} في لوحة التحكم:**\nاختر العملية المطلوبة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        # واجهة الزبون العادي
        keyboard = [
            [InlineKeyboardButton("💳 طلب اشتراك VIP", callback_data="buy")],
            [InlineKeyboardButton("📋 عرض نظامي اليومي", callback_data="my_plan")],
            [InlineKeyboardButton("📩 تواصل مع الكوتش", url="https://t.me/your_username")]
        ]
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

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # محادثات الإدارة
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

    app.add_handler(promo_conv)
    app.add_handler(plan_conv)
    app.add_handler(sendto_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(add_admin_conv)
    app.add_handler(remove_admin_conv)
    app.add_handler(set_owner_conv)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 البوت شغال بالكامل بنظام الأزرار التفاعلية وخطوة بخطوة لكل الصلاحيات!")
    app.run_polling()

if __name__ == "__main__":
    main()