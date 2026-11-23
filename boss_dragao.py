import math
import random
import pygame
from config import LARGURA, ALTURA, OLHO_VIDA, OLHO_VELOCIDADE
from enemies import Enemy
from projectiles import Bullet
from boss_basic import BossBase


class BossDragao(BossBase):
    TIPO = "eye"
    NOME_EXIBICAO = "SENTINELA ESMERALDA"
    SUBTITULO_ENTRADA = "GUARDIÃO III  •  ABISMO VIGILANTE"
    SPRITE_KEY = "boss_eye"
    VIDA_BASE = OLHO_VIDA
    VELOCIDADE_BASE = OLHO_VELOCIDADE
    Y_COMBATE = 58

    def on_init_combate(self):
        self.largura_laser_base = 48
        self.largura_laser_ponta = 78
        self.ciclo = 0
        self.dir_varredura = 1

    def estado_inicial_combate(self):
        return "combate"

    def _mover_horizontal(self, vel, margem=24):
        self.rect.x += vel
        if self.rect.left <= margem:
            self.rect.left = margem
            self.vx = abs(self.vx)
            self.dir_varredura = 1
        elif self.rect.right >= LARGURA - margem:
            self.rect.right = LARGURA - margem
            self.vx = -abs(self.vx)
            self.dir_varredura = -1

    def update_combate(self, players, inimigos, tiros_inimigos, assets):
        vel_mult = 1.25 if self.em_furia else 1.0

        if self.timer < 105:
            self.estado = "combate"
            self.lasers.clear()
            self._mover_horizontal(self.vx * vel_mult, margem=18)
            self.rect.y = int(58 + math.sin(self.anim_t * 0.6) * 10)

            intervalo_tiro = 26 if self.em_furia else 34
            if self.timer > 15 and self.timer % intervalo_tiro == 0:
                assets.tocar_som("tiro")
                cx, bot = self.rect.centerx, self.rect.bottom - 16
                if self.em_furia:
                    for vx_orbe, vy_orbe in [(-2.6, 5.4), (0.0, 6.2), (2.6, 5.4)]:
                        tiros_inimigos.append(
                            Bullet(cx - 5, bot, vx_orbe, vy_orbe, owner="enemy", tipo="orbe_olho")
                        )
                else:
                    tiros_inimigos.append(
                        Bullet(cx - 5, bot, 0, 5.8, owner="enemy", tipo="orbe_olho")
                    )

        elif self.timer < 150:
            if self.estado != "carregando":
                self.estado = "carregando"
                assets.tocar_som("olho_carregar")
                vivos = [p for p in players if p.vivo]
                if vivos:
                    alvo = random.choice(vivos)
                    self.dir_varredura = 1 if alvo.rect.centerx >= self.rect.centerx else -1
                else:
                    self.dir_varredura = random.choice([-1, 1])

            self.rect.y = int(58 + math.sin(self.timer * 0.9) * 3)

        elif self.timer < 205:
            if self.estado != "disparando":
                self.estado = "disparando"
                assets.tocar_som("olho_laser")
                self.shake_request = 10

            vel_varredura = (2.9 if self.em_furia else 2.2) * self.dir_varredura
            self.rect.x += vel_varredura
            if self.rect.left <= 30:
                self.rect.left = 30
                self.dir_varredura = 1
            elif self.rect.right >= LARGURA - 30:
                self.rect.right = LARGURA - 30
                self.dir_varredura = -1

            self.largura_laser_base = 56 if self.em_furia else 44
            self.largura_laser_ponta = 88 if self.em_furia else 70

            cx = self.rect.centerx
            topo_laser = self.rect.bottom - 14
            alt_laser = ALTURA - topo_laser
            self.lasers = [
                pygame.Rect(cx - self.largura_laser_base // 2, topo_laser, self.largura_laser_base, int(alt_laser * 0.55)),
                pygame.Rect(cx - self.largura_laser_ponta // 2, topo_laser + int(alt_laser * 0.55), self.largura_laser_ponta, int(alt_laser * 0.45)),
            ]

        elif self.timer < 265:
            self.lasers.clear()
            if self.ciclo % 2 == 0:
                self.estado = "invocando"
                self._mover_horizontal(self.vx * 0.8, margem=20)
                if self.timer == 220:
                    assets.tocar_som("olho_invocar")
                    qtd_morcegos = 4 if self.em_furia else 3
                    espaco = (LARGURA - 180) // max(1, qtd_morcegos - 1)
                    for i in range(qtd_morcegos):
                        mx = 90 + i * espaco
                        inimigos.append(Enemy(mx, tipo="morcego"))
            else:
                self.estado = "rajada"
                self.rect.y = max(42, self.rect.y - 1)
                self._mover_horizontal(self.vx * 1.15, margem=24)

                if self.timer in (220, 228, 236, 244, 252, 260):
                    assets.tocar_som("tiro")
                    passo = (self.timer - 220) // 8
                    ang = math.radians(-35 + passo * 14)
                    tiros_inimigos.append(
                        Bullet(self.rect.centerx - 5, self.rect.bottom - 16, math.sin(ang) * 4.8, math.cos(ang) * 5.6, owner="enemy", tipo="orbe_olho")
                    )
        else:
            self.lasers.clear()
            self.timer = 0
            self.ciclo += 1
            self.estado = "combate"

    def draw_efeitos(self, tela, assets):
        cx, cy = self.rect.center
        bot = self.rect.bottom - 18

        if self.estado == "carregando":
            prog = (self.timer - 105) / 45.0
            raio_ext = int(34 * (1.2 - prog * 0.6))
            pygame.draw.circle(tela, (255, 80, 60), (cx, bot + 8), max(8, raio_ext), 2)
            pygame.draw.circle(tela, (255, 220, 140), (cx, bot + 8), int(6 + prog * 14))
            pygame.draw.line(tela, (255, 60, 60), (cx, bot + 8), (cx, ALTURA), 1)

        elif self.estado == "disparando":
            topo = self.rect.bottom - 14
            pulso = int(math.sin(self.timer * 0.8) * 6)
            l_base = self.largura_laser_base + pulso
            l_ponta = self.largura_laser_ponta + pulso

            pts_ext = [
                (cx - l_base // 2, topo),
                (cx + l_base // 2, topo),
                (cx + l_ponta // 2, ALTURA),
                (cx - l_ponta // 2, ALTURA),
            ]
            pts_int = [
                (cx - max(8, l_base // 4), topo),
                (cx + max(8, l_base // 4), topo),
                (cx + max(14, l_ponta // 4), ALTURA),
                (cx - max(14, l_ponta // 4), ALTURA),
            ]
            pygame.draw.polygon(tela, (240, 45, 55), pts_ext)
            pygame.draw.polygon(tela, (255, 240, 210), pts_int)

            pygame.draw.circle(tela, (255, 100, 50), (cx, bot + 6), 22 + pulso)
            pygame.draw.circle(tela, (255, 250, 230), (cx, bot + 6), 11)

    # ------------------------------------------------------------------
    # Animação de Derrota — Espiral Ígnea e Colapso em Supernova
    # ------------------------------------------------------------------
    def on_iniciar_derrota(self, assets):
        self.lasers.clear()
        self.derrota_ang = 0.0
        self.derrota_ondas_fogo = [{"raio": 20.0, "alpha": 230}]
        self.flash = 8
        self.shake_request = 9
        self._emitir_explosao_derrota(
            self.rect.centerx,
            self.rect.centery,
            [(255, 85, 45), (255, 190, 70), (255, 245, 200)],
            qtd=30,
        )

    def update_derrota(self, players, inimigos, tiros_inimigos, assets):
        t = self.timer_derrota
        prog = self.progresso_derrota

        self.derrota_ang = math.sin(t * 0.34) * (16.0 + prog * 34.0)
        alvo_x = LARGURA * 0.5 + math.sin(t * 0.22) * (65.0 * (1.0 - prog))
        alvo_y = 140.0 + math.cos(t * 0.28) * 18.0
        self.rect.centerx += int((alvo_x - self.rect.centerx) * 0.08)
        self.rect.centery += int((alvo_y - self.rect.centery) * 0.08)

        for onda in self.derrota_ondas_fogo[:]:
            onda["raio"] += 7.2
            onda["alpha"] = max(0, onda["alpha"] - 9)
            if onda["alpha"] <= 0:
                self.derrota_ondas_fogo.remove(onda)

        if t % 3 == 0:
            self._emitir_explosao_derrota(
                self.rect.centerx + random.randint(-42, 42),
                self.rect.centery + random.randint(-28, 28),
                [(255, 75, 45), (255, 185, 65), (75, 45, 50)],
                qtd=5,
            )

        if t in (30, 62, 92, 115):
            assets.tocar_som("explosao")
            self.flash = 7
            self.shake_request = 8
            self.derrota_ondas_fogo.append({"raio": 18.0, "alpha": 240})
            self._emitir_explosao_derrota(
                self.rect.centerx,
                self.rect.centery,
                [(255, 240, 175), (255, 95, 45), (210, 35, 55)],
                qtd=20,
            )

    def draw_derrota(self, tela, assets):
        prog = self.progresso_derrota
        cx, cy = self.rect.center
        fx_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

        if prog > 0.20:
            fator = min(1.0, (prog - 0.20) / 0.70)
            for i in range(8):
                ang = self.timer_derrota * 0.03 + i * (math.tau / 8)
                comp = 160 + fator * 320
                ex = cx + math.cos(ang) * comp
                ey = cy + math.sin(ang) * comp
                pygame.draw.line(fx_surf, (255, 110, 55, int(140 * (1.0 - prog * 0.5))), (cx, cy), (ex, ey), int(6 + fator * 10))
                pygame.draw.line(fx_surf, (255, 240, 195, int(180 * (1.0 - prog * 0.5))), (cx, cy), (ex, ey), 2)

        par = assets.sprites.get(self.SPRITE_KEY)
        if par:
            img, mask = par
            escala = max(0.12, 1.0 - (prog ** 1.65) * 0.86)
            img_rot = pygame.transform.rotozoom(img, self.derrota_ang, escala)
            tela.blit(img_rot, img_rot.get_rect(center=(cx, cy)))
            if self.flash > 0:
                mask_rot = pygame.transform.rotozoom(mask, self.derrota_ang, escala)
                tela.blit(mask_rot, mask_rot.get_rect(center=(cx, cy)))

        for onda in self.derrota_ondas_fogo:
            pygame.draw.circle(
                fx_surf,
                (255, 130, 60, int(onda["alpha"])),
                (cx, cy),
                int(onda["raio"]),
                3,
            )

        tela.blit(fx_surf, (0, 0))
        self._desenhar_particulas_derrota(tela)