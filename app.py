import os
import logging
import discord
import requests
from decouple import config
from discord.ext import commands
from txt_formating import check_begining, books


log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, filename=os.path.dirname(os.path.abspath(__file__))+'/app.log')

bot = commands.Bot(command_prefix= "$")
AUDIO_PATH = os.path.dirname(os.path.abspath(__file__)) + '/audio/'
FILENAME_TEMPLATE = '{}_{}'
state = {}


# todo:
#  random kapitola
#  premenovat chapter na book a verse na chapter
#  posielat videa z youtube biblia_za_rok
#  posuvanie v case (seek)


def download_audio(chapter, verse):
    url = f'https://api2.biblia.sk/api/audio/{chapter}/{verse}'
    ret = requests.get(url)
    if ret.status_code == 200:
        audio_url = ret.json()['src']
        file_bin = requests.get(audio_url)
        if b'<Error><Code>NoSuchKey' in file_bin.content[:150]:
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


def is_in_voice(func):
    # todo wrapper nefunguje
    async def wrapper(ctx):
        if not ctx.message.author.voice:
            await ctx.send("You are not connected to a voice channel")
            return
        try:
            return func(ctx)
        except discord.ext.commands.errors.CommandInvokeError:
            await ctx.send("You are not connected to a voice channel")

    return wrapper


async def get_channel(channel):
    for voice in bot.voice_clients:
        if voice.channel.id == channel.id:
            return voice
    return await channel.connect()


def get_name(voice, action=''):
    if state.get(voice.channel.id) and len(state[voice.channel.id]) == 2:
        chapter, verse = state[voice.channel.id]
        if action == 'play':
            action = '▶'
        elif action == 'pause':
            action = 'Ⅱ'
        else:
            return 'Biblia'
        print(action, books[chapter])
        return ' '.join([action, books[chapter], verse])


@is_in_voice
@bot.command('stop')
async def stop(ctx):
    voice = await get_channel(ctx.message.author.voice.channel)
    voice.pause()
    # hack na prerusenie infinite loopu
    try:
        voice.play(discord.FFmpegPCMAudio(''))
    except:
        pass

    voice.stop()
    await ctx.message.guild.me.edit(nick=get_name(voice))


@is_in_voice
@bot.command('pause')
async def pause(ctx):
    voice = await get_channel(ctx.message.author.voice.channel)
    voice.pause()
    await ctx.message.guild.me.edit(nick=get_name(voice, 'pause'))


@is_in_voice
@bot.command('resume')
async def resume(ctx):
    voice = await get_channel(ctx.message.author.voice.channel)
    voice.resume()
    await ctx.message.guild.me.edit(nick=get_name(voice, 'play'))


@is_in_voice
@bot.command('next')
async def nexts(ctx):
    message = ctx.message
    voice = await get_channel(message.author.voice.channel)
    global state
    if state.get(voice.channel.id) and len(state[voice.channel.id]) == 2:
        chapter, verse = state[voice.channel.id]
        verse = str(int(verse) + 1)
        audio_url = get_audio(chapter, verse)
        await ctx.send(f'Play next {chapter} {verse}')
        voice.stop()
        state[voice.channel.id] = (chapter, verse)
        voice.play(discord.FFmpegPCMAudio(audio_url))
        await ctx.message.guild.me.edit(nick=get_name(voice, 'play'))
    else:
        await ctx.send(f'No history')


@is_in_voice
@bot.command('infinite')
async def infinite(ctx):
    print(ctx.message.content)
    message = ctx.message
    channel = message.author.voice.channel
    content = message.content[10:]
    print(content)
    if ' ' in content:
        chapter, verse = content.split(' ')
        log.info(chapter + verse)
        ch = await check_begining(chapter)
        if ch:
            audio_url = get_audio(ch, verse)
            audio = discord.FFmpegPCMAudio(audio_url)
            await ctx.send(f'Play infinite from {chapter} {verse}')
            voice = await get_channel(channel)
            # global state
            state[voice.channel.id] = (ch, verse)
            await ctx.message.guild.me.edit(nick=get_name(voice, 'play'))
            voice.play(audio, after=lambda e:audio_iter(voice))


@is_in_voice
@bot.command('play')
async def play(ctx):
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
            await ctx.send(f'Playing {chapter} {verse}')
            voice = await get_channel(channel)
            voice.stop()
            global state
            state[voice.channel.id] = (ch, verse)
            voice.play(discord.FFmpegPCMAudio(audio_url))
            await ctx.message.guild.me.edit(nick=get_name(voice, 'play'))


def audio_iter(voice):
    global state
    if state.get(voice.channel.id) and len(state[voice.channel.id]) == 2:
        chapter, verse = state[voice.channel.id]
        audio_url, chapter, verse = next_path(chapter, verse)
        audio = discord.FFmpegPCMAudio(audio_url)
        state[voice.channel.id] = (chapter, verse)
        voice.play(audio, after=lambda e:audio_iter(voice))
        voice.loop.create_task(voice.guild.me.edit(nick=get_name(voice, 'play')))


def next_path(chapter, verse):
    verse = str(int(verse) + 1)
    path = get_audio(chapter, verse)
    if not path:
        verse = 1
        try:
            chapter = list(books.keys())[list(books.keys()).index(chapter) + 1]
        except KeyError:
            chapter = books.keys()[0]
        return get_audio(chapter, verse), chapter, verse
    return path, chapter, verse


bot.run(config('TOKEN'))

