import disnake
from disnake.ext import tasks, commands
from tatsu.wrapper import ApiWrapper  # NOTE: may not be needed, unsure at this time
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from dateutil.relativedelta import relativedelta
from graphBuilders import generateTimeGraph


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
            pass
            # options.guild = await client.fetch_guild(options.guild)
        except BaseException as err:
            print(f"Error transforming guild ID to an object, please double check your config file before reporting this error!\nn{err=}")
            exit(1)
        else:
            print(f"Logged on as {self.user}!")

    try:
        options = graphBotOptions("./configFile")
    except BaseException as err:
        print(f"Error generating configuration, double check your config file!\n{err=}")
        exit(1)


try:
    client = graphBotClient()
except BaseException as err:
    print(f"Client could not be initialized!\n\n{err=}")
    exit(1)

try:
    options = graphBotOptions("./configFile")
except BaseException as err:
    print(f"Unable to generate configuration class, please double check your config file!\n\n{err=}")


@client.slash_command(name="graph", description="draw a graph based on your user") # inform system we are registering a new command
async def graph(interaction, users_to_include=11, before_date=False, after_date=datetime.now()-relativedelta(years=1), use_nickname=True): # define new command
    """
    Remove all attachments from an archive post

    Parameters
    ----------
    users_to_include: The number of users to be displayed in the graph || Defaults to 11
    before_date: Only include scores before this date || Defaults to None
    after_date: Only include scores after this date || Defaults to 1 year from today
    use_nickname: Toggle between using nicknames or usernames in the graph || Defaults to True
    """
    try:
        requesterID = interaction.author.id
        graph = generateTimeGraph(client, requesterID, usersToChart=users_to_include, beforeDate=before_date, afterDate=after_date, useUsername=not use_nickname)
        await interaction.response.send_message(file=disnake.File(graph, filename="graph.png"))
        pass
    except:
        print(f"An error has occured during the execution of graph(): \n{err.text=}\n{err.code=}\n{err.status=}\n{err.response=}\n{err.args=}\n{err=}") # print error to console
        await interaction.response.send_message(content=f"Uh oh, An error has occured `{err.code=}`") # inform user of failure

client.run(options.token) # run client