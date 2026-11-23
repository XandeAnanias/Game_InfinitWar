import pygame
import random
import math
from config import LARGURA, ALTURA, LULA_TINTA_DURACAO_POCA


class Bullet:
    """Projéteis de jogadores, inimigos comuns e chefes."""

    def __init__(self, x, y, vx, vy, owner="player", tipo="normal", tempo=0, dano=1, y_explosao=None):
        if tipo == "bomba":
            w, h = 12, 12
        elif tipo == "pesado":
            w, h = 10, 22
        elif tipo == "canhao_boss":
            w, h = 18, 28
        elif tipo == "tinta":
            w, h = 16, 16
        elif tipo == "esporo":
            w, h = 14, 14
        elif tipo == "raio_gemeo":
            w, h = 10, 18
        elif tipo == "orbe_olho":
            w, h = 10, 10
        elif owner == "enemy":
            w, h = 6, 16
        else:
            w, h = 4, 14

        self.rect = pygame.Rect(x, y, w, h)
        self.vx = vx
        self.vy = vy
        self.owner = owner
        self.tipo = tipo
        self.tempo = tempo
        self.dano = dano
        # Altura Y em que o projétil de tinta da Lula explode no cenário
        self.y_explosao = y_explosao
        self.anim_t = random.uniform(0, math.pi * 2)

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.anim_t += 0.25
        if self.tipo == "bomba":
            self.tempo -= 1

    def atingiu_ponto_explosao_tinta(self):
        """Retorna True quando a bola roxa da Lula chega ao ponto de detonar."""
        return (
            self.tipo == "tinta"
            and self.y_explosao is not None
            and self.rect.centery >= self.y_explosao
        )

    def fora_da_tela(self):
        return (
            self.rect.bottom < -40
            or self.rect.top > ALTURA + 40
            or self.rect.right < -40
            or self.rect.left > LARGURA + 40
        )

    def draw(self, tela):
        if self.tipo == "tinta":
            pulso = int(math.sin(self.anim_t) * 2)
            pygame.draw.circle(tela, (65, 20, 115), self.rect.center, 9 + pulso)
            pygame.draw.circle(tela, (175, 75, 245), self.rect.center, 9 + pulso, 2)
            pygame.draw.circle(tela, (230, 160, 255), (self.rect.centerx - 2, self.rect.centery - 2), 3)
        elif self.tipo == "esporo":
            pulso = int(math.sin(self.anim_t) * 2)
            pygame.draw.circle(tela, (42, 130, 32), self.rect.center, 8 + pulso)
            pygame.draw.circle(tela, (145, 245, 75), self.rect.center, 6 + pulso, 2)
            pygame.draw.circle(tela, (235, 255, 160), self.rect.center, 3)
        elif self.tipo == "raio_gemeo":
            pygame.draw.rect(tela, (40, 210, 255), self.rect, border_radius=4)
            pygame.draw.rect(tela, (240, 130, 255), self.rect.inflate(-3, -4), border_radius=3)
            pygame.draw.rect(tela, (255, 255, 255), self.rect.inflate(-6, -8), border_radius=2)
        elif self.tipo == "orbe_olho":
            pygame.draw.circle(tela, (255, 50, 50), self.rect.center, 6)
            pygame.draw.circle(tela, (255, 220, 120), self.rect.center, 3)
        elif self.tipo == "canhao_boss":
            cx, cy = self.rect.center
            pygame.draw.circle(tela, (170, 18, 42), (cx, cy), 12)
            pygame.draw.circle(tela, (255, 55, 80), (cx, cy), 9)
            pygame.draw.circle(tela, (255, 225, 230), (cx, cy), 4)
        elif self.owner == "enemy":
            pygame.draw.rect(tela, (255, 70, 40), self.rect, border_radius=3)
            pygame.draw.rect(tela, (255, 220, 120), self.rect.inflate(-2, -4), border_radius=2)
        elif self.tipo == "bomba":
            pygame.draw.circle(tela, (255, 90, 20), self.rect.center, 7)
            pygame.draw.circle(tela, (255, 230, 80), self.rect.center, 3)
        elif self.tipo == "pesado":
            pygame.draw.rect(tela, (255, 110, 40), self.rect, border_radius=4)
            pygame.draw.rect(tela, (255, 240, 180), self.rect.inflate(-4, -6), border_radius=2)
        else:
            cor = (0, 255, 255) if self.tipo == "triplo" else (255, 255, 60)
            pygame.draw.rect(tela, cor, self.rect, border_radius=2)


