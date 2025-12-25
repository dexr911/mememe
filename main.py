import telebot
import requests
import re
import time
import os
import secrets
import logging
import random
import string
import cloudscraper
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- إعدادات التسجيل ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- إعدادات Dexr ---
API_TOKEN = '8488920682:AAEp45yVtWWuVWEIj8eV2P07uwDkXWrNHwI'
bot = telebot.TeleBot(API_TOKEN)
PROXY_FILE = "valid.txt"
ACCOUNTS_FILE = "created_accounts.txt"

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

# --- دوال المساعدة ---
def get_enc_password(pwd):
    """تشفير كلمة المرور لتنسيق Instagram"""
    return f"#PWD_INSTAGRAM_BROWSER:10:{int(time.time())}:{pwd}"

def generate_username():
    """إنشاء اسم مستخدم عشوائي"""
    letters = string.ascii_lowercase
    digits = string.digits
    return ''.join(random.choices(letters, k=8)) + ''.join(random.choices(digits, k=3))

def generate_password():
    """إنشاء كلمة مرور عشوائية"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=12))

def verify_proxy_strict(proxy):
    """فحص البروكسي بشكل صارم"""
    try:
        scraper = cloudscraper.create_scraper()
        test_url = "https://www.instagram.com/accounts/emailsignup/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        proxy_dict = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        
        # إذا كان البروكسي يحتوي على https://
        if proxy.startswith('https://'):
            proxy_dict = {"http": proxy, "https": proxy}
        
        response = scraper.get(
            test_url, 
            proxies=proxy_dict, 
            timeout=10,
            headers=headers
        )
        
        if response.status_code == 200 and 'csrftoken' in response.text:
            logging.info(f"✅ البروكسي شغال: {proxy}")
            return proxy, True
    except Exception as e:
        logging.debug(f"❌ فشل البروكسي {proxy}: {str(e)}")
    return proxy, False

class InstagramAPI:
    def __init__(self, proxy):
        self.ses = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        
        # إعداد البروكسي
        if proxy.startswith('https://'):
            proxy_url = proxy
        else:
            proxy_url = f"http://{proxy}"
        
        self.ses.proxies = {"http": proxy_url, "https": proxy_url}
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-IG-App-ID": "936619743392459",
            "X-ASBD-ID": "129663",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/emailsignup/",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        self.csrf_token = None
        self.logged_in = False

    def get_init_data(self):
        """الحصول على بيانات الجلسة الأولية"""
        try:
            url = "https://www.instagram.com/accounts/emailsignup/"
            response = self.ses.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                logging.error(f"❌ فشل تحميل الصفحة: {response.status_code}")
                return False
            
            # استخراج CSRF Token
            csrf_matches = re.findall(r'csrf_token":"([^"]+)"', response.text)
            if csrf_matches:
                self.csrf_token = csrf_matches[0]
                self.ses.headers.update({'X-CSRFToken': self.csrf_token})
                logging.info("✅ تم الحصول على CSRF Token")
                return True
            else:
                logging.error("❌ لم يتم العثور على CSRF Token")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في get_init_data: {str(e)}")
            return False

    def send_email_code(self, email):
        """إرسال كود التحقق إلى الإيميل"""
        try:
            if not self.csrf_token:
                if not self.get_init_data():
                    return {"status": "error", "message": "Failed to get CSRF token"}
            
            url = "https://www.instagram.com/api/v1/web/accounts/send_signup_email_code_ajax/"
            
            data = {
                'email': email,
                'device_id': secrets.token_hex(8).upper()
            }
            
            headers = self.headers.copy()
            headers['X-CSRFToken'] = self.csrf_token
            
            response = self.ses.post(url, data=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"📧 استجابة إرسال الكود: {result}")
                return result
            else:
                logging.error(f"❌ فشل إرسال الكود: {response.status_code}")
                return {"status": "error", "message": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logging.error(f"❌ خطأ في send_email_code: {str(e)}")
            return {"status": "error", "message": str(e)}

    def create_account(self, email, otp, username, password):
        """إنشاء الحساب النهائي"""
        try:
            if not self.csrf_token:
                return {"status": "error", "message": "No CSRF token"}
            
            url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"
            
            data = {
                'email': email,
                'enc_password': get_enc_password(password),
                'username': username,
                'email_otp': otp,
                'first_name': 'Instagram User',
                'month': str(random.randint(1, 12)),
                'day': str(random.randint(1, 28)),
                'year': str(random.randint(1980, 2000)),
                'client_id': secrets.token_hex(16).upper(),
                'seamless_login_enabled': '1',
                'tos_version': 'row',
                'force_sign_up_code': ''
            }
            
            headers = self.headers.copy()
            headers['X-CSRFToken'] = self.csrf_token
            
            response = self.ses.post(url, data=data, headers=headers, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"🔄 استجابة إنشاء الحساب: {result}")
                
                if result.get('account_created', False) or result.get('user_id'):
                    # حفظ الحساب في ملف
                    with open(ACCOUNTS_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"Username: {username} | Password: {password} | Email: {email} | Proxy: {self.ses.proxies}\n")
                    
                    return {
                        "status": "success",
                        "username": username,
                        "password": password,
                        "user_id": result.get('user_id'),
                        "message": "تم إنشاء الحساب بنجاح!"
                    }
                else:
                    error_msg = result.get('errors', {}).get('email', ['Unknown error'])[0]
                    return {"status": "error", "message": error_msg}
            else:
                logging.error(f"❌ فشل إنشاء الحساب: {response.status_code}")
                return {"status": "error", "message": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logging.error(f"❌ خطأ في create_account: {str(e)}")
            return {"status": "error", "message": str(e)}

# --- معالجات البوت ---
@bot.message_handler(commands=['start'])
def start(message):
    """بدء البوت وعرض القائمة"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = telebot.types.KeyboardButton('🚀 إنشاء تلقائي كامل')
    btn2 = telebot.types.KeyboardButton('🔄 سحب وفحص 30 مصدر')
    btn3 = telebot.types.KeyboardButton('📊 عرض البروكسيات الشغالة')
    btn4 = telebot.types.KeyboardButton('📋 عرض الحسابات المنشأة')
    markup.add(btn1, btn2, btn3, btn4)
    
    welcome = """
    🤖 *مرحباً بك في بوت Dexr*
    
    *الخيارات المتاحة:*
    🚀 إنشاء تلقائي كامل - إنشاء حساب انستغرام تلقائي
    🔄 سحب وفحص 30 مصدر - سحب بروكسيات جديدة
    📊 عرض البروكسيات الشغالة - عرض البروكسيات العاملة
    📋 عرض الحسابات المنشأة - عرض الحسابات المنشأة
    
    *مميزات البوت:*
    ✅ سحب بروكسيات من 30 مصدر مختلف
    ✅ فحص صارم للبروكسيات
    ✅ إنشاء حسابات انستغرام تلقائي
    ✅ تجاوز الحماية باستخدام CloudScraper
    """
    
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=markup)
    logging.info(f"بدأ المستخدم {message.chat.id}")

