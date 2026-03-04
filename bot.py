import ccxt
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import pytz

# --- CONFIGURATION ---
TOKEN = '8710909291:AAFA5knDt_EybhJSF5YiK5ljZhyx9fVG4P' # আপনার টোকেনটি ঠিক আছে তো?
SYMBOL = 'CORE/USDT'
TIMEFRAME = '1h'

exchange = ccxt.bitget({'enableRateLimit': True})

def get_indicators(df):
    # EMA & RSI
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
    status = await update.message.reply_text("⏳ ক্যালকুলেশন হচ্ছে, দয়া করে অপেক্ষা করুন...")
    
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        df, support, resistance = get_indicators(df)
        curr = df.iloc[-1]
        
        # --- ১. ক্যান্ডেল ক্লোজিং টাইমার ---
        tz = pytz.timezone('Asia/Dhaka')
        now = datetime.now(tz)
        # পরবর্তী ঘণ্টার শুরুর সময় বের করা
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        remaining_time = next_hour - now
        minutes_left = int(remaining_time.total_seconds() // 60)
        close_time_str = next_hour.strftime('%I:%00 %p')

        # --- ২. ক্লোজিং প্রাইস প্রেডিকশন (Simple AI logic) ---
        # যদি MACD ও EMA পজিটিভ হয়, তবে হাই প্রাইসের কাছাকাছি ক্লোজ হওয়ার সম্ভাবনা থাকে
        prediction_price = curr['close'] + (curr['macd'] * 0.5) 
        prediction_price = round(prediction_price, 4)

        # --- ৩. সিগন্যাল লজিক ---
        if curr['close'] > curr['ema20'] and curr['macd'] > curr['signal_line']:
            signal = "BUY 🚀"
        elif curr['close'] < curr['ema20'] and curr['macd'] < curr['signal_line']:
            signal = "SELL 📉"
        else:
            signal = "WAIT ⚡"

        msg = (
            f"📊 **CORE/USDT ১ ঘণ্টার রিপোর্ট**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **বর্তমান প্রাইস:** `${curr['close']}`\n"
            f"🔮 **সম্ভাব্য ক্লোজিং প্রাইস:** `${prediction_price}`\n"
            f"⏰ **ক্যান্ডেল ক্লোজ হবে:** `{close_time_str}`\n"
            f"⏳ **বাকি আছে:** `{minutes_left} মিনিট`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚦 **সিগন্যাল:** **{signal}**\n"
            f"📏 **সাপোর্ট:** `${round(support, 4)}`\n"
            f"🧱 **রেজিস্ট্যান্স:** `${round(resistance, 4)}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 **EMA Trend:** " + ("Upward" if curr['close'] > curr['ema20'] else "Downward") + "\n"
            f"📉 **MACD:** " + ("Bullish" if curr['macd'] > curr['signal_line'] else "Bearish") + "\n"
            f"📊 **ভলিউম:** " + ("High 🟢" if curr['vol'] > df['vol'].tail(10).mean() else "Normal ⚪") + "\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 **এখন সময়:** `{now.strftime('%I:%M %p')}`"
        )
        await status.edit_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await status.edit_text(f"❌ এরর: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.run_polling()
