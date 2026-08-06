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

# مراحل المحادثة التفاعلية للإدارة
PROMO_CODE, PROMO_PRICE, PROMO_LIMIT = range(3)
EXTEND_UID = range(3, 4)
SENDTO_UID, SENDTO_MSG = range(4, 6)
BROADCAST_MSG = range(6, 7)
PLAN_UID, PLAN_DAY, PLAN_CONTENT = range(7, 10)

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

# --- أوامر التحكم في الملكية والأدمنز ---
async def set_owner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("⛔ هذا الأمر للمالك الأساسي فقط.")
        return
    if not context.args:
        await update.message.reply_text("⚠️ الاستخدام:\n`/setowner [آيدي_المالك_الجديد]`", parse_mode="Markdown")
        return
    new_owner = context.args[0]
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM owners")
    conn.execute("INSERT INTO owners VALUES (?)", (new_owner,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"👑 تم نقل الملكية بنجاح إلى: `{new_owner}`", parse_mode="Markdown")

async def add_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("⛔ للمالك فقط.")
        return
    if not context.args:
        await update.message.reply_text("⚠️ الاستخدام:\n`/addadmin [آيدي_المشرف]`", parse_mode="Markdown")
        return
    new_admin = context.args[0]
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO admins VALUES (?)", (new_admin,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ تم إضافة المشرف `{new_admin}` بنجاح.", parse_mode="Markdown")

async def remove_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id): return
    if not context.args: return
    admin_to_rm = context.args[0]
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM admins WHERE user_id = ?", (admin_to_rm,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ تم إزالة الأدمن `{admin_to_rm}`.")

# --- دليل أوامر الأدمن ---
async def help_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id): return
    text = (
        "🛠 **لوحة تحكم البوت (خاصة بالإدارة فقط):**\n\n"
        "🎟 `/setpromo` -> لعمل كود خصم جديد.\n"
        "⏳ `/extend` -> لتمديد مهلة التحويل ساعة للمشترك.\n"
        "📋 `/setplan` -> لإضافة أو تعديل نظام (أكل/تمرين) ليوم معين للمشترك.\n"
        "❌ `/removeplan` -> لحذف نظام يوم محدد عن المشترك.\n"
        "🗑 `/clearplan` -> لمسح جميع أنظمة المشترك دفعة واحدة.\n"
        "📩 `/sendto` -> لإرسال رسالة خاصة لمستخدم.\n"
        "📢 `/broadcast` -> لإرسال إعلان للجميع.\n"
    )
    if is_owner(user_id):
        text += "\n👑 **أوامر المالك:**\n• `/setowner [ID]`\n• `/addadmin [ID]`\n• `/removeadmin [ID]`"
    await update.message.reply_text(text, parse_mode="Markdown")

# --- محادثات الإدارة والأنظمة ---
async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("📋 **إضافة/تعديل نظام المشترك:**\nالخطوة 1/3: أرسل **آيدي (ID) المشترك** الآن:")
    return PLAN_UID

async def plan_get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["plan_uid"] = update.message.text.strip()
    await update.message.reply_text("الخطوة 2/3: تمام! الآن أرسل **اليوم** (مثلاً: `الأحد`، `الإثنين`):")
    return PLAN_DAY

async def plan_get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["plan_day"] = update.message.text.strip()
    await update.message.reply_text("الخطوة 3/3: ممتاز! الآن أكتب **تفاصيل النظام** (تمرين اليوم أو الأكل المخصص):")
    return PLAN_CONTENT

async def plan_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("plan_uid")
    day = context.user_data.get("plan_day")
    content = update.message.text

    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO user_plans (user_id, day, content) VALUES (?, ?, ?)", (uid, day, content))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ **تم حفظ النظام بنجاح!**\n👤 المشترك: `{uid}`\n📅 اليوم: {day}\n📝 المحتوى:\n{content}", parse_mode="Markdown")
    try:
        await context.bot.send_message(chat_id=int(uid), text=f"🔔 **تم تحديث نظام يوم {day}:**\n\n{content}", parse_mode="Markdown")
    except:
        pass
    return ConversationHandler.END

async def remove_plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ الاستخدام الصحيح:\n`/removeplan [ID] [اليوم]`", parse_mode="Markdown")
        return
    uid, day = context.args[0], context.args[1]
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM user_plans WHERE user_id = ? AND day = ?", (uid, day))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ تم حذف نظام يوم ({day}) عن المشترك `{uid}` بنجاح.", parse_mode="Markdown")

async def clear_plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("⚠️ الاستخدام الصحيح:\n`/clearplan [ID]`", parse_mode="Markdown")
        return
    uid = context.args[0]
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM user_plans WHERE user_id = ?", (uid,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"🗑 تم مسح كافة الأنظمة الخاصة بالمشترك `{uid}`.", parse_mode="Markdown")

async def promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("🎟 أرسل **كود الخصم** الجديد:", parse_mode="Markdown")
    return PROMO_CODE

async def promo_get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["p_code"] = update.message.text.strip()
    await update.message.reply_text("أرسل **السعر الجديد** بعد الخصم:")
    return PROMO_PRICE

async def promo_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["p_price"] = update.message.text.strip()
    await update.message.reply_text("أرسل **عدد المقاعد** المتاحة:")
    return PROMO_LIMIT

