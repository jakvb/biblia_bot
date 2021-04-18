import os
import discord
import requests
from decouple import config
from discord.ext import commands
from txt_formating import check_begining
import logging


log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, filename=os.path.dirname(os.path.abspath(__file__))+'/app.log')

bot = commands.Bot(command_prefix= "$")
AUDIO_PATH = os.path.dirname(os.path.abspath(__file__)) + '/audio/'
FILENAME_TEMPLATE = '{}_{}'

# TODO: state pre kazdy channel_id alebo state obj
last = ()

async def download_audio(chapter, verse):
    url = f'https://api2.biblia.sk/api/audio/{chapter}/{verse}'
    ret = requests.get(url)
    if ret.status_code == 200:
        audio_url = ret.json()['src']
        file_bin = requests.get(audio_url)
        filename = FILENAME_TEMPLATE.format(chapter, verse)
        log.info(f'downloaded {filename}')
        path = AUDIO_PATH + filename
        with open(path, 'bw') as f:
            f.write(file_bin.content)
            log.info(f'saved {filename}')
        return path


async def get_audio(chapter, verse):
    path = AUDIO_PATH + FILENAME_TEMPLATE.format(chapter, verse)
    if os.path.exists(path):
        return path
    return await download_audio(chapter, verse)


async def get_channel(message):
    voice = []
    for voice in bot.voice_clients:
        pass
    if not voice:
        voice = await message.author.voice.channel.connect()
    return voice


@bot.command('stop')
async def stop(message):
    voice = await get_channel(message)
    voice.stop()


@bot.command('pause')
async def pause(message):
    voice = await get_channel(message)
    voice.pause()


@bot.command('next')
async def next(ctx):
    message = ctx.message
    voice = await get_channel(message)
    global last
    if len(last) == 2:
        chapter, verse = last
        verse = str(int(verse) + 1)
        audio_url = await get_audio(chapter, verse)
        await ctx.send(f'play {chapter} {verse}')
        voice = await get_channel(message)
        voice.stop()
        voice.play(discord.FFmpegPCMAudio(audio_url))
        last = (chapter, verse)


@bot.command('play')
async def play(ctx):
    print(ctx.message.content)
    message = ctx.message

    content = message.content[6:]
    if ' ' in content:
        chapter, verse = content.split(' ')
        log.info(chapter, verse)
        ch = await check_begining(chapter)
        if ch:
            audio_url = await get_audio(ch, verse)
            await ctx.send(f'play {chapter} {verse}')
            voice = await get_channel(message)
            voice.play(discord.FFmpegPCMAudio(audio_url))
            global last
            last = (ch, verse)


bot.run(config('TOKEN'))

