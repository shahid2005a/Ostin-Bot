import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import requests
import time
from datetime import datetime
import threading
import os
import json

# ===== BANNER =====
banner = """
\033[1;31m
 ██████╗  ███████╗████████╗██╗███╗   ██╗
██╔═══██╗ ██╔════╝╚══██╔══╝██║████╗  ██║
██║   ██║ ███████╗   ██║   ██║██╔██╗ ██║
██║   ██║ ╚════██║   ██║   ██║██║╚██╗██║
╚██████╔╝ ███████║   ██║   ██║██║ ╚████║
 ╚═════╝  ╚══════╝   ╚═╝   ╚═╝╚═╝  ╚═══╝

        >>> OSTIN BOT <<<
      DEVELOPER BY DIGITAL CYBER [ARYAN AFRIDI]
\033[0m
"""
print(banner)

# ===== CONFIG =====
BOT_TOKEN = "12345678"
ADMIN_ID = 12345678
DEVELOPER_USERNAME = "@testing"
YOUTUBE_CHANNEL = "https://www.youtube.com/@aryanafridi00"
UPI_ID = "digitalcyber780@okhdfcbank"
DEFAULT_CREDITS = 10 
DEFAULT_START_CREDITS = 10

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ===== API URLS =====
NUMBER_API_URL = "https://users-xinfo-admin.vercel.app/api?key=7daysfree&type=mobile&term={}"
VEHICLE_API_URL = "https://users-xinfo-admin.vercel.app/api?key=7daysfree&type=vehicle&term={}"
AADHAAR_API_URL = "https://users-xinfo-admin.vercel.app/api?key=7daysfree&type=aadhar&term={}"

# ===== DATABASE =====
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
conn = sqlite3.connect(db_path, check_same_thread=False)

def init_db():
    with conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 0, join_date TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS redeem_codes(code TEXT PRIMARY KEY, credits INTEGER, used INTEGER DEFAULT 0)")
        conn.execute("CREATE TABLE IF NOT EXISTS transactions(user_id INTEGER, amount INTEGER, type TEXT, date TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS user_sessions(user_id INTEGER PRIMARY KEY, message_id INTEGER, service TEXT, timestamp TEXT)")
init_db()

# ===== VILLAIN INTRO TEXT =====
Villain_intro = """
🤖 <b>Ostin Bot</b>

<code>Digital Cyber Khamoshi meri pehchaan hai 🔕, aur code mera hathiyaar ⚙️☠️</code>
<code>Main warning nahi deta, seedha execute karta hoon 🎯</code>

<code>🧠 Algorithm tez hai, irade aur tez 🔥</code>
<code>Jo system ko lightly leta hai, uska exit automatic hota hai 🚪❌</code>

<code>😈 Na emotions, na mercy — sirf logic aur power ⚡</code>
<code>Jab main active hota hoon, errors chup jaate hain aur results bolte hain 📉📈</code>

<code>👑 Ostin Bot online hai —</code>
<code>control mere haath mein, chaos tumhare liye 💥💀</code>
"""

# ===== API FETCH FUNCTION =====
def fetch_api_data(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict):
                    if data.get('status') == 'success' and 'data' in data:
                        return {'success': True, 'data': data['data'], 'raw': data}
                    elif data.get('status') == 'error' or data.get('error'):
                        return {'success': False, 'error': data.get('message', data.get('error', 'Unknown error')), 'raw': data}
                    else:
                        if data:
                            return {'success': True, 'data': data, 'raw': data}
                        else:
                            return {'success': False, 'error': 'Empty response', 'raw': data}
                else:
                    return {'success': True if data else False, 'data': data, 'raw': data}
            except ValueError:
                return {'success': False, 'error': 'Invalid JSON response', 'raw': response.text[:200]}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}', 'raw': response.text[:200] if response.text else None}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timeout'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Connection failed'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ===== FORMAT API RESPONSE =====