async def promo_get_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        limit = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ يرجى إدخال رقم صحيح:")
        return PROMO_LIMIT
    code = context.user_data.get("p_code")
    price = context.user_data.get("p_price")
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO promo VALUES (?, ?, ?, 0)", (code, price, limit))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ تم تفعيل كود الخصم `{code}` بسعر {price} لـ {limit} مشترك.", parse_mode="Markdown")
    return ConversationHandler.END

async def extend_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("⏳ أرسل **آيدي المشترك** لتمديد مهلته ساعة:")
    return EXTEND_UID

async def extend_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text.strip()
    new_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE requests SET deadline = ? WHERE user_id = ?", (new_time, uid))
    conn.commit()
    conn.close()
    try:
        await context.bot.send_message(chat_id=int(uid), text="✅ تم تمديد مهلة التحويل ساعة إضافية.")
    except:
        pass
    await update.message.reply_text(f"✅ تم التمديد للمستخدم `{uid}` بنجاح.")
    return ConversationHandler.END

async def sendto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("📩 أرسل **آيدي المستخدم**:")
    return SENDTO_UID

async def sendto_get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["target_uid"] = update.message.text.strip()
    await update.message.reply_text("أرسل **نص الرسالة**:")
    return SENDTO_MSG

async def sendto_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("target_uid")
    msg = update.message.text
    try:
        await context.bot.send_message(chat_id=int(uid), text=f"📬 **رسالة الإدارة:**\n\n{msg}", parse_mode="Markdown")
        await update.message.reply_text("✅ تم الإرسال.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")
    return ConversationHandler.END

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("📢 أرسل نص الإعلان لجميع المشتركين:")
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
    await update.message.reply_text(f"✅ تم الإرسال إلى ({success}) مستخدم.")
    return ConversationHandler.END

async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END

# --- واجهة البوت الديناميكية (تتغير حسب الصلاحية: زبون vs أدمن/مالك) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)", (str(user_id), user.first_name))
    conn.commit()
    conn.close()

    # الأزرار الأساسية للزبون العادي
    keyboard = [
        [InlineKeyboardButton("💳 طلب اشتراك VIP", callback_data="buy")],
        [InlineKeyboardButton("📋 عرض نظامي اليومي", callback_data="my_plan")],
        [InlineKeyboardButton("📩 تواصل مع الكوتش", url="https://t.me/your_username")]
    ]

    # لو الشخص أدمن أو مالك، بنضيف له أزرار الإدارة الخاصة به في الواجهة تلقائياً!
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("🎟 إضافة كود خصم (أدمن)", callback_data="admin_promo")])
        keyboard.append([InlineKeyboardButton("🛠 لوحة التحكم والأوامر", callback_data="admin_help")])

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

    elif query.data == "admin_promo" and is_admin(user_id):
        await query.edit_message_text("🎟 لتوليد كود خصم جديد، يرجى كتابة الأمر التالي في التيرمنال أو الإرسال للبوت مباشرة:\n`/setpromo`", parse_mode="Markdown")

    elif query.data == "admin_help" and is_admin(user_id):
        text = (
            "🛠 **لوحة تحكم البوت (خاصة بالإدارة):**\n\n"
            "• `/setpromo` -> لعمل كود خصم جديد.\n"
            "• `/extend` -> لتمديد مهلة التحويل ساعة.\n"
            "• `/setplan` -> لإضافة أو تعديل نظام المشترك.\n"
            "• `/removeplan` -> لحذف نظام يوم محدد.\n"
            "• `/clearplan` -> لمسح أنظمة المشترك.\n"
            "• `/sendto` -> لإرسال رسالة خاصة.\n"
            "• `/broadcast` -> لإرسال إعلان للجميع.\n"
        )
        if is_owner(user_id):
            text += "\n👑 **أوامر المالك:**\n• `/setowner [ID]`\n• `/addadmin [ID]`\n• `/removeadmin [ID]`"
        await query.edit_message_text(text, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    plan_conv = ConversationHandler(
        entry_points=[CommandHandler("setplan", plan_start)],
        states={
            PLAN_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_get_uid)],
            PLAN_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_get_day)],
            PLAN_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    promo_conv = ConversationHandler(
        entry_points=[CommandHandler("setpromo", promo_start)],
        states={
            PROMO_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_get_code)],
            PROMO_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_get_price)],
            PROMO_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_get_limit)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    extend_conv = ConversationHandler(
        entry_points=[CommandHandler("extend", extend_start)],
        states={
            EXTEND_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, extend_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    sendto_conv = ConversationHandler(
        entry_points=[CommandHandler("sendto", sendto_start)],
        states={
            SENDTO_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, sendto_get_uid)],
            SENDTO_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, sendto_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )

    app.add_handler(plan_conv)
    app.add_handler(promo_conv)
    app.add_handler(extend_conv)
    app.add_handler(sendto_conv)
    app.add_handler(broadcast_conv)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("helpadmin", help_admin))
    app.add_handler(CommandHandler("removeplan", remove_plan_cmd))
    app.add_handler(CommandHandler("clearplan", clear_plan_cmd))
    app.add_handler(CommandHandler("setowner", set_owner_cmd))
    app.add_handler(CommandHandler("addadmin", add_admin_cmd))
    app.add_handler(CommandHandler("removeadmin", remove_admin_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 البوت شغال الآن بكفاءة وبدون أي مشاكل!")
    app.run_polling()

if __name__ == "__main__":
    main()