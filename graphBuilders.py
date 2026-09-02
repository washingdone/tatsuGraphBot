import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patheffects as patheffects
from adjustText import adjust_text

def getContrastingBackground(color):
    # Standard W3C formula for relative luminance
    r, g, b = color[:3]

    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    # If the color is bright, use black background. If dark, use white.
    return (0.0, 0.0, 0.0, 0.25) if luminance > 0.5 else (1.0, 1.0, 1.0, 0.25)

def generateTimeGraph(fileout, requesterRank, usersToChart=10, beforeDate=False, afterDate=datetime.now()-relativedelta(years=1), useUsername=False):
    # TODO: remove fileout param once images are passed natively through discord instead of being saved locally


    leftCount = int((usersToChart - 1) / 2)
    leftBound = requesterRank - leftCount
    if leftBound < 1:
        leftBound = 1
    rightBound = leftBound + usersToChart - 1
    
    
    #initialze variables for the display window if they're not already declared
    runDatetime = datetime.now()
    if not beforeDate:
        beforeDate = runDatetime
    if not afterDate:
        afterDate = datetime(2000, 1, 1)

    #generate the string that will prettily display the date range in the graph title
    if beforeDate == runDatetime and afterDate == datetime(2000, 1, 1):
        timeFrameString = 'All Time'
    else:
        timeFrameString = f"{afterDate.date()} to {beforeDate.date()}"

    #pull the relevant sections of data from the database and store it in the rows variable
    with sqlite3.connect("graphBot.db") as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, score_value, timestamp 
            FROM scores 
            WHERE user_id IN (
                SELECT id FROM users 
                WHERE ranking BETWEEN ? AND ?
            )
            ORDER BY timestamp ASC;
        """, (leftBound, rightBound))
        
        rows = cursor.fetchall()

    if not rows:
        print("No score data available to chart.")
        return

    # Group records by user_id
    scoreData = {}
    for userID, score, timeString in rows:
        dateTime = datetime.fromisoformat(timeString)

        if not (beforeDate and afterDate) or (afterDate <= dateTime <= beforeDate):
            if userID not in scoreData:
                scoreData[userID] = {"times": [], "scores": []}
            
            scoreData[userID]["times"].append(dateTime)
            scoreData[userID]["scores"].append(score)

    # Build graph TODO: convert to a seperate function once i've fixed needing an output file
    axisColor = '#72767d'
    bgColor = (1.0, 1.0, 1.0, 0.15)
    plt.figure(figsize=(15, 9), facecolor=bgColor)
    # guild = client.get_guild(99199781900910592) #TODO: unhardcode the guild id and build the rest of the user data collector
    texts = []

    for userID, data in scoreData.items():
        # userMember = guild.get_member(user_id)
        if useUsername:
            pass #TODO: userMember = userMember.name
        else:
            pass #TODO: userMember = userMember.nick
        line = plt.plot(data["times"], data["scores"], marker='o') # TODO: remove variable and reference user color
        color = line[0].get_color()

        # 2. Add inline text at the end of each series
        if data["times"] and data["scores"]:
            last_x = data["times"][-1]
            last_y = data["scores"][-1]

            txt = plt.text(
                last_x,
                last_y,
                f" {userID}", 
                ha="left",
                va="center",
                color=color,
                weight="bold"
            )

            # Add a 3-pixel wide semi-transparent white outline around the text
            txt.set_path_effects([
                patheffects.withStroke(linewidth=1.5, foreground=(1, 1, 1, 0.75))
            ])
            texts.append(txt)


    plt.title(f"Score Progression - Users Ranked {leftBound} to {rightBound} - {timeFrameString}", color=axisColor)
    plt.xlabel("Date / Time", color=axisColor)
    plt.ylabel("Score", color=axisColor)

    def formatYAxis(x, pos):
        if abs(x) >= 1_000_000:
            return f'{x * 1e-6:.2f}M'.rstrip('0').rstrip('.')  # 1.25M, but 1M instead of 1.00M
        elif abs(x) >= 1_000:
            return f'{x * 1e-3:.0f}k'
        else:
            return f'{x:.0f}'
    
    axis = plt.gca()
    axis.yaxis.set_major_formatter(ticker.FuncFormatter(formatYAxis))
    xmin, xmax = axis.get_xlim()
    axis.set_xlim(xmin, xmax + (xmax - xmin) * 0.12)  # Extends right boundary by 12%
    axis.set_facecolor(bgColor)
    axis.tick_params(colors=axisColor, which='both')

    for spine in axis.spines.values():
        spine.set_color(axisColor)

    plt.grid(True, linestyle="--", alpha=0.6)
    adjust_text(
        texts, 
        only_move={'text': 'y'},                  # Restrict movement to vertical (Y-axis) only
        arrowprops=dict(arrowstyle="-", color='gray', lw=0.5)  # Draws thin lines if label moves far
    )
    plt.tight_layout()

    # Save image
    output_image = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"zimage_{fileout}.png")
    plt.savefig(output_image, dpi=300, facecolor=plt.gcf().get_facecolor(), transparent=False)
    plt.close()
    print(f"Chart saved to {output_image}")




    return 0 #TODO return file output instead

