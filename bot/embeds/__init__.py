import discord

from bot.settings import BOT_COLOR

from . import _elections as elections
from . import _parties as parties
from . import _votes as votes


def success() -> discord.Embed:
    return discord.Embed(
        title = ":white_check_mark: Opération réussie",
        color = discord.Color.brand_green()
    )

def fail(details: str = None) -> discord.Embed:
    return discord.Embed(
        title = ":x: L'opération a échoué",
        description = details,
        color = discord.Color.brand_red()
    )