import re
from enum import Enum

import discord
import phpserialize
import requests
from bs4 import BeautifulSoup
from requests.structures import CaseInsensitiveDict


class MatchType(Enum):
    PUBLIC = 'public'
    MIDWARS = 'midwars'
    FOC = 'foc'


MATCH_TYPES = {
    MatchType.MIDWARS: '#casual-matches',
    MatchType.PUBLIC: '#public-matches',
    MatchType.FOC: '#normal-matches'
}


def fetch_kongor_data(username):
    try:
        url = "https://api.kongor.online/client_requester.php"
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = f"f=show_stats&nickname={username}&cookie=123&table=midwars"
        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            response_content = response.content.decode('utf-8').strip('"')
            cleaned_response_content = response_content.replace('\\"', '"').replace('\\/', '/')
            try:
                parsed_data = phpserialize.loads(cleaned_response_content.encode('utf-8'))
                return convert_php_data(parsed_data)
            except Exception as e:
                print(f"[ERROR] Failed to parse data for {username}: {e}")
                print(f"[DEBUG] Cleaned response content: {cleaned_response_content}")
                return None
        else:
            print(f"[ERROR] Failed to retrieve data for {username}, status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Exception in fetch_kongor_data for {username}: {e}")
        return None


# Function to recursively convert parsed PHP data to a Python dictionary
def convert_php_data(data):
    if isinstance(data, phpserialize.phpobject):
        return {convert_php_data(k): convert_php_data(v) for k, v in data.__dict__.items()}
    elif isinstance(data, dict):
        return {convert_php_data(k): convert_php_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_php_data(v) for v in data]
    elif isinstance(data, bytes):
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return data
    else:
        return data


def scrape_kongor_stats(username, match_type):
    url = f'https://stats.kongor.online/{username}/all'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    match_id = MATCH_TYPES.get(match_type)
    stat_div = soup.select_one(f'{match_id} > div:nth-of-type(6)')
    return stat_div.get_text(strip=True) if stat_div else "No data found."


# Scrape function for detailed stats
def scrape_detailed_stats(username, match_type):
    url = f'https://stats.kongor.online/{username}/all'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    match_id = MATCH_TYPES.get(match_type)
    stat_table = soup.select_one(f'{match_id} > div:nth-of-type(5) > table')
    if not stat_table:
        return "No data found."
    return parse_table(stat_table)


# Parse table data into a formatted string
def parse_table(stat_table):
    rows = stat_table.find_all('tr')
    table_text = "\n".join([" | ".join([ele.text.strip() for ele in row.find_all('td')]) for row in rows])
    return table_text.strip()


# Parse raw string into a dictionary
def parse_raw_string(raw_string):
    parts = re.split(r'\s*\|\s*', raw_string.replace('\n', ' '))
    data_dict = {}
    for part in parts:
        key_value = part.split(':', 1)
        if len(key_value) == 2:
            key, value = key_value[0].strip(), key_value[1].strip()
            value = clean_value(value)
            data_dict[key] = value
    return data_dict


# Clean value for the parsed dictionary
def clean_value(value):
    if '(' in value:
        value = value.split('(')[0].strip()
    if ' ' in value and not value.replace(' ', '').isdigit():
        value = value.split(' ')[0].strip()
    try:
        if '.' in value:
            value = float(value)
        else:
            value = int(value)
    except ValueError:
        pass
    return value


# Create an embed for top stats
def create_top_stats_embed(username, top_teammates):
    embed = discord.Embed(title=f"Top Stats for {username}", color=discord.Color.green())
    stat_string = "\n".join(top_teammates)
    embed.add_field(name="Most Played with Friends", value=stat_string)
    return embed


# Create an embed for detailed stats
def create_detailed_stats_embed(username, detailed_stats):
    embed = discord.Embed(title=f"Detailed Stats for {username}", color=discord.Color.green())
    for key, value in detailed_stats.items():
        embed.add_field(name=key, value=value, inline=True)
    return embed


def format_top_teammates(username):
    friends = scrape_kongor_stats(username)
    friends = friends[13:]  # remove TopTeammates text
    top_teammates = friends.split(',')

    formatted_teammates = []
    for i, teammate in enumerate(top_teammates, start=1):
        match = re.match(r"(.+?)\((\d+\.?\d*%)\)", teammate.strip())
        if match:
            name = match.group(1)
            percentage = match.group(2)
            formatted_teammates.append(f"{i}. **{name}** ({percentage})")

    return formatted_teammates


# Function to compare stats between two users
def compare_stats(data1, data2, match_type):
    # Specify the keys you want to compare
    keys_to_compare = [
        'acc_herokills', 'acc_herodmg', 'acc_heroexp', 'acc_herokillsgold',
        'acc_heroassists', 'acc_deaths', 'acc_teamcreepkills', 'acc_teamcreepdmg',
        'acc_teamcreepexp', 'acc_teamcreepgold', 'acc_neutralcreepkills', 'acc_neutralcreepdmg',
        'acc_neutralcreepexp', 'acc_neutralcreepgold', 'acc_denies', 'acc_exp_denied'
    ]

    comparison = {}
    for key in keys_to_compare:
        stat1 = data1.get(key, 'N/A')
        stat2 = data2.get(key, 'N/A')
        if stat1 != 'N/A' and stat2 != 'N/A':
            comparison[key] = {'username1': stat1, 'username2': stat2}

    return comparison


# Create an embed for comparison results
def create_comparison_embed(username1, username2, comparison):
    embed = discord.Embed(title=f"Comparison between {username1} and {username2}", color=discord.Color.blue())
    for key, values in comparison.items():
        embed.add_field(name=key, value=f"{username1}: {values['username1']}\n{username2}: {values['username2']}", inline=False)
    return embed
