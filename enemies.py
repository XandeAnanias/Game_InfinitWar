import os
import math
import random
import pygame
from config import (
    LARGURA,
    IMAGES_DIR,
    INIMIGO_TIRO_COOLDOWN_BASE,
    INIMIGO_TIRO_COOLDOWN_MIN,
    INIMIGO_TIRO_DELAY_INICIAL,
)
from projectiles import Bullet

_CACHE_ABELHA = None


def obter_sprite_abelha():
    """Gera o sprite de abelha estilo Pokémon (Beedrill/Vespiquen) e salva PNG se não existir."""
    global _CACHE_ABELHA
    if _CACHE_ABELHA is not None:
        return _CACHE_ABELHA

    w, h = 52, 48
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2

    cor_ouro = (252, 198, 36)
    cor_ouro_escuro = (205, 138, 16)
    cor_preto = (24, 20, 22)
    cor_borda_clara = (255, 236, 140)
    cor_ferrao = (240, 245, 255)
    cor_olho = (238, 28, 46)

    # Antenas
    pygame.draw.lines(surf, cor_ouro, False, [(cx - 4, 10), (cx - 9, 4), (cx - 14, 3)], 2)
    pygame.draw.lines(surf, cor_ouro, False, [(cx + 4, 10), (cx + 9, 4), (cx + 14, 3)], 2)

    # Lanças duplas nos braços (estilo Beedrill)
    lanca_esq = [(cx - 10, 18), (2, 35), (cx - 11, 27)]
    lanca_dir = [(cx + 10, 18), (w - 2, 35), (cx + 11, 27)]
    pygame.draw.polygon(surf, cor_ferrao, lanca_esq)
    pygame.draw.polygon(surf, cor_preto, lanca_esq, 2)
    pygame.draw.polygon(surf, cor_ferrao, lanca_dir)
    pygame.draw.polygon(surf, cor_preto, lanca_dir, 2)

    # Abdômen blindado e listrado
    abd_rect = pygame.Rect(cx - 11, 22, 22, 20)
    pygame.draw.ellipse(surf, cor_ouro, abd_rect)
    pygame.draw.rect(surf, cor_preto, (cx - 10, 26, 20, 4), border_radius=2)
    pygame.draw.rect(surf, cor_preto, (cx - 9, 33, 18, 4), border_radius=2)
    pygame.draw.ellipse(surf, cor_borda_clara, abd_rect, 1)

    # Ferrão inferior
    ferrao_baixo = [(cx - 4, 40), (cx + 4, 40), (cx, 47)]
    pygame.draw.polygon(surf, cor_ferrao, ferrao_baixo)
    pygame.draw.polygon(surf, cor_preto, ferrao_baixo, 1)

    # Tórax
    torax_rect = pygame.Rect(cx - 10, 13, 20, 13)
    pygame.draw.ellipse(surf, cor_preto, torax_rect)
    pygame.draw.ellipse(surf, cor_ouro_escuro, torax_rect.inflate(-4, -4))
    pygame.draw.ellipse(surf, cor_ouro, torax_rect, 1)

    # Cabeça + gema frontal (estilo Vespiquen)
    cabeca_rect = pygame.Rect(cx - 9, 6, 18, 12)
    pygame.draw.ellipse(surf, cor_ouro, cabeca_rect)
    pygame.draw.ellipse(surf, cor_preto, cabeca_rect, 2)
    pygame.draw.polygon(surf, cor_olho, [(cx, 7), (cx + 2, 9), (cx, 11), (cx - 2, 9)])

    # Olhos compostos vermelhos angulares
    olho_esq = [(cx - 8, 10), (cx - 2, 12), (cx - 3, 15), (cx - 8, 13)]
    olho_dir = [(cx + 8, 10), (cx + 2, 12), (cx + 3, 15), (cx + 8, 13)]
    pygame.draw.polygon(surf, cor_olho, olho_esq)
    pygame.draw.polygon(surf, cor_olho, olho_dir)
    pygame.draw.circle(surf, (255, 200, 200), (cx - 5, 12), 1)
    pygame.draw.circle(surf, (255, 200, 200), (cx + 5, 12), 1)

    caminho_png = os.path.join(IMAGES_DIR, "inimigo_abelha.png")
    if os.path.isdir(IMAGES_DIR):
        try:
            pygame.image.save(surf, caminho_png)
        except Exception:
            pass

    mask = pygame.mask.from_surface(surf).to_surface(
        setcolor=(255, 255, 255, 190),
        unsetcolor=(0, 0, 0, 0),
    )
    _CACHE_ABELHA = (surf, mask)
    return _CACHE_ABELHA


