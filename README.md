# Dota Data Bot

This project is a Telegram bot that provides various statistics and predictions related to Dota 2 matches.

## Features

- Fetches and displays match data from the OpenDota API.
- Provides player statistics, including win/loss ratios, recent matches, player heroes stats, peers, totals, leaver status, and wordcloud.
- Allows users to add and manage favourite players.
- Provides live match updates.
- Predicts match outcomes using pre-trained machine learning models.

## Code Structure

- [main.py](main.py): The entry point of the application. It sets up the Telegram bot and handles user interactions.
- [helpers/helpers.py](helpers/helpers.py): Contains utility functions used throughout the project.
- [main_menu/players_menu/](main_menu/players_menu/): Handles the player menu interactions.
- [constants.py](constants.py): Contains constants used throughout the project, including pre-loaded machine learning models and database connections.

## Setup

1. Clone the repository.
2. Install the required Python packages using pip:

```shell
pip install -r requirements.txt
```
3. Set up your environment variables in a `.env` file. You'll need to set your Telegram bot token and MongoDB connection string.
4. Run the bot:
```shell
python main.py
```

## Note

The machine learning models used for match prediction are not included in the repository due to their size. You'll need to train your own models and place them in the models/ directory. You can refer to [this project](https://github.com/sukhrobyangibaev/thesis-pub) for an example of how to train these models.