def format_api_data(data, query, service):
    if not data or not data.get('success'):
        error_msg = data.get('error', 'Unknown error') if data else 'No response'
        return f"❌ <b>OPERATION FAILED: {query}</b>\n\nError: {error_msg}\n\nContact {DEVELOPER_USERNAME} if issue persists."
    
    result_data = data.get('data', {})
    if not result_data:
        return f"❌ <b>NO DATA FOUND: {query}</b>\n\nTarget not found in database."
    
    formatted = ""
    if isinstance(result_data, dict):
        for key, value in result_data.items():
            if value and str(value).strip():
                clean_key = key.replace('_', ' ').title()
                formatted += f"<b>{clean_key}:</b> {value}\n"
    elif isinstance(result_data, list):
        for i, item in enumerate(result_data[:10]):
            if isinstance(item, dict):
                formatted += f"\n<b>Record {i+1}:</b>\n"
                for k, v in item.items():
                    if v:
                        formatted += f"  {k}: {v}\n"
            else:
                formatted += f"• {item}\n"
    else:
        formatted = str(result_data)
    
    if not formatted.strip():
        return f"❌ <b>EMPTY DATA: {query}</b>"
    
    return f"✅ <b>OPERATION SUCCESSFUL: {query}</b>\n\n{formatted}"

# ===== SESSION MANAGEMENT =====
def set_user_session(user_id, message_id, service):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn:
        conn.execute("INSERT OR REPLACE INTO user_sessions(user_id, message_id, service, timestamp) VALUES(?, ?, ?, ?)",
                     (user_id, message_id, service, timestamp))

def get_user_session(user_id):
    cur = conn.cursor()
    cur.execute("SELECT message_id, service FROM user_sessions WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    cur.close()
    return row

def clear_user_session(user_id):
    with conn:
        conn.execute("DELETE FROM user_sessions WHERE user_id=?", (user_id,))

# ===== CREDIT HELPERS =====
def get_credits(user_id):
    cur = conn.cursor()
    cur.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    cur.close()
    if not row:
        join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with conn:
            conn.execute("INSERT INTO users(user_id, credits, join_date) VALUES(?, ?, ?)", 
                         (user_id, DEFAULT_START_CREDITS, join_date))
        return DEFAULT_START_CREDITS
    return row[0]

def add_credits(user_id, amount, txn_type="admin"):
    with conn:
        conn.execute("UPDATE users SET credits=credits+? WHERE user_id=?", (amount, user_id))
        txn_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO transactions(user_id, amount, type, date) VALUES(?, ?, ?, ?)",
                     (user_id, amount, txn_type, txn_date))

def use_credit(user_id, amount=1):
    current = get_credits(user_id)
    if current < amount:
        return False
    with conn:
        conn.execute("UPDATE users SET credits=credits-? WHERE user_id=?", (amount, user_id))
        txn_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO transactions(user_id, amount, type, date) VALUES(?, ?, ?, ?)",
                     (user_id, -amount, "usage", txn_date))
    return True

