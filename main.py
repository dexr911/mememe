import telebot
import requests
import re
import time
import os
import secrets
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

# --- إعدادات Dexr ---
API_TOKEN = '8488920682:AAEp45yVtWWuVWEIj8eV2P07uwDkXWrNHwI'
bot = telebot.TeleBot(API_TOKEN)
PROXY_FILE = "valid.txt"
IG_APP_ID = "936619743392459"

# --- 1. قائمة الـ 30 مصدراً لسحب البروكسيات ---
SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/rooster127/proxylist/main/proxylist.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://api.openproxylist.xyz/http.txt",
    "https://proxyspace.pro/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/Free_Proxy_List/master/http.txt",
    "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list.txt",
    "https://raw.githubusercontent.com/officialputuid/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_list.txt",
    "https://raw.githubusercontent.com/VolkanSah/ProxyList/master/http.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
    "https://raw.githubusercontent.com/RX4096/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/saisuiu/Lion_proxy_list/main/all.txt",
    "https://raw.githubusercontent.com/vakhov/free-proxy-list/master/proxies/http.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
    "https://raw.githubusercontent.com/Zispanos/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/prx7/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/Andrey_Onze/Proxy_List/main/http.txt",
    "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
    "https://www.proxyscan.io/download?type=http",
    "https://www.proxy-list.download/api/v1/get?type=http"
]

# --- 2. دالات التشفير والفحص الحقيقي ---
def get_enc_password(pwd):
    return f"#PWD_INSTAGRAM_BROWSER:10:{int(time.time())}:{pwd}"

def verify_proxy(proxy):
    try:
        r = requests.get("https://www.instagram.com/accounts/emailsignup/", 
                         proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, 
                         timeout=8, headers={'User-Agent': generate_user_agent()})
        if 'csrftoken' in r.text or 'csrftoken' in r.cookies.get_dict():
            return proxy, True
    except: pass
    return proxy, False

# --- 3. دالات إنستغرام (تجميع ملفات Dexr) ---
class InstagramAPI:
    def __init__(self, proxy):
        self.ses = requests.Session()
        self.ses.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        self.headers = {
            "X-IG-App-ID": IG_APP_ID,
            "X-ASBD-ID": "198387",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": generate_user_agent(),
            "Referer": "https://www.instagram.com/accounts/emailsignup/"
        }

    def get_init_data(self):
        r = self.ses.get("https://www.instagram.com/accounts/emailsignup/", headers=self.headers)
        csrf = re.findall(r'csrf_token":"(.*?)"', r.text)[0]
        self.ses.headers.update({'X-CSRFToken': csrf})
        return csrf

    def send_code(self, email):
        url = "https://www.instagram.com/api/v1/web/accounts/send_signup_email_code_ajax/"
        return self.ses.post(url, data={'email': email}, headers=self.headers).json()

    def create_final(self, email, otp, user, pwd):
        url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"
        data = {
            'email': email, 'enc_password': get_enc_password(pwd),
            'username': user, 'email_otp': otp, 'first_name': 'Dexr Bot',
            'month': '1', 'day': '1', 'year': '1999', 'opt_into_one_tap': 'false'
        }
        return self.ses.post(url, data=data, headers=self.headers).json()

# --- 4. محرك الإيميل المؤقت ---
def get_temp_email():
    return requests.get("https://www.1secmail.com/api/v1/action/?action=genEmailAddresses&count=1").json()[0]

def get_temp_otp(email):
    u, d = email.split('@')
    for _ in range(15):
        time.sleep(6)
        msgs = requests.get(f"https://www.1secmail.com/api/v1/action/?action=getMessages&login={u}&domain={d}").json()
        for m in msgs:
            c = requests.get(f"https://www.1secmail.com/api/v1/action/?action=readMessage&login={u}&domain={d}&id={m['id']}").json()
            code = re.findall(r'\b\d{6}\b', c['body'])
            if code: return code[0]
    return None

# --- واجهة البوت والأوامر ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🚀 إنشاء تلقائي كامل', '🔄 سحب وفحص 30 مصدر')
    bot.send_message(message.chat.id, "🔥 تم دمج 30 مصدر بروكسي مع دالاتك بنجاح!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🔄 سحب وفحص 30 مصدر')
def handle_scrape(message):
    bot.send_message(message.chat.id, "🔎 جاري سحب البروكسيات من 30 موقع... انتظر قليلاً.")
    all_proxies = []
    for s in SOURCES:
        try: all_proxies.extend(re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', requests.get(s, timeout=5).text))
        except: continue
    
    raw = list(set(all_proxies))
    bot.send_message(message.chat.id, f"📥 تم سحب {len(raw)}. جاري فحص الشغال لإنستغرام بصمت...")
    
    working = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(verify_proxy, raw[:400])) # فحص عينة قوية
    
    with open(PROXY_FILE, "a") as f:
        for p, ok in results:
            if ok:
                f.write(p + "\n")
                working.append(p)
    
    if working:
        with open("working_proxies.txt", "w") as f: f.write("\n".join(working))
        with open("working_proxies.txt", "rb") as doc:
            bot.send_document(message.chat.id, doc, caption=f"✅ تم العثور على {len(working)} بروكسي شغالة وتم تخزينها في الداتا.")
        os.remove("working_proxies.txt")
    else: bot.send_message(message.chat.id, "❌ لم ينجح أي بروكسي في الفحص.")

@bot.message_handler(func=lambda m: m.text == '🚀 إنشاء تلقائي كامل')
def process_creation(message):
    if not os.path.exists(PROXY_FILE) or os.stat(PROXY_FILE).st_size == 0:
        return bot.send_message(message.chat.id, "⚠️ الداتا فارغة! اسحب بروكسيات أولاً.")
    
    with open(PROXY_FILE, "r") as f: proxies = f.readlines()
    prx = proxies[0].strip()
    
    email = get_temp_email()
    user = f"dexr_{secrets.token_hex(3)}"
    pwd = f"Dexr_{secrets.token_hex(4)}!"
    
    bot.send_message(message.chat.id, f"🛠️ استخدام بروكسي: {prx}\n📧 إيميل: {email}")
    
    api = InstagramAPI(prx)
    try:
        api.get_init_data()
        if api.send_code(email).get('email_sent'):
            bot.send_message(message.chat.id, "⏳ جاري انتظار الكود...")
            otp = get_temp_otp(email)
            if otp:
                res = api.create_final(email, otp, user, pwd)
                bot.send_message(message.chat.id, f"🎉 تم الإنشاء بنجاح!\n👤 يوزر: {user}\n🔑 باسوورد: {pwd}\n📦 الرد: {res}")
                # حذف البروكسي المستخدم لضمان التجديد
                with open(PROXY_FILE, "w") as f: f.writelines(proxies[1:])
            else: bot.send_message(message.chat.id, "❌ لم يصل الكود.")
        else: bot.send_message(message.chat.id, "❌ رفض إنستا إرسال الكود لهذا البروكسي.")
    except Exception as e: bot.send_message(message.chat.id, f"❌ خطأ: {e}")

bot.polling()
