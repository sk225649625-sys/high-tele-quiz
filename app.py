import logging
import re
import sqlite3
import asyncio
import os
import requests
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from bs4 import BeautifulSoup
from telegram import Update, Poll, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    PollAnswerHandler,
)
from telegram.request import HTTPXRequest

# --- LOGGING SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TOKEN = "8685169118:AAHzlsEU2IvWtJ44sFpf3r2JAtzpWPv40a8"
DB_NAME = "quiz_group_data.db"

# 👇 Yahan Apne Links Daalein 👇
WEBSITE_LINK = "https://todayvacancy.in" 
TG_GROUP_LINK = "https://t.me/current_affairs_live_quiz"
PROMO_TEXT = f"🌐 <b>check todayvacancy:</b> <a href='{WEBSITE_LINK}'>Click Here</a>\n📢 <b>Join Telegram:</b> <a href='{TG_GROUP_LINK}'>Click Here</a>"

# 👇 ExamVeda URL Mapping 👇
EXAMVEDA_URLS = {
    "src_ev_aptitude": "https://www.examveda.com/mcq-question-on-arithmetic-ability/",
    "src_ev_reasoning": "https://www.examveda.com/mcq-question-on-competitive-reasoning/",
    "src_ev_nvr": "https://www.examveda.com/mcq-question-on-non-verbal-reasoning/",
    "src_ev_english": "https://www.examveda.com/mcq-question-on-competitive-english/",
    "src_ev_di": "https://www.examveda.com/mcq-question-on-data-interpretation/",
    "src_ev_gk": "https://www.examveda.com/mcq-question-on-general-knowledge/",
    "src_ev_state_gk": "https://www.examveda.com/mcq-question-on-state-gk/",
    "src_ev_history_gk": "https://www.examveda.com/mcq-question-on-history/",
    "src_ev_geo_gk": "https://www.examveda.com/mcq-question-on-geography/",
    "src_ev_physics_gk": "https://www.examveda.com/mcq-question-on-physics-gk-chapter-wise/",
    "src_ev_chem_gk": "https://www.examveda.com/mcq-question-on-chemistry-gk-chapter-wise/",
    "src_ev_bio_gk": "https://www.examveda.com/mcq-question-on-biology-gk-chapter-wise/",
    "src_ev_comp_fund": "https://www.examveda.com/computer-fundamentals/practice-mcq-question-on-computer-fundamental-miscellaneous/",
    "src_ev_os": "https://www.examveda.com/computer-fundamentals/practice-mcq-question-on-operating-system/",
    "src_ev_ms_word": "https://www.examveda.com/computer-fundamentals/practice-mcq-question-on-ms-word/",
    "src_ev_ms_excel": "https://www.examveda.com/computer-fundamentals/practice-mcq-question-on-ms-excel/",
    "src_ev_ms_ppt": "https://www.examveda.com/computer-fundamentals/practice-mcq-question-on-power-point/",
    "src_ev_ds": "https://www.examveda.com/mcq-question-on-data-science/",
    "src_ev_ml": "https://www.examveda.com/computer-science/practice-mcq-question-on-machine-learning/",
    "src_ev_cloud": "https://www.examveda.com/computer-science/practice-mcq-question-on-cloud-computing/",
    "src_ev_eng_auto": "https://www.examveda.com/mcq-question-on-automobile-engineering/",
    "src_ev_eng_cse": "https://www.examveda.com/mcq-question-on-computer-science/",
    "src_ev_eng_ece": "https://www.examveda.com/mcq-question-on-electronics-and-communications-engineering/",
    "src_ev_eng_elec": "https://www.examveda.com/mcq-question-on-electrical-engineering/",
    "src_ev_eng_mech": "https://www.examveda.com/mcq-question-on-mechanical-engineering/",
    "src_ev_eng_civil": "https://www.examveda.com/mcq-question-on-civil-engineering/",
    "src_ev_eng_chem": "https://www.examveda.com/mcq-question-on-chemical-engineering/",
    "src_ev_eng_bio": "https://www.examveda.com/mcq-question-on-biotechnology-engineering/",
    "src_ev_eng_mine": "https://www.examveda.com/mcq-question-on-mining-engineering/",
    "src_ev_eng_meta": "https://www.examveda.com/mcq-question-on-metallurgical-engineering/",
    "src_ev_eng_maths": "https://www.examveda.com/mcq-question-on-engineering-maths/",
    "src_ev_eng_phys": "https://www.examveda.com/mcq-question-on-engineering-physics/",
    "src_ev_eng_chemy": "https://www.examveda.com/mcq-question-on-engineering-chemistry/",
    "src_ev_grad_com": "https://www.examveda.com/mcq-question-on-commerce/",
    "src_ev_grad_man": "https://www.examveda.com/mcq-question-on-management/",
    "src_ev_grad_law": "https://www.examveda.com/mcq-question-on-law/",
    "src_ev_grad_agri": "https://www.examveda.com/mcq-question-on-agriculture/",
    "src_ev_grad_soc": "https://www.examveda.com/mcq-question-on-sociology/",
    "src_ev_grad_pol": "https://www.examveda.com/mcq-question-on-political-science/",
    "src_ev_grad_psy": "https://www.examveda.com/mcq-question-on-psychology/",
    "src_ev_grad_home": "https://www.examveda.com/mcq-question-on-home-science/",
    "src_ev_grad_pha": "https://www.examveda.com/mcq-question-on-pharmacy/",
    "src_ev_grad_mass": "https://www.examveda.com/mcq-question-on-mass-communication-and-journalism/",
    "src_ev_grad_phil": "https://www.examveda.com/mcq-question-on-philosophy/",
    "src_ev_ca_month": "https://www.examveda.com/current-affairs/month-wise/",
    "src_ev_ca_down": "https://www.examveda.com/current-affairs/download/",
    "src_ev_int_hr": "https://www.examveda.com/interview/hr-interview-questions-and-answers/",
    "src_ev_int_bank": "https://www.examveda.com/interview/banking-interview-questions-and-answers/",
    "src_ev_int_tech": "https://www.examveda.com/interview/technical-interview-questions-and-answers/",
    "src_ev_bank_aware": "https://www.examveda.com/banking-awareness/practice-mcq-question-on-banking-awareness-miscellaneous/",
    "src_ev_bank_int": "https://www.examveda.com/interview/banking-interview-questions-and-answers/",
}

