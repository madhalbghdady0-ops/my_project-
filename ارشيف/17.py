import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# إعدادات الـ Logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8626691591:AAFGvecOFFTzD6TQejxaK0dZTH8SLjNDAsg"

# ملفات حفظ البيانات
ADMINS_FILE = "admins.json"
CUSTOM_RESPONSES_FILE = "responses.json"
SUBSCRIBERS_FILE = "subscribers.json"

# الآيدي الخاص بك كأدمن رئيسي ومالك للبوت
DEFAULT_ADMINS = [6373995909]

def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    return data
            except:
                return DEFAULT_ADMINS
    return DEFAULT_ADMINS

def save_admins(admins):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins, f, ensure_ascii=False, indent=4)

ADMIN_IDS = load_admins()
if DEFAULT_ADMINS[0] not in ADMIN_IDS:
    ADMIN_IDS.append(DEFAULT_ADMINS[0])
    save_admins(ADMIN_IDS)

# حالات محادثة الاشتراك
COUNTRY, PAYMENT_METHOD = range(2)

# --- دوال مساعدة لحفظ وقراءة البيانات ---
def load_data(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return default
    return default

def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- أمر البدء والقائمة الرئيسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    
    welcome_text = (
        f"أهلاً بك يا {user.first_name} في بوت التدريب الأونلاين الخاص بالكوتش! 🚀\n\n"
        "اختر ما ترغب بمعرفته من الأزرار بالأسفل:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 تفاصيل التدريب", callback_data="show_details")],
        [InlineKeyboardButton("💳 طلب اشتراك جديد", callback_data="start_subscription")]
    ]
    
    # لو الشخص أدمن/مالك، نظهر له زر لوحة التحكم سريعاً
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👨‍💻 لوحة تحكم الأدمن", callback_data="open_admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup)
    return ConversationHandler.END

