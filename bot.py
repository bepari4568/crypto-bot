import ccxt
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import pytz

# --- CONFIGURATION ---
TOKEN = '8710909291:AAFA5knDt_EybhJSF5YiK5ljZhyx9fVGPRQ'
SYMBOL = 'CORE/USDT'
TIMEFRAME = '1h'

exchange = ccxt.bitget({'enableRateLimit': True})

def get_indicators(df):
    # EMA 20
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
    # Support & Resistance
    support = df['low'].tail(24).min()
    resistance = df['high'].tail(24).max()
    return df, support, resistance

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = await update.message.reply_text("🔍 ডিপ এনালাইসিস চলছে, অপেক্ষা করুন...")
    
    try:
        # ডাটা ফেচ করা
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        df, support, resistance = get_indicators(df)
        curr = df.iloc[-1]
        
        # --- ১. ক্যান্ডেল ক্লোজিং টাইমার (বাংলাদেশ সময়) ---
        tz = pytz.timezone('Asia/Dhaka')
        now = datetime.now(tz)
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        remaining = next_hour - now
        minutes_left = int(remaining.total_seconds() // 60)

        # --- ২. ক্লোজিং প্রাইস প্রেডিকশন (স্মার্ট লজিক) ---
        # যদি বর্তমান ক্লোজ EMA এর উপরে থাকে এবং MACD বুলিশ হয়
        diff = curr['macd'] * 0.15
        pred_price = round(curr['close'] + diff, 4)

        # --- ৩. সিগন্যাল তৈরি ---
        if curr['close'] > curr['ema20'] and curr['macd'] > curr['signal_line']:
            signal = "BUY 🚀"
        elif curr['close'] < curr['ema20'] and curr['macd'] < curr['signal_line']:
            signal = "SELL 📉"
        else:
            signal = "WAIT/SIDEWAYS ⚡"

        msg = (
            f"📊 **CORE/USDT ১ ঘণ্টার স্মার্ট রিপোর্ট**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 বর্তমান প্রাইস: `${curr['close']}`\n"
            f"🔮 সম্ভাব্য ক্লোজ: `${pred_price}`\n"
            f"⏳ ক্লোজ হতে বাকি: `{minutes_left} মিনিট`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚦 সিগন্যাল: **{signal}**\n"
            f"📏 সাপোর্ট: `${round(support, 4)}`\n"
            f"🧱 রেজিস্ট্যান্স: `${round(resistance, 4)}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 বিডি সময়: `{now.strftime('%I:%M %p')}`\n"
            f"📊 ভলিউম: " + ("বেশি 📈" if curr['vol'] > df['vol'].tail(10).mean() else "স্বাভাবিক ⚪")
        )
        await status.edit_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        print(f"Error: {e}")
        await status.edit_text("❌ কানেকশনে সমস্যা হচ্ছে। দয়া করে একটু পর আবার চেষ্টা করুন।")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.run_polling()
