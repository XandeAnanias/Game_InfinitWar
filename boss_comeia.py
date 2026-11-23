import math
import random
import pygame
from config import LARGURA, ALTURA, COLMEIA_VIDA, COLMEIA_VELOCIDADE
from enemies import Enemy
from projectiles import Bullet
from boss_basic import BossBase


def _pontos_hexagono(cx, cy, raio, rotacao=0.0):
    pontos = []
    for i in range(6):
        ang = rotacao + math.radians(60 * i + 30)
        pontos.append((int(cx + math.cos(ang) * raio), int(cy + math.sin(ang) * raio)))
    return pontos


class BossColmeia(BossBase):
    """
    Boss 2 — Colmeia Parasita.
    Inspirado em Hollow Knight (Hive Knight / Infecção) e Cuphead (Rumor Honeybottoms).
    """

    TIPO = "colmeia"
    NOME_EXIBICAO = "COLMEIA PROFANA"
    SUBTITULO_ENTRADA = "GUARDIÃO II  •  ORGANISMO CORROMPIDO"
    SPRITE_KEY = "boss_colmeia"
    VIDA_BASE = COLMEIA_VIDA
    VELOCIDADE_BASE = COLMEIA_VELOCIDADE
    Y_COMBATE = 88

    def on_init_combate(self):
        self.onda_t = 0.0
        self.ciclo = 0

        self.casulos = []
        self.favos = []
        self.aviso_favos = None
        self.aviso_enxame = None
        self.nodulo = None
        self.particulas_mel = []

    def estado_inicial_combate(self):
        return "patrulha"

    def _emitir_particulas_locais(self, x, y, cor, qtd=10):
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            vel = random.uniform(1.4, 4.2)
            self.particulas_mel.append({
                "x": float(x),
                "y": float(y),
                "vx": math.cos(ang) * vel,
                "vy": math.sin(ang) * vel,
                "vida": random.randint(16, 26),
                "raio": random.randint(3, 5),
                "cor": cor,
            })

    def _lancar_casulos_esporos(self, assets):
        assets.tocar_som("olho_carregar")
        cx, cy = self.rect.centerx, self.rect.bottom - 18
        alvos = [
            (LARGURA * 0.28, 250),
            (LARGURA * 0.72, 250),
        ]
        if self.em_furia:
            alvos.append((LARGURA * 0.50, 315))

        for idx, (ax, ay) in enumerate(alvos):
            self.casulos.append({
                "x": float(cx),
                "y": float(cy),
                "alvo_x": float(ax),
                "alvo_y": float(ay),
                "timer": 0,
                "duracao": 78 if self.em_furia else 88,
                "rot": idx * 0.52,
            })

    def _atualizar_casulos(self, tiros_inimigos, assets):
        for casulo in self.casulos[:]:
            casulo["timer"] += 1
            casulo["rot"] += 0.015

            casulo["x"] += (casulo["alvo_x"] - casulo["x"]) * 0.09
            casulo["y"] += (casulo["alvo_y"] - casulo["y"]) * 0.09

            if casulo["timer"] >= casulo["duracao"]:
                assets.tocar_som("tiro")
                vel = 4.6 if self.em_furia else 3.9
                for i in range(6):
                    ang = casulo["rot"] + math.radians(60 * i)
                    tiros_inimigos.append(
                        Bullet(
                            casulo["x"] - 6,
                            casulo["y"] - 6,
                            math.cos(ang) * vel,
                            math.sin(ang) * vel,
                            owner="enemy",
                            tipo="esporo",
                        )
                    )
                self._emitir_particulas_locais(casulo["x"], casulo["y"], (255, 195, 65), qtd=12)
                self.casulos.remove(casulo)

    def _preparar_muralha_favos(self, assets):
        assets.tocar_som("olho_carregar")
        colunas = 10
        larg_col = (LARGURA - 80) / colunas
        brecha_1 = random.randint(1, 3)
        brecha_2 = random.randint(6, 8)
        slots = []
        for c in range(colunas):
            if c in (brecha_1, brecha_2):
                continue
            fx = 40 + (c + 0.5) * larg_col
            fy = self.rect.bottom + 38
            slots.append((fx, fy))

        self.aviso_favos = {
            "slots": slots,
            "timer": 0,
            "duracao": 42,
        }

    def _materializar_favos(self, assets):
        if not self.aviso_favos:
            return
        assets.tocar_som("tiro")
        vida_favo = 4.5 if self.em_furia else 3.5
        vy_favo = 2.6 if self.em_furia else 2.15
        for fx, fy in self.aviso_favos["slots"]:
            rect = pygame.Rect(0, 0, 50, 46)
            rect.center = (int(fx), int(fy))
            self.favos.append({
                "x": float(fx),
                "y": float(fy),
                "vy": vy_favo,
                "raio": 26,
                "vida": vida_favo,
                "max_vida": vida_favo,
                "flash": 0,
                "rect": rect,
            })
        self.aviso_favos = None

    def _atualizar_favos(self):
        for favo in self.favos[:]:
            favo["y"] += favo["vy"]
            favo["rect"].center = (int(favo["x"]), int(favo["y"]))
            if favo["flash"] > 0:
                favo["flash"] -= 1
            if favo["y"] - favo["raio"] > ALTURA:
                self.favos.remove(favo)

    def _slots_enxame_atuais(self, formacao):
        cx = self.rect.centerx
        cy = self.rect.bottom + 6
        slots = []
        for ox, vx, vy in formacao:
            px = max(44, min(LARGURA - 44, cx + ox))
            slots.append((px, cy, ox, vx, vy))
        return slots

    def _preparar_enxame(self, assets):
        assets.tocar_som("olho_carregar")
        if self.em_furia:
            formacao = [(-95, -0.9, 3.3), (-34, -0.35, 3.7), (34, 0.35, 3.7), (95, 0.9, 3.3)]
        else:
            formacao = [(-74, -0.75, 3.3), (0, 0.0, 3.7), (74, 0.75, 3.3)]

        self.aviso_enxame = {
            "formacao": formacao,
            "timer": 0,
            "duracao": 46 if self.em_furia else 54,
        }
        self._emitir_particulas_locais(self.rect.centerx, self.rect.bottom, (255, 195, 65), qtd=10)

    def _invocar_nodulo_e_enxame(self, inimigos, assets):
        assets.tocar_som("olho_invocar")

        if self.nodulo is None:
            lado = random.choice([-1, 1])
            vida_nodulo = 24.0 if self.em_furia else 18.0
            self.nodulo = {
                "lado": lado,
                "vida": vida_nodulo,
                "max_vida": vida_nodulo,
                "flash": 0,
                "rect": pygame.Rect(0, 0, 44, 44),
            }
            self._sincronizar_nodulo()

        if self.aviso_enxame is not None:
            formacao = self.aviso_enxame["formacao"]
        elif self.em_furia:
            formacao = [(-95, -0.9, 3.3), (-34, -0.35, 3.7), (34, 0.35, 3.7), (95, 0.9, 3.3)]
        else:
            formacao = [(-74, -0.75, 3.3), (0, 0.0, 3.7), (74, 0.75, 3.3)]

        for px, py, ox, vx, vy in self._slots_enxame_atuais(formacao):
            sx = max(28, min(LARGURA - 68, px - 26))
            abelha = Enemy(sx, tipo="abelha", vx_custom=vx, vy_custom=vy)
            abelha.rect.centery = int(py)
            abelha.y_float = float(abelha.rect.y)
            if hasattr(abelha, "iniciar_emergencia"):
                abelha.iniciar_emergencia(duracao=30, offset_x=ox * 0.22)
            inimigos.append(abelha)
            self._emitir_particulas_locais(px, py, (255, 205, 65), qtd=8)

        self.aviso_enxame = None

    def _sincronizar_nodulo(self):
        if self.nodulo is None:
            return
        ox = self.nodulo["lado"] * (self.rect.width // 2 + 16)
        oy = 14 + math.sin(self.anim_t * 1.4) * 6
        self.nodulo["rect"].center = (int(self.rect.centerx + ox), int(self.rect.centery + oy))

    def update_combate(self, players, inimigos, tiros_inimigos, assets):
        self.onda_t += 0.038

        for pt in self.particulas_mel[:]:
            pt["x"] += pt["vx"]
            pt["y"] += pt["vy"]
            pt["vida"] -= 1
            if pt["vida"] <= 0:
                self.particulas_mel.remove(pt)

        self._atualizar_casulos(tiros_inimigos, assets)
        self._atualizar_favos()

        if self.aviso_favos is not None:
            self.aviso_favos["timer"] += 1
            if self.aviso_favos["timer"] >= self.aviso_favos["duracao"]:
                self._materializar_favos(assets)

        if self.aviso_enxame is not None:
            self.aviso_enxame["timer"] += 1
            if self.aviso_enxame["timer"] % 12 == 0:
                slots = self._slots_enxame_atuais(self.aviso_enxame["formacao"])
                px, py, _, _, _ = random.choice(slots)
                self._emitir_particulas_locais(px, py, (255, 210, 80), qtd=4)
            if self.aviso_enxame["timer"] >= self.aviso_enxame["duracao"]:
                self.estado = "enxame"
                self._invocar_nodulo_e_enxame(inimigos, assets)

        if self.nodulo is not None:
            if self.nodulo["flash"] > 0:
                self.nodulo["flash"] -= 1
            self._sincronizar_nodulo()

        fator_vel = 1.18 if self.em_furia else 1.0
        if self.aviso_favos is not None:
            self.rect.centerx += int((LARGURA // 2 - self.rect.centerx) * 0.05)
        else:
            mult_prep = 0.32 if self.aviso_enxame is not None else 1.0
            self.rect.x += self.vx * fator_vel * mult_prep
            if self.rect.left <= 55:
                self.rect.left = 55
                self.vx = abs(self.vx)
            elif self.rect.right >= LARGURA - 55:
                self.rect.right = LARGURA - 55
                self.vx = -abs(self.vx)

        self.rect.y = int(self.Y_COMBATE + math.sin(self.onda_t) * 14)

        if self.timer == 55:
            self.estado = "esporos"
            self._lancar_casulos_esporos(assets)
        elif self.timer == 145:
            self.estado = "favos"
            self._preparar_muralha_favos(assets)
        elif self.timer == 220:
            self.estado = "enxame_prep"
            self._preparar_enxame(assets)
        elif self.timer >= 340:
            self.timer = 0
            self.ciclo += 1
            self.estado = "patrulha"

    def receber_acerto(self, tiro_rect, dano):
        if self.invulneravel:
            return False

        for favo in self.favos[:]:
            if tiro_rect.colliderect(favo["rect"]):
                favo["vida"] -= dano
                favo["flash"] = 4
                if favo["vida"] <= 0:
                    self._emitir_particulas_locais(favo["x"], favo["y"], (245, 185, 55), qtd=10)
                    self.favos.remove(favo)
                return True

        if self.nodulo is not None and tiro_rect.colliderect(self.nodulo["rect"]):
            self.nodulo["vida"] -= dano
            self.nodulo["flash"] = 5
            self.vida -= dano * 1.25
            if self.nodulo["vida"] <= 0:
                nx, ny = self.nodulo["rect"].center
                self._emitir_particulas_locais(nx, ny, (255, 115, 75), qtd=20)
                self.vida -= 25.0
                self.flash = 8
                self.shake_request = 7
                self.nodulo = None
            return True

        return super().receber_acerto(tiro_rect, dano)

    def verificar_dano_custom(self, player_rect):
        for favo in self.favos:
            if player_rect.colliderect(favo["rect"].inflate(-8, -8)):
                return True
        if self.nodulo is not None and player_rect.colliderect(self.nodulo["rect"].inflate(-6, -6)):
            return True
        return False

    def _desenhar_veias_parasitas(self, tela, fator_comprimento=1.0):
        if fator_comprimento <= 0.02:
            return
        cx, top_y = self.rect.centerx, int((self.rect.top + 18) * fator_comprimento)
        ancoras = [
            (cx - 110, -24),
            (cx - 42, -12),
            (cx + 42, 12),
            (cx + 110, 24),
        ]
        cor_veia = (120, 42, 58) if self.em_furia else (88, 52, 42)
        cor_pulso = (255, 130, 55) if self.em_furia else (235, 185, 65)

        for idx, (ax, off_corpo) in enumerate(ancoras):
            ax = max(20, min(LARGURA - 20, ax))
            bx = cx + int(off_corpo * fator_comprimento)
            pontos = []
            passos = 8
            for s in range(passos + 1):
                t = s / float(passos)
                onda = math.sin(self.anim_t * 0.9 + idx * 1.3 + t * 4.2) * (10 * math.sin(t * math.pi))
                px = int(ax + (bx - ax) * t + onda)
                py = int(top_y * t)
                pontos.append((px, py))

            pygame.draw.lines(tela, cor_veia, False, pontos, 5)
            pygame.draw.lines(tela, (45, 24, 28), False, pontos, 2)

            t_pulso = ((self.anim_t * 0.06) + idx * 0.25) % 1.0
            idx_seg = min(passos - 1, int(t_pulso * passos))
            p_luz = pontos[idx_seg]
            pygame.draw.circle(tela, cor_pulso, p_luz, 4)

    def draw_corpo(self, tela, assets):
        self._desenhar_veias_parasitas(tela)
        super().draw_corpo(tela, assets)

        if self.em_furia and not self.invulneravel:
            cx, cy = self.rect.center
            pulso = 2 + int(abs(math.sin(self.anim_t * 1.4)) * 3)
            pygame.draw.circle(tela, (255, 125, 45), (cx, cy + 8), 16 + pulso, 2)
            pygame.draw.line(tela, (255, 190, 75), (cx - 26, cy - 6), (cx - 6, cy + 8), 2)
            pygame.draw.line(tela, (255, 190, 75), (cx + 26, cy - 6), (cx + 6, cy + 8), 2)

    def draw_efeitos(self, tela, assets):
        if self.aviso_favos is not None:
            prog = self.aviso_favos["timer"] / float(max(1, self.aviso_favos["duracao"]))
            raio_prev = max(12, int(34 * (1.15 - prog * 0.4)))
            for fx, fy in self.aviso_favos["slots"]:
                pts = _pontos_hexagono(fx, fy, raio_prev)
                pygame.draw.polygon(tela, (245, 195, 70), pts, 2)

        if self.aviso_enxame is not None:
            prog = self.aviso_enxame["timer"] / float(max(1, self.aviso_enxame["duracao"]))
            pulso = math.sin(self.anim_t * 2.6) * 2.5
            slots = self._slots_enxame_atuais(self.aviso_enxame["formacao"])
            fx_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

            for px, py, _, vx, vy in slots:
                norma = math.hypot(vx, vy) or 1.0
                dx, dy = vx / norma, vy / norma
                comp_guia = 55 + prog * 65
                ex = px + dx * comp_guia
                ey = py + dy * comp_guia
                pygame.draw.line(fx_surf, (255, 195, 65, int(65 + prog * 120)), (px, py), (ex, ey), 2)
                pygame.draw.circle(fx_surf, (255, 225, 115, int(110 + prog * 130)), (int(ex), int(ey)), 4)

                raio_ext = int(12 + prog * 13 + pulso)
                pts_ext = _pontos_hexagono(px, py, raio_ext)
                pts_int = _pontos_hexagono(px, py, max(5, raio_ext - 6))
                pygame.draw.polygon(fx_surf, (235, 135, 30, int(90 + prog * 110)), pts_ext)
                pygame.draw.polygon(fx_surf, (255, 225, 105, int(150 + prog * 105)), pts_ext, 2)
                pygame.draw.polygon(fx_surf, (255, 240, 175, int(120 + prog * 120)), pts_int)

                pygame.draw.circle(fx_surf, (60, 28, 12, 220), (int(px), int(py)), max(3, int(4 + prog * 4)))

            tela.blit(fx_surf, (0, 0))

        for favo in self.favos:
            pts_ext = _pontos_hexagono(favo["x"], favo["y"], favo["raio"])
            pts_int = _pontos_hexagono(favo["x"], favo["y"], favo["raio"] - 6)
            cor_fill = (255, 240, 190) if favo["flash"] > 0 else (218, 152, 34)
            cor_miolo = (255, 210, 95) if favo["flash"] > 0 else (245, 188, 56)
            pygame.draw.polygon(tela, cor_fill, pts_ext)
            pygame.draw.polygon(tela, cor_miolo, pts_int)
            pygame.draw.polygon(tela, (72, 42, 14), pts_ext, 2)

        if self.nodulo is not None:
            nx, ny = self.nodulo["rect"].center
            pulso = int(math.sin(self.anim_t * 1.8) * 3)
            cor_ext = (255, 235, 210) if self.nodulo["flash"] > 0 else (215, 75, 55)
            cor_int = (255, 190, 70)
            pygame.draw.line(tela, (110, 38, 50), self.rect.center, (nx, ny), 6)
            pygame.draw.circle(tela, cor_ext, (nx, ny), 20 + pulso)
            pygame.draw.circle(tela, cor_int, (nx, ny), 11)
            pygame.draw.circle(tela, (65, 22, 28), (nx, ny), 20 + pulso, 2)

        for casulo in self.casulos:
            cx, cy = int(casulo["x"]), int(casulo["y"])
            prog = casulo["timer"] / float(max(1, casulo["duracao"]))
            raio = int(13 + prog * 8)

            if prog > 0.55:
                comp_linha = int(34 + (prog - 0.55) * 90)
                for i in range(6):
                    ang = casulo["rot"] + math.radians(60 * i)
                    lx = int(cx + math.cos(ang) * comp_linha)
                    ly = int(cy + math.sin(ang) * comp_linha)
                    pygame.draw.line(tela, (255, 195, 85), (cx, cy), (lx, ly), 1)

            pygame.draw.circle(tela, (235, 130, 35), (cx, cy), raio)
            pygame.draw.circle(tela, (255, 225, 110), (cx, cy), max(4, raio - 5))
            pygame.draw.circle(tela, (80, 38, 14), (cx, cy), raio, 2)

        for pt in self.particulas_mel:
            pygame.draw.circle(tela, pt["cor"], (int(pt["x"]), int(pt["y"])), pt["raio"])

    # ------------------------------------------------------------------
    # Animação de Derrota — Rompimento das Veias e Ruptura de Favos/Infecção
    # ------------------------------------------------------------------
    def on_iniciar_derrota(self, assets):
        self.lasers.clear()
        self.casulos.clear()
        self.favos.clear()
        self.aviso_favos = None
        self.aviso_enxame = None
        self.nodulo = None
        self.derrota_veias_fator = 1.0
        self.derrota_ondas_hex = []
        self.flash = 8
        self.shake_request = 8
        self._emitir_explosao_derrota(
            self.rect.centerx,
            self.rect.centery,
            [(255, 205, 65), (235, 130, 35), (155, 55, 45)],
            qtd=28,
        )

    def update_derrota(self, players, inimigos, tiros_inimigos, assets):
        t = self.timer_derrota
        prog = self.progresso_derrota

        self.derrota_veias_fator = max(0.0, 1.0 - prog * 2.5)

        tremor = int(math.sin(t * 1.45) * (4 + prog * 6))
        self.rect.x += tremor
        if t % 2 == 0:
            self.rect.y += 1

        for onda in self.derrota_ondas_hex[:]:
            onda["raio"] += 6.5
            onda["rot"] += 0.04
            onda["alpha"] = max(0, onda["alpha"] - 8)
            if onda["alpha"] <= 0:
                self.derrota_ondas_hex.remove(onda)

        if t % 3 == 0:
            self._emitir_explosao_derrota(
                self.rect.centerx + random.randint(-38, 38),
                self.rect.centery + random.randint(-26, 26),
                [(255, 210, 75), (235, 125, 30), (140, 50, 42)],
                qtd=5,
            )

        if t in (28, 58, 88, 114):
            assets.tocar_som("explosao")
            self.flash = 6
            self.shake_request = 7
            self.derrota_ondas_hex.append({"raio": 28.0, "rot": prog * 2.0, "alpha": 235})
            self._emitir_explosao_derrota(
                self.rect.centerx,
                self.rect.centery,
                [(255, 235, 130), (245, 150, 40), (185, 65, 45)],
                qtd=18,
            )

    def draw_derrota(self, tela, assets):
        prog = self.progresso_derrota
        self._desenhar_veias_parasitas(tela, fator_comprimento=self.derrota_veias_fator)

        par = assets.sprites.get(self.SPRITE_KEY)
        if par:
            img, mask = par
            inchar = math.sin(prog * math.pi) * 0.14
            escala = max(0.14, 1.0 + inchar - (prog ** 2.2) * 0.85)
            ang = math.sin(self.timer_derrota * 0.45) * (10.0 * prog)
            img_rot = pygame.transform.rotozoom(img, ang, escala)
            tela.blit(img_rot, img_rot.get_rect(center=self.rect.center))
            if self.flash > 0:
                mask_rot = pygame.transform.rotozoom(mask, ang, escala)
                tela.blit(mask_rot, mask_rot.get_rect(center=self.rect.center))

        if self.derrota_ondas_hex:
            fx_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            cx, cy = self.rect.center
            for onda in self.derrota_ondas_hex:
                pts = _pontos_hexagono(cx, cy, onda["raio"], rotacao=onda["rot"])
                pygame.draw.polygon(fx_surf, (255, 200, 75, int(onda["alpha"])), pts, 3)
            tela.blit(fx_surf, (0, 0))

        self._desenhar_particulas_derrota(tela)