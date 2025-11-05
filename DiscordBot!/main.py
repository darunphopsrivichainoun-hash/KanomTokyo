import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import random
import json
import datetime
from discord import utils

# --- CONFIGURATION (UPDATE THESE LINES) ---
# 1. Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')  # <-- MUST BE SET IN YOUR .env FILE

# 2. REPLACE THESE URLs with your actual direct GIF/Image links
CUSTOM_WELCOME_IMAGE = "https://cdn.discordapp.com/attachments/1066723795525709824/1435267993142820955/Welcome.gif?ex=690b58fb&is=690a077b&hm=35418717b0853f5da85297a568547fb6c14e3c23aa5932714e0032b4fcf19650&"
CUSTOM_LEAVING_IMAGE = "https://cdn.discordapp.com/attachments/1066723795525709824/1435268136516456499/Leaving.gif?ex=690b591d&is=690a079d&hm=a8dda944fb39f3bd9417d2e33184f6452403a700d7909d00e322239e51ffdd91&"

# 3. CHANNEL CONFIGURATION (CRUCIAL!)
# Enable Developer Mode in Discord, right-click the channel, and select "Copy ID" for each of these:
ANNOUNCEMENT_CHANNEL_ID = 1435279295776817292  # <-- For Birthday announcements (@everyone)
JOIN_CHANNEL_ID = 1435245791265427590  # <-- REPLACE with your dedicated WELCOME channel ID!
LEAVE_CHANNEL_ID = 1435489866598056017  # <-- REPLACE with your dedicated EXIT channel ID!
# --------------------------------------------

# --- Intents and Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for member/join/leave events and accurate stats

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- Game & Aesthetic Constants ---
CHAMBERS = 6
GAME_ACTIVE = False
BULLET_CHAMBER = 0
CURRENT_CHAMBER_INDEX = 0
GAME_COLOR = discord.Color.dark_red()

# --- KanomTokyo's Dramatic Messages (Thai) ---
JOIN_MESSAGES = [
    "สวัสดีครับคุณ {member.mention}, ไม่ได้เจอกันตั้งนาน",
    "โยโยโยว **{member.mention}** ถ้านายกำลังอ่านประโยคนี้อยู่ยินดีตอนรับเข้าดิสคอร์ด.",
    "**สวัสดีครับพ่อแม่พี่น้องทุกท่าน**! วันนี้เรามายินดีต้อนรับ **{member.mention}**!.",
    "อาจเป็นเพราะว่าเธอบางเอิญได้เจอฉัน อาจเป็นเพราะว่าเราบังเอิญอยู่ด้วยกัน",
]

LEAVE_MESSAGES = [
    "โปรดออกไปจากฝัน เพราะฉันกำลังจะลืมเธอได้แล้ว",
    "ใครกันที่อนุญาติให้แกออกไปจากดิสข้า.",
    "เธอเข้ามาทำให้ใครได้รู้สึกดีแล้วเธอก็ไป",
    "**สตาคอมแมนตอบด้วย** เราเสียสมาชิกไปคนนึงแล้ว.",
    "ฉันว่าเราหยุด ก่อนดีไหม?.",
]

# --- Game Picker Constants ---
GAME_LIST = [
    "League of Legends (LOL)",
    "Apex Legends",
    "Valorant",
    "Minecraft",
    "Phasmophobia",
    "Genshin Impact",
    "Among Us",
    "The Russian Roulette (Use !startgame instead!)",
]

# --- Leaderboard Setup ---
SCORE_FILE = 'scores.json'