@bot.message_handler(func=lambda m: m.text == '📋 عرض الحسابات المنشأة')
def show_accounts(message):
    """عرض الحسابات المنشأة"""
    try:
        if not os.path.exists(ACCOUNTS_FILE):
            bot.send_message(message.chat.id, "⚠️ لم يتم إنشاء أي حسابات بعد.")
            return
        
        with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            accounts = f.readlines()
        
        if not accounts:
            bot.send_message(message.chat.id, "⚠️ لم يتم إنشاء أي حسابات بعد.")
            return
        
        response = f"📋 *الحسابات المنشأة ({len(accounts)}):*\n\n"
        for i, acc in enumerate(accounts[-10:], 1):  # عرض آخر 10 حسابات
            response += f"{i}. `{acc.strip()}`\n"
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في عرض الحسابات: {str(e)}")

@bot.message_handler(func=lambda m: m.text == '📊 عرض البروكسيات الشغالة')
def show_proxies(message):
    """عرض البروكسيات الشغالة"""
    try:
        if not os.path.exists(PROXY_FILE):
            bot.send_message(message.chat.id, "⚠️ لا يوجد بروكسيات شغالة.")
            return
        
        with open(PROXY_FILE, 'r') as f:
            proxies = f.readlines()
        
        if not proxies:
            bot.send_message(message.chat.id, "⚠️ لا يوجد بروكسيات شغالة.")
            return
        
        response = f"📊 *البروكسيات الشغالة ({len(proxies)}):*\n\n"
        for i, proxy in enumerate(proxies[:10], 1):  # عرض أول 10 بروكسيات
            response += f"{i}. `{proxy.strip()}`\n"
        
        if len(proxies) > 10:
            response += f"\n... و {len(proxies)-10} بروكسي إضافي"
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في عرض البروكسيات: {str(e)}")