# ===== KEYBOARDS =====
def main_menu(user_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📱 Mobile", callback_data="search_MOBILE"),
        InlineKeyboardButton("🏎️ Vehicle RC", callback_data="search_RC")
    )
    kb.add(
        InlineKeyboardButton("🏛️ EMI", callback_data="search_EMI"),
        InlineKeyboardButton("🆔 Aadhaar", callback_data="search_AADHAAR")
    )
    kb.add(
        InlineKeyboardButton("💸 Buy Credits", callback_data="buy"),
        InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem")
    )
    kb.add(
        InlineKeyboardButton("💬 Chat with Dev", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@', '')}"),
        InlineKeyboardButton("📊 My Balance", callback_data="show_balance")
    )
    kb.add(InlineKeyboardButton("🔴 YouTube Channel", url=YOUTUBE_CHANNEL))
    if user_id == ADMIN_ID:
        kb.add(InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel"))
    return kb

def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        InlineKeyboardButton("👥 Users", callback_data="admin_users")
    )
    kb.add(
        InlineKeyboardButton("🎫 Create Code", callback_data="admin_create_code"),
        InlineKeyboardButton("➕ Add Credits", callback_data="admin_add_credits")
    )
    kb.add(
        InlineKeyboardButton("➖ Remove Credits", callback_data="admin_remove_credits"),
        InlineKeyboardButton("📜 Transactions", callback_data="admin_transactions")
    )
    kb.add(InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu"))
    return kb

# ===== HANDLERS =====
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, Villain_intro, parse_mode="HTML")
    time.sleep(1)
    clear_user_session(msg.chat.id)
    balance = get_credits(msg.chat.id)
    text = f"""🎯 <b>SYSTEM INITIALIZED</b>

💀 <code>Access Granted: Level {DEFAULT_START_CREDITS}</code>
⚡ <code>Processing Power: {balance} Units</code>

<b>🛠️ Available Tools:</b>
• 📱 Mobile Reconnaissance
• 🏎️ Vehicle Intelligence  
• 💰 EMI Database
• 🆔 Identity Verification

<b>⚠️ Warning:</b> Each operation costs 1 Unit
<b>⚙️ Maintenance:</b> {DEVELOPER_USERNAME}"""
    
    bot.send_message(msg.chat.id, text, reply_markup=main_menu(msg.chat.id))

@bot.callback_query_handler(func=lambda c: c.data == "main_menu")
def back_to_main(call):
    clear_user_session(call.from_user.id)
    balance = get_credits(call.message.chat.id)
    text = f"""🏠 <b>CONTROL PANEL</b>

⚡ <code>Power Level: {balance} Units</code>
🔧 <code>Technician: {DEVELOPER_USERNAME}</code>
🔴 <code>Intel Source: YouTube</code>"""
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_menu(call.from_user.id))
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=main_menu(call.from_user.id))

@bot.callback_query_handler(func=lambda c: c.data == "show_balance")
def show_balance(call):
    balance = get_credits(call.from_user.id)
    try:
        bot.answer_callback_query(call.id, f"⚡ Power Units: {balance}", show_alert=True)
    except:
        pass

# ===== ADMIN PANEL =====
@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_panel(call):
    if call.from_user.id != ADMIN_ID:
        try:
            bot.answer_callback_query(call.id, "❌ SYSTEM LOCKED: Admin Access Required", show_alert=True)
        except:
            pass
        return
    
    try:
        admin_text = """👑 <b>MASTER CONTROL</b>

<code>Welcome back, Administrator</code>
<code>System Access: Level 100</code>
<code>All permissions granted ✅</code>"""
        bot.edit_message_text(admin_text, call.message.chat.id, call.message.message_id, reply_markup=admin_menu())
    except:
        bot.send_message(call.message.chat.id, admin_text, reply_markup=admin_menu())

# ===== ADMIN STATS =====
@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def admin_stats(call):
    if call.from_user.id != ADMIN_ID:
        try:
            bot.answer_callback_query(call.id, "❌ ACCESS DENIED", show_alert=True)
        except:
            pass
        return
    
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        cur.execute("SELECT SUM(credits) FROM users")
        total_credits_result = cur.fetchone()
        total_credits = total_credits_result[0] if total_credits_result[0] is not None else 0
        cur.execute("SELECT COUNT(*) FROM redeem_codes WHERE used=0")
        active_codes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM transactions WHERE type='usage'")
        total_searches = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE date(join_date) = date('now')")
        today_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM transactions WHERE type='payment' AND date(date) = date('now')")
        today_payments = cur.fetchone()[0]
        today_revenue = today_payments * 100
        
        text = f"""📊 <b>SYSTEM STATISTICS</b>

👥 Total Agents: <code>{total_users}</code>
👤 New Agents Today: <code>{today_users}</code>
⚡ Total Power Units: <code>{total_credits}</code>
🎫 Active Access Codes: <code>{active_codes}</code>
🔍 Operations Executed: <code>{total_searches}</code>
💵 Resource Acquisition: ₹<code>{today_revenue}</code>"""
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=admin_menu())
    except:
        try:
            bot.answer_callback_query(call.id, f"❌ Database error", show_alert=True)
        except:
            pass
    finally:
        cur.close()

