import os
import logging
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# إعداد السجل لمتابعة الأخطاء والتشغيل
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# توكن البوت الخاص بك
TOKEN = "8935530372:AAFoiz8kfSkbJ5MQ62rWwKyKFZVXn-1Lq8E"

# دالة رسالة البداية مع الأزرار الشفافة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"مرحباً بك {user.first_name} في بوت التحميل الشامل! 🚀\n\n"
        "الرجاء اختيار المنصة التي تريد التحميل منها، أو قم بإرسال الرابط مباشرة:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 تيك توك", callback_data="platform_tiktok"),
            InlineKeyboardButton("👻 سناب شات", callback_data="platform_snapchat")
        ],
        [
            InlineKeyboardButton("📸 إنستغرام", callback_data="platform_instagram"),
            InlineKeyboardButton("📘 فيسبوك", callback_data="platform_facebook")
        ],
        [
            InlineKeyboardButton("📺 يوتيوب", callback_data="platform_youtube")
        ]
    ])
    
    await update.message.reply_text(welcome_text, reply_markup=keyboard)

# دالة التعامل مع ضغط الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    platform_names = {
        "platform_tiktok": "تيك توك",
        "platform_snapchat": "سناب شات",
        "platform_instagram": "إنستغرام",
        "platform_facebook": "فيسبوك",
        "platform_youtube": "يوتيوب"
    }
    
    selected = platform_names.get(query.data, "المنصة المطلوبة")
    await query.message.reply_text(f"✅ تم اختيار: **{selected}**.\nالآن قم بإرسال الرابط لنبدأ التحميل فوراً 📥")

# دالة استقبال الرابط وتحديث نسبة التحميل وإرسال الفيديو
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http"):
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    status_msg = await update.message.reply_text("⏳ جاري بدء التحميل...")

    output_template = "downloaded_video_%(id)s.%(ext)s"
    
    last_update_time = [0]
    def hook(d):
        if d['status'] == 'downloading':
            current_time = time.time()
            if current_time - last_update_time[0] > 3:
                try:
                    p = d.get('_percent_str', '0%').strip()
                    speed = d.get('_speed_str', 'N/A').strip()
                    eta = d.get('_eta_str', 'N/A').strip()
                    
                    text = f"📥 **جاري التحميل...**\n\n📊 النسبة: `{p}`\n⚡ السرعة: `{speed}`\n⏱️ الوقت المتبقي: `{eta}`"
                    
                    context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=status_msg.message_id,
                        text=text,
                        parse_mode="Markdown"
                    )
                    last_update_time[0] = current_time
                except Exception:
                    pass

    # خيارات مخصصة لتحسين الجودة وتجاوز الحقوق قدر الإمكان
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'best',
        'noplaylist': True,
        'progress_hooks': [hook],
        'extractor_args': {
            'snapchat': {'format': 'video'},
            'instagram': {'format': 'video'},
            'tiktok': {'api_hostname': 'api16-normal-c-useast1a.tiktokv.com'}
        }
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text="📤 جاري رفع الفيديو وإرساله..."
        )

        with open(filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file)
        
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ عذراً، حدث خطأ أثناء التحميل. تأكد من صحة الرابط أو جرب رابطاً آخر.")
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
        except:
            pass

    if filename and os.path.exists(filename):
        try:
            os.remove(filename)
        except:
            pass

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 جاري تشغيل بوت تليجرام الشامل...")
    application.run_polling()

if __name__ == "__main__":
    main()
