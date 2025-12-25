import telebot
import requests
import re
import time
import os
import secrets
import cloudscraper
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

# --- إعدادات البوت ---
API_TOKEN = '8488920682:AAEp45yVtWWuVWEIj8eV2P07uwDkXWrNHwI'
bot = telebot.TeleBot(API_TOKEN)
PROXY_FILE = "valid.txt"
IG_APP_ID = "936619743392459"

# --- 1. قائمة الـ 30 مصدر لسحب البروكسيات ---
SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/rooster127/proxylist/main/proxylist.txt",
    "https://api.openproxylist.xyz/http.txt",
    "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
    "https://www.proxyscan.io/download?type=http",
    "https://raw.githubusercontent.com/officialputuid/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_list.txt",
    "https://raw.githubusercontent.com/Zaeem20/Free_Proxy_List/master/http.txt",
    "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list.txt",
    "https://raw.githubusercontent.com/VolkanSah/ProxyList/master/http.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
    "https://raw.githubusercontent.com/RX4096/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/vakhov/free-proxy-list/master/proxies/http.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
    "https://raw.githubusercontent.com/Zispanos/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/prx7/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/Andrey_Onze/Proxy_List/main/http.txt",
    "https://proxyspace.pro/http.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000",
    "https://alexa.lr22.com/http.txt",
    "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt"
]

# --- 2. دالات التشفير وفحص البروكسي الصارم ---
def get_enc_password(pwd):
    return f"#PWD_INSTAGRAM_BROWSER:10:{int(time.time())}:{pwd}"

def verify_proxy_strict(proxy):
    try:
        scraper = cloudscraper.create_scraper()
        r = scraper.get("https://www.instagram.com/accounts/emailsignup/", 
                        proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, 
                        timeout=7)
        if r.status_code == 200 and 'csrftoken' in r.text:
            return proxy, True
    except: pass
    return proxy, False

# --- 3. محرك إنستغرام (تجميع دالات Dexr) ---
class InstagramAPI:
    def __init__(self, proxy):
        self.ses = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','mobile': False})
        self.ses.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        self.headers = {
            "X-IG-App-ID": IG_APP_ID,
            "X-ASBD-ID": "129663",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": generate_user_agent(),
            "Referer": "https://www.instagram.com/accounts/emailsignup/"
        }

    def get_init_data(self):
        r = self.ses.get("https://www.instagram.com/accounts/emailsignup/", headers=self.headers, timeout=12)
        csrf = re.findall(r'csrf_token":"(.*?)"', r.text)[0]
        self.ses.headers.update({'X-CSRFToken': csrf})
        return True

    def send_code(self, email):
        url = "https://www.instagram.com/api/v1/web/accounts/send_signup_email_code_ajax/"
        return self.ses.post(url, data={'email': email}, headers=self.headers).json()

    def create_final(self, email, otp, user, pwd):
        url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"
        time.sleep(2)
        data = {
            'email': email, 'enc_password': get_enc_password(pwd),
            'username': user, 'email_otp': otp, 'first_name': 'Dexr Bot',
            'month': '1', 'day': '1', 'year': '1999',
            'client_id': secrets.token_hex(16).upper(),
            'seamless_login_enabled': '1', 'opt_into_one_tap': 'false'
        }
        csrf = self.ses.cookies.get_dict().get('csrftoken', self.ses.headers.get('X-CSRFToken'))
        self.ses.headers.update({'X-CSRFToken': csrf})
        return self.ses.post(url, data=data, headers=self.headers).json()

# --- 4. محرك الإيميل المؤقت ---
def get_temp_email():
    return requests.get("https://www.1secmail.com/api/v1/action/?action=genEmailAddresses&count=1").json()[0]

