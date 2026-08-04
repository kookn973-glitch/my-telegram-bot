import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعداد السجل لمتابعة الأخطاء والتشغيل
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# توكن البوت الخاص بك
TOKEN = "8935530372:AAFoiz8kfSkbJ5MQ62rWwKyKFZVXn-1Lq8E"

# رسالة البداية عند إرسال /start
async def start(command_update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = command_update.effective_user
    welcome_text = (
        f"مرحباً بك {user.first_name} في بوت التحميل الشامل! 🚀\n\n"
        "فقط قم بإرسال رابط لأي فيديو من (تيك توك، إنستغرام، يوتيوب، فيسبوك، إلخ) "
        "وسأقوم بتحميله وإرساله إليك فوراً بدون علامة مائية إن وجدت!"
    )
    await command_update.message.reply_text(welcome_text)

# دالة استقبال الرابط وتحميل الفيديو من أي منصة وإرساله
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    # التأكد من أن الرسالة عبارة عن رابط يبدأ بـ http
    if not url.startswith("http"):
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    waiting_msg = await update.message.reply_text("⏳ جاري معالجة الرابط وتحميل الفيديو، قد يستغرق ذلك بضع ثوانٍ...")

    output_template = "downloaded_video.%(ext)s"
    
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'best', # اختيار أفضل جودة متاحة
        'noplaylist': True,
    }

    try:
        # تحميل الفيديو باستخدام yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # إرسال الفيديو للمستخدم
        await update.message.reply_video(video=open(filename, 'rb'))
        
        # حذف الفيديو من السيرفر بعد الإرسال لتوفير المساحة
        if os.path.exists(filename):
            os.remove(filename)
            
        # حذف رسالة الانتظار
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_msg.message_id)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ عذراً، حدث خطأ أثناء التحميل. تأكد من صحة الرابط أو جرب رابطاً آخر.")
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_msg.message_id)
        except:
            pass

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 جاري تشغيل بوت تليجرام الشامل...")
    application.run_polling()

if __name__ == "__main__":
    main()
