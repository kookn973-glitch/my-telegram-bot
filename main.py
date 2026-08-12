import os
import logging
import time
import re
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "8935530372:AAFoiz8kfSkbJ5MQ62rWwKyKFZVXn-1Lq8E"

# معرف قناتك العام (تأكد أن القناة عامة ولها معرف يبدأ بـ @)
CHANNEL_USERNAME = "@Wolves_Sudan" 

# ضع معرف تليجرام الخاص بك هنا بدون @ (مثال: myname)
DEVELOPER_USERNAME = "banda_sudan"

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            return True
        return False
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
        return False

def is_tiktok_url(url: str) -> bool:
    tiktok_patterns = [r"tiktok\.com", r"vt\.tiktok\.com", r"vm\.tiktok\.com"]
    return any(re.search(pattern, url) for pattern in tiktok_patterns)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    is_subscribed = await check_subscription(user.id, context)
    
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_sub")]
        ])
        await update.message.reply_text(
            f"مرحباً بك {user.first_name}.\n\n"
            "عذراً، يجب عليك الاشتراك في قناة البوت أولاً لتمكين الخدمة.\n\n"
            "يرجى الاشتراك ثم الضغط على زر التحقق أدناه.",
            reply_markup=keyboard
        )
        return

    welcome_text = (
        f"مرحباً بك {user.first_name}.\n\n"
        "هذا البوت مخصص لتحميل فيديوهات تيك توك.\n\n"
        "قم بإرسال رابط الفيديو للبدء."
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("قناة التحديثات", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"),
            InlineKeyboardButton("تواصل مع المطور", url=f"https://t.me/{DEVELOPER_USERNAME}")
        ]
    ])
    
    await update.message.reply_text(welcome_text, reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_sub":
        user_id = query.from_user.id
        is_subscribed = await check_subscription(user_id, context)
        
        if is_subscribed:
            try:
                await query.message.delete()
            except:
                pass
                
            welcome_text = (
                "تم التحقق من الاشتراك بنجاح.\n\n"
                "يمكنك الآن إرسال رابط تيك توك للتحميل."
            )
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("قناة التحديثات", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"),
                    InlineKeyboardButton("تواصل مع المطور", url=f"https://t.me/{DEVELOPER_USERNAME}")
                ]
            ])
            await query.message.reply_text(welcome_text, reply_markup=keyboard)
        else:
            await query.answer("لم تقم بالاشتراك في القناة بعد.", show_alert=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_sub")]
        ])
        await update.message.reply_text(
            "عذراً، يجب عليك الاشتراك في قناة البوت أولاً.",
            reply_markup=keyboard
        )
        return

    url = update.message.text.strip()
    
    if not url.startswith("http"):
        await update.message.reply_text("يرجى إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    if not is_tiktok_url(url):
        await update.message.reply_text("عذراً، هذا البوت مخصص لفيديوهات تيك توك فقط.")
        return

    status_msg = await update.message.reply_text("جاري تحميل الفيديو...")

    output_template = "tiktok_video_%(id)s.%(ext)s"
    
    last_update_time = [0]
    def hook(d):
        if d['status'] == 'downloading':
            current_time = time.time()
            if current_time - last_update_time[0] > 3:
                try:
                    p = d.get('_percent_str', '0%').strip()
                    speed = d.get('_speed_str', 'N/A').strip()
                    eta = d.get('_eta_str', 'N/A').strip()
                    text = f"جاري التحميل...\n\nالنسبة: {p}\nالسرعة: {speed}\nالوقت المتبقي: {eta}"
                    context.application.create_task(
                        context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=text)
                    )
                    last_update_time[0] = current_time
                except Exception:
                    pass

    ydl_opts = {'outtmpl': output_template, 'format': 'best', 'noplaylist': True, 'progress_hooks': [hook]}

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text="جاري إرسال الفيديو...")

        with open(filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file)
        
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("حدث خطأ أثناء تحميل الفيديو.")
        try: await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
        except: pass

    if filename and os.path.exists(filename):
        try: os.remove(filename)
        except: pass

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("جاري تشغيل البوت...")
    application.run_polling()

if __name__ == "__main__":
    main()