# 👇 IndiaBix URL Mapping 👇
INDIABIX_URLS = {
    "src_ib_arithmetic": "https://www.indiabix.com/aptitude/questions-and-answers/",
    "src_ib_di": "https://www.indiabix.com/data-interpretation/questions-and-answers/",
    "src_ib_verbal_ab": "https://www.indiabix.com/verbal-ability/questions-and-answers/",
    "src_ib_logical": "https://www.indiabix.com/logical-reasoning/questions-and-answers/",
    "src_ib_verbal_re": "https://www.indiabix.com/verbal-reasoning/questions-and-answers/",
    "src_ib_non_verbal": "https://www.indiabix.com/non-verbal-reasoning/questions-and-answers/",
    "src_ib_ca": "https://www.indiabix.com/current-affairs/questions-and-answers/",
    "src_ib_gk": "https://www.indiabix.com/general-knowledge/questions-and-answers/",
    "src_ib_science": "https://www.indiabix.com/general-knowledge/general-science/",
    "src_ib_hr": "https://www.indiabix.com/hr-interview/questions-and-answers/",
    "src_ib_gd": "https://www.indiabix.com/group-discussion/topics-with-answers/",
    "src_ib_place": "https://www.indiabix.com/placement-papers/companies/",
    "src_ib_tech_int": "https://www.indiabix.com/technical/interview-questions-and-answers/",
    "src_ib_mech": "https://www.indiabix.com/mechanical-engineering/questions-and-answers/",
    "src_ib_civil": "https://www.indiabix.com/civil-engineering/questions-and-answers/",
    "src_ib_ece": "https://www.indiabix.com/electronics-and-communication-engineering/questions-and-answers/",
    "src_ib_eee": "https://www.indiabix.com/electrical-engineering/questions-and-answers/",
    "src_ib_cse": "https://www.indiabix.com/computer-science/questions-and-answers/",
    "src_ib_chem": "https://www.indiabix.com/chemical-engineering/questions-and-answers/",
    "src_ib_c": "https://www.indiabix.com/c-programming/questions-and-answers/",
    "src_ib_cpp": "https://www.indiabix.com/cpp-programming/questions-and-answers/",
    "src_ib_csharp": "https://www.indiabix.com/c-sharp-programming/questions-and-answers/",
    "src_ib_java": "https://www.indiabix.com/java-programming/questions-and-answers/",
    "src_ib_db": "https://www.indiabix.com/database/questions-and-answers/",
    "src_ib_net": "https://www.indiabix.com/networking/questions-and-answers/",
}

# --- NETWORK SESSION (ADVANCED REAL BROWSER BYPASS) ---
try:
    from curl_cffi import requests as cffi_requests
    SESSION = cffi_requests.Session(impersonate="chrome120")
    logger.info("✅ Using curl_cffi for Advanced Real Chrome Browser Impersonation")
except ImportError:
    import cloudscraper
    SESSION = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    logger.info("✅ Using cloudscraper as fallback")

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    'Referer': 'https://www.google.com/'
}

# Universal Fetch Function
def fetch_url(url):
    try:
        if hasattr(SESSION, 'impersonate'):
            return SESSION.get(url, timeout=20)
        else:
            return SESSION.get(url, headers=HEADERS, timeout=20)
    except Exception as e:
        logger.error(f"Fetch Error URL {url}: {e}")
        return None

