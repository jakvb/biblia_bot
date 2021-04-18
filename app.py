import os
import discord
import requests
from decouple import config
from discord.ext import commands
from txt_formating import check_begining, books
import logging



log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, filename=os.path.dirname(os.path.abspath(__file__))+'/app.log')

bot = commands.Bot(command_prefix= "$")
AUDIO_PATH = os.path.dirname(os.path.abspath(__file__)) + '/audio/'
FILENAME_TEMPLATE = '{}_{}'

# TODO: state pre kazdy channel_id alebo state obj
last_channel = {}

def download_audio(chapter, verse):
    url = f'https://api2.biblia.sk/api/audio/{chapter}/{verse}'
    ret = requests.get(url)
    if ret.status_code == 200:
        audio_url = ret.json()['src']
        file_bin = requests.get(audio_url)
        if file_bin.content[:6] == '<Error>':
            return None
        filename = FILENAME_TEMPLATE.format(chapter, verse)
        log.info(f'downloaded {filename}')
        path = AUDIO_PATH + filename
        with open(path, 'bw') as f:
            f.write(file_bin.content)
            log.info(f'saved {filename}')
        return path


def get_audio(chapter, verse):
    path = AUDIO_PATH + FILENAME_TEMPLATE.format(chapter, verse)
    if os.path.exists(path):
        return path
    return download_audio(chapter, verse)


async def get_channel(channel):
    for voice in bot.voice_clients:
        if voice.channel.id == channel.id:
            return voice
    return await channel.connect()


@bot.command('stop')
async def stop(ctx):
    voice = await get_channel(ctx.message.author.voice.channel)
    voice.stop()


@bot.command('pause')
async def pause(ctx):
    voice = await get_channel(ctx.message.author.voice.channel)
    voice.pause()


@bot.command('next')
async def nexts(ctx):
    message = ctx.message
    voice = await get_channel(message.author.voice.channel)
    global last_channel
    if last_channel.get(voice.channel.id) and len(last_channel[voice.channel.id]) == 2:
        chapter, verse = last_channel[voice.channel.id]
        verse = str(int(verse) + 1)
        audio_url = get_audio(chapter, verse)
        # await ctx.send(f'next {chapter} {verse}')
        voice.stop()
        voice.play(discord.FFmpegPCMAudio(audio_url))
        last_channel[voice.channel.id] = (chapter, verse)
    else:
        await ctx.send(f'No history')


@bot.command('play')
async def play(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    print(ctx.message.content)
    message = ctx.message
    channel = message.author.voice.channel
    content = message.content[6:]
    if ' ' in content:
        chapter, verse = content.split(' ')
        log.info(chapter + verse)
        ch = await check_begining(chapter)
        if ch:
            audio_url = get_audio(ch, verse)
            # await ctx.send(f'play {chapter} {verse}')
            voice = await get_channel(channel)
            voice.play(discord.FFmpegPCMAudio(audio_url), after=lambda e:audio_iter(voice))
            # global last_channel
            last_channel[voice.channel.id] = (ch, verse)
            # print(last_channel)

            # def repeat(guild, voice, audio):
            #     voice.play(audio, after=lambda e: repeat(guild, voice, next(audio)))
            #     voice.is_playing()

            # if channel and not voice.is_playing():
            #     audio_iter(voice)
            #     # audio = discord.FFmpegPCMAudio(audio_url)
            #     # voice.play(audio, after=lambda e: repeat(ctx.guild, voice, next(audio)))
            #     voice.is_playing()

def audio_iter(voice):
    global last_channel
    if last_channel.get(voice.channel.id) and len(last_channel[voice.channel.id]) == 2:
        chapter, verse = last_channel[voice.channel.id]
        audio_url, chapter, verse = next_path(chapter, verse)
        audio = discord.FFmpegPCMAudio(audio_url)
        voice.play(audio, after=lambda e: audio_iter(voice))
        last_channel[voice.channel.id] = (chapter, verse)


def next_path(chapter, verse):
    verse = str(int(verse) + 1)
    path = get_audio(chapter, verse)
    if not path:
        verse = 1
        try:
            chapter = books.keys()[books.keys().index(chapter) + 1]
        except KeyError:
            chapter = books.keys()[0]
        return get_audio(chapter, verse), chapter, verse
    return path, chapter, verse


bot.run(config('TOKEN'))

