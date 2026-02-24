from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Initialize bot only if token exists
bot = None
if BOT_TOKEN:
    bot = Bot(token=BOT_TOKEN)
else:
    logger.warning("BOT_TOKEN not set. Telegram messages will not be sent.")

def gold_signal():
    """Generate gold trading signal"""
    return {
        "bias": "BUY",
        "confidence": 70,
        "reasons": [
            "Inflation high",
            "Central banks buying gold",
            "ETF inflows positive",
            "Geopolitical risk rising"
        ]
    }

def send_signal():
    """Send signal to Telegram"""
    if not bot or not CHAT_ID:
        logger.warning("Telegram bot or CHAT_ID not configured")
        return
    
    try:
        s = gold_signal()
        msg = f"GOLD SIGNAL\n\n"
        msg += f"Bias: {s['bias']}\n"
        msg += f"Confidence: {s['confidence']}%\n\n"
        msg += f"Reasons:\n"
        for r in s["reasons"]:
            msg += f"- {r}\n"
        
        bot.send_message(chat_id=CHAT_ID, text=msg)
        logger.info("Signal sent successfully")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_signal, "interval", hours=1)
scheduler.start()
logger.info("Scheduler started - will send signals every hour")

@app.get("/", response_class=HTMLResponse)
def home():
    """Web dashboard"""
    s = gold_signal()
    
    # Color coding based on bias
    color = "green" if s['bias'] == "BUY" else "red" if s['bias'] == "SELL" else "orange"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gold AI Signal</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                color: #333;
            }}
            h1 {{
                text-align: center;
                color: #333;
                margin-top: 0;
                border-bottom: 2px solid #f0f0f0;
                padding-bottom: 20px;
            }}
            .bias {{
                font-size: 48px;
                font-weight: bold;
                text-align: center;
                margin: 20px 0;
                padding: 20px;
                border-radius: 10px;
                color: white;
                background-color: {color};
            }}
            .confidence {{
                text-align: center;
                font-size: 24px;
                margin: 20px 0;
                color: #666;
            }}
            .reasons {{
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin-top: 20px;
            }}
            .reasons h3 {{
                margin-top: 0;
                color: #333;
            }}
            .reasons ul {{
                list-style-type: none;
                padding: 0;
            }}
            .reasons li {{
                padding: 10px;
                margin: 5px 0;
                background: white;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                color: #555;
            }}
            .reasons li:before {{
                content: "•";
                color: {color};
                font-weight: bold;
                margin-right: 10px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                font-size: 14px;
                color: rgba(255,255,255,0.8);
            }}
            .status {{
                text-align: center;
                margin-top: 20px;
                padding: 10px;
                background: rgba(255,255,255,0.2);
                border-radius: 5px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Gold AI Signal</h1>
            <div class="bias">
                {s['bias']}
            </div>
            <div class="confidence">
                Confidence: {s['confidence']}%
            </div>
            <div class="reasons">
                <h3>Analysis Reasons:</h3>
                <ul>
                    {''.join(f'<li>{r}</li>' for r in s["reasons"])}
                </ul>
            </div>
        </div>
        <div class="status">
            Telegram alerts: {'Active' if bot and CHAT_ID else 'Not configured'}
            <br>
            Updates every hour
        </div>
        <div class="footer">
            Powered by FastAPI on Render
        </div>
    </body>
    </html>
    """
    return html

@app.get("/api/signal")
def get_signal():
    """API endpoint for signal data"""
    return gold_signal()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "telegram_configured": bool(bot and CHAT_ID),
        "scheduler_running": scheduler.running
    }

# Shutdown handler to properly stop the scheduler
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler stopped")