# --- التعامل مع أزرار القائمة الرئيسية ---
async def main_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_details":
        responses = load_data(CUSTOM_RESPONSES_FILE, {})
        details_text = responses.get("details", "📋 **تفاصيل التدريب:**\nالنظام أونلاين بالكامل، متابعة يومية، جدول تمارين وتغذية مخصص لهدفك.\n\nللإشتراك اضغط على زر 'طلب اشتراك جديد'.")
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home")]]
        await query.edit_message_text(details_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return ConversationHandler.END

    elif data == "start_subscription":
        keyboard = [[InlineKeyboardButton("🔙 إلغاء والرجوع للقائمة", callback_data="back_home")]]
        await query.edit_message_text(
            "ممتاز! لبدء اشتراكك، يرجى إرسال اسم **بلدك** الحالي:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return COUNTRY

    elif data == "open_admin_panel":
        if query.from_user.id in ADMIN_IDS:
            subscribers = load_data(SUBSCRIBERS_FILE, [])
            keyboard = [
                [InlineKeyboardButton("📋 عرض قائمة المشتركين والطلبات", callback_data="admin_list_subs")],
                [InlineKeyboardButton("📢 إرسال رسالة جماعية (Broadcast)", callback_data="admin_broadcast_prompt")],
                [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home")]
            ]
            await query.edit_message_text(
                f"👨‍💻 **لوحة تحكم الأدمن:**\n\n👥 عدد الطلبات/المشتركين: {len(subscribers)}\nاختر الإجراء المطلوب:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        return ConversationHandler.END

    elif data == "back_home":
        await start(update, context)
        return ConversationHandler.END

# --- خطوات التسجيل وطلب الاشتراك (مع زر الرجوع) ---
async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["country"] = text
    
    keyboard = [[InlineKeyboardButton("🔙 إلغاء والرجوع للقائمة", callback_data="back_home")]]
    await update.message.reply_text(
        "رائع. الآن اكتب **وسيلة الدفع** التي تفضل استخدامها (مثل: فودافون كاش، إنستاباي، بايبال... إلخ):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PAYMENT_METHOD

async def get_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    country = context.user_data.get("country", "غير محدد")
    payment_method = update.message.text

    subscribers = load_data(SUBSCRIBERS_FILE, [])
    
    new_request = {
        "id": user.id,
        "username": f"@{user.username}" if user.username else "بدون يوزر",
        "name": user.first_name,
        "country": country,
        "payment": payment_method
    }

    subscribers.append(new_request)
    save_data(SUBSCRIBERS_FILE, subscribers)

    keyboard = [[InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="back_home")]]
    await update.message.reply_text(
        "✅ تم استلام طلب اشتراكك بنجاح!\n"
        "⏳ **انتظر تأكيد المالك/الأدمن**، سيتم مراجعة طلبك والتواصل معك قريباً جداً.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    admin_notification = (
        "🚨 **طلب اشتراك جديد بانتظار التأكيد!**\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🔗 اليوزر: @{user.username if user.username else 'لا يوجد'}\n"
        f"🆔 الآيدي: `{user.id}`\n"
        f"🌍 الدولة: {country}\n"
        f"💳 وسيلة الدفع المقترحة: {payment_method}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_notification, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"فشل إرسال التنبيه للأدمن {admin_id}: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

# --- لوحة تحكم الأدمن والمالك عبر الأمر /panel ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("عذراً، هذه اللوحة مخصصة للمالك والأدمن فقط ⛔")
        return
    
    subscribers = load_data(SUBSCRIBERS_FILE, [])
    keyboard = [
        [InlineKeyboardButton("📋 عرض قائمة المشتركين والطلبات", callback_data="admin_list_subs")],
        [InlineKeyboardButton("📢 إرسال رسالة جماعية (Broadcast)", callback_data="admin_broadcast_prompt")],
        [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👨‍💻 **لوحة تحكم الأدمن:**\n\n"
        f"👥 عدد الطلبات/المشتركين: {len(subscribers)}\n"
        "اختر الإجراء المطلوب:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def admin_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("صلاحية مرفوضة ⛔", show_alert=True)
        return

    await query.answer()
    data = query.data

    if data == "admin_list_subs":
        subscribers = load_data(SUBSCRIBERS_FILE, [])
        if not subscribers:
            keyboard = [[InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="open_admin_panel")]]
            await query.edit_message_text("لا يوجد طلبات اشتراك مسجلة حتى الآن.", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        text = "📋 **قائمة الطلبات والمشتركين:**\n\n"
        for idx, sub in enumerate(subscribers, 1):
            text += f"{idx}. {sub['name']} | {sub['username']} | 🌍 {sub['country']} | 💳 {sub['payment']}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="open_admin_panel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "admin_broadcast_prompt":
        keyboard = [[InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="open_admin_panel")]]
        await query.edit_message_text("لإرسال رسالة جماعية، اكتب الأمر بالطريقة التالية:\n`/broadcast [رسالتك هنا]`", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- أمر عرض الأوامر الخاصة بك (البوت كوماندز) ---
async def bot_commands_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    guide_text = (
        "🛠 **دليل أوامر وإدارة البوت (خاص بالمالك والأدمن):**\n\n"
        "1️⃣ **`/panel`**\n"
        "   - تفتح لوحة التحكم بالأزرار لإدارة المشتركين وعرض الطلبات.\n\n"
        "2️⃣ **`/broadcast [الرسالة]`**\n"
        "   - إرسال إشعار أو رسالة فورية لكل المشتركين المسجلين دفعة واحدة.\n\n"
        "3️⃣ **`/addreply details [النص الجديد]`**\n"
        "   - لتحديث وتغيير محتوى زر 'تفاصيل التدريب' في أي وقت.\n\n"
        "4️⃣ **`/addreply [كلمة_مفتاحية] [الرد]`**\n"
        "   - لإضافة ردود تلقائية جديدة لو المستخدم كتب كلمة معينة في الشات.\n\n"
        "5️⃣ **`/addadmin [User_ID]`**\n"
        "   - لرفع شخص جديد رتبة أدمن معك (للمالك الأساسي فقط).\n\n"
        "6️⃣ **`/botcommands`**\n"
        "   - لعرض هذه القائمة الإرشادية."
    )
    await update.message.reply_text(guide_text, parse_mode="Markdown")

# --- أمر رفع أدمن جديد ---
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != DEFAULT_ADMINS[0]:
        await update.message.reply_text("هذا الأمر للمالك الأساسي فقط ⛔")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("الاستخدام الصحيح:\n`/addadmin [User_ID]`", parse_mode="Markdown")
        return

    try:
        new_admin_id = int(args[0])
        global ADMIN_IDS
        if new_admin_id not in ADMIN_IDS:
            ADMIN_IDS.append(new_admin_id)
            save_admins(ADMIN_IDS)
            await update.message.reply_text(f"تم رفع الآيدي `{new_admin_id}` إلى رتبة أدمن بنجاح! ✅", parse_mode="Markdown")
        else:
            await update.message.reply_text("هذا المستخدم أدمن بالفعل.")
    except ValueError:
        await update.message.reply_text("يرجى إدخال آيدي صحيح (أرقام فقط).")

# --- أمر الإذاعة الجماعية ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return

    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("يرجى كتابة الرسالة بعد الأمر:\n`/broadcast رسالتك هنا`", parse_mode="Markdown")
        return

    subscribers = load_data(SUBSCRIBERS_FILE, [])
    if not subscribers:
        await update.message.reply_text("لا يوجد مشتركين لإرسال الرسالة لهم.")
        return

    success = 0
    fail = 0

    for sub in subscribers:
        try:
            await context.bot.send_message(chat_id=sub["id"], text=f"📢 **إشعار من الإدارة:**\n\n{message_text}", parse_mode="Markdown")
            success += 1
        except Exception:
            fail += 1

    await update.message.reply_text(f"✅ تم الإرسال إلى: {success}\n❌ فشل الإرسال إلى: {fail}")

# --- إضافة ردود أو تفاصيل مخصصة ---
async def add_custom_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("استخدم الأمر هكذا:\n`/addreply details [اكتب تفاصيل التدريب هنا]`", parse_mode="Markdown")
        return

    keyword = args[0].lower()
    reply_text = " ".join(args[1:])

    responses = load_data(CUSTOM_RESPONSES_FILE, {})
    responses[keyword] = reply_text
    save_data(CUSTOM_RESPONSES_FILE, responses)

    await update.message.reply_text(f"تم حفظ النص للقسم (`{keyword}`) بنجاح! ✅")

async def handle_custom_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id in ADMIN_IDS:
        return

    text = update.message.text.lower()
    responses = load_data(CUSTOM_RESPONSES_FILE, {})

    for keyword, response in responses.items():
        if keyword in text:
            await update.message.reply_text(response)
            return

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # محادثة التسجيل لطلب الاشتراك مع التعامل مع زر العودة الرئيسية
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_buttons, pattern="^start_subscription$")],
        states={
            COUNTRY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_country),
                CallbackQueryHandler(main_menu_buttons, pattern="^back_home$")
            ],
            PAYMENT_METHOD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment_method),
                CallbackQueryHandler(main_menu_buttons, pattern="^back_home$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(main_menu_buttons, pattern="^(show_details|back_home|open_admin_panel)$"))
    
    # أوامر الأدمن والمالك المضافة
    application.add_handler(CommandHandler("panel", admin_panel))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("addadmin", add_admin))
    application.add_handler(CommandHandler("addreply", add_custom_response))
    application.add_handler(CommandHandler("botcommands", bot_commands_guide))
    application.add_handler(CallbackQueryHandler(admin_panel_buttons, pattern="^admin_"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_messages))

    print("البوت يعمل الآن بكامل المزايا والأزرار التفاعلية... 🚀")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()