from quart import Quart, render_template, redirect, url_for, request
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
import psycopg
import asyncio
import os
from uvicorn import run
from discord.ext.ipc import Client
from forms import PrefixForm


WTF_CSRF_ENABLED = True
WTF_CSRF_CHECK_DEFAULT = False
WTF_CSRF_SECRET_KEY = os.getenv("CSRF")
WTF_I18N_ENABLED = False

DB_URI = os.getenv("URI")

app = Quart(__name__)
app.config['WTF_CSRF_ENABLED'] = WTF_CSRF_ENABLED
app.config['WTF_CSRF_CHECK_DEFAULT'] = WTF_CSRF_CHECK_DEFAULT
app.config['WTF_CSRF_SECRET_KEY'] = WTF_CSRF_SECRET_KEY
app.config['WTF_I18N_ENABLED'] = WTF_I18N_ENABLED

ipc = Client(host='135.125.205.175', secret_key="Bodyy")

app.config['EXPLAIN_TEMPLATE_LOADING'] = True
app.config['SECRET_KEY'] = os.getenv("SEC")
app.config['DISCORD_CLIENT_ID'] = 1130152470627229858
app.config['DISCORD_CLIENT_SECRET'] = os.getenv("C_SEC")
app.config['DISCORD_REDIRECT_URI'] = "http://135.125.205.175:80/callback"

HEADER_NAME = "Cadmium"
discord = DiscordOAuth2Session(app)
#asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@app.route("/", methods=['GET', 'POST'])
async def home():
    user = None
    response = await ipc.request("get_numbers")
    if await discord.authorized:
        user = await discord.fetch_user()
    return await render_template("index.html", header_name=HEADER_NAME, signed_in=await discord.authorized, user = user, u_num=response.response['users'],g_num=response.response['guilds'],c_num=response.response['channels'])

@app.route('/logout')
async def logout():
    discord.revoke()
    return redirect(url_for('home'))

@app.route("/commands")
async def commands():
    user = None
    response = await ipc.request("get_commands")
    if await discord.authorized:
        user = await discord.fetch_user()
    return await render_template("commands.html", header_name="Commands", signed_in=await discord.authorized, response = response.response, user = user)

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
    bot_guilds = await ipc.request("get_guilds")
    common_guilds = [guild for guild in guilds if guild.id in bot_guilds.response['data'] and guild.permissions.manage_guild == True]
    return await render_template("dashboard.html", header_name="Dashboard", user = user ,  signed_in = await discord.authorized, guilds=common_guilds)


@requires_authorization
@app.route("/edit/<int:id>", methods=["GET", "POST"])
async def editserver(id):
    form = await PrefixForm.create_form(form_data=PrefixForm)
    user = await discord.fetch_user()
    guilds = await user.fetch_guilds()
    current_guild = [guild for guild in guilds if guild.id == id]
    valid = await form.validate_on_submit()
    print("Before")
    async with await psycopg.AsyncConnection.connect(DB_URI) as db:
        async with db.cursor() as cursor:
            await cursor.execute("SELECT GUILD_PREFIX FROM GUILD where GUILD_ID = %s", (id,))
            results = await cursor.fetchone()
            current_prefix = results[0].strip(" ")
            if await form.validate_on_submit():
                await cursor.execute("UPDATE GUILD set GUILD_PREFIX = %s where GUILD_ID = %s", (form.prefix.data, id,))
                return redirect(url_for("editserver", id=id))
    return await render_template("editserver.html", header_name="Edit Server", user = user ,  signed_in = await discord.authorized, form=form, current_prefix=current_prefix, valid = valid, current_guild=current_guild[0])


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
