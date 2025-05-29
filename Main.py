import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from binance.client import Client

# د .env فایل لوستل
load_dotenv()

# د محیط променې اخستل
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

# د Binance API سره وصلیدل
client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

# د بوټ اصلي مینو
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != TELEGRAM_USER_ID:
        await update.message.reply_text("❌ تاسو اجازه نلرئ!")
        return

    keyboard = [
        [InlineKeyboardButton("🟢 سپاټ اخيستل (Buy Spot)", callback_data="buy_spot")],
        [InlineKeyboardButton("🔴 سپاټ خرڅول (Sell Spot)", callback_data="sell_spot")],
        [InlineKeyboardButton("📈 فیوچرز ټریډ (Futures)", callback_data="futures_trade")],
        [InlineKeyboardButton("📊 بیلانس (Balance)", callback_data="balance")],
        [InlineKeyboardButton("📌 فعال پوزیشنونه", callback_data="positions")],
        [InlineKeyboardButton("♻️ لیږد (Spot ⇄ Futures)", callback_data="transfer")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "**سلام کوډ جانه! 👋**\nزه یم ستاسو د فیوچرز او سپاټ ټریډینګ مرستیال. لاندې انتخاب وکړئ:",
        reply_markup=reply_markup,
    )

# د سپاټ پیرود (Buy Spot)
async def buy_spot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("🔷 کوم سکه واخلم؟ (BTCUSDT):")
    context.user_data["action"] = "buy_spot"

# د فیوچرز ټریډ مینو
async def futures_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟢 لانګ (Buy/Long)", callback_data="futures_long")],
        [InlineKeyboardButton("🔴 شارټ (Sell/Short)", callback_data="futures_short")],
        [InlineKeyboardButton("📌 فعال پوزیشنونه", callback_data="futures_positions")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "**📈 فیوچرز ټریډینګ:**", reply_markup=reply_markup
    )

# د بیلانس چیک (Spot + Futures)
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # سپاټ بیلانس
    spot_balance = client.get_account()
    usdt_balance = next((item for item in spot_balance["balances"] if item["asset"] == "USDT"), None)
    
    # فیوچرز بیلانس
    futures_balance = client.futures_account_balance()
    futures_usdt = next((item for item in futures_balance if item["asset"] == "USDT"), None)
    
    response = (
        "**💼 ستاسو بیلانس:**\n"
        f"🔹 سپاټ USDT: **{float(usdt_balance['free']):.2f}**\n"
        f"🔹 فیوچرز USDT: **{float(futures_usdt['balance']):.2f}**"
    )
    await update.callback_query.message.reply_text(response, parse_mode="Markdown")

# د لیږد (Spot ⇄ Futures)
async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔵 Spot → Futures", callback_data="spot_to_futures")],
        [InlineKeyboardButton("🔴 Futures → Spot", callback_data="futures_to_spot")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "♻️ د لیږد ډول وټاکئ:", reply_markup=reply_markup
    )

# د فعال پوزیشنونو لیست
async def positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # د سپاټ پوزیشنونه
    open_orders = client.get_open_orders()
    # د فیوچرز پوزیشنونه
    futures_positions = client.futures_position_information()
    
    response = "**📌 فعال پوزیشنونه:**\n"
    for pos in futures_positions:
        if float(pos["positionAmt"]) != 0:
            response += (
                f"🔹 {pos['symbol']} | {pos['positionSide']} | مقدار: {pos['positionAmt']}\n"
                f"   PNL: {pos['unRealizedProfit']} USDT\n"
            )
    
    await update.callback_query.message.reply_text(response, parse_mode="Markdown")

# د بوټ پیل کول
if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    
    # Callback Handlers
    app.add_handler(CallbackQueryHandler(buy_spot, pattern="buy_spot"))
    app.add_handler(CallbackQueryHandler(futures_trade, pattern="futures_trade"))
    app.add_handler(CallbackQueryHandler(balance, pattern="balance"))
    app.add_handler(CallbackQueryHandler(positions, pattern="positions"))
    app.add_handler(CallbackQueryHandler(transfer, pattern="transfer"))
    
    print("✅ بوټ فعال شو...")
    app.run_polling()