import telebot
import requests
import re
import time
import os
import secrets
import logging
import random
import string
import json
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- إعدادات التسجيل ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --- إعدادات Dexr ---
API_TOKEN = '8488920682:AAEp45yVtWWuVWEIj8eV2P07uwDkXWrNHwI'
bot = telebot.TeleBot(API_TOKEN)
PROXY_FILE = "valid_proxies.json"
ACCOUNTS_FILE = "created_accounts.json"
USER_AGENTS_FILE = "UserAgent.txt"

# --- إعدادات 1secmail API ---
ONESECMAIL_API = "https://www.1secmail.com/api/v1/"
ONESECMAIL_DOMAINS = []  # سيتم تعبئتها تلقائيًا

# --- قائمة المصادر الـ 30 الأصلية ---
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

# --- مصادر بروكسيات متميزة إضافية ---
PREMIUM_SOURCES = [
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxy-list.download/api/v1/get?type=https",
    "https://www.proxy-list.download/api/v1/get?type=socks4",
    "https://www.proxy-list.download/api/v1/get?type=socks5"
]

# --- متغيرات النظام ---
user_agents = []
proxies_pool = []
proxy_index = 0
proxy_lock = threading.Lock()
active_email_creations = {}  # لتتبع عمليات إنشاء الحسابات النشطة

# --- دوال المساعدة ---
def load_user_agents():
    """تحميل قائمة User-Agent من الملف"""
    global user_agents
    try:
        if os.path.exists(USER_AGENTS_FILE):
            with open(USER_AGENTS_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                user_agents = [line.strip() for line in lines if line.strip()]
                logging.info(f"✅ تم تحميل {len(user_agents)} User-Agent")
        else:
            # User-Agent افتراضي إذا لم يوجد ملف
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            logging.warning(f"⚠️ ملف User-Agent غير موجود، استخدام {len(user_agents)} User-Agent افتراضي")
    except Exception as e:
        logging.error(f"❌ خطأ في تحميل User-Agent: {str(e)}")
        user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]

def get_random_user_agent():
    """الحصول على User-Agent عشوائي"""
    if user_agents:
        return random.choice(user_agents)
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def get_enc_password(pwd):
    """تشفير كلمة المرور لتنسيق Instagram"""
    return f"#PWD_INSTAGRAM_BROWSER:10:{int(time.time())}:{pwd}"

def generate_username():
    """إنشاء اسم مستخدم عشوائي"""
    adjectives = ['cool', 'happy', 'smart', 'funny', 'clever', 'brave', 'calm', 'eager', 'gentle', 'jolly']
    nouns = ['panda', 'tiger', 'dragon', 'phoenix', 'wolf', 'eagle', 'lion', 'fox', 'bear', 'hawk']
    numbers = ''.join(random.choices(string.digits, k=4))
    return f"{random.choice(adjectives)}_{random.choice(nouns)}_{numbers}"

def generate_password():
    """إنشاء كلمة مرور عشوائية قوية"""
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*"
    
    password = [
        random.choice(upper),
        random.choice(lower),
        random.choice(digits),
        random.choice(symbols)
    ]
    
    # إضافة حروف عشوائية
    all_chars = upper + lower + digits + symbols
    password.extend(random.choices(all_chars, k=8))
    
    random.shuffle(password)
    return ''.join(password)

def save_proxies(proxies):
    """حفظ البروكسيات في ملف JSON"""
    try:
        data = {
            "last_updated": datetime.now().isoformat(),
            "count": len(proxies),
            "proxies": proxies
        }
        with open(PROXY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"💾 تم حفظ {len(proxies)} بروكسي في {PROXY_FILE}")
    except Exception as e:
        logging.error(f"❌ خطأ في حفظ البروكسيات: {str(e)}")

