# NovaBot

NovaBot is a sophisticated Telegram bot designed to manage a mentorship and fundraising program. It facilitates the registration of participants and mentors, tracks fundraising progress through Monobank Jars, and provides a role-based system for administration, mentorship, and participation.

## About The Project

This bot is built to streamline the organization of a fundraising event. It automates the process of user registration, team formation (mentors and their participants), and progress tracking. Admins can manage the event, approve mentors, and distribute materials, while mentors can oversee their teams, and participants can focus on their fundraising goals.

## Features

- **Role-Based User System:**
    - **Admins:** Have full control over the bot, including user management, mentor approval, and content distribution.
    - **Mentors:** Can register, get approved by admins, and manage a team of participants.
    - **Participants:** Can register, choose a mentor, and set up their fundraising profile.
- **Multi-Step Registration:** A guided, stateful registration process for both mentors and participants.
- **Profile Management:** Users can set up and manage their profiles with details like name, Instagram handle, fundraising goal, and a profile photo.
- **Fundraising Tracking:** The bot automatically fetches the current amount from a user's Monobank Jar URL to track their fundraising progress.
- **Mentor-Participant Matching:** Participants can browse through a list of approved mentors and choose one to join their team.
- **Admin Panel:** A set of commands for admins to:
    - List, remove, and view user profiles.
    - Approve or reject pending mentor applications.
    - Send design materials (images, videos, animations) to users.
    - Export user data to Google Sheets.
- **Google Sheets Integration:** Automatically exports user data to a specified Google Sheet for easy tracking and analysis.
- **Scheduled Tasks:** Periodically refreshes the fundraising amounts from Monobank Jars for all users.
- **Database Integration:** Uses a PostgreSQL database to store user data, roles, and other relevant information.

## Technologies Used

- **Python 3**
- **aiogram:** A modern and fully asynchronous framework for Telegram bots.
- **PostgreSQL:** As the primary database, accessed using `asyncpg`.
- **SQLAlchemy:** For database schema management.
- **Selenium:** For web scraping of Monobank Jar pages to get fundraising amounts.
- **gspread & google-auth:** For integration with Google Sheets.
- **APScheduler:** For scheduling periodic tasks.
- **python-dotenv:** For managing environment variables.

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database

### Installation

1.  **Clone the repository:**
    ```sh
    git clone <your-repository-url>
    cd NovaBot
    ```

2.  **Create a virtual environment and activate it:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up the environment variables:**
    Create a `.env` file in the root directory by copying the `.env.example` file:
    ```sh
    cp .env.example .env
    ```
    Then, fill in the required values in the `.env` file. See the [Configuration](#configuration) section for more details.

## Configuration

The bot is configured using environment variables. The following variables need to be set in your `.env` file:

| Variable                      | Description                                                                                                |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `TELEGRAM_TOKEN`              | Your Telegram bot token from BotFather.                                                                    |
| `DATABASE_URL`                | The connection URL for your PostgreSQL database (e.g., `postgresql://user:password@host:port/database`).   |
| `DATABASE_NAME`               | The name of the database schema to use.                                                                    |
| `ADMINS`                      | A comma-separated list of Telegram user IDs for the bot administrators.                                    |
| `TECH_SUPPORT_ID`             | The Telegram user ID for the tech support contact.                                                         |
| `START_VIDEO_URL`             | A URL to a video to be shown at the start.                                                                 |
| `DB_CHAT_ID`                  | A Telegram chat ID for database-related notifications.                                                     |
| `INIT_RESOURCES_ON_START`     | Set to `yes` to initialize resources on bot start.                                                         |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The JSON content of your Google service account credentials for Google Sheets access.                      |
| `SHEET_KEY`                   | The key of the Google Sheet to export data to.                                                             |
| `SHEET_NAME`                  | The name of the sheet within the Google Sheet document.                                                    |
| `BROWSERLESS_TOKEN`           | A token for a Browserless service (used with Selenium for web scraping).                                   |

## Usage

To start the bot, run the `main.py` file:

```sh
python bot/main.py
```

The bot will then connect to Telegram and start polling for updates.

## Project Structure

```
NovaBot/
├── bot/
│   ├── main.py               # Main entry point for the bot
│   ├── config.py             # Handles configuration and environment variables
│   ├── db/
│   │   ├── database.py       # Database connection and query functions
│   │   └── db_listener.py    # Listens for database changes
│   ├── handlers/             # Contains message and callback query handlers
│   │   ├── admin.py
│   │   ├── mentor.py
│   │   ├── participant.py
│   │   └── start.py
│   ├── keyboards/            # Inline and reply keyboard layouts
│   └── utils/                # Utility functions (formatting, validation, etc.)
├── .env.example              # Example environment file
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```
