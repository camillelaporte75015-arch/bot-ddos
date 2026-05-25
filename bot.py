import discord
from discord.ext import commands
from collections import defaultdict
import time
from datetime import datetime

# ============================================================
#  CONFIG
# ============================================================
TOKEN = "TON_TOKEN_ICI"

OWNER_ID = 1507830698743038122
LOG_CHANNEL_ID = 1508323846636306594
# ============================================================

config = {
    "seuil": 3,
    "fenetre": 6.0,
    "actif": True,
}

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

historique_vocaux: dict[int, list] = defaultdict(list)


def ban_reason():
    return f"Anti-raid : {config['seuil']} salons vocaux rejoints en moins de {config['fenetre']}s"


def est_owner(ctx):
    return ctx.author.id == OWNER_ID


async def envoyer_log_ban(guild: discord.Guild, member: discord.Member):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        print(f"Salon de logs introuvable (ID: {LOG_CHANNEL_ID})")
        return

    maintenant = datetime.now()
    heure = maintenant.strftime("%H:%M:%S")
    date = maintenant.strftime("%d/%m/%Y")

    embed = discord.Embed(title="🚨 DÉTECTION DDOS", color=0xFF0000)
    embed.add_field(
        name="\u200b",
        value=(
            f"**{member.name}** / (`{member.id}`) à tenté de ddos, il a été banni.\n"
            f"**Heure :** {heure}\n"
            f"**Date :** {date}"
        ),
        inline=False
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Système Anti-Raid")
    await channel.send(embed=embed)


@bot.event
async def on_ready():
    print(f"Bot connecte en tant que {bot.user} (ID: {bot.user.id})")
    print(f"Parametres : {config['seuil']} vocaux / {config['fenetre']}s | Actif : {config['actif']}")


# ============================================================
#  COMMANDE !play
# ============================================================
@bot.command(name="play")
async def play(ctx, *, activite: str):
    if not est_owner(ctx):
        await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")
        return

    await bot.change_presence(activity=discord.Game(name=activite))
    await ctx.send(f"je joue maintenant a {activite}")


@play.error
async def play_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage : !play <activite>")


# ============================================================
#  COMMANDE !limit
# ============================================================
@bot.command(name="limit")
async def limit(ctx, arg: str, nombre: int = None, temps: float = None):
    if not est_owner(ctx):
        await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")
        return

    if arg.lower() == "on":
        config["actif"] = True
        historique_vocaux.clear()
        await ctx.send(f"Anti-Raid active. Seuil : {config['seuil']} salons en {config['fenetre']}s")

    elif arg.lower() == "off":
        config["actif"] = False
        historique_vocaux.clear()
        await ctx.send("Anti-Raid desactive.")

    else:
        try:
            nombre = int(arg)
        except ValueError:
            await ctx.send("Usage : !limit on / !limit off / !limit <nombre> <secondes>")
            return

        if temps is None:
            await ctx.send("Usage : !limit <nombre> <secondes>")
            return
        if nombre < 2:
            await ctx.send("Le nombre de salons doit etre au moins 2.")
            return
        if temps <= 0:
            await ctx.send("Le temps doit etre superieur a 0.")
            return

        config["seuil"] = nombre
        config["fenetre"] = temps
        historique_vocaux.clear()
        await ctx.send(f"Limite mise a jour : {nombre} vocaux en {temps}s")


@limit.error
async def limit_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage : !limit on / !limit off / !limit <nombre> <secondes>")
    else:
        await ctx.send(f"Erreur : {error}")


# ============================================================
#  COMMANDE !limitinfo
# ============================================================
@bot.command(name="limitinfo")
async def limitinfo(ctx):
    if not est_owner(ctx):
        await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")
        return

    statut = "Actif" if config["actif"] else "Desactive"
    await ctx.send(
        f"Etat : {statut}\n"
        f"Salons declencheurs : {config['seuil']}\n"
        f"Fenetre : {config['fenetre']}s"
    )


# ============================================================
#  DETECTION VOCALE
# ============================================================
@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return
    if not config["actif"]:
        return
    if after.channel is None:
        return
    if before.channel == after.channel:
        return

    maintenant = time.monotonic()
    uid = member.id
    seuil = config["seuil"]
    fenetre = config["fenetre"]

    historique_vocaux[uid].append((maintenant, after.channel.id))
    historique_vocaux[uid] = [
        (ts, ch) for ts, ch in historique_vocaux[uid]
        if maintenant - ts <= fenetre
    ]

    salons_distincts = {ch for _, ch in historique_vocaux[uid]}
    nb = len(salons_distincts)

    print(f"{member} -> #{after.channel.name} | {nb}/{seuil} salons en {fenetre}s")

    if nb >= seuil:
        if not member.guild.me.guild_permissions.ban_members:
            print(f"Pas la permission de bannir {member}")
            return
        if member.top_role >= member.guild.me.top_role:
            print(f"{member} a un role trop eleve, impossible de bannir")
            return

        try:
            await member.ban(reason=ban_reason(), delete_message_days=0)
            print(f"BANNI : {member} ({member.id})")
            await envoyer_log_ban(member.guild, member)
        except discord.Forbidden:
            print(f"Impossible de bannir {member} : permissions insuffisantes")
        except discord.HTTPException as e:
            print(f"Erreur HTTP lors du ban de {member} : {e}")
        finally:
            historique_vocaux.pop(uid, None)


bot.run(TOKEN)