@bot.message_handler(func=lambda m: m.text == '🔄 سحب وفحص 30 مصدر')
def handle_scrape(message):
    """سحب وفحص البروكسيات"""
    try:
        msg = bot.send_message(message.chat.id, "🔎 جاري سحب البروكسيات من 30 مصدر...")
        all_raw = []
        sources_count = 0
        
        for i, source in enumerate(SOURCES, 1):
            try:
                bot.edit_message_text(
                    f"🔎 جاري سحب البروكسيات... المصدر {i}/30",
                    message.chat.id,
                    msg.message_id
                )
                
                response = requests.get(source, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0'
                })
                
                if response.status_code == 200:
                    proxies = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text)
                    all_raw.extend(proxies)
                    sources_count += 1
                    logging.info(f"✅ المصدر {i}: تم سحب {len(proxies)} بروكسي")
                else:
                    logging.warning(f"⚠️ المصدر {i}: فشل برمز {response.status_code}")
                    
            except Exception as e:
                logging.warning(f"⚠️ المصدر {i}: فشل - {str(e)}")
                continue
        
        unique_proxies = list(set(all_raw))
        bot.edit_message_text(
            f"📥 تم سحب {len(unique_proxies)} بروكسي فريد من {sources_count} مصدر.\n⏳ جاري الفحص الصارم...",
            message.chat.id,
            msg.message_id
        )
        
        working_proxies = []
        total_to_check = min(500, len(unique_proxies))  # فحص حتى 500 بروكسي كحد أقصى
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_proxy = {
                executor.submit(verify_proxy_strict, proxy): proxy 
                for proxy in unique_proxies[:total_to_check]
            }
            
            completed = 0
            for future in as_completed(future_to_proxy):
                completed += 1
                proxy, is_working = future.result()
                
                if is_working:
                    working_proxies.append(proxy)
                
                # تحديث التقدم كل 50 بروكسي
                if completed % 50 == 0 or completed == total_to_check:
                    progress = int((completed / total_to_check) * 100)
                    bot.edit_message_text(
                        f"🔍 فحص البروكسيات... {progress}%\n"
                        f"✅ وجدنا {len(working_proxies)} بروكسي شغال",
                        message.chat.id,
                        msg.message_id
                    )
        
        # حفظ البروكسيات الشغالة
        with open(PROXY_FILE, "w") as f:
            for proxy in working_proxies:
                f.write(proxy + "\n")
        
        if working_proxies:
            final_msg = f"""
✅ *تم الانتهاء من العملية بنجاح!*

📊 *النتائج:*
• المصادر المفحوصة: {sources_count}/{len(SOURCES)}
• البروكسيات المسحوبة: {len(unique_proxies)}
• البروكسيات المفحوصة: {total_to_check}
• ✅ **البروكسيات الشغالة: {len(working_proxies)}**

💾 تم حفظ البروكسيات في `{PROXY_FILE}`
            """
            bot.edit_message_text(final_msg, message.chat.id, msg.message_id, parse_mode='Markdown')
        else:
            bot.edit_message_text(
                "❌ لم ينجح أي بروكسي في الفحص. حاول السحب مرة أخرى.",
                message.chat.id,
                msg.message_id
            )
            
    except Exception as e:
        logging.error(f"❌ خطأ في handle_scrape: {str(e)}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")

