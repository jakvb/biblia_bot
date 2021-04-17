import discord
import os
from decouple import config
import requests
from txt_formating import check_begining
from discord.ext import commands

bot = commands.Bot(command_prefix= "$")
AUDIO_PATH = 'audio/'
FILENAME_TEMPLATE = '{}_{}'


async def download_audio(chapter, verse):
    url = f'https://api2.biblia.sk/api/audio/{chapter}/{verse}'
    ret = requests.get(url)
    if ret.status_code == 200:
        audio_url = ret.json()['src']
        file_bin = requests.get(audio_url)
        filename = FILENAME_TEMPLATE.format(chapter, verse)
        print(f'downloaded {filename}')
        path = AUDIO_PATH + filename
        with open(path, 'bw') as f:
            f.write(file_bin.content)
            print(f'saved {filename}')
        return path


async def get_audio(chapter, verse):
    path = AUDIO_PATH + FILENAME_TEMPLATE.format(chapter, verse)
    if os.path.exists(path):
        return path
    return await download_audio(chapter, verse)


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content and message.content[0] != '$':
        return
    content = message.content[1:]
    try:
        chapter, verse = content.split(' ')
        print(chapter, verse)
        ch = await check_begining(chapter)
        print(ch)
        if ch:
            audio_url = await get_audio(ch, verse)
            await message.channel.send(f'play {chapter} {verse}')
            voice = await message.author.voice.channel.connect()
            voice.play(discord.FFmpegPCMAudio(audio_url))
            # await voice.disconnect()
    except ValueError as e:
        print(e, content)

bot.run(config('TOKEN'))