class Enemy:
    def __init__(
        self,
        x,
        tipo="normal",
        tamanho_idx=1,
        especial=False,
        multiplicador=1.0,
        vx_custom=None,
        vy_custom=None,
    ):
        self.tipo = tipo
        self.tamanho_idx = tamanho_idx
        self.especial = especial
        self.flash = 0
        self.anim_t = random.uniform(0, math.tau)
        self.cooldown_tiro = 0
        self.emergindo = 0
        self.emergindo_max = 0
        self.emergindo_vx = 0.0

        if self.tipo == "atirador":
            self.sprite_key = "inimigo_atirador"
            w, h = 47, 47
            self.vida = round(3.0 * multiplicador, 2)
            self.pontos = 150
            self.vx = vx_custom if vx_custom is not None else random.choice([-1.5, 1.5])
            self.vy = vy_custom if vy_custom is not None else 2.2 * min(1.45, 0.9 + multiplicador * 0.12)
            self.cooldown_tiro = random.randint(*INIMIGO_TIRO_DELAY_INICIAL)
            self.cd_tiro_max = max(INIMIGO_TIRO_COOLDOWN_MIN, int(INIMIGO_TIRO_COOLDOWN_BASE / max(1.0, multiplicador * 0.9)))

        elif self.tipo == "morcego":
            self.sprite_key = "inimigo_morcego"
            w, h = 46, 30
            self.vida = round(2.0 * multiplicador, 2)
            self.pontos = 120
            self.vx = vx_custom if vx_custom is not None else random.choice([-2.2, 2.2])
            self.vy = vy_custom if vy_custom is not None else 4.2

        elif self.tipo == "peixe":
            self.sprite_key = "inimigo_peixe"
            w, h = 46, 38
            self.vida = round(1.25 * multiplicador, 2)
            self.pontos = 130
            self.vx = vx_custom if vx_custom is not None else random.choice([-2.4, 2.4])
            self.vy = vy_custom if vy_custom is not None else 3.5

        elif self.tipo == "abelha":
            self.sprite_key = "inimigo_abelha"
            w, h = 52, 48
            self.vida = round(2.25 * multiplicador, 2)
            self.pontos = 180
            self.vx = vx_custom if vx_custom is not None else random.choice([-1.4, 1.4])
            self.vy = vy_custom if vy_custom is not None else 3.2
            self.cooldown_tiro = random.randint(42, 72)
            self.anim_asa = random.uniform(0, math.tau)

        else:
            idx = max(1, min(3, int(tamanho_idx)))
            self.sprite_key = f"inimigo_{idx}"
            tamanhos = {
                1: (36, 36, 1.0, 100, 3.3),
                2: (44, 44, 2.0, 140, 2.7),
                3: (54, 54, 4.0, 200, 2.1),
            }
            w, h, vida_base, pts_base, vel_base = tamanhos[idx]
            self.vida = round(vida_base * multiplicador, 2)
            self.pontos = pts_base
            self.vx = vx_custom if vx_custom is not None else 0.0
            self.vy = vy_custom if vy_custom is not None else vel_base * min(1.55, 0.88 + multiplicador * 0.14)

        self.x_float = float(x)
        self.y_float = float(-h)
        self.rect = pygame.Rect(int(self.x_float), int(self.y_float), w, h)

    def iniciar_emergencia(self, duracao=30, offset_x=0.0):
        self.emergindo = int(duracao)
        self.emergindo_max = max(1, int(duracao))
        self.emergindo_vx = float(offset_x) / float(self.emergindo_max)

    def update(self, tiros_inimigos):
        self.anim_t += 0.12
        if self.flash > 0:
            self.flash -= 1

        if self.tipo == "abelha":
            if self.emergindo > 0:
                self.emergindo -= 1
                self.anim_asa = getattr(self, "anim_asa", 0.0) + 0.95
                self.x_float += self.emergindo_vx
                self.y_float += 0.45
                self.rect.x = int(round(self.x_float))
                self.rect.y = int(round(self.y_float))

                if self.rect.left <= 16:
                    self.rect.left = 16
                    self.x_float = float(self.rect.x)
                elif self.rect.right >= LARGURA - 16:
                    self.rect.right = LARGURA - 16
                    self.x_float = float(self.rect.x)
                return

            self.anim_asa = getattr(self, "anim_asa", 0.0) + 0.65
            self.x_float += self.vx + math.sin(self.anim_asa * 0.22) * 2.2
            self.y_float += self.vy
            self.rect.x = int(round(self.x_float))
            self.rect.y = int(round(self.y_float))
            if self.cooldown_tiro > 0:
                self.cooldown_tiro -= 1
                if self.cooldown_tiro == 0:
                    tiros_inimigos.append(
                        Bullet(self.rect.centerx - 4, self.rect.bottom - 4, 0.0, 6.2, owner="enemy", tipo="esporo")
                    )
            return

        if self.tipo == "morcego":
            self.x_float += self.vx + math.sin(self.anim_t * 1.4) * 1.6
            self.y_float += self.vy
        elif self.tipo == "peixe":
            self.x_float += self.vx + math.cos(self.anim_t * 1.2) * 1.8
            self.y_float += self.vy
        elif self.tipo == "atirador":
            self.x_float += self.vx
            self.y_float += self.vy
            if self.cooldown_tiro > 0:
                self.cooldown_tiro -= 1
                if self.cooldown_tiro == 0:
                    self.cooldown_tiro = getattr(self, "cd_tiro_max", INIMIGO_TIRO_COOLDOWN_BASE)
                    tiros_inimigos.append(
                        Bullet(self.rect.centerx - 3, self.rect.bottom, 0.0, 5.6, owner="enemy")
                    )
        else:
            self.x_float += self.vx
            self.y_float += self.vy

        self.rect.x = int(round(self.x_float))
        self.rect.y = int(round(self.y_float))

        if self.vx != 0:
            if self.rect.left <= 14:
                self.rect.left = 14
                self.x_float = float(self.rect.x)
                self.vx = abs(self.vx)
            elif self.rect.right >= LARGURA - 14:
                self.rect.right = LARGURA - 14
                self.x_float = float(self.rect.x)
                self.vx = -abs(self.vx)

    def draw(self, tela, assets):
        if self.tipo == "abelha":
            self.anim_asa = getattr(self, "anim_asa", 0.0) + 0.45
            cx, cy = self.rect.centerx, self.rect.centery - 4
            bater = math.sin(self.anim_asa) * 5

            asa_sup_esq = [(cx - 6, cy), (cx - 25, int(cy - 11 + bater)), (cx - 22, int(cy + 3 + bater * 0.5))]
            asa_sup_dir = [(cx + 6, cy), (cx + 25, int(cy - 11 + bater)), (cx + 22, int(cy + 3 + bater * 0.5))]
            asa_inf_esq = [(cx - 5, cy + 3), (cx - 19, int(cy + 4 - bater * 0.6)), (cx - 15, int(cy + 11 - bater * 0.4))]
            asa_inf_dir = [(cx + 5, cy + 3), (cx + 19, int(cy + 4 - bater * 0.6)), (cx + 15, int(cy + 11 - bater * 0.4))]

            for asa in (asa_sup_esq, asa_sup_dir, asa_inf_esq, asa_inf_dir):
                pygame.draw.polygon(tela, (205, 240, 255), asa)
                pygame.draw.polygon(tela, (95, 145, 185), asa, 1)

            par = obter_sprite_abelha()
            assets.sprites["inimigo_abelha"] = par
            img, mask = par

            if self.emergindo > 0:
                prog = 1.0 - (self.emergindo / float(max(1, self.emergindo_max)))
                escala = 0.55 + 0.45 * prog
                novo_w = max(12, int(img.get_width() * escala))
                novo_h = max(12, int(img.get_height() * escala))
                img_esc = pygame.transform.smoothscale(img, (novo_w, novo_h))
                tela.blit(img_esc, img_esc.get_rect(center=self.rect.center))
                pygame.draw.circle(tela, (255, 215, 95), self.rect.center, int(14 + prog * 14), 2)
                if self.flash > 0:
                    mask_esc = pygame.transform.smoothscale(mask, (novo_w, novo_h))
                    tela.blit(mask_esc, mask_esc.get_rect(center=self.rect.center))
                return

            tela.blit(img, img.get_rect(center=self.rect.center))
            if self.flash > 0:
                tela.blit(mask, mask.get_rect(center=self.rect.center))
            return

        if self.especial:
            pulso = int(math.sin(self.anim_t * 2.0) * 3)
            pygame.draw.circle(tela, (255, 215, 70), self.rect.center, max(self.rect.width, self.rect.height) // 2 + 4 + pulso, 2)

        par = assets.sprites.get(self.sprite_key)
        if par:
            img, mask = par
            tela.blit(img, img.get_rect(center=self.rect.center))
            if self.flash > 0:
                tela.blit(mask, mask.get_rect(center=self.rect.center))
        else:
            cor = (255, 210, 75) if self.especial else (220, 75, 85)
            pygame.draw.rect(tela, cor, self.rect, border_radius=6)