def get_temp_otp(email):
    u, d = email.split('@')
    for _ in range(20):
        time.sleep(5)
        msgs = requests.get(f"https://www.1secmail.com/api/v1/action/?action=getMessages&login={u}&domain={d}").json()
        for m in msgs:
            c = requests.get(f"https://www.1secmail.com/api/v1/action/?action=readMessage&login={u}&domain={d}&id={m['id']}").json()
            otp = re.findall(r'\b\d{6}\b', c['body'])
            if otp: return otp[0]
    return None

# --- واجهة التلجرام ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🚀 إنشاء تلقائي كامل', '🔄 سحب وفحص 30 مصدر')
    bot.send_message(message.chat.id, "🔥 نظام Dexr المتكامل (CloudScraper Version)\nجاهز للعمل الحقيقي الآن.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🔄 سحب وفحص 30 مصدر')
def handle_scrape(message):
    bot.send_message(message.chat.id, "🔎 جاري السحب من 30 مصدر وفحص الشغال حقيقياً...")
    all_raw = []
    for s in SOURCES:
        try: all_raw.extend(re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', requests.get(s, timeout=5).text))
        except: continue
    
    unique = list(set(all_raw))
    bot.send_message(message.chat.id, f"📥 تم سحب {len(unique)}. جاري فحص أول 400 بروكسي...")
    
    working = []
    with ThreadPoolExecutor(max_workers=35) as ex:
        results = list(ex.map(verify_proxy_strict, unique[:400]))
    
    with open(PROXY_FILE, "a") as f:
        for p, ok in results:
            if ok:
                f.write(p + "\n")
                working.append(p)
    
    if working:
        with open("dexr_valid.txt", "w") as f: f.write("\n".join(working))
        with open("dexr_valid.txt", "rb") as doc:
            bot.send_document(message.chat.id, doc, caption=f"✅ اكتمل الفحص!\n✔️ شغال (Instagram Ready): {len(working)}")
        os.remove("dexr_valid.txt")
    else:
        bot.send_message(message.chat.id, "❌ لم ينجح أي بروكسي في تجاوز حماية إنستغرام حالياً.")

@bot.message_handler(func=lambda m: m.text == '🚀 إنشاء تلقائي كامل')
def run_creation(message):
    if not os.path.exists(PROXY_FILE) or os.stat(PROXY_FILE).st_size == 0:
        return bot.send_message(message.chat.id, "⚠️ الداتا فارغة! اسحب بروكسيات أولاً.")
    
    with open(PROXY_FILE, "r") as f: proxies = f.readlines()
    prx = proxies[0].strip()
    
    bot.send_message(message.chat.id, f"⚙️ المرحلة 1: محاولة اختراق الحماية عبر {prx}")
    api = InstagramAPI(prx)
    
    try:
        if api.get_init_data():
            email = get_temp_email()
            bot.send_message(message.chat.id, f"✅ المرحلة 2: البروكسي شغال! إيميل: {email}")
            if api.send_code(email).get('email_sent'):
                bot.send_message(message.chat.id, "📨 المرحلة 3: تم طلب الكود. بانتظار وصوله...")
                otp = get_temp_otp(email)
                if otp:
                    user = f"dexr_{secrets.token_hex(3)}"
                    pwd = f"Dexr_{secrets.token_hex(4)}!"
                    res = api.create_final(email, otp, user, pwd)
                    bot.send_message(message.chat.id, f"🎉 تم الإنشاء بنجاح!\n👤 يوزر: {user}\n🔑 باسوورد: {pwd}\n📦 الرد: {res}")
                    with open(PROXY_FILE, "w") as f: f.writelines(proxies[1:])
                else: bot.send_message(message.chat.id, "❌ لم يصل الكود.")
            else: bot.send_message(message.chat.id, "❌ رفض إنستغرام إرسال الكود لهذا البروكسي.")
        else: bot.send_message(message.chat.id, "❌ البروكسي فشل في 'المرحلة 1'. جاري حذفه...")
    except Exception as e: bot.send_message(message.chat.id, f"⚠️ خطأ تقني: {e}")

bot.polling()