def load_proxies():
    """تحميل البروكسيات من ملف JSON"""
    global proxies_pool
    try:
        if os.path.exists(PROXY_FILE):
            with open(PROXY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                proxies_pool = data.get("proxies", [])
                logging.info(f"📂 تم تحميل {len(proxies_pool)} بروكسي من {PROXY_FILE}")
        else:
            proxies_pool = []
            logging.warning("⚠️ ملف البروكسيات غير موجود")
    except Exception as e:
        logging.error(f"❌ خطأ في تحميل البروكسيات: {str(e)}")
        proxies_pool = []

def get_next_proxy():
    """الحصول على البروكسي التالي من المجموعة"""
    global proxy_index
    with proxy_lock:
        if not proxies_pool:
            return None
        
        proxy = proxies_pool[proxy_index % len(proxies_pool)]
        proxy_index += 1
        
        # إعادة ضبط الفهرس إذا تجاوز الحجم
        if proxy_index >= len(proxies_pool):
            proxy_index = 0
            random.shuffle(proxies_pool)  # خلط البروكسيات بعد كل دورة
        
        return proxy

# --- نظام 1secmail للإيميلات المؤقتة ---
class TempEmailManager:
    """مدير الإيميلات المؤقتة باستخدام 1secmail API"""
    
    @staticmethod
    def get_available_domains():
        """الحصول على النطاقات المتاحة"""
        try:
            response = requests.get(f"{ONESECMAIL_API}?action=getDomainList", timeout=10)
            if response.status_code == 200:
                domains = response.json()
                logging.info(f"📧 تم الحصول على {len(domains)} نطاق إيميل")
                return domains
            return []
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على النطاقات: {str(e)}")
            return ["1secmail.com", "1secmail.net", "1secmail.org"]
    
    @staticmethod
    def generate_random_email():
        """إنشاء إيميل عشوائي"""
        try:
            # إذا لم تكن النطاقات محملة، قم بتحميلها
            global ONESECMAIL_DOMAINS
            if not ONESECMAIL_DOMAINS:
                ONESECMAIL_DOMAINS = TempEmailManager.get_available_domains()
            
            if not ONESECMAIL_DOMAINS:
                ONESECMAIL_DOMAINS = ["1secmail.com", "1secmail.net", "1secmail.org"]
            
            # توليد اسم إيميل عشوائي
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            domain = random.choice(ONESECMAIL_DOMAINS)
            email = f"{username}@{domain}"
            
            logging.info(f"📧 تم إنشاء إيميل: {email}")
            return email
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء الإيميل: {str(e)}")
            # إيميل افتراضي في حالة الخطأ
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            return f"{username}@1secmail.com"
    
    @staticmethod
    def get_messages(email):
        """الحصول على رسائل الإيميل"""
        try:
            # فصل الإيميل إلى اسم ونطاق
            username, domain = email.split('@')
            
            # طلب الرسائل
            url = f"{ONESECMAIL_API}?action=getMessages&login={username}&domain={domain}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                messages = response.json()
                logging.info(f"📨 تم الحصول على {len(messages)} رسالة للإيميل {email}")
                return messages
            return []
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على الرسائل: {str(e)}")
            return []
    
    @staticmethod
    def get_message_content(email, message_id):
        """الحصول على محتوى رسالة محددة"""
        try:
            username, domain = email.split('@')
            
            url = f"{ONESECMAIL_API}?action=readMessage&login={username}&domain={domain}&id={message_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                message = response.json()
                return message
            return None
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على محتوى الرسالة: {str(e)}")
            return None
    
    @staticmethod
    def extract_instagram_code_from_email(email, max_attempts=30, wait_time=5):
        """
        استخراج كود Instagram من الإيميل تلقائيًا
        
        Args:
            email: الإيميل المراد فحصه
            max_attempts: أقصى عدد محاولات
            wait_time: وقت الانتظار بين المحاولات (بالثواني)
        
        Returns:
            كود التحقق (6 أرقام) أو None إذا لم يتم العثور
        """
        logging.info(f"🔍 جاري البحث عن كود Instagram في الإيميل: {email}")
        
        for attempt in range(1, max_attempts + 1):
            try:
                logging.info(f"🔄 المحاولة {attempt}/{max_attempts} لاستخراج الكود...")
                
                # الحصول على الرسائل
                messages = TempEmailManager.get_messages(email)
                
                if messages:
                    # البحث عن رسالة Instagram
                    for msg in messages:
                        subject = msg.get('subject', '').lower()
                        from_email = msg.get('from', '').lower()
                        
                        # التحقق إذا كانت الرسالة من Instagram
                        if 'instagram' in subject or 'instagram' in from_email or 'confirmation' in subject:
                            message_id = msg.get('id')
                            
                            # الحصول على محتوى الرسالة
                            message_content = TempEmailManager.get_message_content(email, message_id)
                            
                            if message_content:
                                body = message_content.get('body', '')
                                text_body = message_content.get('textBody', '')
                                
                                # البحث عن كود مكون من 6 أرقام
                                code_patterns = [
                                    r'\b\d{6}\b',  # 6 أرقام متتالية
                                    r'code[:\s]*(\d{6})',  # code: 123456
                                    r'verification[:\s]*(\d{6})',  # verification: 123456
                                    r'confirmation[:\s]*(\d{6})',  # confirmation: 123456
                                ]
                                
                                # البحث في النص
                                search_text = f"{body} {text_body}".lower()
                                
                                for pattern in code_patterns:
                                    matches = re.findall(pattern, search_text)
                                    if matches:
                                        code = matches[0]
                                        logging.info(f"✅ تم العثور على كود Instagram: {code}")
                                        return code
                
                # إذا لم يتم العثور على الرسالة
                if attempt < max_attempts:
                    logging.info(f"⏳ لم يتم العثور على الكود، انتظار {wait_time} ثانية...")
                    time.sleep(wait_time)
                else:
                    logging.warning(f"❌ انتهت المحاولات ولم يتم العثور على كود في {email}")
                    return None
                    
            except Exception as e:
                logging.error(f"❌ خطأ في المحاولة {attempt}: {str(e)}")
                if attempt < max_attempts:
                    time.sleep(wait_time)
                else:
                    return None
        
        return None
    
    @staticmethod
    def wait_for_instagram_code(email, timeout=180):
        """
        انتظار كود Instagram مع وقت محدد
        
        Args:
            email: الإيميل المراد فحصه
            timeout: أقصى وقت انتظار (بالثواني)
        
        Returns:
            كود التحقق أو None
        """
        logging.info(f"⏳ انتظار كود Instagram للإيميل: {email} (الحد الأقصى: {timeout} ثانية)")
        
        start_time = time.time()
        check_interval = 5  # فحص كل 5 ثواني
        
        while time.time() - start_time < timeout:
            try:
                # الحصول على الرسائل
                messages = TempEmailManager.get_messages(email)
                
                if messages:
                    for msg in messages:
                        subject = msg.get('subject', '').lower()
                        from_email = msg.get('from', '').lower()
                        
                        # التحقق إذا كانت الرسالة من Instagram
                        if 'instagram' in subject or 'instagram' in from_email:
                            message_id = msg.get('id')
                            message_content = TempEmailManager.get_message_content(email, message_id)
                            
                            if message_content:
                                body = message_content.get('body', '')
                                text_body = message_content.get('textBody', '')
                                
                                # البحث عن كود مكون من 6 أرقام
                                search_text = f"{body} {text_body}"
                                matches = re.findall(r'\b\d{6}\b', search_text)
                                
                                if matches:
                                    code = matches[0]
                                    logging.info(f"✅ تم استقبال كود Instagram: {code}")
                                    return code
                
                # الانتظار قبل المحاولة التالية
                elapsed = time.time() - start_time
                remaining = timeout - elapsed
                
                if remaining > check_interval:
                    logging.info(f"⏳ انتظار الكود... ({int(elapsed)}/{timeout} ثانية)")
                    time.sleep(check_interval)
                else:
                    break
                    
            except Exception as e:
                logging.error(f"❌ خطأ أثناء انتظار الكود: {str(e)}")
                time.sleep(check_interval)
        
        logging.warning(f"⏰ انتهى وقت انتظار الكود للإيميل: {email}")
        return None

class AdvancedProxyChecker:
    """فحص متقدم للبروكسيات"""
    
    TEST_URLS = [
        "https://www.instagram.com/accounts/emailsignup/",
        "https://httpbin.org/ip",
        "https://api.ipify.org?format=json"
    ]
    
    @staticmethod
    def check_proxy_advanced(proxy):
        """فحص بروكسي متقدم"""
        try:
            # تجهيز البروكسي
            if "://" not in proxy:
                proxy = f"http://{proxy}"
            
            proxy_dict = {
                "http": proxy,
                "https": proxy
            }
            
            # اختيار User-Agent عشوائي
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # اختبار الاتصال
            test_url = random.choice(AdvancedProxyChecker.TEST_URLS)
            response = requests.get(
                test_url,
                proxies=proxy_dict,
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                # اختبار Instagram بشكل خاص
                if "instagram.com" in test_url and 'csrftoken' in response.text:
                    speed = response.elapsed.total_seconds()
                    return {
                        "proxy": proxy,
                        "working": True,
                        "speed": round(speed, 2),
                        "tested_at": datetime.now().isoformat()
                    }
                elif "instagram.com" not in test_url:
                    speed = response.elapsed.total_seconds()
                    return {
                        "proxy": proxy,
                        "working": True,
                        "speed": round(speed, 2),
                        "tested_at": datetime.now().isoformat()
                    }
            
            return {"proxy": proxy, "working": False, "error": f"HTTP {response.status_code}"}
            
        except requests.exceptions.Timeout:
            return {"proxy": proxy, "working": False, "error": "Timeout"}
        except requests.exceptions.ConnectionError:
            return {"proxy": proxy, "working": False, "error": "Connection Error"}
        except Exception as e:
            return {"proxy": proxy, "working": False, "error": str(e)}

class InstagramCreator:
    """محرك إنشاء حسابات Instagram متقدم"""
    
    def __init__(self, proxy=None):
        self.proxy = proxy
        self.session = requests.Session()
        self.csrf_token = None
        self.user_agent = get_random_user_agent()
        
        if proxy:
            if "://" not in proxy:
                proxy = f"http://{proxy}"
            self.session.proxies = {"http": proxy, "https": proxy}
        
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': '936619743392459',
            'X-ASBD-ID': '129663',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        })
    
    def get_initial_data(self):
        """الحصول على البيانات الأولية"""
        try:
            url = "https://www.instagram.com/accounts/emailsignup/"
            
            # إضافة Referer
            self.session.headers['Referer'] = url
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                # استخراج CSRF Token
                csrf_match = re.search(r'"csrf_token":"([^"]+)"', response.text)
                if csrf_match:
                    self.csrf_token = csrf_match.group(1)
                    self.session.headers['X-CSRFToken'] = self.csrf_token
                    logging.info(f"✅ تم الحصول على CSRF Token: {self.csrf_token[:20]}...")
                    return True
                else:
                    logging.error("❌ لم يتم العثور على CSRF Token")
                    return False
            else:
                logging.error(f"❌ فشل تحميل الصفحة: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في get_initial_data: {str(e)}")
            return False
    
    def send_verification_code(self, email):
        """إرسال كود التحقق"""
        try:
            if not self.csrf_token:
                if not self.get_initial_data():
                    return {"success": False, "message": "Failed to get CSRF token"}
            
            url = "https://www.instagram.com/api/v1/web/accounts/send_signup_email_code_ajax/"
            
            data = {
                'email': email,
                'device_id': secrets.token_hex(8).upper()
            }
            
            response = self.session.post(url, data=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"📧 استجابة إرسال الكود: {result}")
                
                if 'email' in result or result.get('email_sent', False):
                    return {
                        "success": True,
                        "message": "تم إرسال الكود بنجاح",
                        "data": result
                    }
                else:
                    error_msg = result.get('errors', {}).get('email', ['Unknown error'])[0]
                    return {"success": False, "message": error_msg}
            else:
                logging.error(f"❌ فشل إرسال الكود: {response.status_code}")
                return {"success": False, "message": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logging.error(f"❌ خطأ في send_verification_code: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def create_account(self, email, otp, username, password):
        """إنشاء الحساب"""
        try:
            if not self.csrf_token:
                return {"success": False, "message": "No CSRF token"}
            
            url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"
            
            # توليد بيانات عشوائية واقعية
            first_names = ['Ahmed', 'Mohamed', 'Ali', 'Omar', 'Khaled', 'Yousef', 'Hassan', 'Mahmoud']
            last_names = ['Al', 'El', 'Ben', 'Ibn', 'Abd']
            
            data = {
                'email': email,
                'enc_password': get_enc_password(password),
                'username': username,
                'email_otp': otp,
                'first_name': f"{random.choice(first_names)} {random.choice(last_names)}",
                'month': str(random.randint(1, 12)),
                'day': str(random.randint(1, 28)),
                'year': str(random.randint(1980, 2000)),
                'client_id': secrets.token_hex(16).upper(),
                'seamless_login_enabled': '1',
                'tos_version': 'row',
                'force_sign_up_code': '',
                'opt_into_one_tap': 'false'
            }
            
            response = self.session.post(url, data=data, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"🔄 استجابة إنشاء الحساب: {result}")
                
                if result.get('account_created', False) or result.get('user_id'):
                    # حفظ الحساب
                    account_data = {
                        "username": username,
                        "password": password,
                        "email": email,
                        "proxy": self.proxy,
                        "user_id": result.get('user_id'),
                        "created_at": datetime.now().isoformat()
                    }
                    
                    save_account(account_data)
                    
                    return {
                        "success": True,
                        "message": "تم إنشاء الحساب بنجاح!",
                        "username": username,
                        "password": password,
                        "user_id": result.get('user_id')
                    }
                else:
                    error_msg = result.get('errors', {}).get('email', ['Unknown error'])[0]
                    return {"success": False, "message": error_msg}
            else:
                logging.error(f"❌ فشل إنشاء الحساب: {response.status_code}")
                return {"success": False, "message": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logging.error(f"❌ خطأ في create_account: {str(e)}")
            return {"success": False, "message": str(e)}

def save_account(account_data):
    """حفظ بيانات الحساب"""
    try:
        accounts = []
        
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
        
        accounts.append(account_data)
        
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False, default=str)
        
        logging.info(f"💾 تم حفظ حساب: {account_data['username']}")
    except Exception as e:
        logging.error(f"❌ خطأ في حفظ الحساب: {str(e)}")

# --- نظام إنشاء الحساب التلقائي الكامل ---
def auto_create_instagram_account(message, max_attempts=3):
    """
    إنشاء حساب Instagram تلقائي بالكامل
    بدون أي تدخل بشري
    """
    try:
        # تحميل البروكسيات
        load_proxies()
        
        if not proxies_pool:
            bot.send_message(
                message.chat.id,
                "⚠️ لا يوجد بروكسيات شغالة!\n"
                "يرجى استخدام زر '🔄 سحب بروكسيات قوية' أولاً."
            )
            return
        
        # إعلام المستخدم ببدء العملية
        status_msg = bot.send_message(
            message.chat.id,
            "🚀 *بدء عملية الإنشاء التلقائي*\n\n"
            "⏳ جاري إعداد النظام...",
            parse_mode='Markdown'
        )
        
        # محاولات متعددة لإنشاء الحساب
        for attempt in range(1, max_attempts + 1):
            try:
                # تحديث حالة المحاولة
                bot.edit_message_text(
                    f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                    f"🔄 المحاولة {attempt}/{max_attempts}\n"
                    f"⏳ جاري إعداد النظام...",
                    message.chat.id,
                    status_msg.message_id,
                    parse_mode='Markdown'
                )
                
                # الخطوة 1: إنشاء إيميل مؤقت
                bot.edit_message_text(
                    f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                    f"🔄 المحاولة {attempt}/{max_attempts}\n"
                    f"📧 جاري إنشاء إيميل مؤقت...",
                    message.chat.id,
                    status_msg.message_id,
                    parse_mode='Markdown'
                )
                
                temp_email = TempEmailManager.generate_random_email()
                username = generate_username()
                password = generate_password()
                
                # الخطوة 2: اختيار بروكسي
                bot.edit_message_text(
                    f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                    f"🔄 المحاولة {attempt}/{max_attempts}\n"
                    f"📧 الإيميل: `{temp_email}`\n"
                    f"🌐 جاري اختيار بروكسي...",
                    message.chat.id,
                    status_msg.message_id,
                    parse_mode='Markdown'
                )
                
                proxy_data = random.choice(proxies_pool)
                proxy = proxy_data if isinstance(proxy_data, str) else proxy_data.get('proxy', '')
                
                # الخطوة 3: إنشاء محرك Instagram
                bot.edit_message_text(
                    f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                    f"🔄 المحاولة {attempt}/{max_attempts}\n"
                    f"📧 الإيميل: `{temp_email}`\n"
                    f"👤 اليوزر: `{username}`\n"
                    f"🌐 البروكسي: `{proxy[:50]}...`\n"
                    f"🔗 جاري الاتصال بـ Instagram...",
                    message.chat.id,
                    status_msg.message_id,
                    parse_mode='Markdown'
                )
                
                creator = InstagramCreator(proxy)
                
                # التحقق من البروكسي
                if not creator.get_initial_data():
                    bot.edit_message_text(
                        f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                        f"🔄 المحاولة {attempt}/{max_attempts}\n"
                        f"❌ البروكسي غير شغال!\n"
                        f"جاري المحاولة بالبروكسي التالي...",
                        message.chat.id,
                        status_msg.message_id,
                        parse_mode='Markdown'
                    )
                    continue
                
                # الخطوة 4: إرسال كود التحقق
                bot.edit_message_text(
                    f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                    f"🔄 المحاولة {attempt}/{max_attempts}\n"
                    f"📧 الإيميل: `{temp_email}`\n"
                    f"👤 اليوزر: `{username}`\n"
                    f"📤 جاري إرسال كود التحقق...",
                    message.chat.id,
                    status_msg.message_id,
                    parse_mode='Markdown'
                )
                
                code_result = creator.send_verification_code(temp_email)
                
                if not code_result.get('success', False):
                    error_msg = code_result.get('message', 'خطأ غير معروف')
                    bot.edit_message_text(
                        f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                        f"🔄 المحاولة {attempt}/{max_attempts}\n"
                        f"❌ فشل إرسال الكود:\n`{error_msg}`\n"
                        f"جاري المحاولة بإيميل جديد...",
                        message.chat.id,
                        status_msg.message_id,
                        parse_mode='Markdown'
                    )
                    continue
                
                # الخطوة 5: انتظار الكود تلقائيًا
                bot.edit_message_text(
                    f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                    f"🔄 المحاولة {attempt}/{max_attempts}\n"
                    f"📧 الإيميل: `{temp_email}`\n"
                    f"👤 اليوزر: `{username}`\n"
                    f"⏳ جاري انتظار كود التحقق...\n"
                    f"⏰ (قد يستغرق حتى 3 دقائق)",
                    message.chat.id,
                    status_msg.message_id,
                    parse_mode='Markdown'
                )
                
                # انتظار الكود مع وقت محدد
                otp_code = TempEmailManager.wait_for_instagram_code(temp_email, timeout=180)
                
                if not otp_code:
                    # محاولة استخراج الكود بطريقة بديلة
                    otp_code = TempEmailManager.extract_instagram_code_from_email(temp_email, max_attempts=10)
                
                if not otp_code:
                    bot.edit_message_text(
                        f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                        f"🔄 المحاولة {attempt}/{max_attempts}\n"
                        f"❌ لم يتم استقبال كود التحقق!\n"
                        f"جاري المحاولة بإيميل جديد...",
                        message.chat.id,
                        status_msg.message_id,
                        parse_mode='Markdown'
                    )
                    continue
                
                # الخطوة 6: إنشاء الحساب باستخدام الكود
                bot.edit_message_text(
                    f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                    f"🔄 المحاولة {attempt}/{max_attempts}\n"
                    f"📧 الإيميل: `{temp_email}`\n"
                    f"👤 اليوزر: `{username}`\n"
                    f"✅ الكود المستلم: `{otp_code}`\n"
                    f"🎯 جاري إنشاء الحساب...",
                    message.chat.id,
                    status_msg.message_id,
                    parse_mode='Markdown'
                )
                
                creation_result = creator.create_account(temp_email, otp_code, username, password)
                
                if creation_result.get('success', False):
                    # نجاح إنشاء الحساب
                    success_msg = f"""
🎉 *تم إنشاء الحساب بنجاح تلقائيًا!*

📋 *معلومات الحساب:*
• **اليوزر:** `{creation_result['username']}`
• **الباسوورد:** `{password}`
• **الإيميل:** `{temp_email}`
• **User ID:** {creation_result.get('user_id', 'N/A')}
• **المحاولة:** {attempt}/{max_attempts}

✅ *تم حفظ الحساب في قاعدة البيانات.*

✨ *المميزات:*
1. إيميل مؤقت تلقائي
2. استخراج كود آلي
3. إنشاء كامل بدون تدخل بشري
                    """
                    
                    bot.edit_message_text(
                        success_msg,
                        message.chat.id,
                        status_msg.message_id,
                        parse_mode='Markdown'
                    )
                    
                    # إرسال رسالة تأكيد إضافية
                    bot.send_message(
                        message.chat.id,
                        f"✅ *عملية إنشاء تلقائي مكتملة!*\n\n"
                        f"🔑 يمكنك الآن تسجيل الدخول باستخدام:\n"
                        f"👤 اليوزر: `{creation_result['username']}`\n"
                        f"🔐 الباسوورد: `{password}`",
                        parse_mode='Markdown'
                    )
                    
                    return True
                else:
                    error_msg = creation_result.get('message', 'خطأ غير معروف')
                    bot.edit_message_text(
                        f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                        f"🔄 المحاولة {attempt}/{max_attempts}\n"
                        f"❌ فشل إنشاء الحساب:\n`{error_msg}`\n"
                        f"جاري المحاولة التالية...",
                        message.chat.id,
                        status_msg.message_id,
                        parse_mode='Markdown'
                    )
                    continue
                    
            except Exception as e:
                logging.error(f"❌ خطأ في المحاولة {attempt}: {str(e)}")
                
                if attempt < max_attempts:
                    bot.edit_message_text(
                        f"🚀 *بدء عملية الإنشاء التلقائي*\n\n"
                        f"🔄 المحاولة {attempt}/{max_attempts}\n"
                        f"❌ خطأ: {str(e)[:100]}...\n"
                        f"جاري المحاولة التالية...",
                        message.chat.id,
                        status_msg.message_id,
                        parse_mode='Markdown'
                    )
                    time.sleep(3)  # انتظار قبل المحاولة التالية
                else:
                    bot.edit_message_text(
                        f"❌ *فشل جميع المحاولات!*\n\n"
                        f"📊 المحاولات: {max_attempts}\n"
                        f"💡 الأسباب المحتملة:\n"
                        f"1. جميع البروكسيات غير شغالة\n"
                        f"2. Instagram حظر الطلبات\n"
                        f"3. مشكلة في خدمة الإيميلات\n\n"
                        f"🔄 حاول مرة أخرى بعد قليل",
                        message.chat.id,
                        status_msg.message_id,
                        parse_mode='Markdown'
                    )
                    return False
        
        return False
        
    except Exception as e:
        logging.error(f"❌ خطأ في auto_create_instagram_account: {str(e)}")
        bot.send_message(
            message.chat.id,
            f"❌ حدث خطأ غير متوقع في الإنشاء التلقائي:\n`{str(e)[:200]}`",
            parse_mode='Markdown'
        )
        return False

# --- معالجات البوت ---
@bot.message_handler(commands=['start'])
def start(message):
    """بدء البوت"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = telebot.types.KeyboardButton('🤖 إنشاء تلقائي كامل')
    btn2 = telebot.types.KeyboardButton('🚀 إنشاء حساب يدوي')
    btn3 = telebot.types.KeyboardButton('🔄 سحب بروكسيات قوية')
    btn4 = telebot.types.KeyboardButton('📊 عرض البروكسيات')
    btn5 = telebot.types.KeyboardButton('📋 عرض الحسابات')
    btn6 = telebot.types.KeyboardButton('⚡ فحص بروكسيات سريع')
    btn7 = telebot.types.KeyboardButton('🎯 إعدادات متقدمة')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    
    welcome = f"""
    🤖 *مرحباً بك في بوت Dexr Pro v3.0*
    
    *المميزات الجديدة:*
    ✅ إنشاء تلقائي كامل بدون تدخل بشري
    ✅ إيميلات مؤقتة تلقائية (1secmail)
    ✅ سحب أكواد Instagram آليًا
    ✅ 1000+ User-Agent عشوائي
    ✅ نظام بروكسيات متقدم
    
    *الإحصائيات:*
    📊 البروكسيات المتاحة: {len(proxies_pool)}
    👤 User-Agent المحملة: {len(user_agents)}
    
    *مطور البوت:* @DexrBot
    """
    
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=markup)
    logging.info(f"بدأ المستخدم {message.chat.id}")

@bot.message_handler(func=lambda m: m.text == '🤖 إنشاء تلقائي كامل')
def handle_auto_create(message):
    """معالجة إنشاء تلقائي كامل"""
    # حذف الرسالة القديمة إذا كانت موجودة
    try:
        if message.chat.id in active_email_creations:
            old_msg_id = active_email_creations[message.chat.id]
            bot.delete_message(message.chat.id, old_msg_id)
    except:
        pass
    
    # بدء العملية التلقائية
    success = auto_create_instagram_account(message, max_attempts=3)
    
    if not success:
        # عرض زر إعادة المحاولة
        markup = telebot.types.InlineKeyboardMarkup()
        retry_btn = telebot.types.InlineKeyboardButton("🔄 إعادة المحاولة", callback_data="retry_auto_create")
        markup.add(retry_btn)
        
        bot.send_message(
            message.chat.id,
            "❌ فشل الإنشاء التلقائي!\n"
            "هل تريد إعادة المحاولة؟",
            reply_markup=markup
        )

@bot.message_handler(func=lambda m: m.text == '🚀 إنشاء حساب يدوي')
def handle_manual_create(message):
    """معالجة إنشاء حساب يدوي"""
    try:
        # تحميل البروكسيات
        load_proxies()
        
        if not proxies_pool:
            bot.send_message(
                message.chat.id,
                "⚠️ لا يوجد بروكسيات شغالة!\n"
                "يرجى استخدام زر '🔄 سحب بروكسيات قوية' أولاً."
            )
            return
        
        # توليد بيانات الحساب
        email_local = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        email_domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"])
        email = f"{email_local}@{email_domain}"
        username = generate_username()
        password = generate_password()
        
        # اختيار بروكسي عشوائي
        proxy_data = random.choice(proxies_pool)
        proxy = proxy_data if isinstance(proxy_data, str) else proxy_data.get('proxy', '')
        
        # إرسال معلومات الحساب
        bot.send_message(
            message.chat.id,
            f"🔄 *بدء إنشاء حساب يدوي*\n\n"
            f"📧 *الإيميل:* `{email}`\n"
            f"👤 *اليوزر:* `{username}`\n"
            f"🔐 *الباسوورد:* `{password}`\n"
            f"🌐 *البروكسي:* `{proxy[:50]}...`\n\n"
            f"⏳ جاري الاتصال بالخادم...",
            parse_mode='Markdown'
        )
        
        # إنشاء المحرك
        creator = InstagramCreator(proxy)
        
        # التحقق من البروكسي
        if not creator.get_initial_data():
            bot.send_message(
                message.chat.id,
                "❌ البروكسي غير شغال مع Instagram!\n"
                "جاري تجربة بروكسي آخر..."
            )
            return handle_manual_create(message)  # إعادة المحاولة
        
        # إرسال كود التحقق
        bot.send_message(message.chat.id, "📧 جاري إرسال كود التحقق إلى الإيميل...")
        code_result = creator.send_verification_code(email)
        
        if not code_result.get('success', False):
            bot.send_message(
                message.chat.id,
                f"❌ فشل إرسال الكود:\n`{code_result.get('message', 'خطأ غير معروف')}`\n\n"
                f"جرب ببروكسي مختلف.",
                parse_mode='Markdown'
            )
            return
        
        # طلب كود OTP
        bot.send_message(
            message.chat.id,
            f"📨 *تم إرسال كود التحقق!*\n\n"
            f"📧 إلى: `{email}`\n\n"
            f"⬇️ **أدخل كود التحقق المكون من 6 أرقام:**",
            parse_mode='Markdown'
        )
        
        # حفظ معلومات الجلسة مؤقتًا
        active_email_creations[message.chat.id] = {
            'creator': creator,
            'email': email,
            'username': username,
            'password': password,
            'proxy': proxy
        }
        
        # الانتظار للإدخال
        bot.register_next_step_handler(message, process_manual_account_creation)
        
    except Exception as e:
        logging.error(f"❌ خطأ في إنشاء الحساب اليدوي: {str(e)}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ غير متوقع: {str(e)}")

def process_manual_account_creation(message):
    """معالجة إنشاء الحساب اليدوي"""
    try:
        # الحصول على بيانات الجلسة
        session_data = active_email_creations.get(message.chat.id)
        if not session_data:
            bot.send_message(message.chat.id, "❌ انتهت الجلسة! يرجى البدء من جديد.")
            return
        
        otp = message.text.strip()
        
        if not otp.isdigit() or len(otp) != 6:
            bot.send_message(message.chat.id, "❌ كود التحقق يجب أن يكون 6 أرقام! حاول مرة أخرى.")
            bot.register_next_step_handler(message, process_manual_account_creation)
            return
        
        bot.send_message(message.chat.id, f"✅ كود التحقق المستلم: {otp}\n⏳ جاري إنشاء الحساب...")
        
        # إنشاء الحساب
        creator = session_data['creator']
        result = creator.create_account(
            session_data['email'],
            otp,
            session_data['username'],
            session_data['password']
        )
        
        # حذف بيانات الجلسة
        if message.chat.id in active_email_creations:
            del active_email_creations[message.chat.id]
        
        if result.get('success', False):
            success_msg = f"""
🎉 *تم إنشاء الحساب بنجاح!*

📋 *معلومات الحساب:*
• **اليوزر:** `{result['username']}`
• **الباسوورد:** `{session_data['password']}`
• **الإيميل:** `{session_data['email']}`
• **User ID:** {result.get('user_id', 'N/A')}

✅ *تم حفظ الحساب في قاعدة البيانات.*
            """
            bot.send_message(message.chat.id, success_msg, parse_mode='Markdown')
        else:
            error_msg = result.get('message', 'خطأ غير معروف')
            bot.send_message(
                message.chat.id,
                f"❌ فشل إنشاء الحساب:\n`{error_msg}`\n\n"
                f"💡 *الحلول المقترحة:*\n"
                f"1. استخدم إيميل مختلف\n"
                f"2. جرب بروكسي جديد\n"
                f"3. انتظر قليلاً ثم حاول\n"
                f"4. تغيير اسم المستخدم",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logging.error(f"❌ خطأ في process_manual_account_creation: {str(e)}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")
        
        # تنظيف بيانات الجلسة في حالة الخطأ
        if message.chat.id in active_email_creations:
            del active_email_creations[message.chat.id]

@bot.message_handler(func=lambda m: m.text == '📋 عرض الحسابات')
def show_accounts(message):
    """عرض الحسابات"""
    try:
        if not os.path.exists(ACCOUNTS_FILE):
            bot.send_message(message.chat.id, "⚠️ لم يتم إنشاء أي حسابات بعد.")
            return
        
        with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        
        if not accounts:
            bot.send_message(message.chat.id, "⚠️ لم يتم إنشاء أي حسابات بعد.")
            return
        
        response = f"📋 *الحسابات المنشأة ({len(accounts)}):*\n\n"
        for i, acc in enumerate(accounts[-5:], 1):
            response += f"*{i}. {acc['username']}*\n"
            response += f"   🔐 `{acc['password']}`\n"
            response += f"   📧 {acc['email']}\n"
            response += f"   🕐 {acc['created_at'][:10]}\n\n"
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في عرض الحسابات: {str(e)}")

@bot.message_handler(func=lambda m: m.text == '📊 عرض البروكسيات')
def show_proxies(message):
    """عرض البروكسيات"""
    try:
        load_proxies()
        
        if not proxies_pool:
            bot.send_message(message.chat.id, "⚠️ لا يوجد بروكسيات شغالة.")
            return
        
        response = f"📊 *البروكسيات الشغالة ({len(proxies_pool)}):*\n\n"
        for i, proxy in enumerate(proxies_pool[:5], 1):
            proxy_info = proxy if isinstance(proxy, str) else proxy.get('proxy', 'N/A')
            response += f"{i}. `{proxy_info}`\n"
        
        if len(proxies_pool) > 5:
            response += f"\n... و {len(proxies_pool)-5} بروكسي إضافي"
        
        # إضافة إحصائيات
        response += f"\n\n📈 *إحصائيات:*\n"
        response += f"• آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        response += f"• User-Agent: {len(user_agents)}\n"
        response += f"• حجم المجموعة: {len(proxies_pool)}"
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في عرض البروكسيات: {str(e)}")

@bot.message_handler(func=lambda m: m.text == '⚡ فحص بروكسيات سريع')
def quick_check_proxies(message):
    """فحص بروكسيات سريع"""
    msg = bot.send_message(message.chat.id, "⚡ جاري فحص سريع للبروكسيات...")
    
    try:
        # تحميل البروكسيات الحالية
        load_proxies()
        
        if not proxies_pool:
            bot.edit_message_text("⚠️ لا يوجد بروكسيات للفحص!", message.chat.id, msg.message_id)
            return
        
        # اختيار عينة عشوائية
        sample_size = min(20, len(proxies_pool))
        sample_proxies = random.sample(proxies_pool, sample_size)
        
        working_proxies = []
        checker = AdvancedProxyChecker()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(checker.check_proxy_advanced, 
                      proxy if isinstance(proxy, str) else proxy.get('proxy', '')): proxy 
                      for proxy in sample_proxies}
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                result = future.result()
                
                if result.get('working', False):
                    working_proxies.append(result)
                
                # تحديث التقدم
                progress = int((completed / sample_size) * 100)
                bot.edit_message_text(
                    f"🔍 فحص سريع... {progress}%\n"
                    f"✅ {len(working_proxies)}/{sample_size} شغال",
                    message.chat.id,
                    msg.message_id
                )
        
        if working_proxies:
            # تحديث المجموعة بالبروكسيات الشغالة فقط
            proxies_pool.clear()
            proxies_pool.extend(working_proxies)
            save_proxies(proxies_pool)
            
            bot.edit_message_text(
                f"✅ *تم الفحص السريع بنجاح!*\n\n"
                f"📊 *النتائج:*\n"
                f"• العينة المفحوصة: {sample_size}\n"
                f"• البروكسيات الشغالة: {len(working_proxies)}\n"
                f"• نسبة النجاح: {(len(working_proxies)/sample_size)*100:.1f}%\n\n"
                f"💾 تم تحديث قاعدة البروكسيات",
                message.chat.id,
                msg.message_id,
                parse_mode='Markdown'
            )
        else:
            bot.edit_message_text(
                "❌ لم ينجح أي بروكسي في الفحص السريع!\n"
                "جرب سحب بروكسيات جديدة.",
                message.chat.id,
                msg.message_id
            )
            
    except Exception as e:
        logging.error(f"❌ خطأ في الفحص السريع: {str(e)}")
        bot.edit_message_text(f"❌ حدث خطأ: {str(e)}", message.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: m.text == '🔄 سحب بروكسيات قوية')
def scrape_proxies(message):
    """سحب بروكسيات من مصادر متعددة"""
    msg = bot.send_message(message.chat.id, "🌐 جاري سحب بروكسيات قوية من 40+ مصدر...")
    
    try:
        all_proxies = []
        successful_sources = 0
        
        # الجمع بين المصادر العادية والمتميزة
        all_sources = SOURCES + PREMIUM_SOURCES
        
        for i, source in enumerate(all_sources, 1):
            try:
                bot.edit_message_text(
                    f"🌐 سحب بروكسيات... المصدر {i}/{len(all_sources)}",
                    message.chat.id,
                    msg.message_id
                )
                
                headers = {'User-Agent': get_random_user_agent()}
                response = requests.get(source, timeout=10, headers=headers)
                
                if response.status_code == 200:
                    # استخراج جميع أنواع البروكسيات
                    patterns = [
                        r'\d+\.\d+\.\d+\.\d+:\d+',  # IP:Port
                        r'http://\d+\.\d+\.\d+\.\d+:\d+',  # http://IP:Port
                        r'https://\d+\.\d+\.\d+\.\d+:\d+',  # https://IP:Port
                        r'socks4://\d+\.\d+\.\d+\.\d+:\d+',  # socks4://IP:Port
                        r'socks5://\d+\.\d+\.\d+\.\d+:\d+',  # socks5://IP:Port
                    ]
                    
                    for pattern in patterns:
                        proxies = re.findall(pattern, response.text)
                        all_proxies.extend(proxies)
                    
                    successful_sources += 1
                    logging.info(f"✅ المصدر {i}: تم سحب {len(proxies)} بروكسي")
                else:
                    logging.warning(f"⚠️ المصدر {i}: فشل برمز {response.status_code}")
                    
            except Exception as e:
                logging.warning(f"⚠️ المصدر {i}: فشل - {str(e)}")
                continue
        
        # إزالة التكرارات
        unique_proxies = list(set(all_proxies))
        
        bot.edit_message_text(
            f"📥 تم سحب {len(unique_proxies)} بروكسي فريد من {successful_sources} مصدر.\n"
            f"🔍 جاري الفحص المتقدم...",
            message.chat.id,
            msg.message_id
        )
        
        working_proxies = []
        checker = AdvancedProxyChecker()
        total_to_check = min(300, len(unique_proxies))
        
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = {executor.submit(checker.check_proxy_advanced, proxy): proxy 
                      for proxy in unique_proxies[:total_to_check]}
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                result = future.result()
                
                if result.get('working', False):
                    working_proxies.append(result)
                
                # تحديث التقدم كل 20 بروكسي
                if completed % 20 == 0 or completed == total_to_check:
                    progress = int((completed / total_to_check) * 100)
                    bot.edit_message_text(
                        f"🔍 فحص متقدم... {progress}%\n"
                        f"✅ وجدنا {len(working_proxies)} بروكسي شغال\n"
                        f"⚡ أسرع بروكسي: {min([p.get('speed', 99) for p in working_proxies] + [99]):.2f}ث",
                        message.chat.id,
                        msg.message_id
                    )
        
        if working_proxies:
            # ترتيب البروكسيات حسب السرعة
            working_proxies.sort(key=lambda x: x.get('speed', 99))
            
            # حفظ البروكسيات
            save_proxies(working_proxies)
            
            # تحديث المجموعة
            global proxies_pool
            proxies_pool = working_proxies
            
            final_msg = f"""
✅ *تم سحب وفحص البروكسيات بنجاح!*

📊 *الإحصائيات:*
• المصادر المفحوصة: {successful_sources}/{len(all_sources)}
• البروكسيات المسحوبة: {len(unique_proxies)}
• البروكسيات المفحوصة: {total_to_check}
• ✅ **البروكسيات الشغالة: {len(working_proxies)}**
• ⚡ **أسرع بروكسي: {working_proxies[0].get('speed')} ثانية**

🎯 *أفضل 3 بروكسيات:*
1. `{working_proxies[0].get('proxy')}` ({working_proxies[0].get('speed')}ث)
2. `{working_proxies[1].get('proxy') if len(working_proxies) > 1 else 'N/A'}`
3. `{working_proxies[2].get('proxy') if len(working_proxies) > 2 else 'N/A'}`

💾 تم حفظ البروكسيات في قاعدة البيانات.
            """
            bot.edit_message_text(final_msg, message.chat.id, msg.message_id, parse_mode='Markdown')
        else:
            bot.edit_message_text(
                "❌ لم ينجح أي بروكسي في الفحص!\n"
                "قد تكون جميع المصادر غير متاحة مؤقتاً.",
                message.chat.id,
                msg.message_id
            )
            
    except Exception as e:
        logging.error(f"❌ خطأ في سحب البروكسيات: {str(e)}")
        bot.edit_message_text(f"❌ حدث خطأ: {str(e)}", message.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: m.text == '🎯 إعدادات متقدمة')
def advanced_settings(message):
    """عرض الإعدادات المتقدمة"""
    try:
        stats_msg = f"""
🎯 *الإعدادات المتقدمة*

📊 *إحصائيات النظام:*
• البروكسيات المحملة: {len(proxies_pool)}
• User-Agent المتاحة: {len(user_agents)}
• الحسابات المنشأة: {get_accounts_count()}
• آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}

⚙️ *خيارات متقدمة:*
1. `/clean` - تنظيف البروكسيات القديمة
2. `/export` - تصدير البيانات
3. `/stats` - إحصائيات مفصلة
4. `/restart` - إعادة تشغيل النظام

🔧 *إعدادات المطور:*
• Token: `{API_TOKEN[:15]}...`
• ملف البروكسيات: `{PROXY_FILE}`
• ملف الحسابات: `{ACCOUNTS_FILE}`
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        btn1 = telebot.types.InlineKeyboardButton("🗑️ تنظيف البروكسيات", callback_data="clean_proxies")
        btn2 = telebot.types.InlineKeyboardButton("📤 تصدير البيانات", callback_data="export_data")
        btn3 = telebot.types.InlineKeyboardButton("🔄 إعادة التحميل", callback_data="reload_data")
        btn4 = telebot.types.InlineKeyboardButton("❌ إغلاق", callback_data="close_settings")
        markup.add(btn1, btn2)
        markup.add(btn3, btn4)
        
        bot.send_message(message.chat.id, stats_msg, parse_mode='Markdown', reply_markup=markup)
        
    except Exception as e:
        logging.error(f"❌ خطأ في الإعدادات المتقدمة: {str(e)}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة Callback Queries"""
    try:
        if call.data == "clean_proxies":
            bot.answer_callback_query(call.id, "جاري تنظيف البروكسيات...")
            clean_old_proxies(call.message)
            
        elif call.data == "export_data":
            bot.answer_callback_query(call.id, "جاري تصدير البيانات...")
            export_data(call.message)
            
        elif call.data == "reload_data":
            bot.answer_callback_query(call.id, "جاري إعادة التحميل...")
            reload_system_data(call.message)
            
        elif call.data == "close_settings":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            
        elif call.data == "retry_auto_create":
            bot.answer_callback_query(call.id, "جاري إعادة المحاولة...")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            auto_create_instagram_account(call.message, max_attempts=3)
            
    except Exception as e:
        logging.error(f"❌ خطأ في handle_callback: {str(e)}")

def clean_old_proxies(message):
    """تنظيف البروكسيات القديمة"""
    try:
        load_proxies()
        
        if not proxies_pool:
            bot.send_message(message.chat.id, "⚠️ لا يوجد بروكسيات لتنظيفها.")
            return
        
        # الاحتفاظ بالبروكسيات التي تم اختبارها خلال 24 ساعة
        now = datetime.now()
        fresh_proxies = []
        
        for proxy in proxies_pool:
            if isinstance(proxy, dict):
                tested_at = proxy.get('tested_at')
                if tested_at:
                    try:
                        tested_time = datetime.fromisoformat(tested_at)
                        if (now - tested_time).total_seconds() < 86400:  # 24 ساعة
                            fresh_proxies.append(proxy)
                    except:
                        fresh_proxies.append(proxy)
                else:
                    fresh_proxies.append(proxy)
            else:
                fresh_proxies.append(proxy)
        
        # حفظ البروكسيات المحدثة
        save_proxies(fresh_proxies)
        
        bot.send_message(
            message.chat.id,
            f"✅ تم تنظيف البروكسيات!\n"
            f"📊 قبل: {len(proxies_pool)}\n"
            f"📊 بعد: {len(fresh_proxies)}\n"
            f"🗑️ تم حذف: {len(proxies_pool) - len(fresh_proxies)} بروكسي قديم"
        )
        
    except Exception as e:
        logging.error(f"❌ خطأ في تنظيف البروكسيات: {str(e)}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ في التنظيف: {str(e)}")

def export_data(message):
    """تصدير البيانات"""
    try:
        # تجميع البيانات
        data = {
            "exported_at": datetime.now().isoformat(),
            "proxies_count": len(proxies_pool),
            "user_agents_count": len(user_agents),
            "accounts_count": get_accounts_count(),
            "sample_proxies": proxies_pool[:10] if proxies_pool else [],
            "sample_user_agents": user_agents[:5] if user_agents else []
        }
        
        # حفظ في ملف مؤقت
        export_file = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # إرسال الملف
        with open(export_file, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="📤 بيانات النظام المصدرة")
        
        # حذف الملف المؤقت
        os.remove(export_file)
        
    except Exception as e:
        logging.error(f"❌ خطأ في تصدير البيانات: {str(e)}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ في التصدير: {str(e)}")

def reload_system_data(message):
    """إعادة تحميل بيانات النظام"""
    try:
        load_user_agents()
        load_proxies()
        
        bot.send_message(
            message.chat.id,
            f"✅ تم إعادة تحميل البيانات!\n"
            f"📊 البروكسيات: {len(proxies_pool)}\n"
            f"👤 User-Agent: {len(user_agents)}"
        )
        
    except Exception as e:
        logging.error(f"❌ خطأ في إعادة التحميل: {str(e)}")
        bot.send_message(message.chat.id, f"❌ حدث خطأ في إعادة التحميل: {str(e)}")

def get_accounts_count():
    """الحصول على عدد الحسابات"""
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
                return len(accounts)
        return 0
    except:
        return 0

# --- اختبار نظام الإيميلات ---
@bot.message_handler(commands=['test_email'])
def test_email_system(message):
    """اختبار نظام الإيميلات"""
    try:
        bot.send_message(message.chat.id, "🔍 جاري اختبار نظام الإيميلات...")
        
        # إنشاء إيميل مؤقت
        temp_email = TempEmailManager.generate_random_email()
        bot.send_message(message.chat.id, f"📧 تم إنشاء إيميل: `{temp_email}`")
        
        # اختبار الحصول على الرسائل
        messages = TempEmailManager.get_messages(temp_email)
        bot.send_message(message.chat.id, f"📨 عدد الرسائل: {len(messages)}")
        
        if messages:
            for msg in messages[:3]:  # عرض أول 3 رسائل
                bot.send_message(
                    message.chat.id,
                    f"📩 الرسالة:\n"
                    f"من: {msg.get('from')}\n"
                    f"الموضوع: {msg.get('subject')}\n"
                    f"التاريخ: {msg.get('date')}"
                )
        
        bot.send_message(message.chat.id, "✅ تم اختبار نظام الإيميلات بنجاح!")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ في اختبار الإيميلات: {str(e)}")

# --- تهيئة النظام ---
def initialize_system():
    """تهيئة النظام"""
    logging.info("🚀 بدء تهيئة نظام Dexr Pro v3.0...")
    
    # تحميل User-Agent
    load_user_agents()
    
    # تحميل البروكسيات
    load_proxies()
    
    # إنشاء الملفات إذا لم تكن موجودة
    for file in [PROXY_FILE, ACCOUNTS_FILE]:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                if file == PROXY_FILE:
                    json.dump({"proxies": []}, f)
                else:
                    json.dump([], f)
            logging.info(f"📁 تم إنشاء ملف: {file}")
    
    # الحصول على نطاقات الإيميلات المتاحة
    domains = TempEmailManager.get_available_domains()
    if domains:
        logging.info(f"📧 تم تحميل {len(domains)} نطاق إيميل")
    else:
        logging.warning("⚠️ استخدام نطاقات إيميل افتراضية")
    
    logging.info(f"✅ تم التهيئة: {len(user_agents)} User-Agent, {len(proxies_pool)} proxies")

# --- تشغيل البوت ---
if __name__ == "__main__":
    initialize_system()
    
    logging.info("🤖 بدء تشغيل بوت Dexr Pro v3.0...")
    
    try:
        bot.polling(none_stop=True, interval=1, timeout=30)
    except Exception as e:
        logging.error(f"❌ فشل تشغيل البوت: {str(e)}")
