import telebot
import requests
import re
import time
import os
import secrets
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

# --- إعدادات البوت ---
API_TOKEN = '8488920682:AAEp45yVtWWuVWEIj8eV2P07uwDkXWrNHwI'
bot = telebot.TeleBot(API_TOKEN)
PROXY_FILE = "valid.txt"

# --- 1. دالة التشفير (التي استخرجناها من كودك) ---
def get_enc_password(pwd):
    # نستخدم التايم-ستامب والتنسيق الذي أرسلته أنت في البداية
    timestamp = int(time.time())
    return f"#PWD_INSTAGRAM_BROWSER:10:{timestamp}:{pwd}"

# --- 2. محرك البروكسي (سحب وفحص وإرسال ملف) ---
def scrape_all_sources():
    sources = [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
    ]
    all_p = []
    for s in sources:
        try: all_p.extend(re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', requests.get(s, timeout=5).text))
        except: continue
    return list(set(all_p))

def verify_proxy(proxy):
    # الفحص الصارم: محاولة جلب التوكن من صفحة التسجيل
    try:
        r = requests.get("https://www.instagram.com/accounts/emailsignup/", 
                         proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, 
                         timeout=8, headers={'User-Agent': generate_user_agent()})
        if 'csrftoken' in r.text or 'csrftoken' in r.cookies.get_dict():
            return proxy, True
    except: pass
    return proxy, False

# --- 3. دالات إنستغرام (المستخلصة من كود Xzero و old_zpoc) ---
class InstagramAPI:
    def __init__(self, proxy):
        self.ses = requests.Session()
        self.proxy = {"http": f"http={proxy}", "https": f"http://{proxy}"}
        self.ses.proxies = self.proxy
        # الـ Headers الحقيقية من كودك الأخير
        self.headers = {
            "X-IG-App-ID": "936619743392459",
            "X-ASBD-ID": "198387",
            "X-IG-WWW-Claim": "0",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": generate_user_agent(),
            "Referer": "https://www.instagram.com/accounts/emailsignup/"
        }

    def get_init_data(self):
        # جلب الـ CSRF والـ Cookies مثل ما في كودك
        r = self.ses.get("https://www.instagram.com/accounts/emailsignup/", headers=self.headers)
        csrf = re.findall(r'csrf_token":"(.*?)"', r.text)[0]
        self.ses.headers.update({'X-CSRFToken': csrf})
        return csrf

    def attempt_signup(self, email, username):
        # دالة الـ attempt اللي كانت في كودك لتقليل الباند
        url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/"
        data = {'email': email, 'username': username, 'first_name': 'Dexr Bot', 'opt_into_one_tap': 'false'}
        return self.ses.post(url, data=data, headers=self.headers).json()

    def send_code(self, email):
        # دالة إرسال الكود AJAX
        url = "https://www.instagram.com/api/v1/web/accounts/send_signup_email_code_ajax/"
        return self.ses.post(url, data={'email': email}, headers=self.headers).json()

    def create_final(self, email, otp, user, pwd):
        # دالة الإنشاء النهائية مع الباسوورد المشفر
        url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"
        data = {
            'email': email, 'enc_password': get_enc_password(pwd),
            'username': user, 'email_otp': otp, 'first_name': 'Dexr Bot',
            'month': '1', 'day': '1', 'year': '1999'
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

# --- أزرار وتحكم البوت ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🚀 إنشاء تلقائي كامل', '🔄 سحب وفحص بروكسي')
    bot.send_message(message.chat.id, "🔥 تم دمج كل دالاتك بنجاح. جاهز للعمل!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🔄 سحب وفحص بروكسي')
def scrape_proxies(message):
    bot.send_message(message.chat.id, "🔎 جاري سحب البروكسيات وفحص الـ CSRF...")
    raw = scrape_all_sources()[:150] # عينة للفحص
    working = []
    with ThreadPoolExecutor(max_workers=15) as ex:
        res = list(ex.map(verify_proxy, raw))
    
    with open(PROXY_FILE, "a") as f:
        for p, ok in res:
            if ok: 
                f.write(p + "\n")
                working.append(p)
    
    # إرسال ملف الشغال
    if working:
        with open("working.txt", "w") as f: f.write("\n".join(working))
        with open("working.txt", "rb") as doc:
            bot.send_document(message.chat.id, doc, caption=f"✅ تم حفظ {len(working)} بروكسي في الداتا.")
    else: bot.send_message(message.chat.id, "❌ لم ينجح أي بروكسي.")

@bot.message_handler(func=lambda m: m.text == '🚀 إنشاء تلقائي كامل')
def process_creation(message):
    # التأكد من وجود بروكسيات
    if not os.path.exists(PROXY_FILE) or os.stat(PROXY_FILE).st_size == 0:
        return bot.send_message(message.chat.id, "⚠️ الداتا فارغة. اسحب بروكسي أولاً.")
    
    with open(PROXY_FILE, "r") as f: prx = f.readlines()[0].strip()
    
    email = get_temp_email()
    user = f"dexr_{secrets.token_hex(3)}"
    pwd = f"Dexr_{secrets.token_hex(4)}!"
    
    api = InstagramAPI(prx)
    try:
        api.get_init_data()
        bot.send_message(message.chat.id, f"📧 إيميل: {email}\n🛠️ طلب الكود...")
        if api.send_code(email).get('email_sent'):
            bot.send_message(message.chat.id, "⏳ بانتظار الكود تلقائياً...")
            otp = get_temp_otp(email)
            if otp:
                res = api.create_final(email, otp, user, pwd)
                bot.send_message(message.chat.id, f"✅ تم الإنشاء!\n👤 اليوزر: {user}\n🔑 الباسوورد: {pwd}\n📦 الرد: {res}")
            else: bot.send_message(message.chat.id, "❌ لم يصل الكود.")
        else: bot.send_message(message.chat.id, "❌ رفض إنستغرام إرسال الكود.")
    except Exception as e: bot.send_message(message.chat.id, f"❌ خطأ: {e}")

bot.polling()
