import sqlite3
from contextlib import closing
from tatsu.wrapper import ApiWrapper
from datetime import datetime


#TODO: replace config json pull with object pull once passing config through bot class
async def cleanDB(config):
    tatsuApi = ApiWrapper(key=config.apiKey)
    result = await tatsuApi.get_guild_rankings(config.guild.id)
    rankings = result.rankings
    activeUserIDs = [u.user_id for u in rankings]

    if not activeUserIDs:
        print(f"Tatsu API reported no active scores - aborting database cleanup")
        return -1

    with sqlite3.connect("graphBot.db") as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("PRAGMA foreign_keys = ON;")

            cursor.execute("CREATE TEMP TABLE active_ids (id TEXT PRIMARY KEY)")
        
            cursor.executemany("INSERT INTO active_ids VALUES (?)", ((uID,) for uID in activeUserIDs))

            # Delete users not in the temp table
            cursor.execute("""
            DELETE FROM users
            WHERE id NOT IN (SELECT id FROM active_ids)
            """)

            removedUsers = cursor.rowcount
    return removedUsers


#TODO: replace config json pull with object pull once passing config through bot class
async def getGuildRankings(config):
    tastuApi = ApiWrapper(key=config.apiKey)
    result = await tastuApi.get_guild_rankings(config.guild.id)
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
            """, (config.scoresToKeep,))




# TODO: remove these unneeded run commands once this is using a bot user instead of being ran manually for testing purposes

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