# --- DUMMY WEB SERVER FOR RENDER ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is alive and running on Render!")

    def log_message(self, format, *args):
        pass # Console clean rakhne ke liye log disable kiya hai

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, DummyHandler)
    logger.info(f"Starting dummy web server on port {port} to satisfy Render health checks...")
    httpd.serve_forever()

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            points INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_state (
            chat_id INTEGER PRIMARY KEY,
            current_index INTEGER DEFAULT 0,
            selected_source TEXT DEFAULT 'src_ev_gk', 
            current_page INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_state(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT current_index, selected_source, current_page FROM quiz_state WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if row: return row
    return (0, "src_ev_gk", 1)

def update_state(chat_id, index, source, page):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM quiz_state WHERE chat_id = ?", (chat_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE quiz_state SET current_index=?, selected_source=?, current_page=? WHERE chat_id=?", (index, source, page, chat_id))
    else:
        cursor.execute("INSERT INTO quiz_state (chat_id, current_index, selected_source, current_page) VALUES (?, ?, ?, ?)", (chat_id, index, source, page))
    conn.commit()
    conn.close()

def update_index(chat_id, new_idx):
    current_state = get_state(chat_id)
    update_state(chat_id, new_idx, current_state[1], current_state[2])

def reset_data(chat_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE quiz_state SET current_index = 0, current_page = 1 WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

# --- ADMIN CHECK HELPER ---
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type == 'private':
        return True 
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        if member.status in ['administrator', 'creator']:
            return True
        else:
            await update.message.reply_text("⚠️ <b>Sirf Group Admins hi is command ko use kar sakte hain.</b>", parse_mode="HTML")
            return False
    except Exception as e:
        logger.error(f"Admin Check Error: {e}")
        return False

# ==========================================
# 1. EXAMVEDA SCRAPER
# ==========================================
def extract_examveda(soup):
    questions = []
    articles = soup.find_all('article', class_='question')
    for art in articles:
        try:
            q_main = art.find('div', class_='question-main')
            if not q_main: continue
            q_text = q_main.get_text(strip=True)
            
            options = []
            opt_div = art.find('div', class_='question-options')
            if not opt_div: continue
            
            p_tags = opt_div.find_all('p')
            for p in p_tags:
                if 'hidden' in p.get('class', []): continue
                labels = p.find_all('label')
                if len(labels) >= 2:
                    opt_text = labels[1].get_text(strip=True)
                else:
                    opt_text = p.get_text(strip=True)
                    opt_text = re.sub(r'^[A-E]\.\s*', '', opt_text)
                
                if opt_text: options.append(opt_text[:100])
            
            if len(options) < 2: continue
            
            ans_hidden = opt_div.find('input', type='hidden')
            if not ans_hidden: continue
            
            correct_val = int(ans_hidden['value']) - 1
            if 0 <= correct_val < len(options):
                questions.append({'q': q_text[:300], 'options': options, 'correct': correct_val})
        except Exception as e:
            continue
    return questions

def scrape_examveda(base_url, page):
    pg = page if page > 0 else 1
    sep = "&" if "?" in base_url else "?"
    url = f"{base_url}{sep}page={pg}"
    try:
        res = fetch_url(url)
        if not res: return url, []
        soup = BeautifulSoup(res.content, 'lxml')
        qs = extract_examveda(soup)
        return url, qs
    except Exception as e:
        logger.error(f"ExamVeda Scrape Error: {e}")
        return url, []

# ==========================================
# 2. INDIABIX SCRAPER
# ==========================================
def extract_indiabix(soup):
    questions = []
    containers = soup.find_all('div', class_='bix-div-container')
    
    for container in containers:
        try:
            q_td = container.find('div', class_='bix-td-qtxt')
            if not q_td: continue
            q_text = q_td.get_text(strip=True)
            
            options = []
            opts_container = container.find('div', class_='bix-tbl-options')
            if not opts_container: continue
            
            opt_rows = opts_container.find_all('div', class_='bix-opt-row')
            for row in opt_rows:
                val_div = row.find('div', class_='bix-td-option-val')
                if val_div:
                    opt_text = val_div.get_text(strip=True)
                    if opt_text:
                        options.append(opt_text[:100])
            
            if len(options) < 2: continue
            
            ans_hidden = container.find('input', class_='jq-hdnakq')
            if not ans_hidden: continue
            ans_letter = ans_hidden.get('value', '').strip().upper()
            
            ans_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
            if ans_letter in ans_map:
                correct_val = ans_map[ans_letter]
                if 0 <= correct_val < len(options):
                    questions.append({
                        'q': q_text[:300],
                        'options': options,
                        'correct': correct_val
                    })
        except Exception as e:
            continue
    return questions

def scrape_indiabix(base_url, page):
    url = base_url
    if page > 1:
        try:
            res1 = fetch_url(base_url)
            if res1:
                soup1 = BeautifulSoup(res1.content, 'lxml')
                page_link = soup1.find('a', string=str(page))
                if page_link and 'href' in page_link.attrs:
                    url = page_link['href']
                    if not url.startswith('http'):
                        url = "https://www.indiabix.com" + url
                else:
                    return base_url, []
        except Exception as e:
            logger.error(f"IndiaBix Pagination Error: {e}")
            return base_url, []

    try:
        res = fetch_url(url)
        if not res: return url, []
        soup = BeautifulSoup(res.content, 'lxml')
        qs = extract_indiabix(soup)
        return url, qs
    except Exception as e:
        logger.error(f"IndiaBix Scrape Error: {e}")
        return url, []

# ==========================================
# 3. CHRONICLE INDIA SCRAPER (NEW)
# ==========================================
def extract_chronicle(soup):
    questions = []
    
    # Chronicle quiz questions hamesha class="qnans" wale div me aate hain
    qnans_div = soup.find('div', class_='qnans')
    if not qnans_div:
        return questions

    current_q = None
    current_options = []
    correct_val = 0
    
    # Sequential parsing: paragraphs(Q), table(Options), div(Answer)
    for elem in qnans_div.find_all(['p', 'table', 'div']):
        # 1. QUESTION EXTRACT KAREN
        if elem.name == 'p' and elem.get('style') and 'inline' in elem.get('style'):
            # Agar pichla question complete ho gaya tha, toh usko list me daalo
            if current_q and len(current_options) >= 2:
                questions.append({
                    'q': current_q[:300], 
                    'options': current_options[:5], 
                    'correct': correct_val
                })
            
            q_text = elem.get_text(strip=True)
            # "[1]. " ya "1. " format ko hata kar saaf sawal nikalna
            current_q = re.sub(r'^\[?\d+\]?\.\s*', '', q_text)
            current_options = []
            correct_val = 0
            
        # 2. OPTIONS EXTRACT KAREN
        elif elem.name == 'table' and current_q is not None and not current_options:
            tds = elem.find_all('td')
            for td in tds:
                opt_text = td.get_text(strip=True)
                # "[A]. " ya "[B]. " format ko hata kar sirf option text rakhna
                opt_text = re.sub(r'^\[[A-Ea-e]\]\.\s*', '', opt_text)
                if opt_text:
                    current_options.append(opt_text[:100])
                    
        # 3. CORRECT ANSWER EXTRACT KAREN
        elif elem.name == 'div' and 'current_quiz_answer' in elem.get('class', []):
            ans_inner = elem.find('div', class_='ques_answer')
            if ans_inner:
                ans_text = ans_inner.get_text(strip=True)
                # "Correct Answer: B [चिली]" me se "B" nikalna
                match = re.search(r'Correct Answer:\s*([A-Ea-e])', ans_text, re.IGNORECASE)
                if match:
                    ans_letter = match.group(1).upper()
                    ans_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
                    correct_val = ans_map.get(ans_letter, 0)

    # Aakhiri sawal ko loop ke bahar list me jodna
    if current_q and len(current_options) >= 2:
        questions.append({
            'q': current_q[:300], 
            'options': current_options[:5], 
            'correct': correct_val
        })
        
    return questions

def scrape_chronicle(url, page):
    try:
        res = fetch_url(url)
        if not res: return url, []
        soup = BeautifulSoup(res.content, 'lxml')
        qs = extract_chronicle(soup)
        return url, qs
    except Exception as e:
        logger.error(f"Chronicle Scrape Error: {e}")
        return url, []

# ==========================================
# KEYBOARD MENUS (UI BUILDING)
# ==========================================
def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 ExamVeda (Maths, Reasoning, etc.)", callback_data="menu_examveda")],
        [InlineKeyboardButton("🎓 IndiaBix (Aptitude, Programming)", callback_data="menu_indiabix")],
        [InlineKeyboardButton("📰 Chronicle (Hindi Current Affairs)", callback_data="menu_chronicle")]
    ])

