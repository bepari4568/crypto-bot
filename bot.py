import ccxt
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import pytz

# --- CONFIGURATION ---
TOKEN = '8710909291:AAFA5knDt_EybhJSF5YiK5ljZhyx9fVGPRQ'
SYMBOL = 'CORE/USDT'
TIMEFRAME = '1h'

exchange = ccxt.bitget({'enableRateLimit': True})

def get_indicators(df):
    # EMA Calculation
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # RSI Calculation
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    # MACD Calculation
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # Support & Resistance (Pivot Points)
    last_low = df['low'].tail(24).min()
    last_high = df['high'].tail(24).max()
    
    return df, last_low, last_high

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = await update.message.reply_text("🔍 Performing Deep Market Analysis (EMA, MACD, RSI)...")
    
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        df, support, resistance = get_indicators(df)
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        avg_vol = df['vol'].tail(20).mean()
        
        # --- Logic for Signal ---
        decision = "NEUTRAL ⚡"
        strength = "Low"
        
        # Buy Condition: Price > EMA20 and MACD > Signal and RSI < 70
        if curr['close'] > curr['ema20'] and curr['macd'] > curr['signal_line'] and curr['rsi'] < 70:
            if curr['vol'] > avg_vol:
                decision = "STRONG BUY 🚀"
                strength = "High"
            else:
                decision = "BUY 📈"
                strength = "Medium"
                
        # Sell Condition: Price < EMA20 and MACD < Signal and RSI > 30
        elif curr['close'] < curr['ema20'] and curr['macd'] < curr['signal_line'] and curr['rsi'] > 30:
            if curr['vol'] > avg_vol:
                decision = "STRONG SELL 📉"
                strength = "High"
            else:
                decision = "SELL 🆘"
                strength = "Medium"

        bd_time = datetime.now(pytz.timezone('Asia/Dhaka')).strftime('%I:%M %p')

        msg = (
            f"🎯 **CORE/USDT 1H SMART REPORT**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Price:** `${curr['close']}`\n"
            f"📊 **Signal:** `{decision}`\n"
            f"💪 **Strength:** `{strength}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📏 **Support:** `${round(support, 4)}`\n"
            f"🧱 **Resistance:** `${round(resistance, 4)}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌡️ **RSI:** `{round(curr['rsi'], 2)}` | " + ("Overbought" if curr['rsi'] > 70 else "Oversold" if curr['rsi'] < 30 else "Normal") + "\n"
            f"📉 **MACD:** " + ("Bullish" if curr['macd'] > curr['signal_line'] else "Bearish") + "\n"
            f"📈 **EMA Trend:** " + ("Upward" if curr['ema20'] > curr['ema50'] else "Downward") + "\n"
            f"📊 **Volume:** " + ("Surging 🟢" if curr['vol'] > avg_vol else "Stable ⚪") + "\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 **BD Time:** `{bd_time}`\n"
            f"⚠️ *Analysis based on multiple indicators.*"
        )
        await status.edit_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await status.edit_text(f"❌ Analysis failed: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.run_polling()
