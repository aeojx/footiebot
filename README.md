# FootieBot: WhatsApp Football Game Organizer

FootieBot is a WhatsApp bot designed to automate the organization of weekly football games for a group. It handles player registration, manages standby lists, facilitates team division, and sends automated announcements.

## Features

*   **Automated List Opening:** Opens the player list every Wednesday at 9:00 PM.
*   **Player Registration:** Players can join the game using the `/play` command.
*   **Player Removal:** Players can leave the list using the `/remove` command.
*   **Standby Management:** Automatically promotes standby players if a main list player drops out.
*   **List Viewing:** Players can view the current list with `/list`.
*   **Automated Cancellation:** Checks for sufficient players by Saturday 11:59 PM and cancels the game if needed.
*   **Team Generation:** Organizer can divide teams using `/teams @player1 @player2 ...`.

## Setup and Deployment Guide

This guide will walk you through setting up and deploying FootieBot on a cloud platform like Render or Heroku. The bot uses Python with Flask for the web server and Twilio for WhatsApp integration.

### Prerequisites

1.  **Python 3.8+:** Ensure Python is installed on your local machine.
2.  **Twilio Account:** A Twilio account is required to send and receive WhatsApp messages. You'll need your Account SID and Auth Token.
3.  **Twilio WhatsApp Sandbox or Approved Sender:** For testing, you can use the Twilio WhatsApp Sandbox. For production, you'll need to get a WhatsApp Business Profile approved by Meta.
4.  **Cloud Platform Account:** An account on a platform like Render (recommended for ease of use) or Heroku.

### Local Setup (for development/testing)

1.  **Clone the repository:**
    ```bash
    git clone <repository_url> # Replace with your repository URL if you host it
    cd footiebot
    ```
2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Create a `.env` file:**
    Create a file named `.env` in the `footiebot` directory with the following content:
    ```
    TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    TWILIO_AUTH_TOKEN=your_auth_token_here
    TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886 # Your Twilio WhatsApp number
    ORGANIZER_PHONE=+1234567890 # Optional: Phone number of the organizer for specific commands
    ```
    Replace the placeholder values with your actual Twilio credentials and phone numbers.

5.  **Run the Flask application:**
    ```bash
    python app.py
    ```
    The bot will start running on `http://localhost:5000`.

### Deployment to Render (Recommended)

1.  **Push your code to GitHub:** Create a new GitHub repository and push your `footiebot` project to it.

2.  **Create a new Web Service on Render:**
    *   Log in to your Render account.
    *   Click "New" -> "Web Service".
    *   Connect your GitHub repository.
    *   **Name:** `footiebot` (or your preferred name)
    *   **Region:** Choose a region close to you.
    *   **Branch:** `main` (or your primary branch)
    *   **Root Directory:** `/`
    *   **Runtime:** `Python 3`
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `gunicorn app:app` (Gunicorn is a production-ready WSGI HTTP server)
    *   **Instance Type:** Choose a free instance for testing, or a paid one for reliability.

3.  **Add Environment Variables:**
    In the Render dashboard for your web service, go to "Environment" and add the following environment variables, matching the values from your local `.env` file:
    *   `TWILIO_ACCOUNT_SID`
    *   `TWILIO_AUTH_TOKEN`
    *   `TWILIO_WHATSAPP_NUMBER`
    *   `ORGANIZER_PHONE`

4.  **Deploy:** Click "Create Web Service". Render will build and deploy your application.

5.  **Configure Twilio Webhook:**
    *   Once your Render service is deployed, you'll get a public URL (e.g., `https://footiebot.onrender.com`).
    *   Go to your Twilio Console -> Messaging -> Try it out -> WhatsApp Sandbox (or your approved WhatsApp Business Profile settings).
    *   Under "WHEN A MESSAGE COMES IN", set the webhook URL to `YOUR_RENDER_URL/bot` (e.g., `https://footiebot.onrender.com/bot`). Make sure it's set to `HTTP POST`.
    *   Save the configuration.

### Usage

Once deployed and configured with Twilio, your FootieBot will be active in your WhatsApp group. Players can interact with it using the commands listed in the "Features" section.

## Project Structure

```
footiebot/
├── app.py              # Main bot logic and Flask application
├── requirements.txt    # Python dependencies
└── README.md           # This deployment guide
```

## Future Enhancements

*   **Database Integration:** Replace `game_data.json` with a proper database (e.g., SQLite, PostgreSQL) for better data persistence and scalability.
*   **Skill-Based Team Balancing:** Implement a more sophisticated algorithm for team balancing based on player skill ratings.
*   **Error Handling:** More robust error handling and user feedback for invalid commands.
*   **Customizable Schedules:** Allow organizers to customize game schedules and cancellation deadlines via commands.
*   **Admin Panel:** A simple web interface for organizers to manage settings and view data.
