# ✅ Advanced Gmail Order Telegram Bot (Python)
# Requirements: pip install pyTelegramBotAPI

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import json
import time

# === Configuration ===
API_KEY = '7576472064:AAG557fuTOucK71bV7Esbv-77CrRSGit1hw'
ADMIN_ID = 5781612136  # Replace with your personal Telegram ID
bot = telebot.TeleBot('7576472064:AAG557fuTOucK71bV7Esbv-77CrRSGit1hw')


# === Order Storage ===
ORDER_FILE = 'orders.json'

# Load existing orders
try:
    with open(ORDER_FILE, 'r') as f:
        orders = json.load(f)
except:
    orders = []

# === Start Command ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Welcome to Gmail Order Bot!\nUse /order to place your custom Gmail order.")

# === Order Flow ===
user_states = {}
user_data = {}

@bot.message_handler(commands=['order'])
def order(message):
    user_states[message.chat.id] = 'get_recovery'
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "📧 Enter your recovery email:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'get_recovery')
def get_recovery(message):
    user_data[message.chat.id]['recovery_email'] = message.text
    user_states[message.chat.id] = 'get_password'
    bot.send_message(message.chat.id, "🔑 Enter your desired Gmail password:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'get_password')
def get_password(message):
    user_data[message.chat.id]['password'] = message.text
    user_states[message.chat.id] = 'ask_2fa'
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Yes"), KeyboardButton("No"))
    bot.send_message(message.chat.id, "🔐 Do you want 2FA (Phone, Authenticator, Backup Code)?", reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'ask_2fa')
def ask_2fa(message):
    user_data[message.chat.id]['need_2fa'] = message.text.strip().lower() == 'yes'
    user_states[message.chat.id] = 'select_country'
    markup = InlineKeyboardMarkup()
    countries = ['USA', 'Germany', 'UK', 'Mexico', 'Brazil']
    for c in countries:
        markup.add(InlineKeyboardButton(c, callback_data=f"country_{c}"))
    bot.send_message(message.chat.id, "🌍 Select your desired Gmail country:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('country_'))
def select_country(call):
    country = call.data.split('_')[1]
    user_data[call.message.chat.id]['country'] = country

    # Save the order
    order = {
        "user_id": call.message.chat.id,
        "username": call.from_user.username,
        "recovery_email": user_data[call.message.chat.id]['recovery_email'],
        "password": user_data[call.message.chat.id]['password'],
        "need_2fa": user_data[call.message.chat.id]['need_2fa'],
        "country": country,
        "status": "Pending",
        "time": time.ctime()
    }
    orders.append(order)
    with open(ORDER_FILE, 'w') as f:
        json.dump(orders, f, indent=4)

    # Notify Admin
    msg = f"📥 New Gmail Order:\n\n👤 User: @{order['username']} ({order['user_id']})\n📧 Recovery: {order['recovery_email']}\n🔑 Password: {order['password']}\n🔐 2FA: {'Yes' if order['need_2fa'] else 'No'}\n🌍 Country: {order['country']}\n🕒 Time: {order['time']}"
    bot.send_message(ADMIN_ID, msg)

    # Confirm to user
    bot.send_message(call.message.chat.id, "✅ Your order has been placed successfully!\nYou will receive your Gmail within 24 hours.")

    # Cleanup
    user_states.pop(call.message.chat.id)
    user_data.pop(call.message.chat.id)

# === Admin Command to View Orders ===
@bot.message_handler(commands=['pending'])
def show_pending(message):
    if message.chat.id != ADMIN_ID:
        return
    pending = [o for o in orders if o['status'] == 'Pending']
    if not pending:
        bot.send_message(message.chat.id, "✅ No pending orders.")
    else:
        for idx, o in enumerate(pending):
            bot.send_message(message.chat.id, f"🔸 Order #{idx + 1}\nUser: {o['user_id']}\nEmail: {o['recovery_email']}\nCountry: {o['country']}")

# === Run the Bot ===
bot.polling(none_stop=True)
