from boss__init__ import criar_boss
from player import Player
from enemies import Enemy
from projectiles import (
    Bullet,
    ManchaTinta,
    Asteroid,
    PowerUp,
    Particle,
    BombShockwave,
)


def Boss(tipo, loop_nivel=1, modo_jogadores=1):
    """Fábrica compatível que instancia a subclasse OOP correspondente do chefe."""
    return criar_boss(tipo, loop_nivel=loop_nivel, modo_jogadores=modo_jogadores)


__all__ = [
    "Player",
    "Enemy",
    "Boss",
    "Asteroid",
    "PowerUp",
    "ManchaTinta",
    "Particle",
    "BombShockwave",
]