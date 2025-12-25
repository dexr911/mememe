import telebot
import requests
import re
import time
import os
import secrets
import cloudscraper
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

# --- إعدادات Dexr ---
API_TOKEN = '8488920682:AAEp45yVtWWuVWEIj8eV2P07uwDkXWrNHwI'
bot = telebot.TeleBot(API_TOKEN)
PROXY_FILE = "valid.txt"

# --- 1. قائمة المصادر الـ 30 ---
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

def get_enc_password(pwd):
    return f"#PWD_INSTAGRAM_BROWSER:10:{int(time.time())}:{pwd}"

def verify_proxy_strict(proxy):
    try:
        scraper = cloudscraper.create_scraper()
        r = scraper.get("https://www.instagram.com/accounts/emailsignup/", 
                        proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, 
                        timeout=5)
        if r.status_code == 200 and 'csrftoken' in r.text:
            return proxy, True
    except: pass
    return proxy, False

class InstagramAPI:
    def __init__(self, proxy):
        self.ses = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','mobile': False})
        self.ses.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        self.headers = {
            "X-IG-App-ID": "936619743392459",
            "X-ASBD-ID": "129663",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/emailsignup/"
        }

    def get_init_data(self):
        try:
            r = self.ses.get("https://www.instagram.com/accounts/emailsignup/", headers=self.headers, timeout=10)
            csrf = re.findall(r'csrf_token":"(.*?)"', r.text)[0]
            self.ses.headers.update({'X-CSRFToken': csrf})
            return True
        except: return False

    def send_code(self, email):
        try:
            url = "https://www.instagram.com/api/v1/web/accounts/send_signup_email_code_ajax/"
            return self.ses.post(url, data={'email': email}, headers=self.headers, timeout=10).json()
        except: return {}

    def create_final(self, email, otp, user, pwd):
        try:
            url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"
            data = {
                'email': email, 'enc_password': get_enc_password(pwd),
                'username': user, 'email_otp': otp, 'first_name': 'Dexr Bot',
                'month': '1', 'day': '1', 'year': '1999',
                'client_id': secrets.token_hex(16).upper(),
                'seamless_login_enabled': '1'
            }
            return self.ses.post(url, data=data, headers=self.headers, timeout=10).json()
        except: return {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🚀 إنشاء تلقائي كامل', '🔄 سحب وفحص 30 مصدر')
    bot.send_message(message.chat.id, "✅ تم تحديث النظام لتخطي أخطاء البروكسي.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🔄 سحب وفحص 30 مصدر')
def handle_scrape(message):
    bot.send_message(message.chat.id, "🔎 جاري سحب البروكسيات...")
    all_raw = []
    for s in SOURCES:
        try: all_raw.extend(re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', requests.get(s, timeout=3).text))
        except: continue
    
    unique = list(set(all_raw))
    bot.send_message(message.chat.id, f"📥 تم سحب {len(unique)}. جاري الفحص...")
    
    working = []
    with ThreadPoolExecutor(max_workers=30) as ex:
        results = list(ex.map(verify_proxy_strict, unique[:300]))
    
    with open(PROXY_FILE, "w") as f:
        for p, ok in results:
            if ok:
                f.write(p + "\n")
                working.append(p)
    
    if working:
        bot.send_message(message.chat.id, f"✅ تم العثور على {len(working)} بروكسي شغال.")
    else:
        bot.send_message(message.chat.id, "❌ لم ينجح أي بروكسي. جرب السحب مرة أخرى.")

@bot.message_handler(func=lambda m: m.text == '🚀 إنشاء تلقائي كامل')
def run_creation(message):
    if not os.path.exists(PROXY_FILE) or os.stat(PROXY_FILE).st_size == 0:
        return bot.send_message(message.chat.id, "⚠️ الداتا فارغة!")
    
    with open(PROXY_FILE, "r") as f: proxies = f.readlines()
    prx = proxies[0].strip()
    
    bot.send_message(message.chat.id, f"⚙️ محاولة الاتصال عبر: {prx}")
    api = InstagramAPI(prx)
    
    if api.get_init_data():
        bot.send_message(message.chat.id, "✅ البروكسي شغال! جاري طلب الكود...")
        # (بقية كود الإيميل والإنشاء هنا...)
    else:
        bot.send_message(message.chat.id, "❌ البروكسي ضعيف أو محظور. جاري الانتقال للبروكسي التالي...")
        with open(PROXY_FILE, "w") as f: f.writelines(proxies[1:])

bot.polling()