def get_examveda_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏆 1. Competitive Exam MCQ", callback_data="ev_cat_1")],
        [InlineKeyboardButton("💻 2. Computer Related MCQ", callback_data="ev_cat_2")],
        [InlineKeyboardButton("⚙️ 3. Engineering & GATE MCQ", callback_data="ev_cat_3")],
        [InlineKeyboardButton("🎓 4. Graduate & Post Graduate", callback_data="ev_cat_4")],
        [InlineKeyboardButton("🎯 5. Current Affairs", callback_data="ev_cat_5")],
        [InlineKeyboardButton("🤝 6. Interview Q/A", callback_data="ev_cat_6")],
        [InlineKeyboardButton("🏦 7. Banking Awareness", callback_data="ev_cat_7")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")]
    ])

def get_indiabix_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📐 General Aptitude", callback_data="ib_cat_aptitude")],
        [InlineKeyboardButton("🧠 Verbal & Reasoning", callback_data="ib_cat_reasoning")],
        [InlineKeyboardButton("🌍 Current Affairs & GK", callback_data="ib_cat_gk")],
        [InlineKeyboardButton("🤝 Interview", callback_data="ib_cat_interview")],
        [InlineKeyboardButton("⚙️ Engineering", callback_data="ib_cat_engineering")],
        [InlineKeyboardButton("💻 Programming", callback_data="ib_cat_programming")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")]
    ])

def get_ib_aptitude_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Arithmetic Aptitude", callback_data="src_ib_arithmetic")],
        [InlineKeyboardButton("Data Interpretation", callback_data="src_ib_di")],
        [InlineKeyboardButton("🔙 Back to IndiaBix", callback_data="menu_indiabix")]
    ])

def get_ib_reasoning_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Verbal Ability", callback_data="src_ib_verbal_ab"), InlineKeyboardButton("Logical Reasoning", callback_data="src_ib_logical")],
        [InlineKeyboardButton("Verbal Reasoning", callback_data="src_ib_verbal_re"), InlineKeyboardButton("Nonverbal Reasoning", callback_data="src_ib_non_verbal")],
        [InlineKeyboardButton("🔙 Back to IndiaBix", callback_data="menu_indiabix")]
    ])

def get_ib_gk_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Current Affairs", callback_data="src_ib_ca"), InlineKeyboardButton("General Knowledge", callback_data="src_ib_gk")],
        [InlineKeyboardButton("General Science", callback_data="src_ib_science")],
        [InlineKeyboardButton("🔙 Back to IndiaBix", callback_data="menu_indiabix")]
    ])

def get_ib_interview_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("HR Interview", callback_data="src_ib_hr"), InlineKeyboardButton("Group Discussion", callback_data="src_ib_gd")],
        [InlineKeyboardButton("Placement Papers", callback_data="src_ib_place"), InlineKeyboardButton("Technical Interview", callback_data="src_ib_tech_int")],
        [InlineKeyboardButton("🔙 Back to IndiaBix", callback_data="menu_indiabix")]
    ])

def get_ib_engineering_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Mechanical", callback_data="src_ib_mech"), InlineKeyboardButton("Civil", callback_data="src_ib_civil")],
        [InlineKeyboardButton("ECE", callback_data="src_ib_ece"), InlineKeyboardButton("EEE", callback_data="src_ib_eee")],
        [InlineKeyboardButton("CSE", callback_data="src_ib_cse"), InlineKeyboardButton("Chemical", callback_data="src_ib_chem")],
        [InlineKeyboardButton("🔙 Back to IndiaBix", callback_data="menu_indiabix")]
    ])

def get_ib_programming_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("C Programming", callback_data="src_ib_c"), InlineKeyboardButton("C++ Programming", callback_data="src_ib_cpp")],
        [InlineKeyboardButton("C# Programming", callback_data="src_ib_csharp"), InlineKeyboardButton("Java Programming", callback_data="src_ib_java")],
        [InlineKeyboardButton("Database", callback_data="src_ib_db"), InlineKeyboardButton("Networking", callback_data="src_ib_net")],
        [InlineKeyboardButton("🔙 Back to IndiaBix", callback_data="menu_indiabix")]
    ])

def get_ev_cat1_menu(): 
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Aptitude", callback_data="src_ev_aptitude"), InlineKeyboardButton("Reasoning", callback_data="src_ev_reasoning")],
        [InlineKeyboardButton("Non Verbal Reasoning", callback_data="src_ev_nvr"), InlineKeyboardButton("English", callback_data="src_ev_english")],
        [InlineKeyboardButton("DI (Data Interpretation)", callback_data="src_ev_di"), InlineKeyboardButton("GK", callback_data="src_ev_gk")],
        [InlineKeyboardButton("Statewise GK", callback_data="src_ev_state_gk"), InlineKeyboardButton("History GK", callback_data="src_ev_history_gk")],
        [InlineKeyboardButton("Geography GK", callback_data="src_ev_geo_gk"), InlineKeyboardButton("Physics GK", callback_data="src_ev_physics_gk")],
        [InlineKeyboardButton("Chemistry GK", callback_data="src_ev_chem_gk"), InlineKeyboardButton("Biology GK", callback_data="src_ev_bio_gk")],
        [InlineKeyboardButton("🔙 Back to ExamVeda", callback_data="menu_examveda")]
    ])

