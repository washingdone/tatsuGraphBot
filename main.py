import disnake
from disnake.ext import tasks, commands
from tatsu.wrapper import ApiWrapper  # NOTE: may not be needed, unsure at this time
import json
import sqlite3
from contextlib import closing
import datetime
from dateutil.relativedelta import relativedelta
from dbHelpers import getGuildRankings


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
async def graph(interaction, usersToInclude=11, beforeDate=False, afterDate=datetime.now()-relativedelta=1, useNickname=True): # define new command
    """
    Remove all attachments from an archive post

    Parameters
    ----------

    """
    try:
        pass
    except:
        print(f"An error has occured during the execution of graph(): \n{err.text=}\n{err.code=}\n{err.status=}\n{err.response=}\n{err.args=}\n{err=}") # print error to console
        await interaction.response.send_message(content=f"Uh oh, An error has occured `{err.code=}`") # inform user of failure

    try:
        message = await options.channel.fetch_message(message_id) # find requested Message object
        await message.edit(attachments=None) # remove attachments from Message
    except disnake.HTTPException as err:
        print(f"An error has occured during the execution of remove_attachments: \n{err.text=}\n{err.code=}\n{err.status=}\n{err.response=}\n{err.args=}\n{err=}") # print error to console
        await interaction.response.send_message(content=f"Uh oh! An error has occured - Check your message ID!", delete_after=5) # inform user of failure
    except:
        print(f"An error has occured during the execution of remove_attachments: \n{err.text=}\n{err.code=}\n{err.status=}\n{err.response=}\n{err.args=}\n{err=}") # print error to console
        await interaction.response.send_message(content=f"Uh oh, An error has occured `{err.code=}`") # inform user of failure
    else:
        await interaction.response.send_message(content="Success!", delete_after=5) # Inform user of completetion





# client.run(options.token) # run client