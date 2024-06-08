import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from utils import *

# Load environment variables
load_dotenv()
DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')
GUILD_ID = int(os.getenv('GUILD_ID'))  # Add your guild (server) ID to the .env file


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    try:
        # bot.tree.clear_commands(guild=discord.Object(GUILD_ID))
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')


@bot.tree.command(name="top", description="Get top stats for a user")
@app_commands.describe(username="The username to get stats for", match_type="Match type: public, midwars, or foc")
@app_commands.choices(
    match_type=[
        app_commands.Choice(name='Public', value=MatchType.PUBLIC.value),
        app_commands.Choice(name='Midwars', value=MatchType.MIDWARS.value),
        app_commands.Choice(name='FoC', value=MatchType.FOC.value)
    ]
)
async def top(interaction: discord.Interaction, username: str, match_type: str):
    try:
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title=f"Loading Top Stats for {username}", description="Please wait...",
                              color=discord.Color.orange())
        await interaction.followup.send(embed=embed)

        msg = await interaction.original_response()

        top_teammates = format_top_teammates(username, MatchType(match_type))
        embed = create_top_stats_embed(username, top_teammates)
        await msg.edit(embed=embed)
    except Exception as e:
        await interaction.followup.send("An error occurred while processing your request. Please try again later.")
        print(f"[ERROR] Exception in 'top' command: {str(e)}")


@bot.tree.command(name="stats", description="Get detailed stats for a user")
@app_commands.describe(username="The username to get detailed stats for", match_type="Match type: public, midwars, or foc")
@app_commands.choices(
    match_type=[
        app_commands.Choice(name='Public', value=MatchType.PUBLIC.value),
        app_commands.Choice(name='Midwars', value=MatchType.MIDWARS.value),
        app_commands.Choice(name='FoC', value=MatchType.FOC.value)
    ]
)
async def stats(interaction: discord.Interaction, username: str, match_type: str):
    try:
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title=f"Loading Detailed Stats for {username}", description="Please wait...",
                              color=discord.Color.orange())
        await interaction.followup.send(embed=embed)

        msg = await interaction.original_response()
        detailed_stats_raw = scrape_detailed_stats(username, MatchType(match_type))
        detailed_stats = parse_raw_string(detailed_stats_raw)
        embed = create_detailed_stats_embed(username, detailed_stats)
        await msg.edit(embed=embed)
    except Exception as e:
        await interaction.followup.send("An error occurred while processing your request. Please try again later.")
        print(f"[ERROR] Exception in 'stats' command: {str(e)}")


@bot.tree.command(name="account_overview", description="Get an overview of the account")
@app_commands.describe(username="The username to get the account overview for")
async def account_overview(interaction: discord.Interaction, username: str):
    try:
        await interaction.response.defer(ephemeral=True)
        data = fetch_kongor_data(username)
        if not data:
            await interaction.followup.send("Failed to retrieve data. Please try again.")
            return

        embed = discord.Embed(title=f"Account Overview for {username}", color=discord.Color.blue())
        embed.add_field(name="Nickname", value=data.get('nickname', 'N/A'))
        embed.add_field(name="Level", value=data.get('level', 'N/A'))
        embed.add_field(name="Standing", value=data.get('standing', 'N/A'))
        embed.add_field(name="Games Played", value=data.get('games_played', 'N/A'))
        embed.add_field(name="Wins", value=data.get('acc_wins', 'N/A'))
        embed.add_field(name="Losses", value=data.get('acc_losses', 'N/A'))
        embed.add_field(name="Favorite Hero", value=data.get('favHero1', 'N/A'))

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send("An error occurred while processing your request. Please try again later.")
        print(f"[ERROR] Exception in 'account_overview' command: {str(e)}")


