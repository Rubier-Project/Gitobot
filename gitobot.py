BOT_TOKEN = ""
WALLET_PRIVATE_KEY = ""
ADMINISTATORS = [ 0000, 1111, 2222 ]

# ----------------------------------

import git.repo
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ( Message, InlineKeyboardButton, InlineKeyboardMarkup )
from tronpy import Tron
from time import ( ctime, time )
from json import ( dumps, loads )
import os
import shutil
import sqlite3
import zipfile
import aiofiles
import git
import asyncio

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

        else: { "status": "INVALID_USER_ID", "is_limit": False }

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

class GitManager(object):
    def __init__(self):
        self.main_url = "https://github.com/"

    async def combine(self, username: str, repo_name: str) -> str:
        return self.main_url + username + "/" + repo_name
    
    async def handle_dir(self, endpoint: str):
        if os.path.exists(endpoint):
            if os.path.isdir(endpoint):
                shutil.rmtree(endpoint)
            elif os.path.isfile(endpoint):
                os.remove(endpoint)
        
        os.makedirs(endpoint, exist_ok=True)

    async def find(self, url: str):
        if "/" in url:
            url = url.split("/")[-1]

        return url

    async def clone(self, url: str) -> dict:
        try:
            finded = await self.find(url)
            await self.handle_dir(finded)
            git.Repo.clone_from(url, finded)
            with zipfile.ZipFile(finded+".zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(finded):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, finded))

            shutil.rmtree(finded)
            return { "status": "OK", "path": finded+".zip" }
        except Exception as ErrorCloning:
            return { "status": "ErrorCloning", "message": str(ErrorCloning) }
        
    async def clone_by_user(self, username: str, repo_name: str):
        try:
            combined = await self.combine(username, repo_name)
            await self.handle_dir(repo_name)
            git.Repo.clone_from(combined, repo_name)
            with zipfile.ZipFile(repo_name+".zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(repo_name):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, repo_name))

            shutil.rmtree(repo_name)
            return { "status": "OK", "path": repo_name+".zip" }
        except Exception as ErrorCloning:
            return { "status": "ErrorCloning", "message": str(ErrorCloning) }

database = DataBase()
gitmanager = GitManager()

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
/clone: clone a repo from github 🛰
/set: set your hash wallet 📪
/myshoppings: see your shoppings ✅
/urls: see your all urls you created 💻
/subscribe: subscribe to use unlimited version 🎶
            """.strip()
        )

    elif message.text == "/up":
        user_data = await database.getUserByID(message.from_user.id)

        if user_data['status'] == "OK":
            shps = await database.calculateShops(message.from_user.id)
            hided_wallet = user_data['user'][4].replace(user_data['user'][4][10:], "...")
            markup = InlineKeyboardMarkup()
            button = InlineKeyboardButton("See Help", callback_data="Help")
            markup.add(button)
            await bot.reply_to(message, f"You already have an account !\nID 🍷: {user_data['user'][0]}\nName ⚜: {user_data['user'][1]}\nUsername 🔰: {user_data['user'][2]}\nFirst Log 📃: {user_data['user'][3]}\nWallet 🎟: {hided_wallet}\nEvery Shoppings 🧤🧣: {shps['shopped']}\nCloned Repos 🤳: {user_data['user'][6]}\nLimit Attempts 🍡: {user_data['user'][7]}", reply_markup=markup)

        else:
            markup = InlineKeyboardMarkup()
            button = InlineKeyboardButton("See Help", callback_data="Help")
            markup.add(button)
            await database.add(message.from_user.id, message.from_user.full_name, message.from_user.username)
            await bot.reply_to(message, "Your account Created ! Welcome User 😆", reply_markup=markup)

    elif message.text.startswith("/clone"):
        user = await database.getUserByID(message.from_user.id)

        if user['status'] == "OK":

            islimit = await database.isLimit(message.from_user.id)

            if islimit['is_limit'] == True:
                markup = InlineKeyboardMarkup()
                button = InlineKeyboardButton("See Help", callback_data="Help")
                markup.add(button)
                await bot.reply_to(message, "Sorry But You Are Limit ! Subscibe to use Unlimited version", reply_markup=markup)

            git_url = message.text[6:].strip()

            if git_url.startswith("https://github.com/"):
                status = await gitmanager.clone(git_url)
                if status['status'] == "OK":
                    user['user'][7] += 1
                    await database.edit(message.from_user.id, limit_attempts=user['user'][7])
                    with aiofiles.open(status['path'], 'rb') as FILE:
                        await bot.send_document(message.chat.id, data=FILE, reply_to_message_id=message.id, caption=f"URL: {git_url}\nLimited in: {user['user'][7]}/10")
                
                else:await bot.reply_to(message, f"Error While Cloning: {status['message']}")
            
            elif git_url.count(" ") == 0:
                splitted = git_url.split(" ")
                username = splitted[0]
                reponame = splitted[1]

                status = await gitmanager.clone_by_user(username, reponame)
                if status['status'] == "OK":
                    user['user'][7] += 1
                    await database.edit(message.from_user.id, limit_attempts=user['user'][7])
                    with aiofiles.open(status['path'], 'rb') as FILE:
                        await bot.send_document(message.chat.id, data=FILE, reply_to_message_id=message.id, caption=f"URL: {git_url}\nLimited in: {user['user'][7]}/10")
                else:await bot.reply_to(message, f"Error While Cloning: {status['message']}")
            
            else:
                markup = InlineKeyboardMarkup()
                button = InlineKeyboardButton("See Help", callback_data="Help")
                markup.add(button)
                await bot.reply_to(message, "Invalid Usage Syntax ! ❌", reply_markup=markup)

        else:
            await bot.reply_to(message, "Please create an account with `/up` command", parse_mode="Markdown")

    elif message.text.startswith("/set"):
        user = await database.getUserByID(message.from_user.id)

        if user['status'] == "OK":
            wallet = message.text[4:].strip()
            if wallet == "":
                await bot.reply_to(message, "Cannot Find the Hash Wallet from Message 👁")

            else:
                user = await database.getUserByID(message.from_user.id)
                markup = InlineKeyboardMarkup()
                shop_button = InlineKeyboardButton("Shoppings", callback_data="Shops")
                subscribe = InlineKeyboardButton("Subscribe", callback_data="Sub")
                markup.add(shop_button, subscribe)
                await database.edit(message.from_user.id, wallet)
                await bot.reply_to(message, f"Wallet Updated 🌐\nOld One 📁: {user['user'][4]}\nNew One 📪: {wallet}", reply_markup=markup)

        else:
            await bot.reply_to(message, "Please create an account with `/up` command", parse_mode="Markdown")

    elif message.text == "/myshoppings":
        user = await database.getUserByID(message.from_user.id)

        if user['status'] == "OK":
            shops = await database.calculateShops(message.from_user.id)
            await bot.reply_to(message, f"Your All Paids are {shops['shopped']} 💲")
        else:
            await bot.reply_to(message, "Please create an account with `/up` command", parse_mode="Markdown")

    elif message.text == "/urls":
        user = await database.getUserByID(message.from_user.id)

        if user['status'] == "OK":
            urls = await database.getClones(message.from_user.id)
            urls = dumps(urls['urls'], indent=2)
            await bot.reply_to(message, f"Urls: 📃\n{urls}")
        else:
            await bot.reply_to(message, "Please create an account with `/up` command", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True) # Add Shops and Sub - Line 322 - Admin Panel
async def handle_query(call):
    if call.data == "Help":
        await bot.reply_to(
            call.message,
            """
/start: start Gito Bot 🎫
/help: get more info 📃
/clone: clone a repo from github 🛰
/up: create an account ( automaticly create when you start the bot ) 📱
/set: set your hash wallet 📪
/myshoppings: see your shoppings ✅
/urls: see your all urls you created 💻
/subscribe: subscribe to use unlimited version 🎶
            """.strip()
        )

def run():
    asyncio.run(bot.polling())

if __name__ == "__main__":
    run()