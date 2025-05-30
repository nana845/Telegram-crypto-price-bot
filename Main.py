import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from binance.spot import Spot as Client
from binance.error import ClientError
from dotenv import load_dotenv

# د چاپیریالي پروینو لوستل
load_dotenv()

# د API کیونو تنظیم
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

# د Binance API سره وصلیدل
client = Client(
    api_key=BINANCE_API_KEY,
    api_secret=BINANCE_SECRET_KEY,
    base_url='https://api.binance.com'
)

# د اررورونو لګ ثبتولو تنظیم
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د بوټ اصلي مینو"""
    if str(update.effective_user.id) != TELEGRAM_USER_ID:
        await update.message.reply_text("❌ تاسو اجازه نلرئ!")
        return

    keyboard = [
        [InlineKeyboardButton("🟢 سپاټ اخيستل", callback_data="buy_spot")],
        [InlineKeyboardButton("🔴 سپاټ خرڅول", callback_data="sell_spot")],
        [InlineKeyboardButton("📈 فیوچرز ټریډ", callback_data="futures_trade")],
        [InlineKeyboardButton("📊 بیلانس", callback_data="balance")],
        [InlineKeyboardButton("📌 پوزیشنونه", callback_data="positions")],
        [InlineKeyboardButton("♻️ لیږد", callback_data="transfer")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "**سلام! زه ستاسو د Binance مرستیال یم.**\nلاندې انتخاب وکړئ:",
        reply_markup=reply_markup
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د سپاټ او فیوچرز بیلانس ښودل"""
    try:
        # سپاټ بیلانس
        spot_balance = client.account()
        usdt_balance = next((item for item in spot_balance["balances"] if item["asset"] == "USDT"), None)
        
        # فیوچرز بیلانس
        futures_balance = client.futures_account()
        futures_usdt = next((item for item in futures_balance["assets"] if item["asset"] == "USDT"), None)
        
        response = (
            "**💼 ستاسو بیلانس:**\n"
            f"🔹 سپاټ USDT: {float(usdt_balance['free']):.2f}\n"
            f"🔹 فیوچرز USDT: {float(futures_usdt['availableBalance']):.2f}"
        )
        await update.callback_query.message.reply_text(response)
    except ClientError as e:
        await update.callback_query.message.reply_text(f"❌ اررور: {e.message}")

async def positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د فعال پوزیشنونو لیست"""
    try:
        positions = client.futures_position_information()
        response = "**📌 فعال پوزیشنونه:**\n"
        
        for pos in positions:
            if float(pos["positionAmt"]) != 0:
                response += (
                    f"{pos['symbol']} | {pos['positionSide']}\n"
                    f"مقدار: {pos['positionAmt']} | PNL: {pos['unRealizedProfit']} USDT\n\n"
                )
        
        await update.callback_query.message.reply_text(response)
    except ClientError as e:
        await update.callback_query.message.reply_text(f"❌ اررور: {e.message}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د کالبکونو مدیریت"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "balance":
        await balance(update, context)
    elif query.data == "positions":
        await positions(update, context)
    else:
        await query.message.reply_text("✅ دا فعالیت به ډیر ژر اضافه شي")

def main():
    """د بوټ پیلولو اصلي فنکشن"""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # د کمانډونو مدیریت
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # د بوټ پیلول
    app.run_polling()
    logging.info("✅ بوټ په بریالیتوب سره پیل شو")

if __name__ == "__main__":
    main()