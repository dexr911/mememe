import telebot
import requests
import re
import time
import os
import secrets
import cloudscraper
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

API_TOKEN = '8488920682:AAEp45yVtWWuVWEIj8eV2P07uwDkXWrNHwI'
bot = telebot.TeleBot(API_TOKEN)
PROXY_FILE = "valid.txt"

# قائمة المصادر (نفس الـ 30 مصدر التي اتفقنا عليها)
SOURCES = ["https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all"] 

# --- محرك إنستغرام المطور ---
class InstagramAPI:
    def __init__(self, proxy):
        # استخدام cloudscraper لتجاوز حماية "المرحلة 1"
        self.ses = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','mobile': False})
        self.ses.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        self.headers = {
            "X-IG-App-ID": "936619743392459",
            "X-ASBD-ID": "129663",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/emailsignup/"
        }

    def get_init_data(self):
        # الفحص الحقيقي: إذا لم يرد إنستا خلال 10 ثواني، يسقط البروكسي
        r = self.ses.get("https://www.instagram.com/accounts/emailsignup/", headers=self.headers, timeout=12)
        if r.status_code == 200:
            csrf = re.findall(r'csrf_token":"(.*?)"', r.text)[0]
            self.ses.headers.update({'X-CSRFToken': csrf})
            return True
        return False

# --- دالة فحص البروكسي (أصبحت دقيقة جداً جداً) ---
def verify_proxy_strict(proxy):
    try:
        # لا نقبل البروكسي إلا إذا استطاع فتح صفحة الإنشاء
        scraper = cloudscraper.create_scraper()
        r = scraper.get("https://www.instagram.com/accounts/emailsignup/", 
                        proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, 
                        timeout=6)
        if r.status_code == 200 and 'csrftoken' in r.text:
            return proxy, True
    except: pass
    return proxy, False

# --- الأوامر ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🚀 نظام Dexr المطور (نسخة CloudScraper).\nاسحب بروكسيات جديدة الآن لتبدأ.", 
                     reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add('🚀 إنشاء تلقائي كامل', '🔄 سحب وفحص 30 مصدر'))

@bot.message_handler(func=lambda m: m.text == '🔄 سحب وفحص 30 مصدر')
def handle_scrape(message):
    bot.send_message(message.chat.id, "🔍 جاري سحب البروكسيات وفحصها بصرامة...")
    # (كود السحب من المصادر هنا...)
    raw = ["201.62.82.4:8080"] # مجرد مثال
    working = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        results = list(ex.map(verify_proxy_strict, raw))
    
    with open(PROXY_FILE, "w") as f:
        for p, ok in results:
            if ok: 
                f.write(p + "\n")
                working.append(p)
    bot.send_message(message.chat.id, f"✅ تم حفظ {len(working)} بروكسي 'حقيقي' قادر على فتح إنستغرام.")

@bot.message_handler(func=lambda m: m.text == '🚀 إنشاء تلقائي كامل')
def run_creation(message):
    if not os.path.exists(PROXY_FILE) or os.stat(PROXY_FILE).st_size == 0:
        return bot.send_message(message.chat.id, "⚠️ الداتا فارغة!")

    with open(PROXY_FILE, "r") as f: proxies = f.readlines()
    prx = proxies[0].strip()
    
    bot.send_message(message.chat.id, f"⚙️ المرحلة 1: محاولة كسر الحماية عبر {prx}")
    api = InstagramAPI(prx)
    
    try:
        if api.get_init_data():
            bot.send_message(message.chat.id, "✅ انتقلنا للمرحلة 2! البروكسي نجح في فتح إنستغرام.")
            # هنا يكمل باقي الكود (الإيميل والكود)
        else:
            bot.send_message(message.chat.id, "❌ البروكسي لم يستجب لإنستغرام. جاري حذفه...")
            with open(PROXY_FILE, "w") as f: f.writelines(proxies[1:])
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ خطأ: {e}")

bot.polling()
