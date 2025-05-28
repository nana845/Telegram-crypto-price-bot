import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import BINANCE_API_KEY, BINANCE_API_SECRET, TELEGRAM_BOT_TOKEN, ALLOWED_USER_ID
from binance.client import Client

client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)

logging.basicConfig(level=logging.INFO)

def private_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ALLOWED_USER_ID:
            await update.message.reply_text("❌ دا بوټ یوازې د مالک لپاره دی.")
            return
        return await func(update, context)
    return wrapper

@private_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ بوټ فعاله شو! کارونه: /buy /sell /balance")

@private_only
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("استعمال: /buy BTCUSDT 10")
        return
    symbol = args[0].upper()
    amount = float(args[1])
    try:
        order = client.order_market_buy(symbol=symbol, quoteOrderQty=amount)
        await update.message.reply_text(f"✅ BUY: {symbol} - {amount} USDT")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

@private_only
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("استعمال: /sell BTCUSDT 10")
        return
    symbol = args[0].upper()
    amount = float(args[1])
    try:
        order = client.order_market_sell(symbol=symbol, quoteOrderQty=amount)
        await update.message.reply_text(f"✅ SELL: {symbol} - {amount} USDT")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

@private_only
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        account = client.get_account()
        msg = "💰 Spot Balance:\n"
        for asset in account['balances']:
            free = float(asset['free'])
            if free > 0:
                msg += f"{asset['asset']}: {free}\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("balance", balance))
    app.run_polling()

if __name__ == "__main__":
    main()