from quart import Quart, render_template, redirect, url_for
import psycopg
import asyncio
import os
from urllib.parse import urlparse


DB_URI = os.getenv("DB_URI")
db_uri = urlparse(DB_URI)

host = db_uri.hostname
database = db_uri.path[1:]
user = db_uri.username
password = db_uri.password
port= db_uri.port

app = Quart(__name__)

app.config['EXPLAIN_TEMPLATE_LOADING'] = True
HEADER_NAME = "Cadmium"

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@app.route("/")
async def index():
    return await render_template("index.html", header_name=HEADER_NAME, signed_in=False)

@app.route("/commands")
async def commands():
    async with await psycopg.AsyncConnection.connect(host=host, dbname=database, user=user, password=password, port=port) as db:
        async with db.cursor() as cursor:
            await cursor.execute("SELECT COMMAND_NAME, COMMAND_DESCRIPTION FROM COMMANDS")
            results = await cursor.fetchall()
            for command in results:
                print(command[0].strip(" "), command[1].strip(" "))   
    return await render_template("commands.html", header_name="Commands", signed_in=False, commands = results)

app.run(debug=True)