class ManchaTinta:
    """Poça de tinta criada quando o projétil roxo da Lula explode. Deixa a nave lenta."""

    def __init__(self, x, y, assets, duracao=LULA_TINTA_DURACAO_POCA):
        self.surf = assets.criar_mancha_tinta()
        self.rect = self.surf.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(0, 0, 145, 145)
        self.hitbox.center = (x, y)
        self.vida = duracao
        self.vida_max = duracao

    def update(self):
        self.vida -= 1
        self.rect.y += 1
        self.hitbox.center = self.rect.center

    def contem_nave(self, player_rect):
        return self.hitbox.colliderect(player_rect)

    def draw(self, tela):
        alpha = min(225, int((self.vida / max(1, self.vida_max)) * 240))
        self.surf.set_alpha(alpha)
        tela.blit(self.surf, self.rect)


class Asteroid:
    """Obstáculo indestrutível por tiros comuns que serve como cobertura."""

    def __init__(self, x, raio, assets):
        self.raio = raio
        self.surf = assets.criar_textura_asteroide(raio)
        self.rect = pygame.Rect(x, -raio * 2, int(raio * 1.8), int(raio * 1.8))
        self.vy = random.uniform(3.5, 5.0)

    def update(self):
        self.rect.y += self.vy

    def draw(self, tela):
        tela.blit(self.surf, self.surf.get_rect(center=self.rect.center))


class PowerUp:
    """Itens coletáveis dropados por inimigos e chefes."""

    CORES = {
        "tiro_triplo": ((16, 48, 86), (0, 235, 255)),
        "escudo":      ((14, 58, 36), (55, 245, 135)),
        "bomba":       ((68, 26, 18), (255, 175, 45)),
    }

    def __init__(self, x, y, tipo):
        self.rect = pygame.Rect(x - 18, y - 18, 36, 36)
        self.tipo = tipo
        self.vy = 2.8
        self.anim_t = 0.0

    def update(self):
        self.rect.y += self.vy
        self.anim_t += 0.16

    def draw(self, tela, assets):
        if self.tipo == "cura":
            tela.blit(assets.coracao_cheio, assets.coracao_cheio.get_rect(center=self.rect.center))
            return

        fundo, borda = self.CORES[self.tipo]
        c = self.rect.center
        pulso = int(math.sin(self.anim_t) * 2)

        badge = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.circle(badge, (*borda, 45), (22, 22), 19 + pulso)
        pygame.draw.circle(badge, (*fundo, 215), (22, 22), 17)
        pygame.draw.circle(badge, (*borda, 255), (22, 22), 17, 2)
        tela.blit(badge, badge.get_rect(center=c))

        icone = assets.icones_poder.get(self.tipo)
        if icone:
            tela.blit(icone, icone.get_rect(center=c))


class Particle:
    def __init__(self, x, y, cor, vel_max=3.5):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-vel_max, vel_max)
        self.vy = random.uniform(-vel_max, vel_max)
        self.vida = random.randint(15, 28)
        self.cor = cor

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vida -= 1

    def draw(self, tela):
        pygame.draw.rect(tela, self.cor, (int(self.x), int(self.y), 3, 3))


class BombShockwave:
    def __init__(self, x, y, raio=85, cor=(255, 140, 30)):
        self.x = x
        self.y = y
        self.raio = raio
        self.vida = 15
        self.cor = cor

    def update(self):
        self.vida -= 1

    def draw(self, tela):
        pygame.draw.circle(tela, self.cor, (self.x, self.y), self.raio, 3)