# ===== ADMIN USERS =====
@bot.callback_query_handler(func=lambda c: c.data == "admin_users")
def admin_users(call):
    if call.from_user.id != ADMIN_ID:
        try:
            bot.answer_callback_query(call.id, "❌ ACCESS DENIED", show_alert=True)
        except:
            pass
        return
    
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id, credits, join_date FROM users ORDER BY join_date DESC LIMIT 20")
        users = cur.fetchall()
        text = "👥 <b>ACTIVE AGENTS (Last 20)</b>\n\n"
        if users:
            for user_id, credits, join_date in users:
                text += f"🆔: <code>{user_id}</code>\n"
                text += f"⚡: {credits} | 📅: {join_date}\n"
                text += "━━━━━━━━━━━━━━━━\n"
        else:
            text += "No users found"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=admin_menu())
    except:
        try:
            bot.answer_callback_query(call.id, "❌ Database error", show_alert=True)
        except:
            pass
    finally:
        cur.close()

# ===== ADMIN CREATE CODE =====
@bot.callback_query_handler(func=lambda c: c.data == "admin_create_code")
def admin_create_code(call):
    if call.from_user.id != ADMIN_ID:
        try:
            bot.answer_callback_query(call.id, "❌ ACCESS DENIED", show_alert=True)
        except:
            pass
        return
    
    msg = bot.send_message(call.message.chat.id, "<b>Enter Access Code Format:</b> <code>CODE UNITS</code>\n<b>Example:</b> <code>ALPHA50 50</code>")
    bot.register_next_step_handler(msg, process_create_code)

def process_create_code(msg):
    if msg.chat.id != ADMIN_ID:
        return
    
    try:
        parts = msg.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(msg, "❌ FORMAT: CODE UNITS")
            return
        code, credits = parts[0].upper(), int(parts[1])
        
        cur = conn.cursor()
        cur.execute("SELECT * FROM redeem_codes WHERE code=?", (code,))
        if cur.fetchone():
            cur.close()
            bot.reply_to(msg, "❌ CODE ALREADY EXISTS!")
            return
        cur.close()
        
        with conn:
            conn.execute("INSERT INTO redeem_codes(code, credits) VALUES(?, ?)", (code, credits))
        bot.reply_to(msg, f"✅ ACCESS CODE CREATED!\n🔑: <code>{code}</code>\n⚡: {credits}")
    except ValueError:
        bot.reply_to(msg, "❌ CREDITS MUST BE A NUMBER!")
    except Exception as e:
        bot.reply_to(msg, "❌ ERROR CREATING CODE")

# ===== ADMIN ADD CREDITS =====
@bot.callback_query_handler(func=lambda c: c.data == "admin_add_credits")
def admin_add_credits(call):
    if call.from_user.id != ADMIN_ID:
        try:
            bot.answer_callback_query(call.id, "❌ ACCESS DENIED", show_alert=True)
        except:
            pass
        return
    
    msg = bot.send_message(call.message.chat.id, "<b>Format:</b> <code>USER_ID UNITS</code>\n<b>Example:</b> <code>123456789 50</code>")
    bot.register_next_step_handler(msg, process_add_credits)

def process_add_credits(msg):
    if msg.chat.id != ADMIN_ID:
        return
    
    try:
        parts = msg.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(msg, "❌ FORMAT: USER_ID UNITS")
            return
        user_id, amount = int(parts[0]), int(parts[1])
        
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        if not cur.fetchone():
            join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with conn:
                conn.execute("INSERT INTO users(user_id, credits, join_date) VALUES(?, ?, ?)", 
                           (user_id, 0, join_date))
        cur.close()
        
        add_credits(user_id, amount, "admin_add")
        bot.reply_to(msg, f"✅ {amount} UNITS ADDED TO USER {user_id}")
        try:
            bot.send_message(user_id, f"⚡ ADMIN ADDED {amount} POWER UNITS TO YOUR SYSTEM!")
        except:
            pass
    except ValueError:
        bot.reply_to(msg, "❌ INVALID INPUT FORMAT!")
    except Exception as e:
        bot.reply_to(msg, f"❌ ERROR: {e}")

