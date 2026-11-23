import math
import random
import pygame
from config import LARGURA, LULA_VIDA, LULA_VELOCIDADE, LULA_TINTA_Y_EXPLOSAO
from enemies import Enemy
from projectiles import Bullet
from boss_basic import BossBase


class BossLula(BossBase):
    TIPO = "squid"
    NOME_EXIBICAO = "DEVORADOR DAS PROFUNDEZAS"
    SUBTITULO_ENTRADA = "GUARDIÃO I  •  DESTRUIDOR DOS MARES"
    SPRITE_KEY = "boss_squid"
    VIDA_BASE = LULA_VIDA
    VELOCIDADE_BASE = LULA_VELOCIDADE
    Y_COMBATE = 85

    def on_init_combate(self):
        self.onda_t = 0.0
        self.alvo_dash = None
        self.y_inicio_dash = 85
        self.rastro_dash = []
        self.ondas_impacto = []

    def estado_inicial_combate(self):
        return "navegando"

    def _disparar_8_direcoes(self, tiros_inimigos, assets):
        cx, cy = self.rect.center
        vel = 6.2 if self.em_furia else 5.5
        assets.tocar_som("tiro")
        for i in range(8):
            ang = math.radians(i * 45)
            tiros_inimigos.append(
                Bullet(cx - 8, cy - 8, math.cos(ang) * vel, math.sin(ang) * vel, owner="enemy", tipo="tinta")
            )
        self.ondas_impacto.append({"pos": (cx, cy), "raio": 18.0, "vida": 16})

    def update_combate(self, players, inimigos, tiros_inimigos, assets):
        self.onda_t += 0.05

        for rastro in self.rastro_dash[:]:
            rastro["vida"] -= 1
            rastro["raio"] += 1.2
            if rastro["vida"] <= 0:
                self.rastro_dash.remove(rastro)

        for onda in self.ondas_impacto[:]:
            onda["vida"] -= 1
            onda["raio"] += 5.5
            if onda["vida"] <= 0:
                self.ondas_impacto.remove(onda)

        if self.estado == "navegando":
            vel_h = self.vx * (1.18 if self.em_furia else 1.0)
            self.rect.x += vel_h
            self.rect.y = int(85 + math.sin(self.onda_t) * 36)
            if self.rect.left <= 20:
                self.rect.left = 20
                self.vx = abs(self.vx)
            elif self.rect.right >= LARGURA - 20:
                self.rect.right = LARGURA - 20
                self.vx = -abs(self.vx)

            if self.timer == 85:
                assets.tocar_som("tiro")
                y_min, y_max = LULA_TINTA_Y_EXPLOSAO
                leque = (-3.6, -1.8, 0.0, 1.8, 3.6) if self.em_furia else (-2.6, 0.0, 2.6)
                for vx_t in leque:
                    tiros_inimigos.append(
                        Bullet(
                            self.rect.centerx - 8,
                            self.rect.bottom - 10,
                            vx_t,
                            5.8,
                            owner="enemy",
                            tipo="tinta",
                            y_explosao=random.randint(y_min, y_max),
                        )
                    )

            elif self.timer == 165:
                posicoes = (110, 290, 510, LARGURA - 110) if self.em_furia else (140, LARGURA // 2, LARGURA - 140)
                for pos_x in posicoes:
                    inimigos.append(Enemy(pos_x, tipo="peixe"))

            tempo_para_dash = 185 if self.em_furia else 225
            if self.timer >= tempo_para_dash:
                vivos = [p for p in players if p.vivo]
                alvo_x = random.choice(vivos).rect.centerx if vivos else LARGURA // 2
                alvo_y = random.randint(435, 480)
                self.alvo_dash = (max(105, min(LARGURA - 105, alvo_x)), alvo_y)
                self.y_inicio_dash = self.rect.y
                self.estado = "preparando_dash"
                self.timer = 0

        elif self.estado == "preparando_dash":
            prog = min(1.0, self.timer / 36.0)
            self.rect.y = int(self.y_inicio_dash - math.sin(prog * math.pi * 0.5) * 24)
            if self.timer >= 36:
                assets.tocar_som("lula_dash")
                self.estado = "dash_avanco"
                self.timer = 0

        elif self.estado == "dash_avanco":
            if not self.alvo_dash:
                self.estado = "navegando"
                self.timer = 0
                return

            tx, ty = self.alvo_dash
            dx, dy = tx - self.rect.centerx, ty - self.rect.centery
            dist = math.hypot(dx, dy)
            vel_dash = 13.0 if self.em_furia else 11.6

            if self.timer % 3 == 0:
                self.rastro_dash.append({"pos": self.rect.center, "raio": 14.0, "vida": 14})

            if dist > 16:
                self.rect.x += int((dx / dist) * vel_dash)
                self.rect.y += int((dy / dist) * vel_dash)
            else:
                self.rect.center = (tx, ty)
                self.shake_request = 8
                self.rastro_dash.append({"pos": self.rect.center, "raio": 24.0, "vida": 18})
                self._disparar_8_direcoes(tiros_inimigos, assets)
                self.estado = "dash_pausa"
                self.timer = 0

        elif self.estado == "dash_pausa":
            if self.timer >= 10:
                self.estado = "dash_recuo"
                self.timer = 0

        elif self.estado == "dash_recuo":
            if self.rect.y > 85:
                self.rect.y -= 6
            else:
                self.rect.y = 85
                self.estado = "navegando"
                self.timer = 0

    def draw_efeitos(self, tela, assets):
        for rastro in self.rastro_dash:
            rx, ry = int(rastro["pos"][0]), int(rastro["pos"][1])
            cor = (0, 235, 200) if rastro["vida"] > 7 else (155, 70, 235)
            pygame.draw.circle(tela, cor, (rx, ry), int(rastro["raio"]), 2)

        for onda in self.ondas_impacto:
            ox, oy = int(onda["pos"][0]), int(onda["pos"][1])
            cor = (0, 245, 215) if onda["vida"] > 8 else (195, 95, 255)
            pygame.draw.circle(tela, cor, (ox, oy), int(onda["raio"]), 3)

        if self.estado == "preparando_dash" and self.alvo_dash:
            sx, sy = self.rect.center
            tx, ty = self.alvo_dash
            prog = min(1.0, self.timer / 36.0)

            raio_alvo = max(16, int(44 * (1.0 - prog * 0.55)))
            pygame.draw.circle(tela, (210, 95, 255), (tx, ty), raio_alvo, 2)
            pygame.draw.circle(tela, (0, 240, 210), (tx, ty), max(6, raio_alvo // 2), 2)

            dx, dy = tx - sx, ty - sy
            dist = max(1.0, math.hypot(dx, dy))
            ux, uy = dx / dist, dy / dist
            px, py = -uy, ux
            for passo in range(3):
                t_seta = ((self.timer * 0.045) + passo / 3.0) % 1.0
                cx, cy = sx + dx * t_seta, sy + dy * t_seta
                ponta = (int(cx + ux * 9), int(cy + uy * 9))
                asa_esq = (int(cx - ux * 6 + px * 11), int(cy - uy * 6 + py * 11))
                asa_dir = (int(cx - ux * 6 - px * 11), int(cy - uy * 6 - py * 11))
                pygame.draw.lines(tela, (195, 110, 255), False, [asa_esq, ponta, asa_dir], 2)

    def on_iniciar_derrota(self, assets):
        self.lasers.clear()
        self.rastro_dash.clear()
        self.ondas_impacto = [{"pos": self.rect.center, "raio": 22.0, "vida": 24}]
        self.derrota_ang = 0.0
        self._emitir_explosao_derrota(
            self.rect.centerx, self.rect.centery,
            [(45, 25, 70), (165, 75, 245), (0, 235, 200)], qtd=26,
        )

    def update_derrota(self, players, inimigos, tiros_inimigos, assets):
        t = self.timer_derrota
        self.derrota_ang += 4.5
        self.rect.y += 2
        self.rect.x += int(math.sin(t * 0.35) * 4)

        for onda in self.ondas_impacto[:]:
            onda["vida"] -= 1
            onda["raio"] += 6.2
            if onda["vida"] <= 0:
                self.ondas_impacto.remove(onda)

        if t % 3 == 0:
            self._emitir_explosao_derrota(
                self.rect.centerx + random.randint(-30, 30),
                self.rect.centery + random.randint(-20, 20),
                [(35, 20, 55), (150, 65, 230), (0, 225, 195)],
                qtd=5,
            )
        if t in (35, 75, 110):
            assets.tocar_som("explosao")
            self.flash = 6
            self.shake_request = 7
            self.ondas_impacto.append({"pos": self.rect.center, "raio": 20.0, "vida": 22})

    def draw_derrota(self, tela, assets):
        prog = self.progresso_derrota
        par = assets.sprites.get(self.SPRITE_KEY)
        if par:
            img, mask = par
            escala = max(0.15, 1.0 - prog * 0.78)
            img_rot = pygame.transform.rotozoom(img, self.derrota_ang, escala)
            tela.blit(img_rot, img_rot.get_rect(center=self.rect.center))
            if self.flash > 0:
                mask_rot = pygame.transform.rotozoom(mask, self.derrota_ang, escala)
                tela.blit(mask_rot, mask_rot.get_rect(center=self.rect.center))

        for onda in self.ondas_impacto:
            ox, oy = int(onda["pos"][0]), int(onda["pos"][1])
            cor = (0, 245, 215) if onda["vida"] > 11 else (195, 95, 255)
            pygame.draw.circle(tela, cor, (ox, oy), int(onda["raio"]), 3)

        self._desenhar_particulas_derrota(tela)
