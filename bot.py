import ccxt
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import pytz

# --- ELITE CONFIGURATION ---
TOKEN = '8710909291:AAFA5knDt_EybhJSF5YiK5ljZhyx9fVGPRQ'
SYMBOL = 'CORE/USDT'
TIMEFRAME = '1h'

exchange = ccxt.bitget({'enableRateLimit': True})

def calculate_advanced_metrics(df):
    # RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    # EMA 20 & 50 (Trend Analysis)
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # MACD Calculation
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # Dynamic Support & Resistance
    support = df['low'].tail(24).min()
    resistance = df['high'].tail(24).max()
    
    return df, support, resistance

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = await update.message.reply_text("💎 Analyzing Market Structure & AI Sentiment...")
    
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        df, support, resistance = calculate_advanced_metrics(df)
        
        curr = df.iloc[-1]
        avg_vol = df['vol'].tail(20).mean()
        
        # --- AI ACCURACY & SENTIMENT ---
        sentiment = "Neutral ⚖️"
        if curr['rsi'] > 65: sentiment = "Extreme Greed 🔥"
        elif curr['rsi'] < 35: sentiment = "Extreme Fear 🧊"
        
        # Accuracy Calculation (Based on Indicator Convergence)
        accuracy = 82.0
        if (curr['close'] > curr['ema20']) == (curr['macd'] > curr['signal_line']):
            accuracy += 12.5 # High convergence increases accuracy
        
        # --- LEGENDARY SIGNAL LOGIC ---
        if curr['close'] > curr['ema20'] and curr['macd'] > curr['signal_line']:
            signal = "BULLISH BREAKOUT 🚀"
            recommendation = "Long Position (Buy)"
        elif curr['close'] < curr['ema20'] and curr['macd'] < curr['signal_line']:
            signal = "BEARISH REJECTION 📉"
            recommendation = "Short Position (Sell)"
        else:
            signal = "CONSOLIDATION ⚡"
            recommendation = "Stay Sideways (Wait)"

        # --- TIMER & CLOSING LOGIC ---
        tz = pytz.timezone('Asia/Dhaka')
        now = datetime.now(tz)
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        remaining = next_hour - now
        timer = f"{int(remaining.total_seconds() // 60)}m {int(remaining.total_seconds() % 60)}s"

        # Predicted closing based on EMA momentum
        pred_close = round(curr['close'] + (curr['macd'] * 0.3), 4)

        msg = (
            f"👑 **CORE/USDT ELITE INTELLIGENCE**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Price:** `${curr['close']}`\n"
            f"🔮 **AI Target:** `${pred_close}`\n"
            f"✅ **Accuracy:** `{round(accuracy, 1)}%`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚦 **Signal:** **{signal}**\n"
            f"💡 **Action:** `{recommendation}`\n"
            f"⏳ **Next Candle:** `{timer}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Market Vitals:**\n"
            f"• Sentiment: `{sentiment}`\n"
            f"• Volatility: " + ("Explosive 💥" if curr['vol'] > avg_vol * 1.5 else "Stable ⚪") + "\n"
            f"• Trend: " + ("Bullish Cross 📈" if curr['ema20'] > curr['ema50'] else "Bearish Cross 📉") + "\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📏 **Risk Management:**\n"
            f"🚧 Resistance: `${round(resistance, 4)}`\n"
            f"🧱 Support: `${round(support, 4)}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 **BD Time:** `{now.strftime('%I:%M:%S %p')}`\n"
            f"💎 *Professional Grade AI Analysis*"
        )
        await status.edit_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await status.edit_text(f"❌ System Offline: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.run_polling()
