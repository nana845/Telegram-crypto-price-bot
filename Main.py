import os
import telebot
import requests
import re

# خپل ټوکن دلته له Environment Variables څخه واخلئ
TOKEN = os.getenv('API_TOKEN')

# که ټوکن نه وي تنظیم شوی، خطا ښکاره کړئ
if not TOKEN:
    raise ValueError("API_TOKEN نه دی تنظیم شوی!")

# ټوکن چاپ کړئ (یوازې د ډیباګ لپاره، وروسته یې لرې کړئ)
print(f"TOKEN: {TOKEN}")

# ټیلیګرام بوټ جوړ کړئ
bot = telebot.TeleBot(TOKEN)

# د قیمت ترلاسه کولو فنکشن
def get_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
        response = requests.get(url, timeout=10)  # د 10 ثانیو ټایم آوټ
        response.raise_for_status()  # د HTTP تېروتنو کنټرول
        data = response.json()
        if 'price' in data:
            return f"د {symbol.upper()} اوسنی قیمت: ${float(data['price']):,.2f} USDT"
        else:
            return f"بخښنه غواړم، {symbol.upper()} ونه موندل شو."
    except requests.exceptions.RequestException:
        return "بخښنه غواړم، د Binance API ته لاسرسی نشته."
    except Exception as e:
        return f"تېروتنه: {e}"

# د هر ډول پیغام هندل کول
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.upper()
    # د کرنسي نوم پیدا کول (لکه BTCUSDT)
    match = re.fullmatch(r'[A-Z]{3,5}USDT', text)
    if match:
        symbol = match.group(0)
        price = get_price(symbol)
        bot.reply_to(message, price)
    else:
        bot.reply_to(message, "مهرباني وکړئ د کرنسي سم نوم ولیکئ، لکه BTCUSDT یا ETHUSDT")

# بوټ چالان کړئ
if __name__ == "__main__":
    try:
        bot.polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Bot Error: {e}")
        print("بوت ونه چلېد. مهرباني وکړئ ټوکن یا کوډ وګورئ.")
