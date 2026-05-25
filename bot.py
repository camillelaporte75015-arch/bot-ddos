import discord
from discord.ext import commands
from collections import defaultdict
import time
from datetime import datetime

# ============================================================
#  CONFIG — modifie ces valeurs
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

bot = commands.Bot(command_prefix="!", intents=intents)

historique_vocaux: dict[int, list] = defaultdict(list)


def ban_reason():
    return f"Anti-raid : {config['seuil']} salons vocaux rejoints en moins de {config['fenetre']}s"


def est_owner(ctx):
    return ctx.author.id == OWNER_ID


async def envoyer_log_ban(guild: discord.Guild, member: discord.Member):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        print(f"  Salon de logs introuvable (ID: {LOG_CHANNEL_ID})")
        return

    maintenanty = datetime.now()
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
    print(f" Bot connecté en tant que {bot.user} (ID: {bot.user.id})")
    print(f"  Paramètres : {config['seuil']} vocaux / {config['fenetre']}s | Actif : {config['actif']}")


@bot.command(name="limit")
async def limit(ctx, arg: str, nombre: int = None, temps: float = None):
    if not est_owner(ctx):
        await ctx.send(" Tu n'as pas la permission d'utiliser cette commande.")
        return

    if arg.lower() == "on":
        config["actif"] = True
        historique_vocaux.clear()
        embed = discord.Embed(
            title=" Anti-Raid activé",
            description=f"Le bot surveille maintenant les vocaux.\n**Seuil :** {config['seuil']} salons en {config['fenetre']}s",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        print(f" Bot activé par {ctx.author}")

    elif arg.lower() == "off":
        config["actif"] = False
        historique_vocaux.clear()
        embed = discord.Embed(
            title=" Anti-Raid désactivé",
            description="Le bot ne surveille plus les vocaux.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        print(f" Bot désactivé par {ctx.author}")

    else:
        try:
            nombre = int(arg)
        except ValueError:
            await ctx.send(
                " Usage :\n"
                "`!limit on` — activer le bot\n"
                "`!limit off` — désactiver le bot\n"
                "`!limit <nombre> <secondes>` — configurer le seuil"
            )
            return

        if temps is None:
            await ctx.send(" Usage : `!limit <nombre> <secondes>`\nExemple : `!limit 3 6`")
            return
        if nombre < 2:
            await ctx.send(" Le nombre de salons doit être **au moins 2**.")
            return
        if temps <= 0:
            await ctx.send(" Le temps doit être **supérieur à 0**.")
            return

        config["seuil"] = nombre
        config["fenetre"] = temps
        historique_vocaux.clear()

        embed = discord.Embed(title=" Limite anti-raid mise à jour", color=discord.Color.orange())
        embed.add_field(name=" Salons vocaux", value=f"**{nombre}** salons distincts", inline=True)
        embed.add_field(name=" Fenêtre de temps", value=f"**{temps}** secondes", inline=True)
        embed.add_field(
            name=" Résultat",
            value=f"Banni si **{nombre} vocaux différents** rejoints en moins de **{temps}s**",
            inline=False
        )
        embed.set_footer(text=f"Configuré par {ctx.author}")
        await ctx.send(embed=embed)
        print(f" Limites mises à jour par {ctx.author} : {nombre} vocaux / {temps}s")


@limit.error
async def limit_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "❌ Usage :\n"
            "`!limit on` — activer\n"
            "`!limit off` — désactiver\n"
            "`!limit <nombre> <secondes>` — configurer"
        )
    else:
        await ctx.send(f"❌ Erreur : {error}")


@bot.command(name="limitinfo")
async def limitinfo(ctx):
    if not est_owner(ctx):
        await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")
        return

    statut = "✅ Actif" if config["actif"] else "⛔ Désactivé"
    embed = discord.Embed(
        title="📊 Configuration anti-raid",
        color=discord.Color.green() if config["actif"] else discord.Color.red()
    )
    embed.add_field(name="État", value=statut, inline=False)
    embed.add_field(name="🔊 Salons déclencheurs", value=f"**{config['seuil']}** salons distincts", inline=True)
    embed.add_field(name="⏱️ Fenêtre", value=f"**{config['fenetre']}** secondes", inline=True)
    await ctx.send(embed=embed)


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

    print(f" {member} → #{after.channel.name} | {nb}/{seuil} salons en {fenetre}s")

    if nb >= seuil:
        if not member.guild.me.guild_permissions.ban_members:
            print(f"⚠️  Pas la permission de bannir {member}")
            return
        if member.top_role >= member.guild.me.top_role:
            print(f"⚠️  {member} a un rôle trop élevé, impossible de bannir")
            return

        try:
            await member.ban(reason=ban_reason(), delete_message_days=0)
            print(f" BANNI : {member} ({member.id})")
            await envoyer_log_ban(member.guild, member)
        except discord.Forbidden:
            print(f" Impossible de bannir {member} : permissions insuffisantes")
        except discord.HTTPException as e:
            print(f" Erreur HTTP lors du ban de {member} : {e}")
        finally:
            historique_vocaux.pop(uid, None)


bot.run(TOKEN)
