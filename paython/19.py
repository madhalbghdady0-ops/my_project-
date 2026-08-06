import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8626691591:AAFGvecOFFTzD6TQejxaK0dZTH8SLjNDAsg"
ADMIN_ID = 6373995909  # آيدي المالك/الأدمن

REQUESTS_FILE = "requests.json"     
VIP_USERS_FILE = "vip_users.json"   
SETTINGS_FILE = "settings.json"     
BANNED_FILE = "banned_users.json"

COUNTRY, SCREENSHOT = range(2)
WAITING_FOR_USER_MSG = 10

MAX_VIP_LIMIT = 20  # الحد الأقصى للمقاعد الحالية

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

# --- أوامر الأدمن الإضافية للاحترافية ---
async def set_text_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ الطريقة:\n`/settext details المحتوى الجديد...`\nأو:\n`/settext payment المحتوى الجديد...`",
            parse_mode="Markdown"
        )
        return

    key = context.args[0]
    text = " ".join(context.args[1:])
    settings = load_data(SETTINGS_FILE, {})
    settings[key] = text
    save_data(SETTINGS_FILE, settings)
    await update.message.reply_text(f"✅ تم تحديث نص قسم ({key}) بنجاح!")

async def send_to_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ الطريقة الصحيحة:\n`/sendto ID_المستخدم رسالتك هنا`", parse_mode="Markdown")
        return

    target_id = context.args[0]
    message_text = " ".join(context.args[1:])

    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"📬 **رسالة من إدارة البوت:**\n\n{message_text}",
            parse_mode="Markdown"
        )
        await update.message.reply_text(f"✅ تم إرسال الرسالة للمستخدم `{target_id}` بنجاح.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل الإرسال تأكد من الآيدي الصحيح.\nالخطأ: {e}")

# أمر إرسال طرق الدفع للمستخدم مع زرارين (متاحة / غير متاحة)
async def send_payment_methods_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ طريقة الاستخدام:\n`/sendpay ID_المستخدم تفاصيل طرق الدفع المتاحة...`\nمثال:\n`/sendpay 12345678 فودافون كاش: 010... أو إنستاباي: name`",
            parse_mode="Markdown"
        )
        return

    target_id = context.args[0]
    payment_details = " ".join(context.args[1:])

    requests_list = load_data(REQUESTS_FILE, {})
    if target_id in requests_list:
        requests_list[target_id]["payment_offered"] = payment_details
        save_data(REQUESTS_FILE, requests_list)

    keyboard = [
        [InlineKeyboardButton("✅ نعم، أستطيع التحويل (متاحة)", callback_data=f"can_pay_{target_id}")],
        [InlineKeyboardButton("❌ لا، لا أستطيع (غير متاحة)", callback_data=f"cant_pay_{target_id}")]
    ]

    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"💳 **طرق الدفع المتاحة لدى الكوتش لك:**\n\n{payment_details}\n\nهل هذه الطريقة متاحة لديك وتستطيع التحويل من خلالها؟",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        await update.message.reply_text(f"✅ تم إرسال خيارات الدفع للمستخدم `{target_id}` بنجاح وانتظار رده.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء الإرسال للمستخدم: {e}")

async def ban_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("⚠️ اكتب الآيدي للحظر:\n`/ban ID`", parse_mode="Markdown")
        return
    uid = context.args[0]
    banned = load_data(BANNED_FILE, [])
    if uid not in banned:
        banned.append(uid)
        save_data(BANNED_FILE, banned)
        await update.message.reply_text(f"⛔ تم حظر المستخدم `{uid}` من استخدام البوت.", parse_mode="Markdown")
    else:
        await update.message.reply_text("المستخدم محظور بالفعل.")

# --- أمر البدء /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    banned = load_data(BANNED_FILE, [])
    if str(user.id) in banned:
        if update.message:
            await update.message.reply_text("⛔ عذراً، تم حظرك من استخدام هذا البوت.")
        return ConversationHandler.END

    vip_list = load_data(VIP_USERS_FILE, {})
    
    welcome_text = (
        f"أهلاً بك يا {user.first_name} في بوت التدريب الأونلاين الخاص بالكوتش! 🚀\n\n"
        f"👑 عدد مشتركي الـ VIP الحاليين: {len(vip_list)} من أصل {MAX_VIP_LIMIT} مقعد.\n\n"
        "اختر ما ترغب بمعرفته من الأزرار بالأسفل:"
    )

    keyboard = [
        [InlineKeyboardButton("📋 تفاصيل التدريب", callback_data="show_details")]
    ]

    if len(vip_list) < MAX_VIP_LIMIT:
        keyboard.append([InlineKeyboardButton("💳 طلب اشتراك VIP جديد", callback_data="start_subscription")])
    else:
        keyboard.append([InlineKeyboardButton("❌ اكتملت المقاعد الحالية", callback_data="full_capacity")])

    keyboard.append([InlineKeyboardButton("📩 تواصل مع الكوتش", callback_data="contact_coach")])

    if user.id == ADMIN_ID:
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

