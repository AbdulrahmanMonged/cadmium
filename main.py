from quart import Quart, render_template, redirect, url_for
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
import psycopg

import os
from urllib.parse import urlparse
from uvicorn import run
from discord.ext.ipc import Client


DB_URI = os.getenv("URI")
db_uri = urlparse(DB_URI)

host = db_uri.hostname
database = db_uri.path[1:]
user = db_uri.username
password = db_uri.password
port= db_uri.port

app = Quart(__name__)
ipc_client = Client(secret_key="Bodyy")

app.config['EXPLAIN_TEMPLATE_LOADING'] = True
app.config['SECRET_KEY'] = "test123"
app.config['DISCORD_CLIENT_ID'] = 1130152470627229858
app.config['DISCORD_CLIENT_SECRET'] = os.getenv("CLIENT_SECRET")
app.config['DISCORD_REDIRECT_URI'] = "http://135.125.205.175:5000/callback"

HEADER_NAME = "Cadmium"
discord = DiscordOAuth2Session(app)
#asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
signed_in = False
@app.route("/")
async def home():
    user = None
    if await discord.authorized:
        user = await discord.fetch_user()

    return await render_template("index.html", header_name=HEADER_NAME, signed_in=await discord.authorized, user = user)

@app.route('/logout')
async def logout():
    discord.revoke()
    return redirect(url_for('home'))

@app.route("/commands")
async def commands():
    user = None
    if await discord.authorized:
        user = await discord.fetch_user()
    async with await psycopg.AsyncConnection.connect(DB_URI) as db:
        async with db.cursor() as cursor:
            await cursor.execute("SELECT COMMAND_NAME, COMMAND_DESCRIPTION FROM COMMANDS")
            results = await cursor.fetchall()
    return await render_template("commands.html", header_name="Commands", signed_in=await discord.authorized, commands = results, user = user)

@app.route("/about")
async def about():
    user = None
    if await discord.authorized:
        user = await discord.fetch_user()
    return await render_template("about.html", header_name="About", signed_in = await discord.authorized, user = user)


@app.route("/dashboard")
@requires_authorization
async def dashboard():
    user = await discord.fetch_user()
    guilds = await user.fetch_guilds()
    bot_guilds = await ipc_client.request("get_guilds")
    common_guilds = [guild for guild in guilds if guild.id in bot_guilds]
    return await render_template("dashboard.html", header_name="Dashboard", user = user ,  signed_in = await discord.authorized, guilds=common_guilds)

@app.route("/login")
async def login():
    return await discord.create_session()

@app.route("/callback/")
async def callback():
    try:
        await discord.callback()
    except:
        return redirect(url_for("login"))
    return redirect(url_for("home"))


@app.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    return redirect(url_for("login"))


# if __name__ == "__main__":
#     app.run(debug=True)

if __name__ == "__main__":
    run(app, host='0.0.0.0' ,port=5000)