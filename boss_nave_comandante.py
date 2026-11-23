import math
import random
import pygame
from config import (
    LARGURA,
    ALTURA,
    BOSS_FINAL_VIDA,
    BOSS_FINAL_VIDA_COOP_EXTRA,
    BOSS_FINAL_VELOCIDADE,
    BOSS_FINAL_BRECHA,
    BOSS_FINAL_LARGURA_CANHAO,
    BOSS_FINAL_COOLDOWN_TIRO,
)
from enemies import Enemy
from projectiles import Bullet
from boss_basic import BossBase


class BossNaveAndromeda(BossBase):
    """Boss 4 — Nave Comandante de Andromeda (limpa, sem torretas laterais)."""

    TIPO = "final"
    NOME_EXIBICAO = "ARAUTO DA EXTINÇÃO"
    SUBTITULO_ENTRADA = "GUARDIÃO IV  •  MENSAGEIRO DO FIM"
    SPRITE_KEY = "boss_final"
    VIDA_BASE = BOSS_FINAL_VIDA
    VELOCIDADE_BASE = BOSS_FINAL_VELOCIDADE
    Y_COMBATE = 52

    def _calcular_vida_base(self, modo_jogadores):
        extra = BOSS_FINAL_VIDA_COOP_EXTRA if modo_jogadores == 2 else 0
        return self.VIDA_BASE + extra

    def on_init_combate(self):
        self.brecha_largura = BOSS_FINAL_BRECHA
        self.brecha_x = (LARGURA - self.brecha_largura) // 2
        self.largura_canhao = BOSS_FINAL_LARGURA_CANHAO
        self.campo_verde_rect = None
        self.tempo_campo_verde = 0
        self.contador_rajadas = 0

    def estado_inicial_combate(self):
        return "tiros"

    def _conjurar_frota_com_brecha(self, inimigos, assets):
        assets.tocar_som("boss_final_frota")
        brecha_inicio = self.brecha_x
        brecha_fim = self.brecha_x + self.brecha_largura

        naves_menores = [("normal", 1), ("normal", 1), ("normal", 2)]
        posicoes_x = [
            x for x in range(24, LARGURA - 64, 76)
            if not (x + 44 > brecha_inicio and x < brecha_fim)
        ]
        if not posicoes_x:
            return

        idx_especial = random.randrange(len(posicoes_x))
        qtd_atiradores = 2 if self.em_furia else 1
        indices_atiradores = set(random.sample(range(len(posicoes_x)), min(qtd_atiradores, len(posicoes_x))))

        for idx, x in enumerate(posicoes_x):
            if idx in indices_atiradores:
                tipo_escolhido, tam_idx = "atirador", 1
            else:
                tipo_escolhido, tam_idx = random.choice(naves_menores)

            inimigos.append(
                Enemy(
                    x,
                    tipo=tipo_escolhido,
                    tamanho_idx=tam_idx,
                    especial=(idx == idx_especial),
                    multiplicador=0.85,
                    vx_custom=0,
                    vy_custom=3.8,
                )
            )

    def _aplicar_turbulencia_campo(self, players):
        if self.campo_verde_rect is None:
            return
        for p in players:
            if p.vivo and p.tempo_escudo == 0 and self.campo_verde_rect.colliderect(p.rect):
                p.rect.y = max(60, int(p.rect.y - 1.1))

    def _mover_horizontal(self, fator=1.0, margem=22):
        self.rect.x += self.vx * fator
        if self.rect.left <= margem:
            self.rect.left = margem
            self.vx = abs(self.vx)
        elif self.rect.right >= LARGURA - margem:
            self.rect.right = LARGURA - margem
            self.vx = -abs(self.vx)

    def update_combate(self, players, inimigos, tiros_inimigos, assets):
        if self.tempo_campo_verde > 0:
            self.tempo_campo_verde -= 1
            self._aplicar_turbulencia_campo(players)
            if self.tempo_campo_verde <= 0:
                self.campo_verde_rect = None

        vel_fator = 1.18 if self.em_furia else 1.0

        if self.timer < 120:
            self.estado = "tiros"
            self.lasers.clear()
            self._mover_horizontal(vel_fator, margem=18)
            self.rect.y = int(52 + math.sin(self.anim_t * 0.65) * 7)

            cd_tiro = max(24, int(BOSS_FINAL_COOLDOWN_TIRO * (0.82 if self.em_furia else 1.0)))
            if self.timer % cd_tiro == 0:
                self.contador_rajadas += 1
                assets.tocar_som("tiro")
                tiros_inimigos.append(Bullet(self.rect.centerx - 48, self.rect.centery + 32, 0, 6.4, "enemy"))
                tiros_inimigos.append(Bullet(self.rect.centerx + 42, self.rect.centery + 32, 0, 6.4, "enemy"))

                if self.em_furia and self.contador_rajadas % 2 == 0:
                    for vx_leque in (-3.2, -1.6, 0.0, 1.6, 3.2):
                        tiros_inimigos.append(Bullet(self.rect.centerx - 3, self.rect.bottom - 10, vx_leque, 6.0, "enemy"))
                else:
                    vivos = [p for p in players if p.vivo]
                    alvos = vivos if vivos else [None]
                    for alvo in alvos:
                        dx = (alvo.rect.centerx - self.rect.centerx) if alvo else 0
                        dy = max(140, (alvo.rect.centery - self.rect.bottom)) if alvo else 400
                        ang = math.atan2(dy, dx)
                        tiros_inimigos.append(
                            Bullet(self.rect.centerx - 3, self.rect.bottom - 10, math.cos(ang) * 6.0, max(4.4, math.sin(ang) * 6.0), "enemy")
                        )

        elif 120 <= self.timer < 180:
            if self.timer == 120:
                self.lasers.clear()
                self.estado = "conjurando_frota"
                assets.tocar_som("boss_final_campo")
                self.brecha_x = random.randint(45, LARGURA - self.brecha_largura - 45)
                self.campo_verde_rect = pygame.Rect(self.brecha_x, 0, self.brecha_largura, ALTURA)
                self.tempo_campo_verde = 120
            elif self.timer == 172:
                self._conjurar_frota_com_brecha(inimigos, assets)

            self._mover_horizontal(0.55, margem=18)

        elif 180 <= self.timer < 235:
            if self.timer == 180:
                assets.tocar_som("boss_final_carregar")
            self.estado = "carregando_canhao"
            if self.timer < 220:
                self._mover_horizontal(0.35, margem=18)

        elif 235 <= self.timer < 280:
            if self.timer == 235:
                assets.tocar_som("boss_final_laser")
                self.shake_request = 12
                tiros_inimigos.append(Bullet(self.rect.centerx - 52, self.rect.bottom - 12, -2.0, 6.6, "enemy", "canhao_boss"))
                tiros_inimigos.append(Bullet(self.rect.centerx + 34, self.rect.bottom - 12, 2.0, 6.6, "enemy", "canhao_boss"))
            self.estado = "disparando_canhao"
            cx, bot = self.rect.centerx, self.rect.bottom - 14
            meia_w = self.largura_canhao // 2
            self.lasers = [pygame.Rect(cx - meia_w, bot, self.largura_canhao, ALTURA)]

        else:
            self.lasers.clear()
            self.timer = 0
            self.estado = "tiros"

    def verificar_lentidao_jogador(self, player_rect):
        return self.campo_verde_rect is not None and self.campo_verde_rect.colliderect(player_rect)

    def draw_efeitos(self, tela, assets):
        cx = self.rect.centerx
        bot = self.rect.bottom - 18

        if self.campo_verde_rect is not None:
            bx1 = self.campo_verde_rect.left
            bx2 = self.campo_verde_rect.right
            alpha_campo = min(34, int((self.tempo_campo_verde / 120.0) * 40) + 10)
            faixa_lenta = pygame.Surface((self.campo_verde_rect.width, ALTURA), pygame.SRCALPHA)
            faixa_lenta.fill((0, 235, 130, alpha_campo))
            tela.blit(faixa_lenta, (bx1, 0))

            deslocamento = int((self.anim_t * 26) % 40)
            for y_linha in range(deslocamento, ALTURA, 40):
                pygame.draw.line(tela, (40, 255, 165), (bx1 + 6, y_linha), (bx2 - 6, y_linha), 1)

            pygame.draw.line(tela, (0, 255, 160), (bx1, 0), (bx1, ALTURA), 2)
            pygame.draw.line(tela, (0, 255, 160), (bx2, 0), (bx2, ALTURA), 2)

        if self.estado == "carregando_canhao":
            prog = (self.timer - 180) / 55.0
            abertura = int(85 * (1.0 - prog)) + (self.largura_canhao // 2)
            cor_linha = (255, 225, 175) if self.timer >= 220 else (255, 130, 85)
            pygame.draw.line(tela, cor_linha, (cx, bot + 4), (cx - abertura, ALTURA), 2)
            pygame.draw.line(tela, cor_linha, (cx, bot + 4), (cx + abertura, ALTURA), 2)
            raio_carga = max(8, int(42 * (1.0 - prog)))
            pygame.draw.circle(tela, (235, 75, 55), (cx, bot + 4), raio_carga, 2)
            pygame.draw.circle(tela, (255, 225, 195), (cx, bot + 4), max(4, raio_carga // 2))

        elif self.estado == "disparando_canhao":
            pulso = int(math.sin(self.timer * 1.5) * 3)
            for lr in self.lasers:
                aura_rect = lr.inflate(14 + pulso, 0)
                nucleo_rect = lr.inflate(-max(22, lr.width // 2), 0)
                pygame.draw.rect(tela, (150, 18, 38), aura_rect, border_radius=8)
                pygame.draw.rect(tela, (240, 55, 75), lr, border_radius=6)
                pygame.draw.rect(tela, (255, 235, 238), nucleo_rect, border_radius=4)
            pygame.draw.circle(tela, (240, 55, 75), (cx, bot + 6), 22 + pulso)
            pygame.draw.circle(tela, (255, 240, 242), (cx, bot + 6), 11)

    # ------------------------------------------------------------------
    # Animação de Derrota — Explosões nas Asas, Fumaça e Queda da Capitânia
    # ------------------------------------------------------------------
    def on_iniciar_derrota(self, assets):
        self.lasers.clear()
        self.campo_verde_rect = None
        self.tempo_campo_verde = 0
        self.derrota_ang = 0.0
        self.derrota_dir = 1 if self.vx >= 0 else -1
        self.derrota_fumaca = []
        self.derrota_ondas = [{"raio": 24.0, "alpha": 230}]
        self.flash = 8
        self.shake_request = 9
        self._emitir_explosao_derrota(
            self.rect.centerx,
            self.rect.centery,
            [(255, 175, 65), (240, 65, 75), (85, 95, 115)],
            qtd=30,
        )

    def update_derrota(self, players, inimigos, tiros_inimigos, assets):
        t = self.timer_derrota
        prog = self.progresso_derrota

        # Nave capitânia aderna (inclina) e perde altitude gradualmente
        self.derrota_ang += 0.28 * self.derrota_dir
        self.rect.y += 1 if t % 2 == 0 else 2
        self.rect.x += int(self.derrota_dir * (1.2 + prog * 1.5))

        for fm in self.derrota_fumaca[:]:
            fm["x"] += fm["vx"]
            fm["y"] += fm["vy"]
            fm["raio"] += 0.32
            fm["vida"] -= 1
            if fm["vida"] <= 0:
                self.derrota_fumaca.remove(fm)

        for onda in self.derrota_ondas[:]:
            onda["raio"] += 7.5
            onda["alpha"] = max(0, onda["alpha"] - 10)
            if onda["alpha"] <= 0:
                self.derrota_ondas.remove(onda)

        if t % 2 == 0:
            asa_ox = random.choice([-62, -24, 24, 62])
            self.derrota_fumaca.append({
                "x": float(self.rect.centerx + asa_ox),
                "y": float(self.rect.centery + random.randint(-12, 16)),
                "vx": random.uniform(-0.8, 0.8),
                "vy": random.uniform(-2.6, -1.1),
                "raio": random.uniform(9.0, 15.0),
                "vida": 34,
                "max_vida": 34,
            })

        if t % 4 == 0:
            self._emitir_explosao_derrota(
                self.rect.centerx + random.randint(-68, 68),
                self.rect.centery + random.randint(-20, 26),
                [(255, 150, 50), (240, 55, 75), (90, 215, 255)],
                qtd=4,
            )

        if t in (24, 48, 74, 98, 118):
            assets.tocar_som("explosao")
            self.flash = 6
            self.shake_request = 8
            ox = random.choice([-64, 0, 64]) if t < 110 else 0
            self.derrota_ondas.append({"raio": 18.0, "alpha": 235})
            self._emitir_explosao_derrota(
                self.rect.centerx + ox,
                self.rect.centery + 8,
                [(255, 235, 175), (245, 70, 75), (255, 165, 55)],
                qtd=20,
            )

    def draw_derrota(self, tela, assets):
        prog = self.progresso_derrota
        cx, cy = self.rect.center

        if self.derrota_fumaca:
            smoke_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            for fm in self.derrota_fumaca:
                alpha = max(0, min(195, int((fm["vida"] / float(fm["max_vida"])) * 195)))
                pygame.draw.circle(
                    smoke_surf,
                    (52, 56, 66, alpha),
                    (int(fm["x"]), int(fm["y"])),
                    int(fm["raio"]),
                )
            tela.blit(smoke_surf, (0, 0))

        par = assets.sprites.get(self.SPRITE_KEY)
        if par:
            img, mask = par
            escala = max(0.18, 1.0 - (prog ** 1.8) * 0.78)
            img_rot = pygame.transform.rotozoom(img, self.derrota_ang, escala)
            tela.blit(img_rot, img_rot.get_rect(center=(cx, cy)))
            if self.flash > 0:
                mask_rot = pygame.transform.rotozoom(mask, self.derrota_ang, escala)
                tela.blit(mask_rot, mask_rot.get_rect(center=(cx, cy)))

        if self.derrota_ondas:
            onda_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            for onda in self.derrota_ondas:
                pygame.draw.circle(
                    onda_surf,
                    (255, 160, 95, int(onda["alpha"])),
                    (cx, cy),
                    int(onda["raio"]),
                    3,
                )
            tela.blit(onda_surf, (0, 0))

        self._desenhar_particulas_derrota(tela)
