import discord
from discord.ext import commands
import requests
import json
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from dotenv import load_dotenv
import os
from collections import defaultdict

load_dotenv()

BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
CRCON_TOKEN = os.getenv('CRCON_TOKEN')

SERVERS = [
    {'name': 'Server 1', 'url': os.getenv('CRCON_URL_SERVER1') + '/api/', 'headers': {'Authorization': f'Bearer {CRCON_TOKEN}'}},
    # Server 2 und 3 kommentiert – nur Server 1
    # {'name': 'Server 2', 'url': os.getenv('CRCON_URL_SERVER2') + '/api/', 'headers': {'Authorization': f'Bearer {CRCON_TOKEN}'}},
    # {'name': 'Server 3', 'url': os.getenv('CRCON_URL_SERVER3') + '/api/', 'headers': {'Authorization': f'Bearer {CRCON_TOKEN}'}},
]

MESSAGE_FILE = 'multi_ranking_message_ids.json'
STATS_FILE = 'monthly_stats.json'  # Kumulative Stats diesen Monat
LAST_LOG_FILE = 'last_log_ids.json'  # Last id per server

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

def load_message_ids():
    try:
        with open(MESSAGE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_message_ids(ids):
    with open(MESSAGE_FILE, 'w') as f:
        json.dump(ids, f)

message_ids = load_message_ids()

def load_stats():
    try:
        with open(STATS_FILE, 'r') as f:
            data = json.load(f)
            stats = defaultdict(lambda: {'kills': 0, 'deaths': 0, 'teamkills': 0, 'teamkill_deaths': 0, 'longest_streak': 0, 'current_streak': 0, 'playtime_min': 0, 'name': ''})
            for id, s in data.items():
                stats[id] = s
            return stats
    except FileNotFoundError:
        return defaultdict(lambda: {'kills': 0, 'deaths': 0, 'teamkills': 0, 'teamkill_deaths': 0, 'longest_streak': 0, 'current_streak': 0, 'playtime_min': 0, 'name': ''})

def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(dict(stats), f)

current_stats = load_stats()

def load_last_log_ids():
    try:
        with open(LAST_LOG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {server['url']: 0 for server in SERVERS}

def save_last_log_ids(ids):
    with open(LAST_LOG_FILE, 'w') as f:
        json.dump(ids, f)

last_log_ids = load_last_log_ids()

connect_times = defaultdict(lambda: None)  # player_id: connect_timestamp

def fetch_historical_logs(server):
    try:
        full_url = server['url'] + 'get_historical_logs'
        body = {"limit": 1000}
        resp = requests.post(full_url, headers=server['headers'], json=body, timeout=30, verify=False)
        resp.raise_for_status()
        data = resp.json()
        logs = data.get('result', [])
        print(f"[LOGS] {server['name']}: {len(logs)} Logs erhalten")
        return logs
    except Exception as e:
        print(f"[ERROR] {server['name']}: {e}")
        return []

def update_stats():
    global current_stats

    for server in SERVERS:
        logs = fetch_historical_logs(server)
        new_logs = [log for log in logs if log.get('id', 0) > last_log_ids.get(server['url'], 0)]

        if new_logs:
            last_log_ids[server['url']] = max(log.get('id', 0) for log in logs)
            save_last_log_ids(last_log_ids)

            for log in new_logs:
                log_type = log.get('type', '').upper()
                killer_id = log.get('player1_id')
                killer_name = log.get('player1_name') or log.get('player_name')
                victim_id = log.get('player2_id')
                victim_name = log.get('player2_name') or log.get('victim_name')
                if not killer_id:
                    continue

                ts_str = log.get('time') or log.get('timestamp')  # Adjust key if needed
                ts = datetime.datetime.now() if not ts_str else datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')  # Adjust format if needed

                s = current_stats[killer_id]
                s['name'] = killer_name or s['name']
                if 'KILL' in log_type and 'TEAM KILL' not in log_type:
                    s['kills'] += 1
                    s['current_streak'] += 1
                    s['longest_streak'] = max(s['longest_streak'], s['current_streak'])
                    if victim_id:
                        v = current_stats[victim_id]
                        v['name'] = victim_name or v['name']
                        v['deaths'] += 1
                        v['current_streak'] = 0
                elif 'TEAM KILL' in log_type:
                    s['teamkills'] += 1
                    if victim_id:
                        v = current_stats[victim_id]
                        v['name'] = victim_name or v['name']
                        v['teamkill_deaths'] += 1
                    s['current_streak'] = 0
                elif 'DEATH' in log_type:
                    s['deaths'] += 1
                    s['current_streak'] = 0
                elif 'CONNECT' in log_type:
                    connect_times[killer_id] = ts
                elif 'DISCONNECT' in log_type:
                    if connect_times[killer_id]:
                        duration = (ts - connect_times[killer_id]).total_seconds() / 60
                        s['playtime_min'] += max(0, duration)
                        connect_times[killer_id] = None

    # K/D berechnen
    for s in current_stats.values():
        s['kd'] = s['kills'] / max(1, s['deaths'])

    save_stats(current_stats)
    print(f"[STATS] Updated – Gesamt Spieler: {len(current_stats)}")
    return dict(current_stats)

def is_new_month():
    today = datetime.date.today()
    return today.day == 1

async def freeze_and_reset_stats(channel):
    global current_stats
    # Post finales Ranking
    month = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%B %Y')
    embed = discord.Embed(title=f"Finales Ranking {month}", color=0x00ff00)
    embed.description = "Stats des abgelaufenen Monats (gefreezt)"

    for ranking in RANKINGS:
        sorted_players = sorted(current_stats.items(), key=lambda x: x[1].get(ranking['key'], 0), reverse=ranking['reverse'])[:30]
        text = "\n".join(f"{i+1}. **{s['name'][:20]}** – {ranking['format'].format(s[ranking['key']])}" for i, (id, s) in enumerate(sorted_players))
        embed.add_field(name=ranking['title'], value=text or "Keine Daten", inline=False)

    await channel.send(embed=embed)

    # Reset Stats
    current_stats = defaultdict(lambda: {'kills': 0, 'deaths': 0, 'teamkills': 0, 'teamkill_deaths': 0, 'longest_streak': 0, 'current_streak': 0, 'playtime_min': 0, 'name': ''})
    save_stats(current_stats)

async def update_all_rankings():
    global message_ids
    all_stats = update_stats()
    now = datetime.datetime.now()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel nicht gefunden!")
        return

    if is_new_month():
        await freeze_and_reset_stats(channel)

    new_ids = []
    for idx, ranking in enumerate(RANKINGS):
        embed = create_ranking_embed(ranking, all_stats, now)
        try:
            if len(message_ids) > idx and message_ids[idx]:
                msg = await channel.fetch_message(message_ids[idx])
                await msg.edit(embed=embed)
                new_ids.append(message_ids[idx])
            else:
                msg = await channel.send(embed=embed)
                new_ids.append(msg.id)
        except discord.NotFound:
            msg = await channel.send(embed=embed)
            new_ids.append(msg.id)
        except Exception as e:
            print(f"Discord-Fehler {ranking['title']}: {e}")
            new_ids.append(None)
        await asyncio.sleep(1)  # Länger Delay to avoid rate limits
    message_ids = new_ids
    save_message_ids(message_ids)

RANKINGS = [
    {'title': '🔫 Meiste Kills', 'key': 'kills', 'format': '{:,}', 'reverse': True},
    {'title': '💀 Beste K/D (≥1 Kill)', 'key': 'kd', 'format': '{:.2f}', 'reverse': True},
    {'title': '🔥 Längste Killstreak', 'key': 'longest_streak', 'format': '{}', 'reverse': True},
    {'title': '🤦 Meiste Teamkills', 'key': 'teamkills', 'format': '{}', 'reverse': True},
    {'title': '😭 Am meisten geteamkillt', 'key': 'teamkill_deaths', 'format': '{}', 'reverse': True},
    {'title': '☠️ Meiste Tode', 'key': 'deaths', 'format': '{:,}', 'reverse': True},
    {'title': '⏰ Meiste Spielzeit (Stunden)', 'key': 'playtime_min', 'format': '{} Std', 'reverse': True, 'value_func': lambda v: v // 60},
]

def create_ranking_embed(ranking_def, stats, update_time):
    embed = discord.Embed(title=ranking_def['title'], description=f"Aktualisiert: {update_time.strftime('%H:%M:%S')} | 3 Server", color=0xff0000)
    filtered = [(id, s) for id, s in stats.items() if ranking_def.get('min_filter', lambda s: True)(s)]
    sorted_players = sorted(filtered, key=lambda x: ranking_def.get('value_func', lambda v: v)(x[1].get(ranking_def['key'], 0)), reverse=ranking_def.get('reverse', True))[:30]

    if not sorted_players:
        embed.add_field(name="Keine Daten", value="Noch keine Stats vorhanden.", inline=False)
        return embed

    text = "\n".join(f"{i+1:2}. **{s['name'][:20]}** – {ranking_def['format'].format(ranking_def.get('value_func', lambda v: v)(s[ranking_def['key']]))}" for i, (id, s) in enumerate(sorted_players))
    embed.add_field(name="Top 30", value=text, inline=False)
    embed.set_footer(text="Monatlich reset | get_historical_logs")
    return embed

@bot.event
async def on_ready():
    print(f'Bot online als {bot.user}')
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_all_rankings, 'interval', seconds=60, next_run_time=datetime.datetime.now())
    scheduler.start()
    await update_all_rankings()

bot.run(BOT_TOKEN)