@bot.tree.command(name="match_statistics", description="Get recent match statistics")
@app_commands.describe(username="The username to get recent match statistics for")
async def match_statistics(interaction: discord.Interaction, username: str):
    try:
        await interaction.response.defer(ephemeral=True)
        data = fetch_kongor_data(username)
        if not data:
            await interaction.followup.send("Failed to retrieve data. Please try again.")
            return

        match_ids = data.get('matchIds', 'N/A').split()
        match_dates = data.get('matchDates', 'N/A').split()

        embed = discord.Embed(title=f"Recent Match Statistics for {username}", color=discord.Color.green())
        for match_id, match_date in zip(match_ids, match_dates):
            embed.add_field(name=f"Match ID: {match_id}", value=f"Date: {match_date}", inline=False)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send("An error occurred while processing your request. Please try again later.")
        print(f"[ERROR] Exception in 'match_statistics' command: {str(e)}")


@bot.tree.command(name="hero_statistics", description="Get favorite hero statistics")
@app_commands.describe(username="The username to get favorite hero statistics for")
async def hero_statistics(interaction: discord.Interaction, username: str):
    try:
        await interaction.response.defer(ephemeral=True)
        data = fetch_kongor_data(username)
        if not data:
            await interaction.followup.send("Failed to retrieve data. Please try again.")
            return

        embed = discord.Embed(title=f"Favorite Heroes for {username}", color=discord.Color.purple())
        for i in range(1, 6):
            hero_name = data.get(f'favHero{i}', 'N/A')
            hero_time = data.get(f'favHero{i}Time', 'N/A')
            embed.add_field(name=f"Hero {i}", value=f"{hero_name} - {hero_time} hours")

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send("An error occurred while processing your request. Please try again later.")
        print(f"[ERROR] Exception in 'hero_statistics' command: {str(e)}")


@bot.tree.command(name="game_performance", description="Get game performance statistics")
@app_commands.describe(username="The username to get game performance statistics for")
async def game_performance(interaction: discord.Interaction, username: str):
    try:
        await interaction.response.defer(ephemeral=True)
        data = fetch_kongor_data(username)
        if not data:
            await interaction.followup.send("Failed to retrieve data. Please try again.")
            return

        embed = discord.Embed(title=f"Game Performance for {username}", color=discord.Color.orange())
        embed.add_field(name="K/D/A", value=data.get('k_d_a', 'N/A'))
        embed.add_field(name="Average Game Length", value=f"{data.get('avgGameLength', 'N/A')} seconds")
        embed.add_field(name="Average XP per Minute", value=data.get('avgXP_min', 'N/A'))
        embed.add_field(name="Average Denies", value=data.get('avgDenies', 'N/A'))
        embed.add_field(name="Average Creep Kills", value=data.get('avgCreepKills', 'N/A'))
        embed.add_field(name="Average Neutral Kills", value=data.get('avgNeutralKills', 'N/A'))
        embed.add_field(name="Average Actions per Minute", value=data.get('avgActions_min', 'N/A'))
        embed.add_field(name="Average Wards Used", value=data.get('avgWardsUsed', 'N/A'))

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send("An error occurred while processing your request. Please try again later.")
        print(f"[ERROR] Exception in 'game_performance' command: {str(e)}")


@bot.tree.command(name="compare", description="Compare stats between two users")
@app_commands.describe(username1="The first username to compare", username2="The second username to compare", match_type="Match type: public, midwars, or foc")
@app_commands.choices(
    match_type=[
        app_commands.Choice(name='Public', value=MatchType.PUBLIC.value),
        app_commands.Choice(name='Midwars', value=MatchType.MIDWARS.value),
        app_commands.Choice(name='FoC', value=MatchType.FOC.value)
    ]
)
async def compare(interaction: discord.Interaction, username1: str, username2: str, match_type: str):
    try:
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title=f"Comparing Stats for {username1} and {username2}", description="Please wait...",
                              color=discord.Color.orange())
        await interaction.followup.send(embed=embed)

        msg = await interaction.original_response()

        data1 = fetch_kongor_data(username1)
        data2 = fetch_kongor_data(username2)

        if not data1 or not data2:
            await interaction.followup.send("Failed to retrieve data for one or both users. Please try again.")
            return

        comparison = compare_stats(data1, data2, MatchType(match_type))

        embed = create_comparison_embed(username1, username2, comparison)
        await msg.edit(embed=embed)
    except Exception as e:
        await interaction.followup.send("An error occurred while processing your request. Please try again later.")
        print(f"[ERROR] Exception in 'compare' command: {str(e)}")


bot.run(DISCORD_API_KEY)
