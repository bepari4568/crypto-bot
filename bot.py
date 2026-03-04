import ccxt
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import pytz
import asyncio

# --- CONFIGURATION ---
TOKEN = '8710909291:AAFA5knDt_EybhJSF5YiK5ljZhyx9fVGPRQ'
SYMBOL = 'CORE/USDT'
TIMEFRAME = '4h'

# Enhanced connection for stability
exchange = ccxt.bitget({
    'enableRateLimit': True,
    'timeout': 60000, 
    'options': {'defaultType': 'spot'}
})

def get_candle_time_left():
    now = datetime.now(pytz.utc)
    hours_passed = now.hour % 4
    next_close = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=(4 - hours_passed))
    time_left = next_close - now
    h, rem = divmod(int(time_left.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"

async def get_comprehensive_data():
    # Attempting to fetch data with retries for low battery stability
    for attempt in range(3):
        try:
            ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=101)
            df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
            
            # Summary (Previous Candle)
            prev_candle = df.iloc[-2]
            
            # AI Prediction (Current Trend)
            curr_price = df['close'].iloc[-1]
            X = np.array(range(len(df))).reshape(-1, 1)
            y = df['close'].values
            model = LinearRegression().fit(X, y)
            ai_target = round(model.predict([[len(df)]])[0], 4)
            
            # Time Settings
            utc_now = datetime.now(pytz.utc)
            bd_time = utc_now.astimezone(pytz.timezone('Asia/Dhaka')).strftime('%I:%M %p (%d %b)')
            utc_time = utc_now.strftime('%I:%M %p')

            return {
                'p_open': prev_candle['open'], 'p_close': prev_candle['close'],
                'entry': curr_price, 'ai_pred': ai_target,
                'bd': bd_time, 'utc': utc_time, 'tl': get_candle_time_left()
            }
        except:
            await asyncio.sleep(3)
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = await update.message.reply_text("📡 Generating Full Market Report...")
    data = await get_comprehensive_data()
    
    if data:
        msg = (
            f"📊 **LAST 4H SUMMARY**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏁 Prev Open: `${data['p_open']}`\n"
            f"✅ Prev Close: `${data['p_close']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔮 **AI NEXT 4H FORECAST**\n"
            f"💰 Entry Price: `${data['entry']}`\n"
            f"🎯 AI Target: `${data['ai_pred']}`\n"
            f"🚦 Signal: " + ("BUY 🚀" if data['ai_pred'] > data['entry'] else "SELL 📉") + "\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ **Candle Close In:** `{data['tl']}`\n"
            f"🕒 **BD Time:** {data['bd']}\n"
            f"🌐 **UTC Time:** {data['utc']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Not Financial Advice!*"
        )
        await status.edit_text(msg, parse_mode='Markdown')
    else:
        await status.edit_text("❌ Connection Error. Please wait 1 min and try again.")

if __name__ == '__main__':
    print("Bot is LIVE! Ensure battery is above 15%.")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.run_polling(drop_pending_updates=True)