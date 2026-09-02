import sqlite3
from contextlib import closing
import csv
from graphBuilders import generateTimeGraph
from datetime import datetime
from os import remove

class dbLine():
     def __init__(self, username, ranking, timestamp, score):
          self.user_id = username
          self.rank = int(ranking)
          self.score = int(score)
          self.timestamp = timestamp


remove('./graphBot.db')
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


rankings = []

with open('/mnt/c/users/marci/downloads/score_history_final.csv') as file:
     reader = csv.DictReader(file)

     for row in reader:
          obj = dbLine(
            username=row["username"],
            ranking=row["ranking"],
            timestamp=row["timestamp"],
            score=row["score"],
          )
          rankings.append(obj)
          
     
with sqlite3.connect("graphBot.db") as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            # Prepare data batches for executemany
            user_data = [(u.user_id, u.rank) for u in rankings]
            score_data = [(u.user_id, u.score, u.timestamp) for u in rankings]

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
            """, (1000000000000,))

generateTimeGraph('default_time_7', 7)
generateTimeGraph('all_time_7', 7, afterDate=False)
generateTimeGraph('custom_time_7', 7, beforeDate=datetime(2024, 1, 1), afterDate=datetime(2023, 1, 1))

generateTimeGraph('rank_11_window_9', 11, usersToChart=9, afterDate=False)
generateTimeGraph('rank_3_window_9', 3, usersToChart=9, afterDate=False)
generateTimeGraph('rank_11_window_8', 11, usersToChart=8, afterDate=False)