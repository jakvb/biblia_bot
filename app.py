import os
import logging
import discord
import requests
from decouple import config
from discord.ext import commands
from txt_formating import Book


log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, filename=os.path.dirname(os.path.abspath(__file__))+'/app.log')

bot = commands.Bot(command_prefix= "$")
AUDIO_PATH = os.path.dirname(os.path.abspath(__file__)) + '/audio/'
FILENAME_TEMPLATE = '{}_{}'
state = {}


# todo:
#  random kapitola
#  likovanie kapitol
#  zamutovat si sluchadla po connecte
#  pauznut sa ked je sam v kanali
#  posielat videa z youtube biblia_za_rok
#  posuvanie v case (seek)


def download_audio(book, chapter):
    url = f'https://api2.biblia.sk/api/audio/{book}/{chapter}'
    ret = requests.get(url)
    if ret.status_code == 200:
        audio_url = ret.json()['src']
        file_bin = requests.get(audio_url)
        if b'<Error><Code>NoSuchKey' in file_bin.content[:150]:
            return None
        filename = FILENAME_TEMPLATE.format(book, chapter)
        log.info(f'downloaded {filename}')
        path = AUDIO_PATH + filename
        with open(path, 'bw') as f:
            f.write(file_bin.content)
            log.info(f'saved {filename}')
        return path


def get_audio(book, chapter):
    path = AUDIO_PATH + FILENAME_TEMPLATE.format(book, chapter)
    if os.path.exists(path):
        return path
    return download_audio(book, chapter)


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
    if state.get(voice.channel.id):
        st = state[voice.channel.id]
        if action == 'play':
            action = '▶'
        elif action == 'pause':
            action = 'Ⅱ'
        else:
            return 'Biblia'
        print(action, st.book.pretty)
        return ' '.join([action, st.book.pretty, st.chapter])


@is_in_voice
@bot.command('stop')
async def stop(ctx):
    voice = await get_channel(ctx.message.author.voice.channel)
    Player(voice).stop()
    await ctx.message.guild.me.edit(nick=get_name(voice))
    await ctx.channel.purge(limit=1)
    await ctx.send("command STOP")


@is_in_voice
@bot.command('pause')
async def pause(ctx):
    voice = await get_channel(ctx.message.author.voice.channel)
    voice.pause()
    await ctx.message.guild.me.edit(nick=get_name(voice, 'pause'))
    await ctx.channel.purge(limit=1)
    await ctx.send("command PAUSE")


@is_in_voice
@bot.command('resume')
async def resume(ctx):
    voice = await get_channel(ctx.message.author.voice.channel)
    voice.resume()
    await ctx.message.guild.me.edit(nick=get_name(voice, 'play'))
    await ctx.channel.purge(limit=1)
    await ctx.send("command RESUME")


@bot.command('next')
async def next(ctx):
    message = ctx.message
    channel = message.author.voice.channel
    channel = await get_channel(channel)
    Player(channel).next()
    await ctx.channel.purge(limit=1)
    await ctx.send("command NEXT")


@bot.command('play')
async def play(ctx):
    message = ctx.message
    channel = message.author.voice.channel
    content = message.content[6:]
    channel = await get_channel(channel)
    await ctx.channel.purge(limit=1)
    if not content:
        # todo metoda na pause
        channel.resume()
        await ctx.message.guild.me.edit(nick=get_name(channel, 'play'))
        await ctx.send(f"command PLAY")
    else:
        s= State(channel, *content.split(' '))
        Player(channel, s).play()
        await ctx.send(f"command PLAY {s.book.pretty} {s.chapter}")


@bot.command('infinite')
async def infinite(ctx):
    message = ctx.message
    channel = message.author.voice.channel
    channel = await get_channel(channel)
    content = message.content[10:]
    await ctx.channel.purge(limit=1)
    if 'on' in content or not content:
        Player(channel).state.infinite = True
        await ctx.send(f"command INFINITE ON")
    elif 'off' in content:
        Player(channel).state.infinite = False
        await ctx.send(f"command PLAY OFF")
    else:
        s = State(channel, *content.split(' '), infinite=True)
        Player(channel, s).play()
        await ctx.send(f"command INFINITE play from {s.book.pretty} {s.chapter}")


class Player:
    def __init__(self, channel, new_state=None):
        global state
        if new_state:
            self.state = new_state
        elif state.get(channel.channel.id):
            self.state = state[channel.channel.id]
        else:
            raise Exception('No state!')
        self.voice = channel

    def play(self, next_state=False):
        if next_state:
            self.state.next()
        voice = self.voice
        audio = discord.FFmpegPCMAudio(self.state.path)
        if self.state.infinite:
            voice.play(audio, after=lambda e:self.play(next_state=True))
        else:
            task = lambda e:voice.loop.create_task(voice.guild.me.edit(nick=get_name(voice, 'stop')))
            voice.play(audio, after=task)
        voice.loop.create_task(voice.guild.me.edit(nick=get_name(voice, 'play')))

    def next(self):
        self.stop()
        self.play(next_state=True)

    def stop(self):
        self.voice.pause()
        # hack na prerusenie infinite loopu
        try:
            self.voice.play(discord.FFmpegPCMAudio(''))
        except:
            pass

        self.voice.stop()


class State:
    def __init__(self, channel, book, chapter, infinite=False):
        self.channel_id = channel.channel.id
        self.book = Book(book)
        self.chapter = chapter
        self._infinite = infinite
        state[self.channel_id] = self

    @property
    def infinite(self):
        print('get infinite', self._infinite)
        return self._infinite

    @infinite.setter
    def infinite(self, v):
        self._infinite = bool(v)
        print('set infinite', self._infinite)
        state[self.channel_id] = self

    @property
    def path(self):
        return get_audio(self.book, self.chapter)

    def next(self):
        self.chapter = str(int(self.chapter) + 1)
        if not self.path:
            self.chapter = '1'
            self.book.next()
        state[self.channel_id] = self
        return self

    def previous(self):
        state[self.channel_id] = self
        pass

bot.run(config('TOKEN'))
