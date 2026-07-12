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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= إعدادات البوت الأساسية =================
BOT_TOKEN = '8977626671:AAEGQ3GyRA-AFL2k1HBd63Vgd0m5WQ1bcY0'  # توكن البوت الخاص بك
CHANNELS_ID = '@RCOEt'                 # يوزر قناتك
ADMIN_ID = 7459127293                   # معرف حسابك (ID)
GROQ_API_KEY = "Gsk_t0MBk6kcG1KP5MVPDbRIWGdyb3FY4euPvAtrlma90CyhYZ83c1qP"  # مفتاح Groq الخاص بك

bot = telebot.TeleBot(BOT_TOKEN)

# 🔥 الحل النهائي لمشكلة خطأ 409 (Conflict): إجبار تليجرام على تصفير أي اتصال قديم معلق
try:
    bot.remove_webhook()
except Exception as e:
    print(f"Webhook removal skip: {e}")

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

# دالة جلب البيانات من الـ API بدقة HD
def get_tiktok_data(tiktok_url):
    try:
        api_url = f"https://www.tikwm.com/api/?url={tiktok_url}"
        response = requests.get(api_url).json()
        if response.get('code') == 0:
            return response['data']
        return None
    except Exception:
        return None

# دالة التحقق من الاشتراك الإجباري
def is_subscribed(user_id):
    try:
        check = bot.get_chat_member(CHANNELS_ID, user_id)
        if check.status in ['left', 'kicked']:
            return False
        return True
    except Exception:
        return True

# رسالة الترحيب
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