def get_ev_cat2_menu(): 
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Computer Fundamental", callback_data="src_ev_comp_fund"), InlineKeyboardButton("Operating System", callback_data="src_ev_os")],
        [InlineKeyboardButton("MS Word", callback_data="src_ev_ms_word"), InlineKeyboardButton("MS Excel", callback_data="src_ev_ms_excel")],
        [InlineKeyboardButton("MS PowerPoint", callback_data="src_ev_ms_ppt"), InlineKeyboardButton("Data Science", callback_data="src_ev_ds")],
        [InlineKeyboardButton("Machine Learning", callback_data="src_ev_ml"), InlineKeyboardButton("Cloud Computing", callback_data="src_ev_cloud")],
        [InlineKeyboardButton("🔙 Back to ExamVeda", callback_data="menu_examveda")]
    ])

def get_ev_cat3_menu(): 
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Automobile", callback_data="src_ev_eng_auto"), InlineKeyboardButton("CSE", callback_data="src_ev_eng_cse")],
        [InlineKeyboardButton("ECE", callback_data="src_ev_eng_ece"), InlineKeyboardButton("Electrical", callback_data="src_ev_eng_elec")],
        [InlineKeyboardButton("Mechanical", callback_data="src_ev_eng_mech"), InlineKeyboardButton("Civil", callback_data="src_ev_eng_civil")],
        [InlineKeyboardButton("Chemical", callback_data="src_ev_eng_chem"), InlineKeyboardButton("Biotech", callback_data="src_ev_eng_bio")],
        [InlineKeyboardButton("Mining", callback_data="src_ev_eng_mine"), InlineKeyboardButton("Metallurgical", callback_data="src_ev_eng_meta")],
        [InlineKeyboardButton("Engg. Maths", callback_data="src_ev_eng_maths"), InlineKeyboardButton("Engg. Physics", callback_data="src_ev_eng_phys")],
        [InlineKeyboardButton("Engg. Chemistry", callback_data="src_ev_eng_chemy")],
        [InlineKeyboardButton("🔙 Back to ExamVeda", callback_data="menu_examveda")]
    ])

def get_ev_cat4_menu(): 
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Commerce", callback_data="src_ev_grad_com"), InlineKeyboardButton("Management", callback_data="src_ev_grad_man")],
        [InlineKeyboardButton("Law", callback_data="src_ev_grad_law"), InlineKeyboardButton("Agriculture", callback_data="src_ev_grad_agri")],
        [InlineKeyboardButton("Sociology", callback_data="src_ev_grad_soc"), InlineKeyboardButton("Political Science", callback_data="src_ev_grad_pol")],
        [InlineKeyboardButton("Psychology", callback_data="src_ev_grad_psy"), InlineKeyboardButton("Home Science", callback_data="src_ev_grad_home")],
        [InlineKeyboardButton("Pharmacy", callback_data="src_ev_grad_pha"), InlineKeyboardButton("Mass Comm", callback_data="src_ev_grad_mass")],
        [InlineKeyboardButton("Philosophy", callback_data="src_ev_grad_phil")],
        [InlineKeyboardButton("🔙 Back to ExamVeda", callback_data="menu_examveda")]
    ])

def get_ev_cat5_menu(): 
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Month Wise Current Affair", callback_data="src_ev_ca_month")],
        [InlineKeyboardButton("Current Affair Download", callback_data="src_ev_ca_down")],
        [InlineKeyboardButton("🔙 Back to ExamVeda", callback_data="menu_examveda")]
    ])

def get_ev_cat6_menu(): 
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("HR Interview", callback_data="src_ev_int_hr"), InlineKeyboardButton("Banking Interview", callback_data="src_ev_int_bank")],
        [InlineKeyboardButton("Technical Interview", callback_data="src_ev_int_tech")],
        [InlineKeyboardButton("🔙 Back to ExamVeda", callback_data="menu_examveda")]
    ])

def get_ev_cat7_menu(): 
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Banking Awareness", callback_data="src_ev_bank_aware")],
        [InlineKeyboardButton("Banking Interview", callback_data="src_ev_bank_int")],
        [InlineKeyboardButton("🔙 Back to ExamVeda", callback_data="menu_examveda")]
    ])

# --- MAIN CONTROLLER ---
CACHED_DATA = {} 
EXAMVEDA_TEMP_CHAPTERS = {} 
INDIABIX_TEMP_CHAPTERS = {} 
CHRONICLE_TEMP_CHAPTERS = {} # Chronicle caching variable

async def fetch_and_start(update, context, source, page, chat_id):
    global CACHED_DATA
    pg = page if page > 0 else 1
    
    if "indiabix" in source:
        url, qs = scrape_indiabix(source, pg)
        src_name = f"IndiaBix - Set {pg}"
    elif "chronicleindia" in source: # Chronicle condition
        url, qs = scrape_chronicle(source, pg)
        src_name = f"Chronicle Hindi CA"
    else:
        url, qs = scrape_examveda(source, pg)
        src_name = f"ExamVeda - Set {pg}"

    if not qs:
        await context.bot.send_message(chat_id, "❌ Error: Data nahi mila ya is page par aur sawal nahi hain.")
        return

    CACHED_DATA[chat_id] = qs
    
    job_name = f"quiz_{chat_id}"
    for job in context.job_queue.get_jobs_by_name(job_name): job.schedule_removal()
    
    start_msg = (
        f"🚀 <b>Quiz Started!</b>\n"
        f"📚 Source: {src_name}\n"
        f"📄 Page/Set: {pg}\n"
        f"🔢 Questions: {len(qs)}\n\n"
        f"<i>Starting in 5s...</i>"
    )
    
    await context.bot.send_message(chat_id, start_msg, parse_mode="HTML", disable_web_page_preview=True)
    
    try:
        context.job_queue.run_repeating(send_quiz, interval=25, first=5, chat_id=chat_id, name=job_name)
    except Exception as e:
        logger.error(f"Job Queue Error: {e}. PLEASE CHECK requirements.txt for job-queue package.")
        await context.bot.send_message(chat_id, "⚠️ Error: Quiz start nahi hua. Piche dekhein (logs).")