# --- معالج الأزرار العامة ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "show_details":
        settings = load_data(SETTINGS_FILE, {})
        details_text = settings.get(
            "details", 
            "📋 **تفاصيل تدريب الـ VIP:**\nمتابعة يومية خاصة، جدول تمارين وتغذية مخصص، وتواصل مباشر."
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home")]]
        await query.edit_message_text(details_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return ConversationHandler.END

    elif data == "full_capacity":
        await query.answer("عذراً، لقد اكتملت المقاعد المتاحة حالياً (20 مشترك)، انتظر الدفعة القادمة!", show_alert=True)
        return ConversationHandler.END

    elif data == "start_subscription":
        vip_list = load_data(VIP_USERS_FILE, {})
        if len(vip_list) >= MAX_VIP_LIMIT:
            await query.answer("عذراً، اكتملت المقاعد!", show_alert=True)
            return await start(update, context)

        keyboard = [[InlineKeyboardButton("🔙 إلغاء والرجوع", callback_data="back_home")]]
        await query.edit_message_text(
            "💳 **طلب اشتراك VIP جديد:**\nأرسل اسم **بلدك** الحالي (مثلاً: مصر، السعودية...):",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return COUNTRY

    elif data == "contact_coach":
        keyboard = [[InlineKeyboardButton("🔙 إلغاء والرجوع", callback_data="back_home")]]
        await query.edit_message_text(
            "📩 **تواصل مباشر مع الكوتش:**\nاكتب رسالتك وسنحولها فوراً للإدارة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return WAITING_FOR_USER_MSG

    elif data.startswith("can_pay_"):
        await query.edit_message_text(
            "✅ **ممتاز!** لقد أكدت قدرتك على التحويل.\n📸 الآن قم بإرسال **(صورة إيصال التحويل / السكرين شوت)** لتأكيد الطلب نهائياً وإرساله للأدمن:",
            parse_mode="Markdown"
        )
        return SCREENSHOT

    elif data.startswith("cant_pay_"):
        target_uid = data.replace("cant_pay_", "")
        
        # الرد بالرسالة اللطيفة اللي طلبناها للمشترك
        await query.edit_message_text(
            "❌ للأسف لا يمكنك الاشتراك مع الكوتش أحمد إلا لو تستطيع التحويل على هذه الطرق، ننتظرك في المرات القادمة لو توفرت لديك وسيلة أخرى!",
            parse_mode="Markdown"
        )
        
        # إشعار الأدمن في الخلفية
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"ℹ️ المستخدم بالآيدي (`{target_uid}`) اعتذر عن إتمام الدفع لعدم توفر الطريقة لديه.",
                parse_mode="Markdown"
            )
        except:
            pass
        return ConversationHandler.END

    elif data == "open_admin_panel":
        if user_id == ADMIN_ID:
            vip_list = load_data(VIP_USERS_FILE, {})
            requests_list = load_data(REQUESTS_FILE, {})
            
            keyboard = [
                [InlineKeyboardButton(f"👥 إدارة المشتركين ({len(vip_list)}/{MAX_VIP_LIMIT})", callback_data="admin_list_vip")],
                [InlineKeyboardButton(f"🔔 الطلبات المعلقة ({len(requests_list)})", callback_data="admin_list_requests")],
                [InlineKeyboardButton("📢 إرسال رسالة للجميع", callback_data="admin_broadcast_info")],
                [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home")]
            ]
            await query.edit_message_text(
                "👨‍💻 **لوحة تحكم الأدمن الاحترافية:**\nاختر القسم المطلوب:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await query.answer("هذه لوحة التحكم الخاصة بالأدمن فقط ⛔", show_alert=True)
        return ConversationHandler.END

    elif data == "admin_list_vip":
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        vip_list = load_data(VIP_USERS_FILE, {})
        if not vip_list:
            keyboard = [[InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="open_admin_panel")]]
            await query.edit_message_text("لا توجد مشتركين في الـ VIP حالياً.", reply_markup=InlineKeyboardMarkup(keyboard))
            return ConversationHandler.END

        keyboard = []
        text = f"👑 **مشتركي الـ VIP ({len(vip_list)}/{MAX_VIP_LIMIT}):**\n\n"
        for uid_str, user_info in vip_list.items():
            name = user_info.get("name", "مستخدم")
            text += f"• {name} (ID: `{uid_str}`)\n"
            keyboard.append([InlineKeyboardButton(f"❌ إزالة: {name}", callback_data=f"remove_vip_{uid_str}")])

        keyboard.append([InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="open_admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return ConversationHandler.END

    elif data.startswith("remove_vip_"):
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        uid_to_remove = data.replace("remove_vip_", "")
        vip_list = load_data(VIP_USERS_FILE, {})
        if uid_to_remove in vip_list:
            vip_list.pop(uid_to_remove)
            save_data(VIP_USERS_FILE, vip_list)
            await query.answer("تم إزالة المشترك بنجاح!", show_alert=True)
        return await button_handler(update, context)

    elif data == "admin_list_requests":
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        requests_list = load_data(REQUESTS_FILE, {})
        if not requests_list:
            keyboard = [[InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="open_admin_panel")]]
            await query.edit_message_text("لا توجد طلبات اشتراك معلقة.", reply_markup=InlineKeyboardMarkup(keyboard))
            return ConversationHandler.END

        keyboard = []
        for uid_str, req in requests_list.items():
            name = req.get("name")
            country = req.get("country")
            keyboard.append([InlineKeyboardButton(f"👤 {name} ({country}) - ID: {uid_str}", callback_data=f"view_req_{uid_str}")])

        keyboard.append([InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="open_admin_panel")])
        await query.edit_message_text("🔔 **الطلبات المعلقة (اختر لإرسال طرق الدفع أو مراجعة الإيصال):**", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    elif data.startswith("view_req_"):
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        uid_str = data.replace("view_req_", "")
        requests_list = load_data(REQUESTS_FILE, {})
        if uid_str in requests_list:
            req = requests_list[uid_str]
            text = (
                "📋 **تفاصيل طلب المستخدم:**\n\n"
                f"👤 الاسم: {req['name']}\n"
                f"🔗 اليوزر: @{req['username']}\n"
                f"🆔 الآيدي: `{uid_str}`\n"
                f"🌍 الدولة: {req['country']}\n\n"
                f"💡 **لإرسال طرق الدفع له استخدم الأمر:**\n`/sendpay {uid_str} تفاصيل طرق الدفع هنا...`"
            )
            keyboard = []
            if "photo_id" in req:
                keyboard.append([InlineKeyboardButton("✅ موافقة وترقية لـ VIP", callback_data=f"accept_req_{uid_str}")])
                keyboard.append([InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_req_{uid_str}")])
            
            keyboard.append([InlineKeyboardButton("🔙 رجوع للطلبات", callback_data="open_admin_panel")])
            
            if "photo_id" in req:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=req["photo_id"],
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                await query.message.delete()
            else:
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return ConversationHandler.END

    elif data.startswith("accept_req_"):
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        uid_str = data.replace("accept_req_", "")
        requests_list = load_data(REQUESTS_FILE, {})
        if uid_str in requests_list:
            user_data = requests_list.pop(uid_str)
            save_data(REQUESTS_FILE, requests_list)

            vip_list = load_data(VIP_USERS_FILE, {})
            vip_list[uid_str] = user_data
            save_data(VIP_USERS_FILE, vip_list)

            await query.answer("✅ تمت الموافقة وتفعيل الاشتراك!", show_alert=True)
            try:
                await context.bot.send_message(
                    chat_id=int(uid_str),
                    text="🎉 **مبروك! تم قبول إيصال الدفع وتفعيل حسابك كـ VIP بنجاح.**",
                    parse_mode="Markdown"
                )
            except:
                pass
        return await button_handler(update, context)

    elif data.startswith("reject_req_"):
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        uid_str = data.replace("reject_req_", "")
        requests_list = load_data(REQUESTS_FILE, {})
        if uid_str in requests_list:
            requests_list.pop(uid_str)
            save_data(REQUESTS_FILE, requests_list)
            await query.answer("❌ تم رفض الطلب.", show_alert=True)
            try:
                await context.bot.send_message(
                    chat_id=int(uid_str),
                    text="عذراً، تم رفض إيصال الدفع من قبل الإدارة. تأكد من صحة التحويل وتواصل معنا.",
                )
            except:
                pass
        return await button_handler(update, context)

    elif data == "admin_broadcast_info":
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        keyboard = [[InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="open_admin_panel")]]
        await query.edit_message_text(
            "📢 **الإذاعة:** اكتب في الشات مباشرة:\n`/broadcast نص الرسالة`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    elif data == "back_home":
        await start(update, context)
        return ConversationHandler.END

# --- خطوات محادثة الاشتراك ---
async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    country = update.message.text.strip()
    user = update.effective_user

    request_info = {
        "name": user.first_name,
        "username": user.username if user.username else "لا يوجد",
        "country": country
    }

    requests_list = load_data(REQUESTS_FILE, {})
    requests_list[str(user.id)] = request_info
    save_data(REQUESTS_FILE, requests_list)

    keyboard = [[InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="back_home")]]
    await update.message.reply_text(
        "✅ **تم تسجيل بلدك بنجاح!**\n⏳ جارٍ إرسال طلبك للإدارة لتحديد وسائل الدفع المناسبة لك وإرسالها إليك قريباً.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    username_str = f"@{user.username}" if user.username else "لا يوجد"
    admin_notif = (
        "🚨 **طلب اشتراك VIP جديد (بانتظار تحديد طرق الدفع):**\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🔗 اليوزر: {username_str}\n"
        f"🆔 الآيدي: `{user.id}`\n"
        f"🌍 الدولة: {country}\n\n"
        f"💡 لإرسال طرق الدفع له استخدم الأمر:\n`/sendpay {user.id} اكتب طرق الدفع هنا...`"
    )
    keyboard_admin = [[InlineKeyboardButton("🔔 مراجعة الطلب من لوحة التحكم", callback_data="open_admin_panel")]]
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_notif,
            reply_markup=InlineKeyboardMarkup(keyboard_admin),
            parse_mode="Markdown"
        )
    except:
        pass

    return ConversationHandler.END

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    
    if not update.message.photo:
        await update.message.reply_text("⚠️ يرجى إرسال صورة إيصال التحويل كـ (صورة / سكرين شوت) وليس نصاً.")
        return SCREENSHOT

    photo_file_id = update.message.photo[-1].file_id

    requests_list = load_data(REQUESTS_FILE, {})
    uid_str = str(user.id)
    
    if uid_str in requests_list:
        requests_list[uid_str]["photo_id"] = photo_file_id
        save_data(REQUESTS_FILE, requests_list)

    keyboard = [[InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="back_home")]]
    await update.message.reply_text(
        "✅ **تم إرسال إيصال الدفع بنجاح!**\n⏳ جارٍ مراجعة الإيصال نهائياً من قبل الإدارة لتفعيل حسابك كـ VIP.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    req = requests_list.get(uid_str, {})
    username_str = f"@{user.username}" if user.username else "لا يوجد"
    admin_notif = (
        "🚨 **وصل إيصال تحويل جديد من مشترك أكد الدفع!**\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🔗 اليوزر: {username_str}\n"
        f"🆔 الآيدي: `{user.id}`\n"
        f"🌍 الدولة: {req.get('country', 'غير محدد')}"
    )
    keyboard_admin = [
        [InlineKeyboardButton("✅ موافقة وترقية لـ VIP", callback_data=f"accept_req_{uid_str}")],
        [InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_req_{uid_str}")],
        [InlineKeyboardButton("🔔 لوحة التحكم", callback_data="open_admin_panel")]
    ]
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=admin_notif,
            reply_markup=InlineKeyboardMarkup(keyboard_admin),
            parse_mode="Markdown"
        )
    except:
        pass

    return ConversationHandler.END

async def receive_coach_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    msg = update.message.text

    keyboard = [[InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="back_home")]]
    await update.message.reply_text("✅ تم إرسال رسالتك للكوتش بنجاح!", reply_markup=InlineKeyboardMarkup(keyboard))

    username_str = f"@{user.username}" if user.username else "لا يوجد"
    admin_text = (
        "📩 **رسالة جديدة من مستخدم:**\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🔗 اليوزر: {username_str}\n"
        f"🆔 الآيدي: `{user.id}`\n\n"
        f"💬 النص:\n{msg}\n\n"
        f"💡 للرد عليه:\n`/sendto {user.id} ردك هنا`"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except:
        pass
    return ConversationHandler.END

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("⚠️ استخدم الأمر هكذا:\n`/broadcast رسالتك`", parse_mode="Markdown")
        return

    text = " ".join(context.args)
    vip_list = load_data(VIP_USERS_FILE, {})
    
    success = 0
    for uid_str in vip_list.keys():
        try:
            await context.bot.send_message(chat_id=int(uid_str), text=f"📢 **إشعار VIP:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            pass

    await update.message.reply_text(f"✅ تم الإرسال إلى {success} مشترك VIP بنجاح.")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    sub_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^start_subscription$")],
        states={
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country), CallbackQueryHandler(button_handler, pattern="^back_home$")],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot), CallbackQueryHandler(button_handler, pattern="^back_home$")]
        },
        fallbacks=[]
    )

    coach_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^contact_coach$")],
        states={
            WAITING_FOR_USER_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_coach_msg), CallbackQueryHandler(button_handler, pattern="^back_home$")]
        },
        fallbacks=[]
    )

    application.add_handler(sub_conv)
    application.add_handler(coach_conv)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast_cmd))
    application.add_handler(CommandHandler("settext", set_text_cmd))
    application.add_handler(CommandHandler("sendto", send_to_user_cmd))
    application.add_handler(CommandHandler("sendpay", send_payment_methods_cmd))
    application.add_handler(CommandHandler("ban", ban_user_cmd))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("البوت يعمل بأعلى مستوى من الاحترافية ودورة الدفع الذكية... 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()