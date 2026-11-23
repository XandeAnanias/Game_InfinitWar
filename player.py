import pygame
from config import (
    VIDA_MAXIMA,
    NAVES_CONFIG,
    TIRO_RAPIDO_COOLDOWN, TIRO_RAPIDO_DANO,
    TIRO_PESADO_COOLDOWN, TIRO_PESADO_DANO,
    TIRO_TRIPLO_COOLDOWN, TIRO_TRIPLO_DANO, TIRO_TRIPLO_DURACAO,
    TIRO_BOMBA_COOLDOWN, TIRO_BOMBA_DANO_DIRETO, TIRO_BOMBA_DURACAO,
    FATOR_LENTIDAO_TINTA, FATOR_LENTIDAO_CAMPO_VERDE,
)
from projectiles import Bullet


class Player:
    """Controla a nave do jogador, atributos da classe escolhida, armas e escudo."""

    def __init__(self, player_id, x, y, sprite_key, pode_alternar_tiro=True, nave_tipo="cruzador"):
        self.id = player_id
        self.rect = pygame.Rect(x, y, 40, 40)
        self.nave_tipo = nave_tipo

        spec = NAVES_CONFIG.get(nave_tipo, NAVES_CONFIG["cruzador"])
        chave_padrao = spec["sprite_p1"] if player_id == 0 else spec["sprite_p2"]
        self.sprite_key = chave_padrao if nave_tipo in NAVES_CONFIG else sprite_key

        self.velocidade_base = float(spec.get("velocidade", 6.0))
        self.max_vidas = int(spec.get("vidas", VIDA_MAXIMA))
        self.vidas = self.max_vidas
        self.fator_recarga = float(spec.get("fator_recarga", 1.0))
        self.invencivel = 0

        self.pode_alternar_tiro = pode_alternar_tiro
        self.modo_tiro = "rapido"
        self.cooldown_tiro = 0
        self.cooldown_max = self._calc_cooldown(TIRO_RAPIDO_COOLDOWN)

        self.tempo_tiro_triplo = 0
        self.tempo_escudo = 0
        self.tempo_tiro_bomba = 0

        self.lento_tinta = False
        self.lento_campo_verde = False

    def _calc_cooldown(self, base_cd):
        return max(6, int(round(base_cd * self.fator_recarga)))

    @property
    def vivo(self):
        return self.vidas > 0

    @property
    def tem_powerup_arma_ativo(self):
        return self.tempo_tiro_triplo > 0 or self.tempo_tiro_bomba > 0

    @property
    def esta_lento(self):
        return self.tempo_escudo == 0 and (self.lento_tinta or self.lento_campo_verde)

    @property
    def velocidade_atual(self):
        if self.tempo_escudo > 0:
            return self.velocidade_base
        fator = 1.0
        if self.lento_tinta:
            fator = min(fator, FATOR_LENTIDAO_TINTA)
        if self.lento_campo_verde:
            fator = min(fator, FATOR_LENTIDAO_CAMPO_VERDE)
        return self.velocidade_base * fator

    def alternar_modo_tiro(self):
        if not self.pode_alternar_tiro:
            self.modo_tiro = "rapido"
            return
        if self.tem_powerup_arma_ativo:
            return
        self.modo_tiro = "pesado" if self.modo_tiro == "rapido" else "rapido"

    def update(self, teclas, limites_tela):
        if not self.vivo:
            return

        if self.invencivel > 0:
            self.invencivel -= 1
        if self.cooldown_tiro > 0:
            self.cooldown_tiro -= 1
        if self.tempo_tiro_triplo > 0:
            self.tempo_tiro_triplo -= 1
        if self.tempo_escudo > 0:
            self.tempo_escudo -= 1
        if self.tempo_tiro_bomba > 0:
            self.tempo_tiro_bomba -= 1

        vel = self.velocidade_atual

        if self.id == 0:
            if teclas[pygame.K_a]: self.rect.x -= vel
            if teclas[pygame.K_d]: self.rect.x += vel
            if teclas[pygame.K_w] and self.rect.top > 55: self.rect.y -= vel
            if teclas[pygame.K_s]: self.rect.y += vel
        else:
            if teclas[pygame.K_LEFT]: self.rect.x -= vel
            if teclas[pygame.K_RIGHT]: self.rect.x += vel
            if teclas[pygame.K_UP] and self.rect.top > 55: self.rect.y -= vel
            if teclas[pygame.K_DOWN]: self.rect.y += vel

        self.rect.clamp_ip(limites_tela)

    def atirar(self, tiros_aliados, assets):
        if not self.vivo or self.cooldown_tiro > 0:
            return

        cx, top = self.rect.centerx, self.rect.top

        if self.tempo_tiro_triplo > 0:
            self.cooldown_max = self._calc_cooldown(TIRO_TRIPLO_COOLDOWN)
            self.cooldown_tiro = self.cooldown_max
            tiros_aliados.append(Bullet(cx - 2, top - 10, 0, -11, "player", "triplo", dano=TIRO_TRIPLO_DANO))
            tiros_aliados.append(Bullet(self.rect.left + 2, top - 6, -2.8, -11, "player", "triplo", dano=TIRO_TRIPLO_DANO))
            tiros_aliados.append(Bullet(self.rect.right - 6, top - 6, 2.8, -11, "player", "triplo", dano=TIRO_TRIPLO_DANO))
            assets.tocar_som("tiro_triplo")
        elif self.tempo_tiro_bomba > 0:
            self.cooldown_max = self._calc_cooldown(TIRO_BOMBA_COOLDOWN)
            self.cooldown_tiro = self.cooldown_max
            tiros_aliados.append(Bullet(cx - 5, top - 12, 0, -5.5, "player", "bomba", tempo=95, dano=TIRO_BOMBA_DANO_DIRETO))
            assets.tocar_som("tiro")
        elif self.modo_tiro == "pesado":
            self.cooldown_max = self._calc_cooldown(TIRO_PESADO_COOLDOWN)
            self.cooldown_tiro = self.cooldown_max
            tiros_aliados.append(Bullet(cx - 5, top - 16, 0, -8.5, "player", "pesado", dano=TIRO_PESADO_DANO))
            assets.tocar_som("tiro")
        else:
            self.cooldown_max = self._calc_cooldown(TIRO_RAPIDO_COOLDOWN)
            self.cooldown_tiro = self.cooldown_max
            tiros_aliados.append(Bullet(cx - 2, top - 10, 0, -11.5, "player", "normal", dano=TIRO_RAPIDO_DANO))
            assets.tocar_som("tiro")

    def receber_dano(self, assets):
        if self.invencivel > 0 or not self.vivo:
            return False
        self.vidas -= 1
        self.invencivel = 120
        assets.tocar_som("morte" if self.vidas <= 0 else "dano")
        return True

    def aplicar_poder(self, tipo, assets=None):
        if tipo == "tiro_triplo":
            self.tempo_tiro_triplo = TIRO_TRIPLO_DURACAO
            self.tempo_tiro_bomba = 0
            if assets:
                assets.tocar_som("powerup")
        elif tipo == "escudo":
            self.tempo_escudo = 360
            self.lento_tinta = False
            self.lento_campo_verde = False
            if assets:
                assets.tocar_som("powerup")
        elif tipo == "bomba":
            self.tempo_tiro_bomba = TIRO_BOMBA_DURACAO
            self.tempo_tiro_triplo = 0
            if assets:
                assets.tocar_som("powerup")
        elif tipo == "cura":
            self.vidas = min(self.max_vidas, self.vidas + 1)
            if assets:
                assets.tocar_som("cura")

    def draw(self, tela, assets, mostrar_tag=False):
        if not self.vivo:
            return

        if self.esta_lento:
            cor_lento = (180, 80, 255) if self.lento_tinta else (50, 255, 160)
            pygame.draw.circle(tela, cor_lento, self.rect.center, 29, 2)

        if self.invencivel == 0 or (self.invencivel // 6) % 2 == 0:
            par = assets.sprites.get(self.sprite_key) or assets.sprites.get("nave_p1")
            if par:
                img, _ = par
                tela.blit(img, img.get_rect(center=self.rect.center))
            if mostrar_tag:
                cor_tag = (100, 255, 180) if self.id == 0 else (100, 200, 255)
                tag = assets.fontes["pequena"].render(f"P{self.id + 1}", True, cor_tag)
                tela.blit(tag, (self.rect.centerx - tag.get_width() // 2, self.rect.bottom + 2))

        if self.tempo_escudo > 0:
            if self.tempo_escudo > 60 or (self.tempo_escudo // 5) % 2 == 0:
                pygame.draw.circle(tela, (0, 255, 140), self.rect.center, 32, 2)