# --- BOT HANDLERS ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "👋 <b>Namaste! Main Daily Quiz Bot hoon.</b>\n\n"
        "Main aapke group me GK, Maths, aur Current Affairs ke quizzes chala sakta hoon.\n"
        "Quiz shuru karne ke liye /startcomp type karein."
    )
    await update.message.reply_text(welcome_msg, parse_mode="HTML", disable_web_page_preview=True)

async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    await update.message.reply_text(
        "📣 <b>Choose Quiz Category:</b>", 
        reply_markup=get_main_menu(), 
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def button_tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = update.effective_chat.id
    
    if data == "menu_main":
        await context.bot.send_message(chat_id=chat_id, text="📣 <b>Choose Quiz Category:</b>", reply_markup=get_main_menu(), parse_mode="HTML")
    elif data == "menu_examveda":
        await context.bot.send_message(chat_id=chat_id, text="🧠 <b>ExamVeda Main Categories:</b>\n<i>Choose an option below:</i>", reply_markup=get_examveda_main_menu(), parse_mode="HTML")
    elif data == "menu_indiabix":
        await context.bot.send_message(chat_id=chat_id, text="🎓 <b>IndiaBix Categories:</b>\n<i>Choose an option below:</i>", reply_markup=get_indiabix_main_menu(), parse_mode="HTML")
        
    # --- CHRONICLE INDIA MENU HANDLER ---
    elif data == "menu_chronicle":
        await context.bot.send_message(chat_id=chat_id, text="📰 <b>Chronicle Current Affairs</b> लोड हो रहा है...\n<i>कृपया प्रतीक्षा करें ⏳</i>", parse_mode="HTML")
        try:
            res = fetch_url("https://www.chronicleindia.in/hindi/current-affairs-quiz-questions-answers")
            if not res: raise Exception("Fetch failed")
            soup = BeautifulSoup(res.content, 'lxml')
            
            quiz_links = []
            # Extract links based exactly on provided source code layout <div id="w0" class="list-view">
            list_view = soup.find('div', id='w0', class_='list-view')
            if list_view:
                for a_tag in list_view.find_all('a'):
                    title = a_tag.get_text(strip=True)
                    href = a_tag.get('href')
                    if href:
                        if not href.startswith("http"):
                            href = "https://www.chronicleindia.in" + href
                        quiz_links.append({"name": title, "url": href})
            
            if quiz_links:
                keyboard = []
                CHRONICLE_TEMP_CHAPTERS[chat_id] = []
                # Top 10 latest daily quizzes dikhayein
                for idx, link in enumerate(quiz_links[:10]): 
                    btn_name = link["name"][:35] + ".." if len(link["name"]) > 35 else link["name"]
                    CHRONICLE_TEMP_CHAPTERS[chat_id].append(link)
                    keyboard.append([InlineKeyboardButton(btn_name, callback_data=f"chr_chap_{idx}")])
                
                keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")])
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="📰 <b>Chronicle Daily Quizzes:</b>\n👇 नीचे दिए गए किसी भी दिन का क्विज़ चुनें:", 
                    reply_markup=InlineKeyboardMarkup(keyboard), 
                    parse_mode="HTML"
                )
            else:
                await context.bot.send_message(chat_id, "❌ कोई नया क्विज़ लिंक नहीं मिला।")
        except Exception as e:
            logger.error(f"Chronicle Fetch Error: {e}")
            await context.bot.send_message(chat_id, "❌ लोड करने में समस्या आई।", parse_mode="HTML")

    elif data.startswith("chr_chap_"):
        idx = int(data.replace("chr_chap_", ""))
        chapters = CHRONICLE_TEMP_CHAPTERS.get(chat_id, [])
        if idx < len(chapters):
            c_name = chapters[idx]['name'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            c_url = chapters[idx]['url']
            page = 1
            update_state(chat_id, 0, c_url, page)  
            await context.bot.send_message(chat_id=chat_id, text=f"✅ <b>आपने चुना:</b> <code>{c_name}</code>\n🔄 प्रश्न लाये जा रहे हैं...", parse_mode="HTML")
            await fetch_and_start(update, context, c_url, page, chat_id)
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ Session Expired. Please select category again.", parse_mode="HTML")

    elif data == "ib_cat_aptitude":
        await context.bot.send_message(chat_id=chat_id, text="📐 <b>General Aptitude:</b>", reply_markup=get_ib_aptitude_menu(), parse_mode="HTML")
    elif data == "ib_cat_reasoning":
        await context.bot.send_message(chat_id=chat_id, text="🧠 <b>Verbal & Reasoning:</b>", reply_markup=get_ib_reasoning_menu(), parse_mode="HTML")
    elif data == "ib_cat_gk":
        await context.bot.send_message(chat_id=chat_id, text="🌍 <b>Current Affairs & GK:</b>", reply_markup=get_ib_gk_menu(), parse_mode="HTML")
    elif data == "ib_cat_interview":
        await context.bot.send_message(chat_id=chat_id, text="🤝 <b>Interview:</b>", reply_markup=get_ib_interview_menu(), parse_mode="HTML")
    elif data == "ib_cat_engineering":
        await context.bot.send_message(chat_id=chat_id, text="⚙️ <b>Engineering:</b>", reply_markup=get_ib_engineering_menu(), parse_mode="HTML")
    elif data == "ib_cat_programming":
        await context.bot.send_message(chat_id=chat_id, text="💻 <b>Programming:</b>", reply_markup=get_ib_programming_menu(), parse_mode="HTML")

    elif data == "ev_cat_1":
        await context.bot.send_message(chat_id=chat_id, text="🏆 <b>Competitive Exam MCQ (Option 1):</b>", reply_markup=get_ev_cat1_menu(), parse_mode="HTML")
    elif data == "ev_cat_2":
        await context.bot.send_message(chat_id=chat_id, text="💻 <b>Computer Related MCQ (Option 2):</b>", reply_markup=get_ev_cat2_menu(), parse_mode="HTML")
    elif data == "ev_cat_3":
        await context.bot.send_message(chat_id=chat_id, text="⚙️ <b>Engineering & GATE (Option 3):</b>", reply_markup=get_ev_cat3_menu(), parse_mode="HTML")
    elif data == "ev_cat_4":
        await context.bot.send_message(chat_id=chat_id, text="🎓 <b>Graduate & Post Grad (Option 4):</b>", reply_markup=get_ev_cat4_menu(), parse_mode="HTML")
    elif data == "ev_cat_5":
        await context.bot.send_message(chat_id=chat_id, text="🎯 <b>Current Affairs (Option 5):</b>", reply_markup=get_ev_cat5_menu(), parse_mode="HTML")
    elif data == "ev_cat_6":
        await context.bot.send_message(chat_id=chat_id, text="🤝 <b>Interview Questions (Option 6):</b>", reply_markup=get_ev_cat6_menu(), parse_mode="HTML")
    elif data == "ev_cat_7":
        await context.bot.send_message(chat_id=chat_id, text="🏦 <b>Banking Awareness (Option 7):</b>", reply_markup=get_ev_cat7_menu(), parse_mode="HTML")
        
    elif data.startswith("src_ib_"):
        topic_name = data.replace("src_ib_", "").replace("_", " ").upper()
        base_url = INDIABIX_URLS.get(data)
        
        if not base_url:
            await context.bot.send_message(chat_id=chat_id, text="❌ Error: Category not found.", parse_mode="HTML")
            return

        await context.bot.send_message(chat_id=chat_id, text=f"✅ <b>{topic_name}</b> लोड हो रहा है...\n<i>कृपया प्रतीक्षा करें ⏳</i>", parse_mode="HTML")
        
        try:
            res = fetch_url(base_url)
            if not res: raise Exception("Fetch failed")
            soup = BeautifulSoup(res.content, 'lxml')
            
            has_chapters = False
            keyboard = []
            row = []
            INDIABIX_TEMP_CHAPTERS[chat_id] = []
            
            ul_filter = soup.find('ul', class_='need-ul-filter')
            if not ul_filter:
                ul_filter = soup.find('div', class_='topics-wrapper')
                
            if ul_filter:
                a_tags = ul_filter.find_all('a')
                for a_tag in a_tags:
                    has_chapters = True
                    c_name = a_tag.text.strip()
                    c_url = a_tag.get('href', '')
                    
                    if not c_url.startswith("http"):
                        c_url = "https://www.indiabix.com" + c_url
                        
                    btn_name = (c_name[:30] + '..') if len(c_name) > 30 else c_name
                    idx = len(INDIABIX_TEMP_CHAPTERS[chat_id])
                    INDIABIX_TEMP_CHAPTERS[chat_id].append({"name": c_name, "url": c_url})
                    
                    row.append(InlineKeyboardButton(btn_name, callback_data=f"ib_chap_{idx}"))
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
            if row:
                keyboard.append(row)
                
            if has_chapters:
                keyboard.append([InlineKeyboardButton("🔙 Back to IndiaBix", callback_data="menu_indiabix")])
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"📚 <b>{topic_name} Chapters:</b>\n👇 नीचे दिए गए किसी भी चैप्टर को चुनें:", 
                    reply_markup=InlineKeyboardMarkup(keyboard), 
                    parse_mode="HTML"
                )
            else:
                page = 1
                update_state(chat_id, 0, base_url, page)  
                await context.bot.send_message(chat_id=chat_id, text=f"✅ <b>आपने चुना:</b> <code>{topic_name}</code>\n🔄 प्रश्न लाये जा रहे हैं...", parse_mode="HTML")
                await fetch_and_start(update, context, base_url, page, chat_id)

        except Exception as e:
            logger.error(f"Chapter Fetch Error: {e}")
            await context.bot.send_message(chat_id=chat_id, text="❌ लोड करने में समस्या आई।", parse_mode="HTML")

    elif data.startswith("ib_chap_"):
        idx = int(data.replace("ib_chap_", ""))
        chapters = INDIABIX_TEMP_CHAPTERS.get(chat_id, [])
        
        if idx < len(chapters):
            c_name = chapters[idx]['name']
            c_name_safe = c_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            c_url = chapters[idx]['url'] 
            
            page = 1
            update_state(chat_id, 0, c_url, page)  
            
            await context.bot.send_message(chat_id=chat_id, text=f"✅ <b>आपने चुना:</b> <code>{c_name_safe}</code>\n🔄 प्रश्न लाये जा रहे हैं...", parse_mode="HTML")
            await fetch_and_start(update, context, c_url, page, chat_id)
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ Session Expired. Please select category again.", parse_mode="HTML")

    elif data.startswith("src_ev_"):
        topic_name = data.replace("src_ev_", "").replace("_", " ").upper()
        base_url = EXAMVEDA_URLS.get(data)
        if not base_url:
            await context.bot.send_message(chat_id=chat_id, text="❌ Error: Category not found.", parse_mode="HTML")
            return

        await context.bot.send_message(chat_id=chat_id, text=f"✅ <b>{topic_name}</b> लोड हो रहा है...\n<i>कृपया प्रतीक्षा करें ⏳</i>", parse_mode="HTML")
        
        try:
            res = fetch_url(base_url)
            if not res: raise Exception("Fetch failed")
            soup = BeautifulSoup(res.content, 'lxml')
            
            articles = soup.find_all('article')
            has_chapters = False
            keyboard = []
            row = []
            EXAMVEDA_TEMP_CHAPTERS[chat_id] = []
            
            for art in articles:
                h3 = art.find('h3')
                if h3:
                    a_tag = h3.find('a')
                    if a_tag and 'href' in a_tag.attrs:
                        has_chapters = True
                        c_name = a_tag.text.strip()
                        c_url = a_tag['href']
                        
                        btn_name = (c_name[:30] + '..') if len(c_name) > 30 else c_name
                        idx = len(EXAMVEDA_TEMP_CHAPTERS[chat_id])
                        EXAMVEDA_TEMP_CHAPTERS[chat_id].append({"name": c_name, "url": c_url})
                        
                        row.append(InlineKeyboardButton(btn_name, callback_data=f"ev_chap_{idx}"))
                        if len(row) == 2:
                            keyboard.append(row)
                            row = []
            if row:
                keyboard.append(row)
                
            if has_chapters:
                keyboard.append([InlineKeyboardButton("🔙 Back to ExamVeda", callback_data="menu_examveda")])
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"📚 <b>{topic_name} Chapters:</b>\n👇 नीचे दिए गए किसी भी चैप्टर को चुनें:", 
                    reply_markup=InlineKeyboardMarkup(keyboard), 
                    parse_mode="HTML"
                )
            else:
                page = 1
                update_state(chat_id, 0, base_url, page)  
                await context.bot.send_message(chat_id=chat_id, text=f"✅ <b>आपने चुना:</b> <code>{topic_name}</code>\n🔄 प्रश्न लाये जा रहे हैं...", parse_mode="HTML")
                await fetch_and_start(update, context, base_url, page, chat_id)

        except Exception as e:
            logger.error(f"Chapter Fetch Error: {e}")
            await context.bot.send_message(chat_id=chat_id, text="❌ लोड करने में समस्या आई।", parse_mode="HTML")

    elif data.startswith("ev_chap_"):
        idx = int(data.replace("ev_chap_", ""))
        chapters = EXAMVEDA_TEMP_CHAPTERS.get(chat_id, [])
        
        if idx < len(chapters):
            c_name = chapters[idx]['name']
            c_name_safe = c_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            c_url = chapters[idx]['url'] 
            
            page = 1
            update_state(chat_id, 0, c_url, page)  
            
            await context.bot.send_message(chat_id=chat_id, text=f"✅ <b>आपने चुना:</b> <code>{c_name_safe}</code>\n🔄 प्रश्न लाये जा रहे हैं...", parse_mode="HTML")
            await fetch_and_start(update, context, c_url, page, chat_id)
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ Session Expired. Please select category again.", parse_mode="HTML")

