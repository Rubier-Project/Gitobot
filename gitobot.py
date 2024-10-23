BOT_TOKEN = ""
WALLET_PRIVATE_KEY = ""
ADMINISTATORS = [ 0000, 1111, 2222 ]

# ----------------------------------

from telebot.async_telebot import AsyncTeleBot
from telebot.types import ( Message, InlineKeyboardButton, InlineKeyboardMarkup )
from tronpy import Tron
from time import ( ctime, time )
from json import ( dumps, loads )
from os import path
import sqlite3
import git

bot = AsyncTeleBot(BOT_TOKEN)
tron = Tron()

class DataBase(object):
    def __init__(self):
        self.dbs = sqlite3.connect("database.db", check_same_thread=False)
        self.setup()

    def setup(self):
        self.dbs.execute(
            """
            CREATE TABLE IF NOT EXISTS handled_users (
                userid TEXT PRIMARY KEY,
                fullname TEXT,
                username TEXT,
                first_log TEXT,
                wallet_hash TEXT,
                every_shoppings TEXT,
                cloned_repos TEXT,
                limit_attempts TEXT
            )
            """
        )

    async def getUsers(self) -> list:
        return self.dbs.execute("SELECT * FROM handled_users").fetchall()
    
    async def getUserByID(self, user_id: str) -> dict:
        for user in await self.getUsers():
            if user[0] == user_id:
                return { "status": "OK", "user": user }
            
        return { "status": "INVALID_USER_ID", "user": () }
    
    async def getUserByWallet(self, wallet_hash: str) -> dict:
        for user in await self.getUsers():
            if user[4] == wallet_hash:
                return { "status": "OK", "user": user }
            
        return { "status": "INVALID_WALLET_HASH", "user": () }
    
    async def getClones(self, user_id: str) -> dict:
        user = await self.getUserByID(user_id)

        if user['status']:
            return { "status": "OK", "urls": user['user'][6] }
        else: return user

    async def calculateShops(self, user_id: str) -> dict:
        user = await self.getUserByID(user_id)

        if user['status']:
            every = user['user'][5]
            shopped = 0

            for evry in every:
                shopped += evry

            return { "status": "OK", "shopped": shopped }

        else: return user

    async def isLimit(self, user_id: str, limit: int = 10):
        user = await self.getUserByID(user_id)

        if user['status']:
            attmpt = user['user'][7]
            if int(attmpt) > limit or int(attmpt) >= limit:
                return { "status": "OK", "is_limit": True }
            
            else: return { "status": "OK", "is_limit": False }

        else: return user

    async def getTime(self) -> str:
        return ctime(time())

    async def add(
        self,
        user_id: str,
        fullname: str,
        username: str
    ) -> dict:
        
        verify = await self.getUserByID(user_id)

        if verify['status']:
            return { "status": "EXISTS_USER_ID" }
        
        _time = await self.getTime()

        self.dbs.execute(
            """
            INSERT INTO handled_users (userid, fullname, username, first_log, wallet_hash, every_shoppings, cloned_repos) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                fullname.strip(),
                username.strip(),
                _time,
                "null",
                "[]",
                "[]"
            )
        )

        self.dbs.commit()

        return { "status": "OK", "user": (
                user_id,
                fullname.strip(),
                username.strip(),
                _time,
                "null",
                "[]",
                "[]"
            ) }

    async def delete(
        self,
        user_id: str
    ) -> dict:
        
        verify = await self.getUserByID(user_id)

        if verify['status']:
            self.dbs.execute("DELETE FROM handled_users WHERE userid = ?", (user_id,))
            self.dbs.commit()
            return { "status": "OK" }
        else:return { "status": "INVALID_USER_ID" }

    async def edit(
        self,
        user_id: str,
        wallet_hash: str = None,
        limit_attempts: str = None,
        every_shoppings: list = None,
        cloned_repos: list = None
    ) -> dict:
        
        verify = await self.getUserByID(user_id)

        if not verify['status']:
            return { "status": "INVALID_USER_ID" }
        
        verify['user'][4] = wallet_hash if wallet_hash != None else verify['user'][4]
        verify['user'][5] = every_shoppings if every_shoppings != None else verify['user'][5]
        verify['user'][6] = cloned_repos if cloned_repos != None else verify['user'][6]
        verify['user'][7] = limit_attempts if limit_attempts != None else verify['user'][7]

        self.dbs.execute("UPDATE handled_users SET wallet_hash = ? , every_shoppings = ? , cloned_repos = ? , limit_attempts = ? WHERE userid = ?", (verify['user'][4], verify['user'][5], verify['user'][6], verify['user'][7], verify['user'][0]))
        self.dbs.commit()

database = DataBase()

@bot.message_handler(content_types=['text'], chat_types=['private', 'supergroup'])
async def on(message: Message):
    message.text = message.text.strip()

    if message.text == "/start":
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton("See Help", callback_data="Help")
        markup.add(button)
        await database.add(message.from_user.id, message.from_user.full_name, message.from_user.username)
        await bot.reply_to(message, "Welcome to GitoBot 👁", reply_markup=markup)

    elif message.text == "/help":
        await bot.reply_to(
            message,
            """
/start: start Gito Bot 🎫
/help: get more info 📃
/up: create an account ( automaticly create when you start the bot ) 📱
/set: set your hash wallet 📪
/myshoppings: see your shoppings ✅
/urls: see your all urls you created 💻
            """
        )

    #elif message

@bot.callback_query_handler(func=lambda call: True)
async def handle_query(call):
    if call.data == "Help":
        await bot.reply_to(
            call.message,
            """
/start: start Gito Bot 🎫
/help: get more info 📃
/up: create an account ( automaticly create when you start the bot ) 📱
/set: set your hash wallet 📪
/myshoppings: see your shoppings ✅
/urls: see your all urls you created 💻
            """
        )