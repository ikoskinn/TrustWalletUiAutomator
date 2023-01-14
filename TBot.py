import asyncio
import hashlib
from typing import Any
import requests
import urllib.parse
import time

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineQuery, \
    InputTextMessageContent, InlineQueryResultArticle, InlineQueryResult, ParseMode, ContentType
from aiogram.utils.markdown import bold, code

import Classes
import PlayerClasses

#bot = Bot('')
#disp = Dispatcher(bot=bot)

bot = None
disp = None


BOT_TOKEN = ""
Usernames = []
chat_ids = []
Manager = None


async def start_handler(event: types.Message):
    if event.chat.username in Usernames:
        try:
            test = PlayerClasses.config['_RegisteredUsers'][event.chat.username]
        except:
            Manager.save_config('_RegisteredUsers', event.chat.username, str(event.chat.id))

        text = f"Добро пожаловать в настройки бота Trust Wallet 👋!"

        await event.answer(
            text,
            parse_mode=types.ParseMode.MARKDOWN
        )

async def change_param(event: types.Message):
    if event.chat.username in PlayerClasses.config['_RegisteredUsers'].keys():
        try:
            test = PlayerClasses.config['_RegisteredUsers'][event.chat.username]
        except:
            Manager.save_config('_RegisteredUsers', event.chat.username, str(event.chat.id))
        t = 0
        file = await bot.download_file_by_id(event.document.file_id, destination="phrases.txt")

        await bot.send_message(text=f"Начинаем импортирование фраз в БД. Это может занять некоторое время..",
                               chat_id=event.chat.id,
                               parse_mode=ParseMode.MARKDOWN)

        PlayerClasses.ImportingNow = True
        allphrases = PlayerClasses.sqlite.getAllPhrases().fetchall()
        curtime = time.time()
        with open(file.name) as f:
            for phrase in f:
                if (phrase.replace('\n', ''),) not in allphrases:
                    PlayerClasses.sqlite.importPhrase(phrase)
                    t += 1

        curtime = time.time() - curtime

        PlayerClasses.ImportingNow = False

        await bot.send_message(text=f"Импортировали в БД - {t} фраз за {round(curtime)} сек.",
                               chat_id=event.chat.id,
                               parse_mode=ParseMode.MARKDOWN)

def SendMessage(text):
    for id in PlayerClasses.config['_RegisteredUsers'].values():
        requestText = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?" + \
                     f"chat_id={id}&" + \
                     f"text={urllib.parse.quote_plus(text)}&parse_mode=MARKDOWN"
        requests.get(requestText)


async def main():
    try:
        global bot
        global disp

        bot = Bot(BOT_TOKEN)
        disp = Dispatcher(bot=bot)
        disp.register_message_handler(start_handler, commands={"start", "restart"})
        disp.register_message_handler(change_param, content_types=ContentType.DOCUMENT)
        await disp.start_polling()
    finally:
        await bot.close()