# ===== ADMIN REMOVE CREDITS =====
@bot.callback_query_handler(func=lambda c: c.data == "admin_remove_credits")
def admin_remove_credits(call):
    if call.from_user.id != ADMIN_ID:
        try:
            bot.answer_callback_query(call.id, "❌ ACCESS DENIED", show_alert=True)
        except:
            pass
        return
    
    msg = bot.send_message(call.message.chat.id, "<b>Format:</b> <code>USER_ID UNITS</code>\n<b>Example:</b> <code>123456789 10</code>")
    bot.register_next_step_handler(msg, process_remove_credits)

def process_remove_credits(msg):
    if msg.chat.id != ADMIN_ID:
        return
    
    try:
        parts = msg.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(msg, "❌ FORMAT: USER_ID UNITS")
            return
        user_id, amount = int(parts[0]), int(parts[1])
        
        cur = conn.cursor()
        cur.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            bot.reply_to(msg, f"❌ USER {user_id} NOT FOUND!")
            return
        current = row[0]
        new_amount = max(0, current - amount)
        cur.close()
        
        with conn:
            conn.execute("UPDATE users SET credits=? WHERE user_id=?", (new_amount, user_id))
        bot.reply_to(msg, f"✅ {amount} UNITS REMOVED FROM USER {user_id}")
        try:
            bot.send_message(user_id, f"⚠️ ADMIN REMOVED {amount} POWER UNITS FROM YOUR SYSTEM!")
        except:
            pass
    except ValueError:
        bot.reply_to(msg, "❌ INVALID INPUT FORMAT!")
    except Exception as e:
        bot.reply_to(msg, f"❌ ERROR: {e}")

# ===== ADMIN TRANSACTIONS =====
@bot.callback_query_handler(func=lambda c: c.data == "admin_transactions")
def admin_transactions(call):
    if call.from_user.id != ADMIN_ID:
        try:
            bot.answer_callback_query(call.id, "❌ ACCESS DENIED", show_alert=True)
        except:
            pass
        return
    
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id, amount, type, date FROM transactions ORDER BY date DESC LIMIT 20")
        txns = cur.fetchall()
        text = "📜 <b>SYSTEM LOGS (Last 20)</b>\n\n"
        if txns:
            for user_id, amount, txn_type, date in txns:
                text += f"👤: <code>{user_id}</code>\n"
                text += f"⚡: {'+' if amount > 0 else ''}{amount} | 📝: {txn_type}\n"
                text += f"📅: {date}\n━━━━━━━━━━━━━━━━\n"
        else:
            text += "No transactions found"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=admin_menu())
    except:
        try:
            bot.answer_callback_query(call.id, "❌ Database error", show_alert=True)
        except:
            pass
    finally:
        cur.close()

# ===== SEARCH FUNCTIONS =====
@bot.callback_query_handler(func=lambda c: c.data.startswith('search_'))
def handle_search_req(call):
    service = call.data.split('_')[1]
    user_id = call.from_user.id
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    
    session = get_user_session(user_id)
    if session:
        bot.send_message(user_id, "⚠️ OPERATION IN PROGRESS! Use /cancel")
        return
    
    if get_credits(user_id) < 1:
        bot.send_message(user_id, "❌ INSUFFICIENT POWER UNITS!")
        return
    
    clear_user_session(user_id)
    set_user_session(user_id, call.message.message_id, service)
    
    service_names = {
        "MOBILE": "Mobile Number (10 digits)",
        "RC": "Vehicle RC Number",
        "EMI": "Loan/EMI ID Number",
        "AADHAAR": "Aadhaar Number (12 digits)"
    }
    
    msg = bot.send_message(user_id, f"🎯 <b>TARGET INPUT:</b> {service_names.get(service, service)}\n⚠️ Send /cancel to abort")
    bot.register_next_step_handler(msg, perform_lookup, service)

