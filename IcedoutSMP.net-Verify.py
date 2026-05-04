import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import threading
import random
import string
import time

# ================= CONFIG =================
import os
TOKEN = os.getenv("DISCORD_TOKEN")
ROLE_NAME = "» sᴘɪᴇʟᴇʀ"
PORT = 5000

# ================= DISCORD =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# discord_id -> (code, timestamp)
verify_data = {}
# code -> discord_id
code_map = {}

# ================= CODE =================
def generate_code():
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(8))

# ================= DISCORD COMMAND =================
@bot.command()
async def verify(ctx):
    code = generate_code()
    verify_data[ctx.author.id] = (code, time.time())
    code_map[code] = ctx.author.id

    await ctx.reply(
        f"🔐 Dein Minecraft Code:\n\n"
        f"**{code}**\n\n"
        f"In Minecraft eingeben:\n"
        f"`/verify {code}`\n"
        f"⏱ gültig: 10 Minuten"
    )

# ================= CHECK FUNCTION =================
def check_code(code):
    if code not in code_map:
        return None

    discord_id = code_map[code]
    stored = verify_data.get(discord_id)

    if not stored:
        return None

    _, timestamp = stored

    # 10 min expiry
    if time.time() - timestamp > 600:
        del verify_data[discord_id]
        del code_map[code]
        return None

    return discord_id

# ================= FLASK API =================
app = Flask(__name__)

@app.route("/verify", methods=["POST"])
def verify_mc():
    data = request.json
    code = data.get("code")
    player = data.get("player")

    discord_id = check_code(code)

    if not discord_id:
        return jsonify({"status": "error"}), 400

    guild = bot.guilds[0]
    member = guild.get_member(discord_id)
    role = discord.utils.get(guild.roles, name=ROLE_NAME)

    if member:
        # Rolle geben
        if role:
            bot.loop.create_task(member.add_roles(role))

        # Nickname ändern
        bot.loop.create_task(member.edit(nick=player))

    # cleanup
    del verify_data[discord_id]
    del code_map[code]

    return jsonify({"status": "ok"})

# ================= FLASK START =================
def run_flask():
    app.run(host="0.0.0.0", port=PORT)

threading.Thread(target=run_flask).start()

# ================= BOT READY =================
@bot.event
async def on_ready():
    print(f"✅ Erfolgreich online als {bot.user}")

# ================= START =================
bot.run(TOKEN)