@bot.message_handler(func=lambda m: m.text == '🚀 إنشاء تلقائي كامل')
def run_creation(message):
    """إنشاء حساب انستغرام تلقائي"""
    try:
        # التحقق من وجود بروكسيات
        if not os.path.exists(PROXY_FILE) or os.stat(PROXY_FILE).st_size == 0:
            bot.send_message(
                message.chat.id,
                "⚠️ لا يوجد بروكسيات شغالة!\n"
                "يرجى استخدام زر '🔄 سحب وفحص 30 مصدر' أولاً."
            )
            return
        
        # قراءة البروكسيات
        with open(PROXY_FILE, "r") as f:
            proxies = [p.strip() for p in f.readlines() if p.strip()]
        
        if not proxies:
            bot.send_message(message.chat.id, "⚠️ ملف البروكسيات فارغ!")
            return
        
        # إعداد البيانات
        email_domain = "gmail.com"  # يمكن تغييره
        email_local = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{email_local}@{email_domain}"
        username = generate_username()
        password = generate_password()
        
        # محاولة استخدام البروكسيات بالترتيب
        for i, proxy in enumerate(proxies[:5]):  # محاولة أول 5 بروكسيات فقط
            try:
                bot.send_message(
                    message.chat.id,
                    f"🔄 المحاولة {i+1}/5\n"
                    f"⚙️ البروكسي: `{proxy}`\n"
                    f"📧 الإيميل: `{email}`\n"
                    f"👤 اليوزر: `{username}`\n"
                    f"🔐 الباسوورد: `{password}`",
                    parse_mode='Markdown'
                )
                
                # إنشاء API instance
                api = InstagramAPI(proxy)
                
                # التحقق من البروكسي
                bot.send_message(message.chat.id, "🔍 جاري التحقق من البروكسي...")
                if not api.get_init_data():
                    bot.send_message(message.chat.id, f"❌ البروكسي {proxy} غير شغال. جاري المحاولة بالبروكسي التالي...")
                    continue
                
                # إرسال كود التحقق
                bot.send_message(message.chat.id, "📧 جاري إرسال كود التحقق إلى الإيميل...")
                code_result = api.send_email_code(email)
                
                if code_result.get('status') == 'error' or 'email' not in code_result:
                    error_msg = code_result.get('message', 'خطأ غير معروف')
                    bot.send_message(message.chat.id, f"❌ فشل إرسال الكود: {error_msg}")
                    continue
                
                # طلب كود OTP من المستخدم
                bot.send_message(
                    message.chat.id,
                    f"📨 تم إرسال كود التحقق إلى:\n`{email}`\n\n"
                    f"⬇️ **أدخل كود التحقق المكون من 6 أرقام:**",
                    parse_mode='Markdown'
                )
                
                # الانتظار للإدخال
                bot.register_next_step_handler(message, process_otp, api, email, username, password, proxy)
                return
                
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ خطأ مع البروكسي {proxy}: {str(e)}")
                continue
        
        # إذا فشلت جميع المحاولات
        bot.send_message(
            message.chat.id,
            "❌ فشلت جميع محاولات الاتصال.\n"
            "يرجى سحب بروكسيات جديدة وحاول مرة أخرى."
        )
        
    except Exception as e:
        logging.error(f"❌ خطأ في run_creation: {str(e)}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ غير متوقع: {str(e)}")

def process_otp(message, api, email, username, password, proxy):
    """معالجة كود OTP"""
    try:
        otp = message.text.strip()
        
        if not otp.isdigit() or len(otp) != 6:
            bot.send_message(message.chat.id, "❌ كود التحقق يجب أن يكون 6 أرقام! حاول مرة أخرى.")
            return
        
        bot.send_message(message.chat.id, f"✅ كود التحقق المستلم: {otp}\n⏳ جاري إنشاء الحساب...")
        
        # إنشاء الحساب
        result = api.create_account(email, otp, username, password)
        
        if result.get('status') == 'success':
            success_msg = f"""
🎉 *تم إنشاء الحساب بنجاح!*

📋 *معلومات الحساب:*
• **اليوزر:** `{result['username']}`
• **الباسوورد:** `{password}`
• **الإيميل:** `{email}`
• **البروكسي:** `{proxy}`

🔑 **User ID:** {result.get('user_id', 'N/A')}

💾 تم حفظ الحساب في قاعدة البيانات.
            """
            bot.send_message(message.chat.id, success_msg, parse_mode='Markdown')
        else:
            error_msg = result.get('message', 'خطأ غير معروف')
            bot.send_message(
                message.chat.id,
                f"❌ فشل إنشاء الحساب:\n`{error_msg}`\n\n"
                f"جرب ببروكسي مختلف أو بيانات مختلفة.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logging.error(f"❌ خطأ في process_otp: {str(e)}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")

# --- تشغيل البوت ---
if __name__ == "__main__":
    logging.info("🚀 بدء تشغيل بوت Dexr...")
    
    # إنشاء الملفات إذا لم تكن موجودة
    for file in [PROXY_FILE, ACCOUNTS_FILE]:
        if not os.path.exists(file):
            with open(file, 'w'): pass
    
    try:
        bot.polling(none_stop=True, interval=1, timeout=30)
    except Exception as e:
        logging.error(f"❌ فشل تشغيل البوت: {str(e)}")
