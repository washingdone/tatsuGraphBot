import asyncio
import disnake
from disnake.ext import tasks, commands
from tatsu.wrapper import ApiWrapper  # NOTE: may not be needed, unsure at this time
import json
import datetime
from dateutil.relativedelta import relativedelta
from graphBuilders import generateTimeGraph
import dbHelpers

tz = datetime.datetime.now().astimezone().tzinfo
midnight = datetime.time(hour=0, minute=0, second=0, tzinfo=tz)


class graphBotOptions():
    def __init__(self, configPath):
        config = json.load(open(configPath))

        self.token = config["discordToken"]
        self.guild = config["discordGuildID"]
        self.apiKey = config["tatsuKey"]
        self.updateInterval = config["updateInterval"]
        self.usersToChart = config["usersToChart"] # TODO: evaluate necessity
        self.scoresToKeep = config["scoresToKeep"]

class graphBotClient(commands.InteractionBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create a custom flag that starts as False
        self.guildTransformed = asyncio.Event()

    async def on_ready(self):
        try:
            options.guild = await self.fetch_guild(options.guild)
        except BaseException as err:
            print(f"Error transforming guild ID to an object, please double check your config file before reporting this error!\nn{err=}")
            exit(1)
        else:
            print(f"Logged on as {self.user}!")
            self.guildTransformed.set()


class databasePoller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll.start()

    def cog_unload(self):
        self.poll.cancel()

    @tasks.loop(minutes=1)
    async def poll(self):
        print('Polling API')
        await dbHelpers.getGuildRankings(self.bot.options)
        print('Database updated')

    @poll.before_loop
    async def await_ready(self):
        await self.bot.guildTransformed.wait()
        self.poll.change_interval(minutes=self.bot.options.updateInterval)

class databaseCleaner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll.start()

    def cog_unload(self):
        self.poll.cancel()

    @tasks.loop(time=midnight)
    async def clean(self):
        print('Beginning database cleanup')
        cleaned = await dbHelpers.cleanDB(self.bot.options)
        print(f'Database cleaned of {cleaned} users and their associated scores')

    @clean.before_loop
    async def await_ready(self):
        await self.bot.guildTransformed.wait()



try:
    intents = disnake.Intents.default()
    intents.members = True
    client = graphBotClient(intents=intents)
except BaseException as err:
    print(f"Error loading intents, did disnake install correctly?\n{err=}")
    exit(1)

try:
    options = graphBotOptions("./configFile")
except BaseException as err:
    print(f"Unable to generate configuration class, please double check your config file!\n\n{err=}")

try:
    client.options = options
except BaseException as err:
    print(err)

# TODO: build suggestion generators for the datetime.datetime entries
@client.slash_command(name="graph", description="draw a graph based on your user") # inform system we are registering a new command
async def graph(interaction, users_to_include=11, before_date=False, after_date=datetime.datetime.now()-relativedelta(years=1), use_nickname=True): # define new command
    """
    Remove all attachments from an archive post

    Parameters
    ----------
    users_to_include: The number of users to be displayed in the graph || Defaults to 11
    before_date: Only include scores before this date || Defaults to None
    after_date: Only include scores after this date || Defaults to 1 year ago today
    use_nickname: Toggle between using nicknames or usernames in the graph || Defaults to True
    """
    await interaction.response.defer()
    try:
        requesterID = interaction.author.id
        graph = await generateTimeGraph(client, requesterID, usersToChart=users_to_include, beforeDate=before_date, afterDate=after_date, useUsername=not use_nickname)
        await interaction.edit_original_response(file=disnake.File(graph, filename="graph.png"))
    except BaseException as err:
        print(f"An error has occured during the execution of graph(): \n{err.text=}\n{err.code=}\n{err.status=}\n{err.response=}\n{err.args=}\n{err=}") # print error to console
        await interaction.edit_original_response(content=f"Uh oh, An error has occured `{err.code=}`") # inform user of failure

@client.slash_command(name="graph_top", description="draw a graph based on your user") # inform system we are registering a new command
async def graphTop(interaction, users_to_include=10, before_date=False, after_date=datetime.datetime.now()-relativedelta(years=1), use_nickname=True): # define new command
    """
    Remove all attachments from an archive post

    Parameters
    ----------
    users_to_include: The number of users to be displayed in the graph || Defaults to 10
    before_date: Only include scores before this date || Defaults to None
    after_date: Only include scores after this date || Defaults to 1 year ago today
    use_nickname: Toggle between using nicknames or usernames in the graph || Defaults to True
    """
    await interaction.response.defer()
    try:
        graph = await generateTimeGraph(client, 1, usersToChart=users_to_include, beforeDate=before_date, afterDate=after_date, useUsername=not use_nickname)
        await interaction.edit_original_response(file=disnake.File(graph, filename="graph.png"))
    except Exception as err:
        print(f"An error has occured during the execution of graph(): \n{err.text=}\n{err.code=}\n{err.status=}\n{err.response=}\n{err.args=}\n{err=}") # print error to console
        await interaction.edit_original_response(content=f"Uh oh, An error has occured `{err.code=}`") # inform user of failure


# TODO: Create task items for regular api polling
client.add_cog(databasePoller(client))

client.run(options.token) # run client