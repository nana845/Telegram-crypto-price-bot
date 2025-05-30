import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
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

async def buy_spot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د سپاټ پیرود پروسه پیلول"""
    await update.callback_query.message.reply_text("🔷 لطفاً د سکې سمبول ولیکئ (BTCUSDT):")
    context.user_data['action'] = 'buy_spot'

async def sell_spot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د سپاټ خرڅولو پروسه پیلول"""
    await update.callback_query.message.reply_text("🔷 لطفاً د سکې سمبول ولیکئ (BTCUSDT):")
    context.user_data['action'] = 'sell_spot'

async def futures_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د فیوچرز ټریډ مینو"""
    keyboard = [
        [InlineKeyboardButton("🟢 لانګ (Buy)", callback_data="futures_long")],
        [InlineKeyboardButton("🔴 شارټ (Sell)", callback_data="futures_short")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "📈 د فیوچرز ټریډ ډول وټاکئ:",
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
        
        if len(response) <= 20:  # که هیڅ فعال پوزیشن نشته
            response = "❌ تاسو هیڅ فعال پوزیشن نلرئ"
        
        await update.callback_query.message.reply_text(response)
    except ClientError as e:
        await update.callback_query.message.reply_text(f"❌ اررور: {e.message}")

async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د لیږد مینو"""
    keyboard = [
        [InlineKeyboardButton("🔵 Spot → Futures", callback_data="spot_to_futures")],
        [InlineKeyboardButton("🔴 Futures → Spot", callback_data="futures_to_spot")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "♻️ د لیږد ډول وټاکئ:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د پیغامونو مدیریت"""
    if 'action' not in context.user_data:
        return
    
    text = update.message.text.upper()
    
    if context.user_data['action'] == 'buy_spot':
        try:
            # د سکې د پیرود پروسه
            order = client.new_order(
                symbol=text,
                side='BUY',
                type='MARKET',
                quantity=0.001  # یا د مقدار د پوښتنې پروسه اضافه کړئ
            )
            await update.message.reply_text(f"✅ په بریالیتوب سره واخیستل شو: {text}")
        except ClientError as e:
            await update.message.reply_text(f"❌ اررور: {e.message}")
        
        context.user_data.clear()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د کالبکونو مدیریت"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "buy_spot":
        await buy_spot(update, context)
    elif query.data == "sell_spot":
        await sell_spot(update, context)
    elif query.data == "futures_trade":
        await futures_trade(update, context)
    elif query.data == "balance":
        await balance(update, context)
    elif query.data == "positions":
        await positions(update, context)
    elif query.data == "transfer":
        await transfer(update, context)
    elif query.data in ["futures_long", "futures_short"]:
        side = "BUY" if query.data == "futures_long" else "SELL"
        context.user_data['futures_side'] = side
        await query.message.reply_text(f"🔷 د فیوچرز ټریډ لپاره د سکې سمبول ولیکئ (BTCUSDT):")
    elif query.data in ["spot_to_futures", "futures_to_spot"]:
        await query.message.reply_text(f"♻️ د لیږد لپاره مقدار په USDT ولیکئ:")

def main():
    """د بوټ پیلولو اصلي فنکشن"""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # د کمانډونو مدیریت
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # د بوټ پیلول
    app.run_polling()
    logging.info("✅ بوټ په بریالیتوب سره پیل شو")

if __name__ == "__main__":
    main()