import disnake
from disnake.ext import tasks, commands
from tatsu.wrapper import ApiWrapper
import json
import sqlite3
from contextlib import closing
import datetime
from initDB import getGuildRankings
import matplotlib.pyplot as matplot
import os

# import asyncio # temp import for making python work 



class graphBotOptions():
    def __init__(self, configPath):
        config = json.load(open(configPath))

        self.token = config["discordToken"]
        self.guild = config["discordGuildID"]
        self.apiKey = config["tatsuKey"]
        self.updateInterval = config["updateInterval"]
        self.usersToChart = config["usersToChart"]

class graphBotClient(commands.InteractionBot):
    async def on_ready(self):
        try:
            options.guild = await client.fetch_guild(options.guild)
        except BaseException as err:
            print(f"Error transforming guild ID to an object, please double check your config file before reporting this error!\nn{err=}")
            exit(1)
        else:
            print(f"Logged on as {self.user} and linked to {options.guild.name}!")

    try:
        options = graphBotOptions("./configFile")
    except BaseException as err:
        print(f"Error generating configuration, double check your config file!\n{err=}")
        exit(1)



def generateScoreChart():
    with sqlite3.connect("graphBot.db") as conn:
        cursor = conn.cursor()
        
        # Query score history for top X ranked users
        cursor.execute("""
            SELECT user_id, score_value, timestamp 
            FROM scores 
            WHERE user_id IN (
                SELECT id FROM users 
                ORDER BY ranking ASC 
                LIMIT ?
            )
            ORDER BY timestamp ASC;
        """, (options.usersToChart,))
        
        rows = cursor.fetchall()

    if not rows:
        print("No score data available to chart.")
        return

    # Group records by user_id
    user_data = {}
    for user_id, score, ts_str in rows:
        if user_id not in user_data:
            user_data[user_id] = {"times": [], "scores": []}
        
        # Parse ISO string format to datetime object
        dt = datetime.fromisoformat(ts_str)
        user_data[user_id]["times"].append(dt)
        user_data[user_id]["scores"].append(score)

    # Build graph
    matplot.figure(figsize=(10, 6))

    for user_id, data in user_data.items():
        matplot.plot(data["times"], data["scores"], marker='o', label=f"User {user_id}")

    matplot.title(f"Score Progression - Top {options.usersToChart} Users")
    matplot.xlabel("Date / Time")
    matplot.ylabel("Score")
    matplot.legend(title="Users", bbox_to_anchor=(1.05, 1), loc='upper left')
    matplot.grid(True, linestyle="--", alpha=0.6)
    matplot.xticks(rotation=45)
    matplot.tight_layout()

    # Save image
    output_image = os.path.join(os.path.dirname(os.path.abspath(__file__)), "top_users_scores.png")
    matplot.savefig(output_image, dpi=300)
    matplot.close()
    print(f"Chart saved to {output_image}")



try:
    client = graphBotClient()
except BaseException as err:
    print(f"Client could not be initialized!\n\n{err=}")
    exit(1)

try:
    options = graphBotOptions("./configFile")
except BaseException as err:
    print(f"Unable to generate configuration class, please double check your config file!\n\n{err=}")

# client.run(options.token) # run client
generateScoreChart()