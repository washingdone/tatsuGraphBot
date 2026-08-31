import sqlite3
from contextlib import closing
from tatsu.wrapper import ApiWrapper
import asyncio
import json
from datetime import datetime
import matplotlib.pyplot as plt
import os

async def getGuildRankings():
    config = json.load(open("./configFile"))
    tastuApi = ApiWrapper(key=config["tatsuKey"])
    result = await tastuApi.get_guild_rankings(config["discordGuildID"])
    rankings = result.rankings
    timestamp = datetime.now()

    with sqlite3.connect("graphBot.db") as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            # Prepare data batches for executemany
            user_data = [(u.user_id, u.rank) for u in rankings]
            score_data = [(u.user_id, u.score, timestamp) for u in rankings]

            # Upsert users
            cursor.executemany("""
            INSERT INTO users (id, ranking) VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET ranking = excluded.ranking;
            """, user_data)

            # Insert scores
            cursor.executemany("""
            INSERT INTO scores (user_id, score_value, timestamp) VALUES (?, ?, ?);
            """, score_data)

            cursor.execute("""
            DELETE FROM scores
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (
                        PARTITION BY user_id 
                        ORDER BY id DESC
                    ) as row_num
                    FROM scores
                )
                WHERE row_num > ?
            );
            """, (config["scoresToKeep"],))

            

# Using 'with' on conn automatically handles commits or rollbacks
with sqlite3.connect("graphBot.db") as conn:
    # closing() ensures the cursor is closed even if an error occurs
    with closing(conn.cursor()) as cursor:
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            ranking INTEGER
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            score_value INTEGER,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)
        
        # conn.commit() is automatically called at the end of the block 
        # if no exceptions were raised.

def generate_score_chart():
    config = json.load(open("./configFile"))
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
        """, (config["usersToChart"],))
        
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
    plt.figure(figsize=(10, 6))

    for user_id, data in user_data.items():
        plt.plot(data["times"], data["scores"], marker='o', label=f"User {user_id}")

    plt.title(f"Score Progression - Top {config["usersToChart"]} Users")
    plt.xlabel("Date / Time")
    plt.ylabel("Score")
    plt.legend(title="Users", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save image
    output_image = os.path.join(os.path.dirname(os.path.abspath(__file__)), "top_users_scores.png")
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Chart saved to {output_image}")




asyncio.run(getGuildRankings())