def load_scores():
    try:
        with open(SCORE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(SCORE_FILE, 'w') as f:
            json.dump({}, f)
        return {}


def save_scores(scores):
    with open(SCORE_FILE, 'w') as f:
        json.dump(scores, f, indent=4)


PLAYER_WINS = load_scores()

# --- Birthday Setup ---
BIRTHDAY_FILE = 'birthdays.json'


def load_birthdays():
    try:
        with open(BIRTHDAY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(BIRTHDAY_FILE, 'w') as f:
            json.dump({}, f)
        return {}


def save_birthdays(birthdays):
    with open(BIRTHDAY_FILE, 'w') as f:
        json.dump(birthdays, f, indent=4)


PLAYER_BDAYS = load_birthdays()


# --- Helper Functions (No more flexible get_welcome_channel needed) ---

def create_ambatron_embed(member, message_type="join"):
    title = ""
    description = ""
    thumbnail_url = None
    footer_text = ""
    image_url = None

    if message_type == "join":
        title = "WELCUM"
        color = discord.Color.green()
        description = random.choice(JOIN_MESSAGES).format(member=member)
        thumbnail_url = member.avatar.url if member.avatar else member.default_avatar.url
        footer_text = f"ขอยินดีต้อนรับสู่ {member.guild.name}, ขอให้อยู่กันนานๆ!"
        image_url = CUSTOM_WELCOME_IMAGE

    else:  # leave
        title = "AMLEAVING"
        color = discord.Color.red()
        description = random.choice(LEAVE_MESSAGES).format(member=member)
        thumbnail_url = member.guild.icon.url if member.guild.icon else None
        footer_text = f"ขอให้เจอกันในภายภาคหน้า."
        image_url = CUSTOM_LEAVING_IMAGE

    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    embed.set_footer(text=footer_text, icon_url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    embed.timestamp = discord.utils.utcnow()

    if image_url:
        embed.set_image(url=image_url)

    return embed


# --- ONE-TIME BIRTHDAY CHECKER ---
async def announce_today_birthday():
    """Checks for today's birthdays and announces them once on startup."""

    now = datetime.datetime.now()
    today_dm = f"{now.day:02d}/{now.month:02d}"

    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if not channel:
        print(f"Error: Could not find channel with ID {ANNOUNCEMENT_CHANNEL_ID} for birthday announcement.")
        return

    birthday_users = []
    for user_id_str, bday_str in PLAYER_BDAYS.items():
        if bday_str == today_dm:
            user = bot.get_user(int(user_id_str))
            if user:
                birthday_users.append(user)

    if birthday_users:
        mentions = ", ".join([user.mention for user in birthday_users])

        embed = discord.Embed(
            title="🎉 วันเกิด! KanomTokyo ขอร่วมฉลอง! 🎉",
            description=f"สมาชิกผู้โชคดีของเรา: **{mentions}** วันนี้คือวันเกิดของคุณ!\n"
                        f"ขอให้โชคชะตาอยู่ข้างคุณเสมอ และมีแต่ความสุขตลอดปีนี้!",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"วันนี้วันที่ {today_dm} ขอให้มีความสุขในวันเกิดนะ!")

        # --- Uses @everyone for max visibility ---
        await channel.send(f"**@everyone Happy Birthday!** สุขสันต์วันเกิดสำหรับ: {mentions}", embed=embed)
        print(f"Announced birthday for: {mentions} with @everyone ping.")


# --- Events ---

@bot.event
async def on_ready():
    """Confirms the bot is logged in, ready, and starts the one-time birthday check."""
    print(f'KanomTokyo ({bot.user.name}) has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name=f"!help"))

    # Run the simple birthday check once upon startup
    await announce_today_birthday()


@bot.event
async def on_member_join(member):
    """KanomTokyo's grand welcome using a special Embed, directed to JOIN_CHANNEL_ID."""
    # Find the specific channel ID for joins
    channel = member.guild.get_channel(JOIN_CHANNEL_ID)
    if channel and not member.bot:
        welcome_embed = create_ambatron_embed(member, message_type="join")
        await channel.send(embed=welcome_embed)


@bot.event
async def on_member_remove(member):
    """KanomTokyo's dramatic farewell using a special Embed, directed to LEAVE_CHANNEL_ID."""
    # Find the specific channel ID for leaves
    channel = member.guild.get_channel(LEAVE_CHANNEL_ID)
    if channel and not member.bot:
        farewell_embed = create_ambatron_embed(member, message_type="leave")
        await channel.send(embed=farewell_embed)


# --- Commands: General ---

@bot.command(name='help', help='แสดงรายการคำสั่งและกติกาเกมทั้งหมด.')
async def help_command(ctx):
    """Shows all available commands in a clear embed."""
    embed = discord.Embed(
        title="🃏 คู่มือคำสั่งและกติกาเกม (กง-เต็ก)",
        description="**กง-เต็ก:** พร้อมจะทดสอบโชคชะตาของคุณแล้ว! นี่คือสิ่งที่คุณต้องรู้:",
        color=GAME_COLOR
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)

    # Game Commands Section
    embed.add_field(
        name="🔫 คำสั่งเกม (Russian Roulette)",
        value="**กติกา:** เกมจะนับช่องกระสุนเรียงตามลำดับ (1 ถึง 6) และจะจบเซสชันเมื่อยิงโดนกระสุนหรือยิงครบ 6 นัด\n",
        inline=False
    )
    embed.add_field(
        name="`!startgame`",
        value="เริ่มเซสชันเกมใหม่!",
        inline=True
    )
    embed.add_field(
        name="`!fire`",
        value="เหนี่ยวไกช่องถัดไป!",
        inline=True
    )
    embed.add_field(
        name="`!spin`",
        value="หมุนโม่ปืน **ระหว่างเซสชัน** เพื่อรีเซ็ตโอกาสและเปลี่ยนตำแหน่งกระสุน",
        inline=True
    )

    # Utility Commands Section
    embed.add_field(
        name="📊 คำสั่งข้อมูลและบันทึก (Utilities)",
        value="\u200b",
        inline=False
    )
    embed.add_field(
        name="`!serverstatus`",
        value="แสดงข้อมูลโดยละเอียดเกี่ยวกับเซิร์ฟเวอร์",
        inline=True
    )
    embed.add_field(
        name="`!status`",
        value="แสดงสถานะเกมปัจจุบัน โอกาสรอด และหมายเลขช่องกระสุนที่กำลังเล็ง",
        inline=True
    )
    embed.add_field(
        name="`!leaderboard`",
        value="ดูตารางอันดับผู้รอดชีวิตสูงสุดจากการเหนี่ยวไก",
        inline=True
    )
    embed.add_field(
        name="`!setbday DD/MM`",
        value="บันทึกวันเกิดของคุณเพื่อฉลอง. (เช่น `!setbday 01/01`)",
        inline=True
    )
    embed.add_field(
        name="`!bday`",
        value="แสดงผู้ที่มีวันเกิดคนถัดไปในเซิร์ฟเวอร์.",
        inline=True
    )
    embed.add_field(
        name="`!gamepick`",
        value="ให้ **KanomTokyo** เลือกเกมแบบสุ่มให้คุณเล่น (Aliases: `!whattoplay`, `!randomgame`)",
        inline=True
    )
    embed.add_field(
        name="`!help`",
        value="คุณกำลังใช้คำสั่งนี้อยู่!",
        inline=True
    )

    embed.set_footer(text="โชคชะตาอยู่แค่ปลายนิ้วคุณ กง-เต็กเฝ้าดูอยู่",
                     icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    embed.timestamp = discord.utils.utcnow()

    await ctx.send(embed=embed)


# --- Commands: Server Status ---

@bot.command(name='serverstatus', aliases=['serverinfo', 'guildinfo'], help='แสดงข้อมูลโดยละเอียดเกี่ยวกับเซิร์ฟเวอร์.')
async def server_status(ctx):
    """Displays detailed information about the current Discord server (guild)."""

    guild = ctx.guild
    now = datetime.datetime.now(datetime.timezone.utc)

    # Calculate Server Age
    age = now - guild.created_at
    days_old = age.days

    # Get Member Counts
    member_count = guild.member_count
    # Requires members intent and cache to be accurate
    online_members = sum(1 for member in guild.members if member.status != discord.Status.offline and not member.bot)
    bot_count = sum(1 for member in guild.members if member.bot)

    # Get Text/Voice Channel Counts
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)

    embed = discord.Embed(
        title=f"ข้อมูลเซิร์ฟเวอร์: {guild.name}",
        color=discord.Color.blue()
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    # General Info
    embed.add_field(name="เจ้าของเซิร์ฟเวอร์", value=guild.owner.mention, inline=True)
    embed.add_field(name="ID เซิร์ฟเวอร์", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="ภูมิภาคหลัก", value=str(guild.preferred_locale).upper(), inline=True)

    # Creation Info
    embed.add_field(
        name="สร้างเมื่อ",
        value=f"{discord.utils.format_dt(guild.created_at, style='f')}\n($\approx$ {days_old} วันที่ผ่านมา)",
        inline=False
    )

    # Member Info
    embed.add_field(
        name="จำนวนสมาชิกทั้งหมด",
        value=f"**{member_count}** สมาชิก\n({online_members} ออนไลน์, {bot_count} บอท)",
        inline=True
    )

    # Channel Info
    embed.add_field(
        name="จำนวนช่อง",
        value=f"Text: {text_channels}\nVoice: {voice_channels}",
        inline=True
    )

    # Features
    features = ", ".join(f"`{feat.replace('_', ' ').title()}`" for feat in guild.features[:3])
    if features:
        embed.add_field(
            name="ฟีเจอร์เด่น",
            value=f"{features}...",
            inline=False
        )

    embed.set_footer(text=f"ร้องขอโดย {ctx.author.name}",
                     icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    embed.timestamp = discord.utils.utcnow()

    await ctx.send(embed=embed)


# --- Commands: Birthday Tracker ---

@bot.command(name='setbday', help='ให้บอทบันทึกวันเกิดของคุณเพื่อฉลอง (รูปแบบ: DD/MM).')
async def set_birthday(ctx, bday_str: str):
    """Allows a user to set their birthday (DD/MM format)."""

    global PLAYER_BDAYS
    user_id = str(ctx.author.id)

    try:
        day, month = map(int, bday_str.split('/'))
        # Simple validation to ensure the date is valid (using year 2000 as a placeholder)
        datetime.date(year=2000, month=month, day=day)

        PLAYER_BDAYS[user_id] = f"{day:02d}/{month:02d}"
        save_birthdays(PLAYER_BDAYS)

        await ctx.send(
            f"🎉 **สำเร็จ!** **กง-เต็ก** บันทึกวันเกิดของคุณ ({day:02d}/{month:02d}) ไว้แล้ว! "
            f"เตรียมตัวรับการฉลองที่น่าประหลาดใจได้เลย."
        )

    except ValueError:
        await ctx.send(
            f"❌ **กง-เต็ก:** วันที่ไม่ถูกต้อง. โปรดใช้รูปแบบ **DD/MM** เท่านั้น (เช่น `25/12`)."
        )
    except Exception:
        await ctx.send(
            "❌ **กง-เต็ก:** เกิดข้อผิดพลาดในการบันทึก. ลองตรวจสอบรูปแบบ **DD/MM** อีกครั้ง."
        )


@bot.command(name='bday', help='แสดงวันเกิดถัดไปที่จะมาถึงในเซิร์ฟเวอร์.')
async def next_birthday(ctx):
    """Calculates and displays the next upcoming birthday on the server."""

    global PLAYER_BDAYS

    if not PLAYER_BDAYS:
        await ctx.send("🎂 **กง-เต็ก:** ยังไม่มีใครบันทึกวันเกิดเลย! ใช้ `!setbday DD/MM` เพื่อเริ่มฉลอง.")
        return

    now = datetime.datetime.now()

    next_bday = None
    min_days_to_bday = 366

    for user_id_str, bday_str in PLAYER_BDAYS.items():
        try:
            day, month = map(int, bday_str.split('/'))

            # Determine the correct year (current year or next year)
            if (month, day) < (now.month, now.day):
                year = now.year + 1
            else:
                year = now.year

            bday_date = datetime.datetime(year=year, month=month, day=day)

            time_until = bday_date - now
            days_until = time_until.days

            if days_until < min_days_to_bday:
                min_days_to_bday = days_until
                next_bday = (user_id_str, bday_date)

        except ValueError:
            continue

    if next_bday:
        user_id_str, bday_date = next_bday

        user_id = int(user_id_str)
        user = bot.get_user(user_id)
        user_display = user.mention if user else f"ผู้เล่นที่ไม่รู้จัก (ID: {user_id_str})"

        if min_days_to_bday == 0:
            days_message = "**ในวันนี้!** 🎉"
        elif min_days_to_bday == 1:
            days_message = "**ในวันพรุ่งนี้!** 🎈"
        else:
            # We add 1 back because time_until.days calculates difference, not count
            days_message = f"ในอีก **{min_days_to_bday + 1}** วัน"

        embed = discord.Embed(
            title="🎂 วันเกิดถัดไปในเซิร์ฟเวอร์",
            description=f"**กง-เต็ก** ได้ค้นพบผู้โชคดีคนถัดไปแล้ว!",
            color=GAME_COLOR
        )
        embed.add_field(
            name=f"🎈 {user_display}",
            value=f"วันเกิดของพวกเขาคือ {bday_date.strftime('%d %B')} ({days_message})",
            inline=False
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(
            "🎂 **กง-เต็ก:** มีข้อมูลวันเกิดที่ไม่ถูกต้องอยู่ หรือยังไม่มีใครบันทึกเลย! โปรดตรวจสอบให้แน่ใจว่าทุกคนใช้รูปแบบ DD/MM.")


# --- Commands: Random Game Picker ---

@bot.command(name='gamepick', aliases=['whattoplay', 'randomgame'], help='KanomTokyo เลือกเกมแบบสุ่มให้คุณเล่น.')
async def game_picker(ctx):
    """Randomly selects a game from the predefined list."""

    global GAME_LIST

    if not GAME_LIST:
        await ctx.send("🚫 **กง-เต็ก:** ไม่มีเกมในรายการ! แอดมินต้องเพิ่มเกมก่อน.")
        return

    selected_game = random.choice(GAME_LIST)

    embed = discord.Embed(
        title="🤔 คำแนะนำเกมจาก กง-เต็ก",
        description="คุณไม่จำเป็นต้องเลือก **โชคชะตา** จะเลือกให้เอง:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🎉 เกมที่เลือกได้แก่:",
        value=f"**{selected_game}**\n\nโชคชะตาได้ตัดสินแล้ว จงเล่นซะ!",
        inline=False
    )

    embed.set_footer(
        text="KanomTokyo: ปัญหาการตัดสินใจของคุณได้รับการแก้ไขแล้ว.",
        icon_url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url
    )
    embed.timestamp = discord.utils.utcnow()

    await ctx.send(embed=embed)


# --- Commands: Russian Roulette (Squid Game Recruiter Edition) ---

@bot.command(name='startgame', help='Recruiter says: Start a new Russian Roulette session (Lobby).')
async def start_game_session(ctx):
    """Initializes the game session if one is not already active."""

    global GAME_ACTIVE
    global BULLET_CHAMBER
    global CURRENT_CHAMBER_INDEX

    if GAME_ACTIVE:
        await ctx.send(
            "🚫 **กง-เต็ก:** เกมกำลังดำเนินอยู่แล้ว! ใช้ `!fire` เพื่อเล่นต่อ หรือยอมแพ้แล้วใช้ `!spin` เพื่อเปลี่ยนโม่.")
        return

    GAME_ACTIVE = True
    BULLET_CHAMBER = random.randint(1, CHAMBERS)
    CURRENT_CHAMBER_INDEX = 1

    instruction_message = (
        f"🃏 **กง-เต็ก:** เราจะผลัดกันยิงคนละที โดยไม่ต้องหมุนเพื่อรีเซ็ทโอกาส แปลว่าถ้าหากว่ายิงครบ 6 นัดเกมนี้จะจบทันที **ว่าไงหละ**\n"
        f"**กติกา:** เราจะยิงปืนไปทีละช่อง **เรียงตามลำดับ** **(1 ไป 6)**\n"
        f"ตอนนี้เรากำลังเล็งไปที่ **หมายเลข 1** โชคชะตาของคุณขึ้นอยู่กับช่องนี้ครับคุณกีฮุน\n"
        f"ใช้คำสั่ง `!fire` เพื่อเหนี่ยวไก. (ใช้ `!spin` เพื่อเปลี่ยนโม่ในรอบเดียวกัน)."
    )
    await ctx.send(instruction_message)


@bot.command(name='fire', help=f'Recruiter challenges you! Pull the trigger on the current chamber.')
async def russian_roulette(ctx):
    """Fires the current chamber, advancing the index 1-6 and recording wins."""

    global GAME_ACTIVE
    global BULLET_CHAMBER
    global CURRENT_CHAMBER_INDEX
    global PLAYER_WINS

    if not GAME_ACTIVE:
        await ctx.send(
            "🚨 **กง-เต็ก:** **คุณซ็อง กี-ฮุนครับอย่ารีบสิครับ** ใช้ `!startgame` เพื่อเริ่มเซสชันใหม่.")
        return

    if BULLET_CHAMBER == 0:
        await ctx.send(
            " **กง-เต็ก:** กระสุนเพิ่งยิงออกไป! ผู้เล่นคนถัดไปต้อง **หมุนโม่** ก่อนด้วยคำสั่ง `!spin`.")
        return

    if CURRENT_CHAMBER_INDEX == BULLET_CHAMBER:
        # --- HIT (The Bullet Fired) ---
        response = (
            f"💥 **แคว๊ก!!** **หมายเลข {CURRENT_CHAMBER_INDEX}** คือกระสุน! 😈"
            f"\n{ctx.author.mention}, **กง-เต็ก:** น่าเสียดายนะครับแต่ **เซสชันจบลงแล้ว** ใช้ `!startgame` เพื่อเริ่มต้นใหม่."
        )
        GAME_ACTIVE = False
        BULLET_CHAMBER = 0
        CURRENT_CHAMBER_INDEX = 1

    else:
        # --- MISS (The Chamber Was Empty - Player Survives This Pull) ---
        user_id = str(ctx.author.id)
        PLAYER_WINS[user_id] = PLAYER_WINS.get(user_id, 0) + 1
        save_scores(PLAYER_WINS)

        response = (
            f"💨 **แกร๊ก...** หมายเลข **{CURRENT_CHAMBER_INDEX}** ว่างเปล่า"
            f"\n{ctx.author.mention}, **กง-เต็ก:** เชิญยิงต่อได้เลยครับ **{CHAMBERS - CURRENT_CHAMBER_INDEX}** ใน **{CHAMBERS}**."
        )
        CURRENT_CHAMBER_INDEX += 1

        if CURRENT_CHAMBER_INDEX > CHAMBERS:
            response += "\n\n🎉 **กง-เต็ก:** **เป็นไปไม่ได้!** **เซสชันจบลงแล้ว** ใช้ `!startgame` เพื่อเริ่มต้นใหม่."
            GAME_ACTIVE = False
            BULLET_CHAMBER = 0
            CURRENT_CHAMBER_INDEX = 1

    await ctx.send(response)


@bot.command(name='spin', help='Recruiter says: Spin to reset the odds during an active game.')
async def spin_cylinder(ctx):
    """Resets the cylinder state MID-SESSION, changing the bullet location."""

    global GAME_ACTIVE
    global BULLET_CHAMBER
    global CURRENT_CHAMBER_INDEX

    if not GAME_ACTIVE:
        await ctx.send(
            "🚨 **กง-เต็ก:** **เกมยังไม่เริ่มครับคุญกีฮุน!** ใช้ `!startgame` เพื่อเริ่มเซสชันก่อน.")
        return

    BULLET_CHAMBER = random.randint(1, CHAMBERS)
    CURRENT_CHAMBER_INDEX = 1

    instruction_message = (
        f"🃏 **กง-เต็ก:** **โม่ปืนถูกหมุนแล้ว!** เชิญเลยครับ\n"
        f"ตอนนี้เล็งกลับไปที่ **หมายเลข 1** อีกครั้ง!\n"
        f"ใช้คำสั่ง `!fire` เพื่อเหนี่ยวไก."
    )

    await ctx.send(instruction_message)


@bot.command(name='status', help='Shows the current game status and index.')
async def game_status(ctx):
    """Shows the current game status."""

    global GAME_ACTIVE

    if not GAME_ACTIVE:
        await ctx.send(
            "**กง-เต็ก:** คุณซ็อง กี-ฮุนครับอย่ารีบสิครับ ใช้ `!startgame` เพื่อเริ่มเซสชันใหม่")
        return

    chambers_left = CHAMBERS - CURRENT_CHAMBER_INDEX + 1

    await ctx.send(
        f"🔫 **สถานะเกม (กง-เต็ก):**"
        f"\n> **ตอนนี้เล็งไปที่หมายเลข:** **{CURRENT_CHAMBER_INDEX}** จาก **{CHAMBERS}**"
        f"\n> **โอกาสรอด:** **{chambers_left}** ใน **{CHAMBERS}** ช่องที่เหลือ"
        f"\n> **ช่องกระสุน** (สำหรับ Admin/DM เท่านั้น): {BULLET_CHAMBER}"
    )


@bot.command(name='leaderboard', help='Shows the top survivors of KanomTokyo\'s game.')
async def show_leaderboard(ctx):
    """Displays the top 10 players based on survival count."""

    global PLAYER_WINS

    if not PLAYER_WINS:
        await ctx.send(
            "📊 **กง-เต็ก:** ยังไม่มีผู้รอดชีวิตที่ถูกบันทึกไว้! ใช้ `!fire` เพื่อเริ่มบันทึก.")
        return

    sorted_wins = sorted(PLAYER_WINS.items(), key=lambda item: item[1], reverse=True)

    embed = discord.Embed(
        title="🏆 ทะเบียนผู้รอดชีวิตสูงสุด (Survival Leaderboard)",
        description="ผู้ที่เหนี่ยวไกแล้วรอดชีวิตมากที่สุดเท่านั้นที่จะได้รับการจารึก...",
        color=GAME_COLOR
    )

    rank_count = 0
    for user_id_str, wins in sorted_wins:
        if rank_count >= 10:
            break

        user_id = int(user_id_str)
        user = bot.get_user(user_id)
        user_display_name = user.name if user else f"ผู้เล่นที่ไม่รู้จัก (ID: {user_id_str})"

        embed.add_field(
            name=f"#{rank_count + 1}. {user_display_name}",
            value=f"**{wins} ครั้ง**",
            inline=False
        )
        rank_count += 1

    await ctx.send(embed=embed)


# Run the bot with the token
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_TOKEN not found. Check your .env file or environment variables.")