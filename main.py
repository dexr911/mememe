import telebot
import requests
import re
import time
import os
import secrets
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

# --- إعدادات Dexr المتقدمة ---
API_TOKEN = '8488920682:AAEp45yVtWWuVWEIj8eV2P07uwDkXWrNHwI'
bot = telebot.TeleBot(API_TOKEN)
PROXY_FILE = "valid.txt"
IG_APP_ID = "936619743392459"

# --- قائمة المصادر الـ 30 ---
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
    "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list.txt"
    # يمكنك إضافة بقية الروابط هنا لتصل لـ 30
]

# --- دالة تشفير الباسوورد (من كودك الأصلي) ---
def get_enc_password(pwd):
    return f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{pwd}"

# --- محرك الفحص الدقيق ---
def verify_proxy(proxy):
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        r = requests.get("https://www.instagram.com/accounts/emailsignup/", 
                         proxies=proxies, timeout=10, 
                         headers={'User-Agent': generate_user_agent()})
        if 'csrftoken' in r.text or 'csrftoken' in r.cookies.get_dict():
            return proxy, True
    except: pass
    return proxy, False

# --- محرك إنستغرام (تجميع كل دالاتك) ---
class InstagramAPI:
    def __init__(self, proxy):
        self.ses = requests.Session()
        self.ses.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        self.headers = {
            "X-IG-App-ID": IG_APP_ID,
            "X-ASBD-ID": "198387",
            "X-IG-WWW-Claim": "0",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": generate_user_agent(),
            "Referer": "https://www.instagram.com/accounts/emailsignup/",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def get_init_data(self):
        r = self.ses.get("https://www.instagram.com/accounts/emailsignup/", headers=self.headers)
        csrf = re.findall(r'csrf_token":"(.*?)"', r.text)[0]
        self.ses.headers.update({'X-CSRFToken': csrf})
        return csrf

    def send_code(self, email):
        url = "https://www.instagram.com/api/v1/web/accounts/send_signup_email_code_ajax/"
        data = {'email': email}
        return self.ses.post(url, data=data, headers=self.headers).json()

    def create_final(self, email, otp, user, pwd):
        url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"
        # Sleep 2 ثانية لمحاكاة السلوك البشري
        time.sleep(2)
        data = {
            'email': email, 'enc_password': get_enc_password(pwd),
            'username': user, 'email_otp': otp, 'first_name': 'Dexr Bot',
            'month': '1', 'day': '1', 'year': '1999',
            'client_id': secrets.token_hex(16).upper(),
            'seamless_login_enabled': '1', 'opt_into_one_tap': 'false'
        }
        # تحديث التوكن قبل الإرسال النهائي
        csrf = self.ses.cookies.get_dict().get('csrftoken', self.ses.headers.get('X-CSRFToken'))
        self.ses.headers.update({'X-CSRFToken': csrf})
        
        response = self.ses.post(url, data=data, headers=self.headers)
        return response.json()

# --- دالة الإيميل المؤقت ---
def get_temp_email():
    return requests.get("https://www.1secmail.com/api/v1/action/?action=genEmailAddresses&count=1").json()[0]

def get_temp_otp(email):
    u, d = email.split('@')
    for i in range(20): # محاولة لمدة 100 ثانية
        time.sleep(5)
        msgs = requests.get(f"https://www.1secmail.com/api/v1/action/?action=getMessages&login={u}&domain={d}").json()
        for m in msgs:
            c = requests.get(f"https://www.1secmail.com/api/v1/action/?action=readMessage&login={u}&domain={d}&id={m['id']}").json()
            otp = re.findall(r'\b\d{6}\b', c['body'])
            if otp: return otp[0]
    return None

# --- أوامر التلجرام ---
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🚀 إنشاء تلقائي كامل', '🔄 سحب وفحص 30 مصدر')
    bot.send_message(message.chat.id, "⚡ نظام Dexr المتكامل جاهز.\nالآن سيقوم البوت بإبلاغك بكل خطوة بالتفصيل.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🔄 سحب وفحص 30 مصدر')
def handle_scrape(message):
    bot.send_message(message.chat.id, "🔍 جاري تجميع البروكسيات من المصادر...")
    all_raw = []
    for s in SOURCES:
        try: all_raw.extend(re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', requests.get(s, timeout=5).text))
        except: continue
    
    unique = list(set(all_raw))
    bot.send_message(message.chat.id, f"📥 تم سحب {len(unique)}. جاري الفحص الدقيق لإنستغرام...")
    
    working = []
    with ThreadPoolExecutor(max_workers=30) as ex:
        results = list(ex.map(verify_proxy, unique[:500]))
    
    with open(PROXY_FILE, "a") as f:
        for p, ok in results:
            if ok:
                f.write(p + "\n")
                working.append(p)
    
    if working:
        with open("proxies_dexr.txt", "w") as f: f.write("\n".join(working))
        with open("proxies_dexr.txt", "rb") as doc:
            bot.send_document(message.chat.id, doc, caption=f"✅ اكتمل الفحص.\nتم العثور على {len(working)} شغال وتم حفظهم.")
        os.remove("proxies_dexr.txt")
    else:
        bot.send_message(message.chat.id, "❌ لم ينجح أي بروكسي في الوصول لإنستغرام.")

@bot.message_handler(func=lambda m: m.text == '🚀 إنشاء تلقائي كامل')
def run_creation(message):
    if not os.path.exists(PROXY_FILE) or os.stat(PROXY_FILE).st_size == 0:
        return bot.send_message(message.chat.id, "⚠️ الداتا فارغة. اسحب بروكسيات أولاً!")
    
    with open(PROXY_FILE, "r") as f: proxies = f.readlines()
    prx = proxies[0].strip()
    
    bot.send_message(message.chat.id, f"⚙️ المرحلة 1: الاتصال بإنستغرام عبر {prx}")
    api = InstagramAPI(prx)
    
    try:
        api.get_init_data()
        email = get_temp_email()
        bot.send_message(message.chat.id, f"📧 المرحلة 2: تم إنشاء إيميل مؤقت: {email}")
        
        send_res = api.send_code(email)
        if send_res.get('email_sent'):
            bot.send_message(message.chat.id, "📨 المرحلة 3: تم طلب الكود بنجاح. جاري الفحص...")
            otp = get_temp_otp(email)
            if otp:
                bot.send_message(message.chat.id, f"🔑 المرحلة 4: استلام الكود {otp}. جاري الإنشاء النهائي...")
                user = f"dexr_{secrets.token_hex(3)}"
                pwd = f"Dexr_{secrets.token_hex(4)}!"
                
                final = api.create_final(email, otp, user, pwd)
                if 'account_created' in str(final) or final.get('status') == 'ok':
                    bot.send_message(message.chat.id, f"✅ تم الإنشاء بنجاح!\n👤 يوزر: {user}\n🔑 باسوورد: {pwd}\n📦 الرد: {final}")
                else:
                    bot.send_message(message.chat.id, f"❌ فشل في الخطوة الأخيرة. الرد: {final}")
                
                # إزالة البروكسي المستخدم
                with open(PROXY_FILE, "w") as f: f.writelines(proxies[1:])
            else:
                bot.send_message(message.chat.id, "❌ انتهى الوقت ولم يصل الكود.")
        else:
            bot.send_message(message.chat.id, f"❌ إنستغرام رفض إرسال الكود لهذا البروكسي.\nالرد: {send_res}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ خطأ تقني: {e}")

bot.polling()
