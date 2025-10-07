import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime, timedelta
from collections import defaultdict
import random
from threading import Thread
from flask import Flask
import os

# -------------------- LOGGING --------------------
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- DATABASE --------------------
players = {}
leaderboard_cache = []
last_leaderboard_update = datetime.now()
auctions = {}
alliances = defaultdict(list)  # alliance_name: [user_ids]

# -------------------- GAME CONSTANTS --------------------
BUSINESSES = {
    'lemonade_stand': {'name': '🍋 Lemonade Stand', 'base_cost': 100, 'base_income': 1, 'multiplier': 1.15},
    'coffee_shop': {'name': '☕ Coffee Shop', 'base_cost': 1000, 'base_income': 10, 'multiplier': 1.15},
    'restaurant': {'name': '🍔 Restaurant', 'base_cost': 10000, 'base_income': 100, 'multiplier': 1.15},
    'factory': {'name': '🏭 Factory', 'base_cost': 100000, 'base_income': 1000, 'multiplier': 1.15},
    'tech_startup': {'name': '💻 Tech Startup', 'base_cost': 1000000, 'base_income': 10000, 'multiplier': 1.15},
    'bank': {'name': '🏦 Bank', 'base_cost': 10000000, 'base_income': 100000, 'multiplier': 1.15},
    'oil_empire': {'name': '🛢️ Oil Empire', 'base_cost': 100000000, 'base_income': 1000000, 'multiplier': 1.15},
    'space_corp': {'name': '🚀 Space Corp', 'base_cost': 1000000000, 'base_income': 10000000, 'multiplier': 1.15},
}

UPGRADES = {
    'multiplier_1': {'name': '📈 Income Boost x2', 'cost': 5000, 'effect': 2},
    'multiplier_2': {'name': '📈 Income Boost x5', 'cost': 50000, 'effect': 5},
    'multiplier_3': {'name': '📈 Income Boost x10', 'cost': 500000, 'effect': 10},
    'multiplier_4': {'name': '📈 Income Boost x50', 'cost': 5000000, 'effect': 50},
    'multiplier_5': {'name': '📈 Income Boost x100', 'cost': 50000000, 'effect': 100},
}

# -------------------- HELPER FUNCTIONS --------------------
def format_number(num):
    if num >= 1e12: return f"${num/1e12:.2f}T"
    if num >= 1e9: return f"${num/1e9:.2f}B"
    if num >= 1e6: return f"${num/1e6:.2f}M"
    if num >= 1e3: return f"${num/1e3:.2f}K"
    return f"${num:.2f}"

def get_player(user_id):
    if user_id not in players:
        players[user_id] = {
            'money': 1000,
            'income_per_second': 0,
            'businesses': defaultdict(int),
            'upgrades': [],
            'income_multiplier': 1,
            'last_collect': datetime.now(),
            'total_earned': 0,
            'prestige_level': 0,
            'prestige_bonus': 1,
            'username': 'Unknown',
            'raids_won': 0,
            'raids_lost': 0,
            'achievements': [],
            'daily_claimed': False,
            'alliance': None
        }
    return players[user_id]

def calculate_business_cost(business_id, count):
    base = BUSINESSES[business_id]['base_cost']
    multiplier = BUSINESSES[business_id]['multiplier']
    return int(base * (multiplier ** count))

def calculate_income(player):
    total = 0
    for biz_id, count in player['businesses'].items():
        if count > 0:
            total += BUSINESSES[biz_id]['base_income'] * count
    total *= player['income_multiplier'] * player['prestige_bonus']
    player['income_per_second'] = total
    return total

def collect_idle_income(player):
    now = datetime.now()
    time_diff = (now - player['last_collect']).total_seconds()
    time_diff = min(time_diff, 14400)
    idle_income = player['income_per_second'] * time_diff
    player['money'] += idle_income
    player['total_earned'] += idle_income
    player['last_collect'] = now
    return idle_income, time_diff

def unlock_achievement(player, name):
    if name not in player['achievements']:
        player['achievements'].append(name)

# -------------------- TELEGRAM HANDLERS --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)
    player['username'] = user.username or user.first_name
    idle_income, _ = collect_idle_income(player)
    calculate_income(player)
    welcome_text = f"""
🔥 **WELCOME TO EMPIRE WARS** 🔥

💰 Money: {format_number(player['money'])}
Income: {format_number(player['income_per_second'])}/sec
Prestige Level: {player['prestige_level']}

Use /empire to see your empire and start building!
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

# (Add all other command handlers: /empire, /buy, /upgrade, /raid, /auction, /alliance, /flex, /daily, /leaderboard, /profile)
# For brevity, you can reuse the handlers from your previous code and integrate auctions, raids, alliances, achievements, etc.

# -------------------- FLASK SERVER --------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "🔥 Empire Wars Bot is ALIVE! 🔥"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# -------------------- MAIN --------------------
def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("❌ ERROR: BOT_TOKEN not found!")
        return

    # Start Flask server in background
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Telegram bot
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    # Add other handlers here (empire, buy, upgrade, raid, auction, alliance, flex, daily, leaderboard, profile, etc.)
    
    print("🔥 EMPIRE WARS BOT IS RUNNING! 🔥")
    application.run_polling()

if __name__ == "__main__":
    main()