def perform_lookup(msg, service):
    user_id = msg.chat.id
    
    if msg.text and msg.text.strip() == "/cancel":
        clear_user_session(user_id)
        bot.send_message(user_id, "❌ OPERATION CANCELLED.")
        bot.send_message(user_id, "🏠 Returning to main menu...", reply_markup=main_menu(user_id))
        return
    
    session = get_user_session(user_id)
    if not session:
        bot.send_message(user_id, "❌ SESSION EXPIRED.")
        bot.send_message(user_id, "🏠 Returning to main menu...", reply_markup=main_menu(user_id))
        return
    
    query = msg.text.strip() if msg.text else ""
    if not query:
        clear_user_session(user_id)
        bot.send_message(user_id, "❌ INVALID TARGET")
        bot.send_message(user_id, "🏠 Returning to main menu...", reply_markup=main_menu(user_id))
        return
    
    # Validation
    if service == "MOBILE":
        if not query.isdigit() or len(query) != 10:
            clear_user_session(user_id)
            bot.send_message(user_id, "❌ TARGET MUST BE 10 DIGITS")
            bot.send_message(user_id, "🏠 Returning to main menu...", reply_markup=main_menu(user_id))
            return
    elif service == "AADHAAR":
        if not (query.isdigit() and len(query) == 12):
            clear_user_session(user_id)
            bot.send_message(user_id, "❌ TARGET MUST BE 12 DIGITS")
            bot.send_message(user_id, "🏠 Returning to main menu...", reply_markup=main_menu(user_id))
            return
    elif service == "RC" and len(query) < 5:
        clear_user_session(user_id)
        bot.send_message(user_id, "❌ INVALID RC TARGET")
        bot.send_message(user_id, "🏠 Returning to main menu...", reply_markup=main_menu(user_id))
        return
    elif service == "EMI" and len(query) < 5:
        clear_user_session(user_id)
        bot.send_message(user_id, "❌ INVALID EMI/Loan ID")
        bot.send_message(user_id, "🏠 Returning to main menu...", reply_markup=main_menu(user_id))
        return

    if not use_credit(user_id, 1):
        clear_user_session(user_id)
        bot.send_message(user_id, "❌ INSUFFICIENT POWER UNITS!")
        bot.send_message(user_id, "🏠 Returning to main menu...", reply_markup=main_menu(user_id))
        return
    
    wait_msg = bot.send_message(user_id, "⚡ <i>EXECUTING OPERATION...</i>")
    
    data = None
    try:
        if service == "MOBILE":
            data = fetch_api_data(NUMBER_API_URL.format(query))
        elif service == "AADHAAR":
            data = fetch_api_data(AADHAAR_API_URL.format(query))
        elif service == "RC":
            data = fetch_api_data(VEHICLE_API_URL.format(query))
        elif service == "EMI":
            data = {'success': False, 'error': 'EMI API not available'}
    except Exception as e:
        data = {'success': False, 'error': str(e)}
    
    clear_user_session(user_id)
    
    try:
        bot.delete_message(user_id, wait_msg.message_id)
    except:
        pass
    
    if service == "EMI":
        result_text = "❌ <b>EMI SERVICE UNAVAILABLE</b>\n\nThis service is currently under maintenance."
    else:
        result_text = format_api_data(data, query, service)
    
    bot.send_message(user_id, result_text, parse_mode="HTML")
    time.sleep(1)
    bot.send_message(user_id, "🏠 <b>RETURNING TO CONTROL PANEL</b>", reply_markup=main_menu(user_id))

# ===== OTHER HANDLERS =====
@bot.message_handler(commands=['cancel'])
def cancel_operation(msg):
    user_id = msg.chat.id
    session = get_user_session(user_id)
    if session:
        clear_user_session(user_id)
        bot.reply_to(msg, "✅ OPERATION CANCELLED.")
        bot.send_message(user_id, "🏠 Returning to main menu...", reply_markup=main_menu(user_id))
    else:
        bot.reply_to(msg, "ℹ️ No active operation to cancel.")

