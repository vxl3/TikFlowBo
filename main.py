import os
import sqlite3
import telebot
import requests
from threading import Thread
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo

# ================= سيرفر ويب وهمي لإبقاء البوت شغالاً على Render =================
app = Flask('')

@app.route('/')
def home():
    return "البوت شغال بنجاح 24/7! 🚀"

def run_web_server():
    # Render يعطي البوت منفذ (Port) تلقائي، نسحبه هنا أو نستخدم 8080 كافتراضي
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= إعدادات البوت الأساسية =================
BOT_TOKEN = '8977626671:AAEGQ3GyRA-AFL2k1HBd63Vgd0m5WQ1bcY0'  # ⚠️ توكن البوت
CHANNELS_ID = '@RCOEt'                 # ✅ يوزر قناتك
ADMIN_ID = 7459127293                   # ⚠️ معرف حسابك (ID)
GROQ_API_KEY = "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"      # 🔑 مفتاح Groq API الخاص بك

bot = telebot.TeleBot(BOT_TOKEN)

# ================= إعداد قاعدة البيانات الدائمة =================
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id):
    try:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

def get_all_users():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

init_db()

last_audio_url = {}
search_results = {}

def get_tiktok_data(tiktok_url):
    try:
        api_url = f"https://www.tikwm.com/api/?url={tiktok_url}"
        response = requests.get(api_url).json()
        if response.get('code') == 0:
            return response['data']
        return None
    except Exception:
        return None

def is_subscribed(user_id):
    try:
        check = bot.get_chat_member(CHANNELS_ID, user_id)
        if check.status in ['left', 'kicked']:
            return False
        return True
    except Exception:
        return True

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    add_user(user_id)
    user_name = message.from_user.first_name
    
    welcome_text = f"""
🚀 <b>مرحباً بك في تيك فلو برو | TikFlow Pro</b>

أهلاً بك عزيزي <b>{user_name}</b> 💎
النسخة الذكية الأسرع لتحميل وتحليل محتوى TikTok بالذكاء الاصطناعي.

📥 <b>أرسل رابط الفيديو الآن وتجول في عالم الذكاء الاصطناعي!</b>
"""
    markup = InlineKeyboardMarkup()
    tiktok_url = "https://www.tiktok.com/@RCOE"
    channel_url = f"https://t.me/{CHANNELS_ID.replace('@','')}"
    markup.add(InlineKeyboardButton("🌟 تيك توك | RCOE", url=tiktok_url))
    markup.add(InlineKeyboardButton("📢 قناة البوت | RCOEt", url=channel_url))
    bot.reply_to(message, welcome_text, parse_mode="HTML", reply_markup=markup)

# [بقية الدوال مثل البحث، واستخراج النص، وصانع الهاشتاقات تبقى كما هي تماماً بدون تعديل]

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    user_id = message.from_user.id
    add_user(user_id)

    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 اشترك في القناة أولاً", url=f"https://t.me/{CHANNELS_ID.replace('@','')}"))
        bot.reply_to(message, "❌ عذراً عزيزي، يجب عليك الاشتراك في قناة البوت أولاً!", reply_markup=markup)
        return

    if "tiktok.com" in url:
        msg = bot.reply_to(message, "جاري معالجة الرابط وتحميل المحتوى... ⏳")
        data = get_tiktok_data(url)
        if data:
            try:
                caption_text = f"🎬: {data.get('title', 'فيديو تيك توك')}\n\n✨ تم التحميل بأعلى جودة Pro"
                if 'images' in data and data['images']:
                    media_group = []
                    for img in data['images'][:10]:
                        media_group.append(InputMediaPhoto(img))
                    bot.send_media_group(message.chat.id, media_group)
                    bot.delete_message(message.chat.id, msg.message_id)
                    return

                video_url = data.get('hdplay') or data.get('play')
                markup = InlineKeyboardMarkup()
                markup.row(InlineKeyboardButton("🎵 تحميل صوت الفيديو (MP3)", callback_data=f"audio_{user_id}"))
                markup.row(InlineKeyboardButton("🧠 استخراج النص + تلخيص ذكي", callback_data=f"transcribe_{user_id}"))
                markup.row(InlineKeyboardButton("🏷️ توليد هاشتاقات ذكية", callback_data=f"hashtags_{user_id}"))
                
                bot.send_video(message.chat.id, video_url, caption=caption_text, reply_markup=markup)
                bot.delete_message(message.chat.id, msg.message_id)
                last_audio_url[user_id] = data.get('music')
            except Exception:
                bot.edit_message_text("رابط التحميل المباشر:\n\n" + data.get('play'), message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("لم أتمكن من العثور على الفيديو.", message.chat.id, msg.message_id)

# ================= تشغيل البوت مع السيرفر =================
if __name__ == "__main__":
    # تشغيل سيرفر الويب الوهمي في Thread منفصل لكي لا يعطل البوت
    server_thread = Thread(target=run_web_server)
    server_thread.start()
    
    print("🔥 السيرفر الوهمي شغال، جاري تشغيل البوت السحابي...")
    bot.infinity_polling()
