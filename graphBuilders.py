from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
import sqlite3
from contextlib import closing
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patheffects as patheffects
from adjustText import adjust_text
from disnake import errors as disErrors


def timeGraphOptionValidation(usersToChart, beforeDate=None, afterDate=datetime.now()-relativedelta(years=1), useUsername=False):
    try:
        usersToChart = int(usersToChart)
    except (ValueError, TypeError):
        raise TypeError(f'Error: {usersToChart} is not of type {int}')
    
    try:
        if beforeDate is not None:
            beforeDate = datetime.strptime(beforeDate, "%Y-%m-%d")
        else:
            beforeDate = False
    except ValueError:
        raise TypeError(f'Error: {beforeDate} is not in format YYYY-MM-DD')

    try:
        if isinstance(afterDate, str):
            if afterDate == 'None':
                afterDate = False
            else:
                afterDate = datetime.strptime(afterDate, "%Y-%m-%d")
        if not isinstance(afterDate, datetime):
            raise ValueError()
    except ValueError:
        raise TypeError(f'Error: {afterDate} is not in format YYYY-MM-DD or None')

    return (usersToChart, beforeDate, afterDate, useUsername)


async def generateTimeGraph(client, requesterID, optionTuple):
    # TODO: enhancement: allow for manually specifiying left and right bounds
    # TODO: enhancement-xl: allow for pulling milestone data and displaying them on the graph

    usersToChart, beforeDate, afterDate, useUsername = optionTuple
    
    isTop = False
    if requesterID == 1:
        requesterRank = 1
        isTop = True
    else:
        with sqlite3.connect("graphBot.db") as conn:
            with closing(conn.cursor()) as cursor:

                cursor.execute("""
                SELECT ranking FROM users
                WHERE id IS ?
                """, (requesterID,))
                requesterRank = cursor.fetchone()[0]

    leftCount = usersToChart // 2
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
        with closing(conn.cursor()) as cursor:

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

    # Build graph 
    # TODO: convert to a seperate function once i've fixed needing an output file
    # NOTE: may not be needed
    axisColor = '#72767d'
    bgColor = (1.0, 1.0, 1.0, 0.15)
    plt.figure(figsize=(15, 9), facecolor=bgColor)
    texts = []

    for userID, data in scoreData.items():
        try:
            userMember = await client.options.guild.fetch_member(userID)
            color = userMember.color.to_rgb()
            color = "#{:02x}{:02x}{:02x}".format(*color)
            if useUsername:
                userPrintout = userMember.name
            else:
                userPrintout = userMember.nick or userMember.name
        except disErrors.NotFound:
            missingUser = await client.fetch_user(userID)
            userPrintout = missingUser.name
            color = userMember.color.to_rgb()
            color = "#{:02x}{:02x}{:02x}".format(*color) 

        plt.plot(data["times"], data["scores"], linewidth=3.0, color=color)
        
        # 2. Add inline text at the end of each series
        if data["times"] and data["scores"]:
            last_x = data["times"][-1]
            last_y = data["scores"][-1]

            txt = plt.text(
                last_x,
                last_y,
                f" {userPrintout}", 
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

    if isTop:
        plt.title(f"Score Progression - Top {usersToChart} Users - {timeFrameString}", color=axisColor)
    else:
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
    outputImage = BytesIO()
    plt.savefig(outputImage, dpi=300, facecolor=plt.gcf().get_facecolor(), transparent=False, format='png')
    outputImage.seek(0)
    plt.close()

    return outputImage