# ================= استقبال ضغطات الأزرار (الإصدار المحصن والمصلح) =================
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    data_parts = call.data.split("|")
    action = data_parts[0]
    
    # التحقق إذا كانت البيانات تحتوي على الرابط المباشر لمنع فقدان الذاكرة
    if len(data_parts) < 2:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية هذه الأزرار القديمة، أرسل الرابط مجدداً.", show_alert=True)
        return
        
    audio_url = data_parts[1]

    if action == "audio":
        bot.answer_callback_query(call.id, "جاري إرسال الـ MP3... 🎧")
        try:
            bot.send_audio(chat_id, audio_url, caption="🎵 الصوت الأصلي المستخرج بدون حقوق")
        except Exception:
            bot.send_message(chat_id, "❌ فشل إرسال الصوت، قد يكون الرابط منتهي الصلاحية من سيرفرات تيك توك.")

    elif action == "transcribe":
        bot.answer_callback_query(call.id, "جاري بدء المعالجة والتحليل... 🧠⚙️")
        status_msg = bot.send_message(chat_id, "⏳ جاري تفريغ الصوت وتحليله سيكولوجياً عبر السحابة الذكية، انتظر ثوانٍ...")
        temp_mp3 = f"temp_{chat_id}.mp3"
        
        try:
            audio_data = requests.get(audio_url).content
            with open(temp_mp3, 'wb') as f:
                f.write(audio_data)
                
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            
            with open(temp_mp3, "rb") as file:
                files = {"file": (temp_mp3, file, "audio/mp3")}
                data = {"model": "whisper-large-v3", "language": "ar"}
                response = requests.post(url, headers=headers, files=files, data=data).json()
                
            extracted_text = response.get("text", "")
            
            if extracted_text:
                llm_url = "https://api.groq.com/openai/v1/chat/completions"
                llm_data = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "أنت خبير محترف في علم النفس الاجتماعي وتحليل المحتوى وصناعة الفيديوهات القصيرة الغامضة والذكية. قم بقراءة النص العربي المفرغ من مقطع فيديو، ثم أخرج لنا بشكل منظم باللغة العربية: 1- الفكرة العامة العميقة للمقطع، 2- الدرس النفسي أو المستفاد، 3- 3 نصائح عملية أو تطبيقية للمشاهد بناءً على الكلام. اجعل الأسلوب غامضاً ومثيراً للاهتمام وجذاباً جداً وقصيراً."},
                        {"role": "user", "content": extracted_text}
                    ]
                }
                llm_response = requests.post(llm_url, headers=headers, json=llm_data).json()
                ai_analysis = llm_response['choices'][0]['message']['content']
                
                success_text = f"📝 <b>التفريغ الحرفي للصوت:</b>\n\n<code>{extracted_text}</code>\n\n"
                success_text += f"🧠 <b>التحليل والملخص السيكولوجي الذكي:</b>\n\n{ai_analysis}"
                
                bot.edit_message_text(success_text, chat_id, status_msg.message_id, parse_mode="HTML")
            else:
                bot.edit_message_text("❌ تعذر تفريغ المقطع، يرجى التحقق من توكن Groq API.", chat_id, status_msg.message_id)
            
        except Exception as e:
            bot.edit_message_text("❌ واجهنا خطأ أثناء التحليل السحابي. تأكد من تفعيل وتغيير مفتاح Groq الخاص بك.", chat_id, status_msg.message_id)
        finally:
            if os.path.exists(temp_mp3): 
                os.remove(temp_mp3)

    elif action == "hashtags":
        bot.answer_callback_query(call.id, "جاري دراسة خوارزميات الهاشتاقات... 🏷️")
        status_msg = bot.send_message(chat_id, "⏳ جاري توليد أنسب الهاشتاقات لرفع المشاهدات...")
        temp_mp3 = f"temp_hash_{chat_id}.mp3"
        
        try:
            audio_data = requests.get(audio_url).content
            with open(temp_mp3, 'wb') as f:
                f.write(audio_data)
                
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            
            with open(temp_mp3, "rb") as file:
                files = {"file": (temp_mp3, file, "audio/mp3")}
                data = {"model": "whisper-large-v3", "language": "ar"}
                response = requests.post(url, headers=headers, files=files, data=data).json()
                
            extracted_text = response.get("text", "")
            
            if extracted_text:
                llm_url = "https://api.groq.com/openai/v1/chat/completions"
                llm_data = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "بناءً على النص المفرغ من فيديو تيك توك، قم بتوليد واقتراح 7 إلى 10 هاشتاقات قوية ومستهدفة جداً لرفع مشاهدات الفيديو على تيك توك ومناسبة لخوارزمياته، واجعل بعضها عاماً مثل #fyp والبعض الآخر مخصصاً جداً لمفهوم النص (مثال: إذا كان النص عن علم النفس ضع #علم_نفس #ذكاء_اجتماعي وهكذا). اطبع الهاشتاقات فقط وبشكل منسق وسطر واحد ليتمكن المستخدم من نسخها فوراً."},
                        {"role": "user", "content": extracted_text}
                    ]
                }
                llm_response = requests.post(llm_url, headers=headers, json=llm_data).json()
                generated_hashtags = llm_response['choices'][0]['message']['content']
                
                hash_text = f"🏷️ <b>أقوى الهاشتاقات المقترحة للفيديو (اضغط للنسخ الفوري):</b>\n\n<code>{generated_hashtags}</code>"
                bot.edit_message_text(hash_text, chat_id, status_msg.message_id, parse_mode="HTML")
            else:
                bot.edit_message_text("❌ تعذر توليد الهاشتاقات لعدم وجود كلمات منطوقة كافية بالمقطع.", chat_id, status_msg.message_id)
                
        except Exception as e:
            bot.edit_message_text("❌ حدث خطأ في النظام السحابي للهاشتاقات.", chat_id, status_msg.message_id)
        finally:
            if os.path.exists(temp_mp3): 
                os.remove(temp_mp3)

# معالجة الروابط المباشرة
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
                music_url = data.get('music')
                
                # تمرير رابط الصوت في الـ callback لحماية عمل الأزرار من التصفير السحابي
                markup = InlineKeyboardMarkup()
                markup.row(InlineKeyboardButton("🎵 تحميل صوت الفيديو (MP3)", callback_data=f"audio|{music_url}"))
                markup.row(InlineKeyboardButton("🧠 استخراج النص + تلخيص ذكي", callback_data=f"transcribe|{music_url}"))
                markup.row(InlineKeyboardButton("🏷️ توليد هاشتاقات ذكية", callback_data=f"hashtags|{music_url}"))
                
                bot.send_video(message.chat.id, video_url, caption=caption_text, reply_markup=markup)
                bot.delete_message(message.chat.id, msg.message_id)
                
            except Exception:
                bot.edit_message_text("رابط التحميل المباشر:\n\n" + data.get('play'), message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("لم أتمكن من العثور على الفيديو.", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "الرجاء إرسال رابط تيك توك صحيح.")

# تشغيل البوت
if __name__ == "__main__":
    server_thread = Thread(target=run_web_server)
    server_thread.start()
    print("🔥 تم إطلاق النسخة المحصنة المحدثة بمفتاحك الحقيقي...")
    bot.infinity_polling()
