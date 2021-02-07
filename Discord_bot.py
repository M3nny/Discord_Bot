#https://pypi.org/project/discord-pretty-help/

import discord
from discord.ext import commands,tasks
from discord.voice_client import VoiceClient #per far riprodurre mp3 al bot
from pretty_help import PrettyHelp #comando help con interfaccia grafica (personalizzabile)
import youtube_dl #per prendere video da youtube
import random
from random import choice



#TOKEN = put here your discord bot token

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)



client = commands.Bot(command_prefix = '.', help_command=PrettyHelp()) #prefisso del bot

@client.event
async def on_ready():
    change_status.start()
    print('ready to grab')

@tasks.loop(seconds=120) #ogni quanto cambia lo stato
async def change_status():
    status = ['raccogliere campanelle','creare portali','lasciare adc da solo','salvare i nemici'] #stato del bot 
    await client.change_presence(activity=discord.Game(choice(status)))




@client.event
async def on_member_join(member): #quando entra un nuovo utente gli verrà assegnato il ruolo tra ''
    role  = discord.utilis.get(member.server.roles, name = 'meep')
    channel = discord.utils.get(member.guild.channels, name = 'meeps-gathering')
    await client.add_roles(member,role)

@client.command(pass_context=True,help = ".clear [n messaggi]") #cancella n messaggi (il comando clear conta come messaggio)
async def clear(ctx, amount=100):
    channel = ctx.message.channel
    messages = []
    async for message in channel.history(limit=amount):
        messages.append(message)
    await channel.delete_messages(messages)
    await ctx.send('Bardo ha fatto pulizia')

####################################################################################################################################################################
player1 = ""
player2 = ""
turn = ""
gameover = True
board = []


haswon = [
    [0,1,2],
    [3,4,5],
    [6,7,8],
    [0,3,6],
    [1,4,7],
    [2,5,8],
    [0,4,8],
    [2,4,6]

]

@client.command(help = ".tris @giocatore1 @giocatore2")
async def tris(ctx, p1 : discord.Member, p2 : discord.Member):
    global player1
    global player2
    global turn
    global gameover
    global cont 

    if gameover:
        global board
        board =[":white_large_square:",":white_large_square:",":white_large_square:",
                ":white_large_square:",":white_large_square:",":white_large_square:",
                ":white_large_square:",":white_large_square:",":white_large_square:"]
        turn = ""
        gameover = False
        cont = 0

        player1 = p1
        player2 = p2

        line = ""
        for x in range(len(board)):
            if x==2 or x==5 or x==8:
                line += " " + board[x]
                await ctx.send(line)
                line = ""
            else:
                line += " " + board[x]
        
        num = random.randint(1,2)
        if(num == 1):
            turn = player1
            await ctx.send("it is <@" + str(player1.id) + ">'s turn.")
        elif num == 2:
            turn = player2
            await ctx.send("it is <@" + str(player2.id) + ">'s turn.")
    
    else:
        await ctx.send("c'è già un game")
    

@client.command(help=".place [1-9] per selezionare la casella")
async def place(ctx, pos : int):
    global turn
    global player1
    global player2 
    global board 
    global cont 

    if not gameover:
        mark = ""
        if turn == ctx.author:
            if turn == player1:
                mark = ":regional_indicator_x:"
            elif turn == player2:
                mark = ":o2:"
            if 0<pos<10 and board[pos-1] == ":white_large_square:":
                board[pos-1] = mark
                cont += 1

                line = ""
                for x in range(len(board)):
                    if x==2 or x==5 or x==8:
                        line += " " + board[x]
                        await ctx.send(line)
                        line = ""
                    else:
                        line += " " + board[x]
                
                check(haswon, mark)
                if gameover:
                    await ctx.send(mark + " vince!")
                elif cont >= 9:
                    await ctx.send("pareggio")
                
                #cambio turni
                if turn == player1:
                    turn = player2
                elif turn == player2:
                    turn = player1



            else:
                 await ctx.send("scegli un valore tra 1 e 9")
        else:
            await ctx.send("non è il tuo turno")
    else:
        await ctx.send("comincia una nuova parita")


def check(haswon, mark):
    global gameover
    for condition in haswon:
        if board[condition[0]] == mark and board[condition[1]] == mark and board[condition[2]] == mark:
            gameover = True


@tris.error
async def tris_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("menziona 2 giocatori per giocare")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("menziona i giocatori")

@place.error
async def place_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("seleziona una casella")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("inserisci un intero")
###################################################################################################################################################################

@client.command(help="Bardo ti mostrerà quante campanelle ha raccolto") #restituisce un numero random 
async def bell(ctx):
    bel = random.randint(0,100)
    await ctx.send("ho " + str(bel) + " campanelle!")

@client.command(help = "ascolta della musica") #quando dentro ad un canale riproduce musica 
async def play(ctx,url):
    if not ctx.message.author.voice:
        await ctx.send('non sei connesso a un canale vocale')
        return

    else:
        channel = ctx.message.author.voice.channel
    
    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('errore: %s' %e) if e else None)
    



@client.command(help = "ferma la canzone")
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()


client.run(TOKEN)

