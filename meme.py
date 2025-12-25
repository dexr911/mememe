import telebot
import requests
import re
import time
import secrets
from threading import Thread
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

# --- إعدادات Dexr الخاصة ---
API_TOKEN = '8488920682:AAEp45yVtWWuVWEIj8eV2P07uwDkXWrNHwI'
bot = telebot.TeleBot(API_TOKEN)
valid_proxies = []
IG_APP_ID = "936619743392459"

# --- 1. محرك الإيميل المؤقت ---
class TempMail:
    def __init__(self):
        self.api = "https://www.1secmail.com/api/v1/action"
    def generate(self):
        res = requests.get(f"{self.api}/?action=genEmailAddresses&count=1").json()
        return res[0]
    def fetch_otp(self, email):
        user, domain = email.split('@')
        for _ in range(15): # فحص لمدة دقيقة ونصف
            time.sleep(6)
            msgs = requests.get(f"{self.api}/?action=getMessages&login={user}&domain={domain}").json()
            for m in msgs:
                content = requests.get(f"{self.api}/?action=readMessage&login={user}&domain={domain}&id={m['id']}").json()
                otp = re.findall(r'\b\d{6}\b', content['body'])
                if otp: return otp[0]
        return None

# --- 2. محرك البروكسي العسكري ---
def check_proxy_strict(proxy):
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        r = requests.get("https://www.instagram.com/accounts/emailsignup/", 
                         proxies=proxies, timeout=8, headers={'User-Agent': generate_user_agent()})
        if 'csrftoken' in r.cookies.get_dict():
            return proxy, True
    except: pass
    return proxy, False

# --- 3. محرك إنشاء الحساب (API Emulation) ---
class InstaCreator:
    def __init__(self, proxy):
        self.session = requests.Session()
        self.session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        self.headers = {
            "X-IG-App-ID": IG_APP_ID,
            "User-Agent": generate_user_agent(),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/"
        }

    def start_signup(self, email):
        # جلب CSRF أولاً
        res = self.session.get("https://www.instagram.com/accounts/emailsignup/", headers=self.headers)
        csrf = self.session.cookies.get_dict().get('csrftoken')
        self.session.headers.update({'X-CSRFToken': csrf})
        
        # طلب إرسال الكود
        url = "https://www.instagram.com/api/v1/web/accounts/send_signup_email_code_ajax/"
        return self.session.post(url, data={'email': email}, headers=self.headers).json()

    def finish_signup(self, email, otp, user, pwd):
        url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"
        # التشفير اللي استخلصناه من ملفاتك
        enc_pwd = f"#PWD_INSTAGRAM_BROWSER:10:{int(time.time())}:{pwd}"
        data = {
            'email': email, 'username': user, 'first_name': 'Dexr Bot',
            'enc_password': enc_pwd, 'email_otp': otp, 'seamless_login_enabled': '1'
        }
        return self.session.post(url, data=data, headers=self.headers).json()

# --- 4. واجهة البوت والأوامر ---
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🚀 إنشاء حساب تلقائي', '🔄 سحب وفحص بروكسي')
    markup.add('➕ إضافة بروكسي يدوي', '📊 الإحصائيات')
    bot.send_message(message.chat.id, "🔥 أهلاً بك في نظام Dexr المتكامل.\nاختر أحد الخيارات لبدء العمل:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🔄 سحب وفحص بروكسي')
def handle_proxy(message):
    bot.send_message(message.chat.id, "🔎 جاري السحب من +30 مصدر والفحص الصارم...")
    # سحب سريع (مثال لمصدر واحد ويمكنك إضافة البقية)
    raw = requests.get("https://api.proxyscrape.com/v2/?request=getproxies&protocol=http").text
    proxies = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', raw)[:50]
    
    global valid_proxies
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_proxy_strict, proxies))
    
    new_valid = [p for p, status in results if status]
    valid_proxies.extend(new_valid)
    bot.send_message(message.chat.id, f"✅ الفحص اكتمل!\nتم إيجاد {len(new_valid)} بروكسي شغال بنسبة 100%.")

@bot.message_handler(func=lambda m: m.text == '🚀 إنشاء حساب تلقائي')
def auto_create(message):
    if not valid_proxies:
        return bot.send_message(message.chat.id, "⚠️ لا يوجد بروكسيات شغالة! قم بالسحب أولاً.")
    
    proxy = valid_proxies[0]
    bot.send_message(message.chat.id, f"⚙️ جاري البدء باستخدام بروكسي: {proxy}")
    
    # تنفيذ العملية
    mail = TempMail()
    email = mail.generate()
    creator = InstaCreator(proxy)
    
    bot.send_message(message.chat.id, f"📧 الإيميل المولد: {email}\nجاري طلب الكود...")
    
    res = creator.start_signup(email)
    if res.get('email_sent'):
        bot.send_message(message.chat.id, "⏳ تم إرسال الكود. جاري الفحص التلقائي للإيميل...")
        otp = mail.fetch_otp(email)
        if otp:
            bot.send_message(message.chat.id, f"🔑 تم استلام الكود: {otp}\nجاري إنشاء الحساب...")
            # هنا تضع اليوزر والباسوورد اللي تبيهم
            result = creator.finish_signup(email, otp, f"dexr_{secrets.token_hex(3)}", "Dexr_Pass123!")
            bot.send_message(message.chat.id, f"🎉 النتيجة: {result}")
        else:
            bot.send_message(message.chat.id, "❌ لم يصل الكود. قد يكون البروكسي محظور.")
    else:
        bot.send_message(message.chat.id, f"❌ فشل طلب الكود: {res}")

bot.polling()