async def more_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    chat_id = update.effective_chat.id
    
    if context.job_queue.get_jobs_by_name(f"quiz_{chat_id}"):
        await update.message.reply_text("⚠️ Quiz is running! Please finish it or use /stop first.")
        return

    curr_idx, source, curr_page = get_state(chat_id)
    next_page = curr_page + 1
    
    update_state(chat_id, 0, source, next_page)
    await update.message.reply_text(f"🔄 Loading Next (Page {next_page})...")
    await fetch_and_start(update, context, source, next_page, chat_id)

async def send_quiz(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    curr_idx, _, _ = get_state(chat_id)
    
    qs_list = CACHED_DATA.get(chat_id, [])
    if curr_idx >= len(qs_list):
        await context.bot.send_message(chat_id, "🏁 Done! Use /more for next page.")
        context.job.schedule_removal()
        await show_stats(context, chat_id)
        return

    q = qs_list[curr_idx]
    if len(q['options']) < 2:
        update_index(chat_id, curr_idx + 1)
        return

    try:
        correct_ans_text = q['options'][q['correct']].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # ✅ YAHAN BULB MEIN PROMO TEXT AAYEGA ✅
        promo_explanation = f"Correct Answer: {correct_ans_text}\n\n{PROMO_TEXT}"
        
        msg = await context.bot.send_poll(
            chat_id=chat_id, 
            question=f"Q{curr_idx+1}: {q['q']}", 
            options=q['options'], 
            type=Poll.QUIZ, 
            correct_option_id=q['correct'], 
            open_period=20, 
            is_anonymous=False,
            explanation=promo_explanation,
            explanation_parse_mode="HTML"
        )
        
        context.bot_data[msg.poll.id] = q['correct']
        update_index(chat_id, curr_idx + 1)
    except Exception as e:
        logger.error(f"Error sending poll: {e}")
        update_index(chat_id, curr_idx + 1)

async def poll_ans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ans = update.poll_answer
    if context.bot_data.get(ans.poll_id) == ans.option_ids[0]:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("UPDATE scores SET points = points + 2 WHERE user_id = ?", (ans.user.id,))
        if conn.total_changes == 0:
            conn.execute("INSERT INTO scores (user_id, full_name, points) VALUES (?, ?, 2)", (ans.user.id, ans.user.full_name))
        conn.commit()
        conn.close()

async def show_stats(context, chat_id):
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("SELECT full_name, points FROM scores ORDER BY points DESC LIMIT 10").fetchall()
    conn.close()
    if rows:
        escaped_rows = []
        for i, r in enumerate(rows):
            name = str(r[0]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            escaped_rows.append(f"{i+1}. {name} - {r[1]} pts")
            
        txt = "🏆 <b>GLOBAL LEADERBOARD</b> 🏆\n\n" + "\n".join(escaped_rows)
        await context.bot.send_message(chat_id, txt, parse_mode="HTML", disable_web_page_preview=True)

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    chat_id = update.effective_chat.id
    for job in context.job_queue.get_jobs_by_name(f"quiz_{chat_id}"): job.schedule_removal()
    await update.message.reply_text("🛑 Quiz Stopped.")

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    chat_id = update.effective_chat.id
    for job in context.job_queue.get_jobs_by_name(f"quiz_{chat_id}"): job.schedule_removal()
    reset_data(chat_id)
    await update.message.reply_text("🧹 Database Page/Index Reset Done for this group.")

async def setup_commands(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Bot Start Karein"),
        BotCommand("startcomp", "Quiz Shuru Karein (Admins Only)"),
        BotCommand("stop", "Quiz Rokein (Admins Only)"),
        BotCommand("more", "Agla Page Load Karein"),
        BotCommand("reset", "Quiz Data Reset Karein")
    ])

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()

    init_db()
    logger.info("Bot Live! With Dummy Web Server for Render and CloudScraper.")
    req = HTTPXRequest(connection_pool_size=20, connect_timeout=30, read_timeout=30)
    app = Application.builder().token(TOKEN).request(req).post_init(setup_commands).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("startcomp", start_menu))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("more", more_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CallbackQueryHandler(button_tap))
    app.add_handler(PollAnswerHandler(poll_ans))
    
    app.run_polling()

if __name__ == "__main__":
    main()
