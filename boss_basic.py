import math
import random
import pygame
from config import LARGURA, ALTURA, SPRITES_CONFIG


class BossBase:
    """
    Classe base para todos os chefes.
    Gerencia entrada cinematográfica, combate e animação de derrota.
    """

    TIPO = "base"
    NOME_EXIBICAO = "CHEFE"
    SUBTITULO_ENTRADA = "SETOR HOSTIL"
    SPRITE_KEY = "boss_final"
    VIDA_BASE = 200
    VELOCIDADE_BASE = 2.8
    Y_COMBATE = 75
    DURACAO_ENTRADA = 115  # ~1.9s descendo suavemente do topo
    DURACAO_DERROTA = 135  # ~2.25s de animação de derrota

    def __init__(self, loop_nivel=1, modo_jogadores=1):
        self.tipo = self.TIPO
        self.nome = self.NOME_EXIBICAO
        self.subtitulo = self.SUBTITULO_ENTRADA
        self.loop_nivel = max(1, int(loop_nivel))
        self.modo_jogadores = modo_jogadores

        vida_base = self._calcular_vida_base(modo_jogadores)
        fator_loop = 1.0 + (self.loop_nivel - 1) * 0.35
        self.max_vida = round(vida_base * fator_loop, 1)
        self.vida_max = self.max_vida
        self.vida = self.max_vida

        w, h = SPRITES_CONFIG.get(self.SPRITE_KEY, {"tamanho": (160, 160)})["tamanho"]
        self.y_inicial_entrada = -float(h) - 24.0
        self.y_combate = float(self.Y_COMBATE)
        self.y_float = self.y_inicial_entrada

        self.rect = pygame.Rect(LARGURA // 2 - w // 2, int(self.y_float), w, h)
        self.vx = self.VELOCIDADE_BASE
        self.timer = 0
        self.timer_entrada = 0
        self.timer_derrota = 0
        self.anim_t = 0.0
        self.flash = 0
        self.lasers = []
        self.shake_request = 0
        self.ignorar_hitbox_principal = False

        self.derrotado = False
        self.derrota_concluida = False
        self.particulas_derrota = []
        self.derrota_ang = 0.0
        self.derrota_vx = 0.0
        self.derrota_vy = 0.0
        self.derrota_rot_vel = 0.0

        self.estado = "entrando"
        self.on_init_combate()

    def _calcular_vida_base(self, modo_jogadores):
        return self.VIDA_BASE

    def on_init_combate(self):
        """Sobrescreva nas subclasses para inicializar variáveis do chefe."""
        pass

    def estado_inicial_combate(self):
        return "combate"

    def ao_concluir_entrada(self):
        """Chamado no exato frame em que o boss termina de descer e inicia a luta."""
        pass

    @property
    def invulneravel(self):
        return self.estado in ("entrando", "derrotado")

    @property
    def em_furia(self):
        return self.vida <= self.max_vida * 0.5

    @property
    def progresso_entrada(self):
        return min(1.0, self.timer_entrada / float(max(1, self.DURACAO_ENTRADA)))

    @property
    def progresso_derrota(self):
        return min(1.0, self.timer_derrota / float(max(1, self.DURACAO_DERROTA)))

    # ------------------------------------------------------------------
    # Sistema de Derrota Cinematográfica
    # ------------------------------------------------------------------
    def iniciar_derrota(self, assets):
        if self.derrotado:
            return
        self.derrotado = True
        self.derrota_concluida = False
        self.estado = "derrotado"
        self.timer_derrota = 0
        self.lasers.clear()
        self.flash = 10
        self.shake_request = 12
        assets.tocar_som("explosao")
        self.on_iniciar_derrota(assets)

    def on_iniciar_derrota(self, assets):
        """Comportamento padrão: pega fogo, inclina e cai fora da tela."""
        lado = 1 if self.rect.centerx < LARGURA // 2 else -1
        self.derrota_vx = lado * 1.35
        self.derrota_vy = -0.9
        self.derrota_rot_vel = -lado * 0.52
        self._emitir_explosao_derrota(self.rect.centerx, self.rect.centery, qtd=22)

    def _emitir_fumaca_derrota(self, x, y, qtd=2, escala=1.0):
        for _ in range(qtd):
            tom = random.randint(42, 95)
            self.particulas_derrota.append({
                "x": float(x + random.uniform(-14, 14)),
                "y": float(y + random.uniform(-10, 10)),
                "vx": random.uniform(-1.1, 1.1),
                "vy": random.uniform(-2.6, -0.9),
                "vida": random.randint(24, 42),
                "max_vida": 42,
                "raio": random.uniform(7.0, 13.0) * escala,
                "crescimento": 0.28 * escala,
                "cor": (tom, tom, tom + 6),
                "tipo": "fumaca",
            })

    def _emitir_fogo_derrota(self, x, y, qtd=4, escala=1.0):
        paleta = [(255, 235, 110), (255, 155, 35), (245, 70, 25)]
        for _ in range(qtd):
            self.particulas_derrota.append({
                "x": float(x + random.uniform(-16, 16)),
                "y": float(y + random.uniform(-12, 12)),
                "vx": random.uniform(-1.6, 1.6),
                "vy": random.uniform(-3.4, -1.1),
                "vida": random.randint(14, 26),
                "max_vida": 26,
                "raio": random.uniform(5.0, 10.0) * escala,
                "crescimento": -0.14 * escala,
                "cor": random.choice(paleta),
                "tipo": "fogo",
            })

    def _emitir_explosao_derrota(self, x, y, paleta=None, qtd=18):
        cores = paleta or [(255, 245, 175), (255, 185, 55), (255, 95, 35), (220, 45, 45)]
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            vel = random.uniform(1.8, 6.8)
            self.particulas_derrota.append({
                "x": float(x),
                "y": float(y),
                "vx": math.cos(ang) * vel,
                "vy": math.sin(ang) * vel,
                "vida": random.randint(18, 34),
                "max_vida": 34,
                "raio": random.uniform(4.0, 9.0),
                "crescimento": -0.12,
                "cor": random.choice(cores),
                "tipo": "faisca",
            })

    def _atualizar_particulas_derrota(self):
        for pt in self.particulas_derrota[:]:
            pt["x"] += pt["vx"]
            pt["y"] += pt["vy"]
            pt["raio"] = max(1.0, pt["raio"] + pt.get("crescimento", 0.0))
            pt["vida"] -= 1
            if pt["vida"] <= 0:
                self.particulas_derrota.remove(pt)

    def _desenhar_particulas_derrota(self, tela):
        for pt in self.particulas_derrota:
            raio = int(pt["raio"])
            if raio <= 0:
                continue
            if pt.get("tipo") == "fumaca":
                alpha = int(175 * (pt["vida"] / float(max(1, pt["max_vida"]))))
                s = pygame.Surface((raio * 2 + 2, raio * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*pt["cor"], max(0, min(255, alpha))), (raio + 1, raio + 1), raio)
                tela.blit(s, (int(pt["x"] - raio - 1), int(pt["y"] - raio - 1)))
            else:
                pygame.draw.circle(tela, pt["cor"], (int(pt["x"]), int(pt["y"])), raio)

    def update_derrota(self, players, inimigos, tiros_inimigos, assets):
        """Animação padrão de derrota caso a subclasse não sobrescreva."""
        t = self.timer_derrota
        if t < 45:
            self.derrota_vy = min(1.2, self.derrota_vy + 0.05)
            self.rect.x += int(self.derrota_vx + math.sin(t * 0.9) * 3.0)
            self.rect.y += int(self.derrota_vy)
        else:
            self.derrota_vy = min(9.5, self.derrota_vy + 0.24)
            self.derrota_vx *= 1.015
            self.derrota_ang += self.derrota_rot_vel
            self.rect.x += int(self.derrota_vx)
            self.rect.y += int(self.derrota_vy)

        if t % 2 == 0:
            self._emitir_fumaca_derrota(self.rect.centerx - 22, self.rect.centery - 10, qtd=2, escala=1.2)
            self._emitir_fogo_derrota(self.rect.centerx + 18, self.rect.centery + 8, qtd=3, escala=1.15)
        if t in (24, 52, 82):
            assets.tocar_som("explosao")
            self.flash = 6
            self.shake_request = 7
            self._emitir_explosao_derrota(
                self.rect.centerx + random.randint(-36, 36),
                self.rect.centery + random.randint(-24, 24),
                qtd=16,
            )

        if self.rect.top > ALTURA + 90 or t >= self.DURACAO_DERROTA:
            self.derrota_concluida = True

    def draw_derrota(self, tela, assets):
        par = assets.sprites.get(self.SPRITE_KEY)
        if par:
            img, mask = par
            if abs(self.derrota_ang) > 0.5:
                img_rot = pygame.transform.rotate(img, self.derrota_ang)
                tela.blit(img_rot, img_rot.get_rect(center=self.rect.center))
                if self.flash > 0:
                    mask_rot = pygame.transform.rotate(mask, self.derrota_ang)
                    tela.blit(mask_rot, mask_rot.get_rect(center=self.rect.center))
            else:
                tela.blit(img, img.get_rect(center=self.rect.center))
                if self.flash > 0:
                    tela.blit(mask, mask.get_rect(center=self.rect.center))
        self._desenhar_particulas_derrota(tela)

    # ------------------------------------------------------------------
    # Loop Principal
    # ------------------------------------------------------------------
    def update(self, players, inimigos, tiros_inimigos, assets):
        self.anim_t += 0.1
        if self.flash > 0:
            self.flash -= 1

        if self.estado == "entrando":
            self.timer_entrada += 1
            t = self.progresso_entrada
            ease = 1.0 - (1.0 - t) ** 3
            self.y_float = self.y_inicial_entrada + (self.y_combate - self.y_inicial_entrada) * ease
            self.rect.y = int(round(self.y_float))
            self.rect.centerx = LARGURA // 2
            self.on_update_entrada(players, assets)

            if self.timer_entrada >= self.DURACAO_ENTRADA:
                self.rect.y = int(self.y_combate)
                self.timer = 0
                self.estado = self.estado_inicial_combate()
                self.ao_concluir_entrada()
            return

        if self.estado == "derrotado":
            self.timer_derrota += 1
            self._atualizar_particulas_derrota()
            self.update_derrota(players, inimigos, tiros_inimigos, assets)
            if self.timer_derrota >= self.DURACAO_DERROTA:
                self.derrota_concluida = True
            return

        self.timer += 1
        self.update_combate(players, inimigos, tiros_inimigos, assets)

    def on_update_entrada(self, players, assets):
        """Hook opcional durante a descida de entrada."""
        pass

    def update_combate(self, players, inimigos, tiros_inimigos, assets):
        raise NotImplementedError

    def receber_acerto(self, tiro_rect, dano):
        if self.invulneravel:
            return False
        if self.ignorar_hitbox_principal:
            return self.verificar_acerto_custom(tiro_rect, dano)
        if tiro_rect.colliderect(self.rect):
            self.vida -= dano
            self.flash = 4
            return True
        return False

    def receber_dano_area(self, area_rect, dano):
        if self.invulneravel:
            return
        if self.ignorar_hitbox_principal:
            self.verificar_acerto_custom(area_rect, dano)
        elif area_rect.colliderect(self.rect):
            self.vida -= dano
            self.flash = 6

    def verificar_acerto_custom(self, hitbox, dano):
        return False

    def verificar_dano_jogador(self, player_rect):
        if self.invulneravel:
            return False
        if not self.ignorar_hitbox_principal:
            if player_rect.colliderect(self.rect.inflate(-16, -16)):
                return True
        for lr in self.lasers:
            if player_rect.colliderect(lr):
                return True
        return self.verificar_dano_custom(player_rect)

    def verificar_dano_custom(self, player_rect):
        return False

    def verificar_lentidao_jogador(self, player_rect):
        return False

    def draw(self, tela, assets):
        if self.estado == "derrotado":
            self.draw_derrota(tela, assets)
            return
        self.draw_corpo(tela, assets)
        self.draw_efeitos(tela, assets)

    def draw_corpo(self, tela, assets):
        par = assets.sprites.get(self.SPRITE_KEY)
        if par:
            img, mask = par
            tela.blit(img, img.get_rect(center=self.rect.center))
            if self.flash > 0:
                tela.blit(mask, mask.get_rect(center=self.rect.center))

    def draw_efeitos(self, tela, assets):
        pass