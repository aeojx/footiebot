import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Configuration & Data ---
# In a production app, use a database (SQLite/PostgreSQL). 
# For this prototype, we'll use a JSON file for persistence.
DATA_FILE = 'game_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {
        "is_open": False,
        "main_list": [],
        "standby_list": [],
        "max_players": 14,
        "max_standby": 2,
        "teams": {"black": [], "white": []},
        "game_time": "Tuesday 8:30 PM",
        "location": "RAD Sports"
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Bot Logic ---

def get_list_message(data):
    main_list_str = "\n".join([f"{i+1}. {name}" for i, name in enumerate(data['main_list'])])
    standby_list_str = "\n".join([f"{i+1}. {name}" for i, name in enumerate(data['standby_list'])])
    
    msg = f"*Footie List Status*\n\n"
    msg += f"*Game Details:*\n{data['game_time']}\n{data['location']}\n\n"
    msg += f"*Main List ({len(data['main_list'])}/{data['max_players']}):*\n{main_list_str if main_list_str else 'Empty'}\n\n"
    msg += f"*Standby ({len(data['standby_list'])}/{data['max_standby']}):*\n{standby_list_str if standby_list_str else 'Empty'}\n\n"
    msg += "Type */play* to join or */remove* to leave."
    return msg

def handle_play(sender_name, sender_phone):
    data = load_data()
    if not data['is_open']:
        return "The list is currently closed. It opens every Wednesday at 9 PM."
    
    # Check if already on either list
    if sender_name in data['main_list'] or sender_name in data['standby_list']:
        return f"Hey {sender_name}, you're already on the list!"

    if len(data['main_list']) < data['max_players']:
        data['main_list'].append(sender_name)
        response = f"Nice! {sender_name} added to the main list."
    elif len(data['standby_list']) < data['max_standby']:
        data['standby_list'].append(sender_name)
        response = f"Main list full. {sender_name} added to standby."
    else:
        response = "Sorry, both the main list and standby are full!"
    
    save_data(data)
    return f"{response}\n\n{get_list_message(data)}"

def handle_remove(sender_name):
    data = load_data()
    if sender_name in data['main_list']:
        data['main_list'].remove(sender_name)
        # Move first standby to main list if available
        if data['standby_list']:
            promoted = data['standby_list'].pop(0)
            data['main_list'].append(promoted)
            response = f"{sender_name} removed. {promoted} moved from standby to main list."
        else:
            response = f"{sender_name} has been removed from the list."
    elif sender_name in data['standby_list']:
        data['standby_list'].remove(sender_name)
        response = f"{sender_name} removed from standby."
    else:
        response = "You weren't on the list anyway!"
    
    save_data(data)
    return f"{response}\n\n{get_list_message(data)}"

def handle_teams(command_text):
    # Command format: /teams @player1 @player2 ...
    data = load_data()
    
    # Extract players tagged (names starting with @)
    tagged_players = [p.strip() for p in command_text.split('@') if p.strip() and p.strip() != 'teams']
    
    if len(tagged_players) != 7:
        return f"Please tag exactly 7 players for the Black Team. You tagged {len(tagged_players)}. Example: /teams @Ali @Omar..."

    # We need to find the full names from the main list that match the tags
    black_team = []
    white_team = []
    
    # For each player in the main list, check if they were tagged
    for p in data['main_list']:
        found = False
        for tag in tagged_players:
            if tag.lower() in p.lower():
                black_team.append(p)
                found = True
                break
        if not found:
            white_team.append(p)
            
    # Check if we actually found 7 players
    if len(black_team) != 7:
         return f"Found {len(black_team)} matching players from the main list for the Black Team. Please make sure the names match exactly or are unique enough."

    data['teams'] = {"black": black_team, "white": white_team}
    save_data(data)
    
    msg = "*Game is On!*\n\n"
    msg += f"*Time:* {data['game_time']}\n"
    msg += f"*Location:* {data['location']}\n\n"
    msg += "*Black Team:*\n" + "\n".join(black_team) + "\n\n"
    msg += "*White Team:*\n" + "\n".join(white_team)
    return msg

# --- Scheduler Tasks ---

def open_list_job():
    data = load_data()
    data['is_open'] = True
    data['main_list'] = []
    data['standby_list'] = []
    data['teams'] = {"black": [], "white": []}
    save_data(data)
    logger.info("Game list opened automatically.")
    # In a real scenario, you'd use Twilio's client to send a message to the group here.

def check_game_status_job():
    data = load_data()
    if len(data['main_list']) < data['max_players']:
        logger.info("Game cancelled due to insufficient players.")
        # Trigger cancellation message via Twilio API
    else:
        logger.info("Game confirmed!")

# Setup Scheduler
scheduler = BackgroundScheduler()
# Open list every Wednesday at 9 PM
scheduler.add_job(open_list_job, 'cron', day_of_week='wed', hour=21, minute=0)
# Check status Saturday at 11:59 PM
scheduler.add_job(check_game_status_job, 'cron', day_of_week='sat', hour=23, minute=59)
scheduler.start()

# --- Flask Routes ---

@app.route("/bot", methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower().strip()
    sender_name = request.values.get('ProfileName', 'Player')
    
    resp = MessagingResponse()
    msg = resp.message()
    
    if incoming_msg.startswith('/play'):
        reply = handle_play(sender_name, "")
        msg.body(reply)
    elif incoming_msg.startswith('/remove'):
        reply = handle_remove(sender_name)
        msg.body(reply)
    elif incoming_msg.startswith('/list'):
        data = load_data()
        msg.body(get_list_message(data))
    elif incoming_msg.startswith('/teams'):
        reply = handle_teams(incoming_msg)
        msg.body(reply)
    elif incoming_msg.startswith('/open'): # Manual override for testing/organizer
        open_list_job()
        data = load_data()
        msg.body("List is now OPEN!\n\n" + get_list_message(data))
    elif incoming_msg.startswith('/help'):
        help_text = (
            "*FootieBot Commands:*\n"
            "*/play* - Join the game list\n"
            "*/remove* - Leave the list\n"
            "*/list* - See current players\n"
            "*/teams @p1 @p2...* - (Organizer) Set Black Team (7 players)"
        )
        msg.body(help_text)
        
    return str(resp)

if __name__ == "__main__":
    # In production, use Gunicorn or Waitress
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