@bot.callback_query_handler(func=lambda c: c.data == "buy")
def buy(call):
    clear_user_session(call.from_user.id)
    text = f"""💳 <b>RESOURCE ACQUISITION</b>

💰 <code>UPI ID: {UPI_ID}</code>
⚡ <code>Acquire {DEFAULT_CREDITS} Power Units for ₹10</code>

<b>Procedure:</b>
1. Transfer ₹10 to above UPI
2. Upload transaction proof
3. Await authorization"""
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    bot.send_message(call.message.chat.id, text)

@bot.message_handler(content_types=['photo'])
def handle_proof(msg):
    clear_user_session(msg.chat.id)
    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    bot.send_message(ADMIN_ID, f"""📩 <b>RESOURCE REQUEST</b>
🆔 Agent ID: <code>{msg.chat.id}</code>
⚡ Authorize: /approve {msg.chat.id}""")
    bot.reply_to(msg, "✅ PROOF RECEIVED. AWAITING AUTHORIZATION...")

@bot.message_handler(commands=['approve'])
def approve(msg):
    if msg.chat.id != ADMIN_ID:
        bot.reply_to(msg, "❌ COMMAND RESTRICTED: ADMIN ONLY")
        return
    
    try:
        parts = msg.text.split()
        if len(parts) != 2:
            bot.reply_to(msg, "⚠️ USAGE: /approve USER_ID")
            return
        uid = int(parts[1])
        add_credits(uid, DEFAULT_CREDITS, "payment")
        bot.send_message(uid, f"""✅ <b>RESOURCES DEPLOYED</b>

⚡ <code>{DEFAULT_CREDITS} Power Units added to your system</code>
🎯 <code>All tools now operational</code>

<b>Current Power:</b> {get_credits(uid)} Units""")
        bot.reply_to(msg, f"✅ RESOURCES DEPLOYED TO USER {uid}")
    except Exception as e:
        bot.reply_to(msg, f"❌ ERROR: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "redeem")
def red(call):
    clear_user_session(call.from_user.id)
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    m = bot.send_message(call.message.chat.id, "🔑 <b>ENTER ACCESS CODE:</b>\n<code>Example: ALPHA50</code>")
    bot.register_next_step_handler(m, process_red)

def process_red(msg):
    code = msg.text.strip().upper()
    cur = conn.cursor()
    try:
        cur.execute("SELECT credits FROM redeem_codes WHERE code=? AND used=0", (code,))
        row = cur.fetchone()
        if row:
            add_credits(msg.chat.id, row[0], "redeem")
            with conn:
                conn.execute("UPDATE redeem_codes SET used=1 WHERE code=?", (code,))
            bot.reply_to(msg, f"🎯 <b>ACCESS GRANTED!</b>\n⚡ +{row[0]} Power Units\n\n<b>Total Power:</b> {get_credits(msg.chat.id)} Units")
        else:
            bot.reply_to(msg, f"❌ INVALID ACCESS CODE\n\n🔧 Contact: {DEVELOPER_USERNAME}")
    except:
        bot.reply_to(msg, "❌ DATABASE ERROR")
    finally:
        cur.close()

# ===== CLEANUP =====
def cleanup_sessions():
    while True:
        try:
            with conn:
                conn.execute("DELETE FROM user_sessions WHERE timestamp < datetime('now', '-10 minutes')")
            time.sleep(300)
        except:
            pass

cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
cleanup_thread.start()

# ===== START BOT =====
print("=" * 50)
print("🤖 OSTIN BOT INITIALIZING...")
print(f"🎯 ADMIN ID: {ADMIN_ID}")
print(f"⚡ NEW AGENTS GET: {DEFAULT_START_CREDITS} POWER UNITS")
print(f"🔧 MAINTENANCE: {DEVELOPER_USERNAME}")
print(f"📺 INTEL SOURCE: {YOUTUBE_CHANNEL}")
print("✅ SYSTEM READY")
print("=" * 50)

try:
    bot.infinity_polling()
except Exception as e:
    print(f"❌ SYSTEM CRASH: {e}")