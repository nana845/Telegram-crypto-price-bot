import os
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

# Binance credentials
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
client = Client(api_key, api_secret)

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# Check access
def is_owner(user_id):
    return user_id == OWNER_ID

# Format price
def format_price(symbol, price):
    return "{:.8f}".format(price) if 'BTC' in symbol else "{:.4f}".format(price)

# Commands

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text("سلام! بوټ چالان دی.")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        symbol = context.args[0].upper()
        usdt_amount = float(context.args[1])
        tp = float(context.args[2]) if len(context.args) > 2 else None
        sl = float(context.args[3]) if len(context.args) > 3 else None

        price = client.get_symbol_ticker(symbol=symbol + "USDT")
        current_price = float(price["price"])
        quantity = round(usdt_amount / current_price, 5)

        # Market Buy
        client.order_market_buy(symbol=symbol + "USDT", quantity=quantity)

        msg = f"Buy executed: {symbol}, Qty: {quantity}"
        if tp:
            client.order_limit_sell(
                symbol=symbol + "USDT",
                quantity=quantity,
                price=format_price(symbol, tp),
                timeInForce=TIME_IN_FORCE_GTC
            )
            msg += f"\nTake Profit set at {tp}"
        if sl:
            client.create_order(
                symbol=symbol + "USDT",
                side=SIDE_SELL,
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                quantity=quantity,
                price=format_price(symbol, sl),
                stopPrice=format_price(symbol, sl),
                timeInForce=TIME_IN_FORCE_GTC
            )
            msg += f"\nStop Loss set at {sl}"

        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        symbol = context.args[0].upper()
        usdt_amount = float(context.args[1])
        tp = float(context.args[2]) if len(context.args) > 2 else None
        sl = float(context.args[3]) if len(context.args) > 3 else None

        price = client.get_symbol_ticker(symbol=symbol + "USDT")
        current_price = float(price["price"])
        quantity = round(usdt_amount / current_price, 5)

        # Market Sell
        client.order_market_sell(symbol=symbol + "USDT", quantity=quantity)

        msg = f"Sell executed: {symbol}, Qty: {quantity}"
        if tp:
            client.order_limit_buy(
                symbol=symbol + "USDT",
                quantity=quantity,
                price=format_price(symbol, tp),
                timeInForce=TIME_IN_FORCE_GTC
            )
            msg += f"\nTake Profit set at {tp}"
        if sl:
            client.create_order(
                symbol=symbol + "USDT",
                side=SIDE_BUY,
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                quantity=quantity,
                price=format_price(symbol, sl),
                stopPrice=format_price(symbol, sl),
                timeInForce=TIME_IN_FORCE_GTC
            )
            msg += f"\nStop Loss set at {sl}"

        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        assets = client.get_account()["balances"]
        text = ""
        for asset in assets:
            free = float(asset["free"])
            if free > 0:
                text += f"{asset['asset']}: {free}\n"
        await update.message.reply_text(text if text else "خالي حساب")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        symbol = context.args[0].upper()
        trades = client.get_my_trades(symbol=symbol + "USDT")
        text = ""
        for t in trades[-5:]:
            side = "Buy" if t['isBuyer'] else "Sell"
            text += f"{side} | Price: {t['price']} | Qty: {t['qty']}\n"
        await update.message.reply_text(text if text else "هیڅ ټریډ نشته.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        symbol = context.args[0].upper()
        orders = client.get_open_orders(symbol=symbol + "USDT")
        for order in orders:
            client.cancel_order(symbol=symbol + "USDT", orderId=order["orderId"])
        await update.message.reply_text(f"ټول فعال امرونه لغوه شول ({symbol})")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def open_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        symbol = context.args[0].upper()
        orders = client.get_open_orders(symbol=symbol + "USDT")
        text = ""
        for o in orders:
            text += f"{o['side']} {o['origQty']} at {o['price']}\n"
        await update.message.reply_text(text if text else "هیڅ فعال امر نشته.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Run bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("sell", sell))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("history", history))
app.add_handler(CommandHandler("cancel", cancel))
app.add_handler(CommandHandler("open", open_orders))

print("Bot is running...")
app.run_polling()