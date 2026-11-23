import os
import math
import random
import pygame
from config import (
    LARGURA,
    ALTURA,
    IMAGES_DIR,
    ARQUITETO_VIDA,
    ARQUITETO_VELOCIDADE,
)
from projectiles import Bullet
from boss_basic import BossBase


def _dist_ponto_segmento(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    comp_sq = dx * dx + dy * dy
    if comp_sq <= 1e-6:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / comp_sq))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _obter_sprite_arquiteto():
    """Gera o sprite do Arquiteto Estelar (Astrolábio + Singularidade) e salva PNG se não existir."""
    w, h = 188, 188
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2

    cor_ouro = (248, 210, 102)
    cor_ouro_esc = (178, 132, 42)
    cor_roxo_luz = (182, 118, 255)
    cor_roxo_esc = (58, 24, 104)
    cor_vazio = (12, 8, 22)

    # Aura externa de nebulosa
    pygame.draw.circle(surf, (130, 70, 220, 44), (cx, cy), 90)
    pygame.draw.circle(surf, (170, 110, 255, 72), (cx, cy), 74)

    # Estrela octogonal dourada de fundo (geometria sagrada)
    for rot_deg in (0, 45):
        pts = []
        for i in range(4):
            ang = math.radians(rot_deg + i * 90)
            pts.append((int(cx + math.cos(ang) * 86), int(cy + math.sin(ang) * 86)))
            ang_m = math.radians(rot_deg + i * 90 + 45)
            pts.append((int(cx + math.cos(ang_m) * 43), int(cy + math.sin(ang_m) * 43)))
        pygame.draw.polygon(surf, cor_ouro_esc, pts)
        pygame.draw.polygon(surf, cor_ouro, pts, 2)

    # Anel principal do Astrolábio
    pygame.draw.circle(surf, (26, 18, 46), (cx, cy), 64)
    pygame.draw.circle(surf, cor_ouro, (cx, cy), 64, 4)
    pygame.draw.circle(surf, cor_ouro_esc, (cx, cy), 53, 2)

    # Marcações de bússola no anel
    for i in range(12):
        ang = math.radians(i * 30)
        r1 = 53 if i % 3 == 0 else 56
        p1 = (int(cx + math.cos(ang) * r1), int(cy + math.sin(ang) * r1))
        p2 = (int(cx + math.cos(ang) * 63), int(cy + math.sin(ang) * 63))
        pygame.draw.line(surf, cor_ouro, p1, p2, 2)

    # Disco de acreção violeta + horizonte de eventos
    pygame.draw.circle(surf, cor_roxo_esc, (cx, cy), 45)
    pygame.draw.circle(surf, cor_roxo_luz, (cx, cy), 45, 3)
    pygame.draw.circle(surf, cor_vazio, (cx, cy), 34)
    pygame.draw.circle(surf, (255, 232, 150), (cx, cy), 34, 2)

    # Olho Estelar Central (pupila vertical luminosa)
    olho_ext = [(cx - 21, cy), (cx, cy - 11), (cx + 21, cy), (cx, cy + 11)]
    pygame.draw.polygon(surf, (255, 218, 100), olho_ext)
    pygame.draw.polygon(surf, (255, 252, 235), [(cx - 12, cy), (cx, cy - 6), (cx + 12, cy), (cx, cy + 6)])
    pygame.draw.ellipse(surf, cor_vazio, (cx - 3, cy - 9, 6, 18))

    caminho_png = os.path.join(IMAGES_DIR, "boss_buraco_negro.png")
    if os.path.isdir(IMAGES_DIR):
        try:
            pygame.image.save(surf, caminho_png)
        except Exception:
            pass

    mask = pygame.mask.from_surface(surf).to_surface(
        setcolor=(255, 255, 255, 195),
        unsetcolor=(0, 0, 0, 0),
    )
    return surf, mask


class BossArquiteto(BossBase):
    """
    Boss 6 (Final do Loop) — O Arquiteto Estelar.
    Inspirado em Hollow Knight (The Radiance) e Cuphead (Hilda Berg).
    """

    TIPO = "arquiteto"
    NOME_EXIBICAO = "A ÚLTIMA SINGULARIDADE"
    SUBTITULO_ENTRADA = "GUARDIÃO FINAL  •  LAMENTO DO VAZIO"
    SPRITE_KEY = "boss_buraco_negro"
    VIDA_BASE = ARQUITETO_VIDA
    VELOCIDADE_BASE = ARQUITETO_VELOCIDADE
    Y_COMBATE = 118

    def on_init_combate(self):
        self.sub_estado = "patrulha"
        self.sub_timer = 0
        self.sub_duracao = 66
        self.ciclo = 0

        # Ataque 1: Feixes Solares Radiais (3 rajadas alternadas estilo Radiance)
        self.malha_etapa = 0
        self.malha_etapas_total = 3
        self.malha_offset_base = 0.0
        self.malha_feixes = []
        self.aviso_malha = False
        self.malha_ativa = False

        # Ataque 2: Chuva de Lanças Celestiais
        self.lancas_onda = 0
        self.lancas_ondas_total = 2
        self.lancas_slots = []
        self.aviso_lancas = False
        self.lancas_ativas = []

        # Ataque 3: Constelação de Obeliscos
        self.pilares = []

        # Ataque 4: Singularidade Gravitacional
        self.aviso_sing = False
        self.sing_ativa = False
        self.sing_onda_idx = 0
        self.orbes_sing = []

        self.particulas_locais = []

    def estado_inicial_combate(self):
        return "patrulha"

    def _limpar_flags(self):
        self.aviso_malha = False
        self.malha_ativa = False
        self.malha_feixes = []
        self.aviso_lancas = False
        self.lancas_slots = []
        self.aviso_sing = False
        self.sing_ativa = False

    def _emitir_faiscas(self, x, y, cor, qtd=10):
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            vel = random.uniform(1.8, 5.2)
            self.particulas_locais.append({
                "x": float(x),
                "y": float(y),
                "vx": math.cos(ang) * vel,
                "vy": math.sin(ang) * vel,
                "vida": random.randint(14, 24),
                "raio": random.randint(2, 5),
                "cor": cor,
            })

    def _garantir_sprite(self, assets):
        par = assets.sprites.get(self.SPRITE_KEY)
        if par and par[0].get_bounding_rect().width > 8:
            return par
        gerado = _obter_sprite_arquiteto()
        assets.sprites[self.SPRITE_KEY] = gerado
        return gerado

    # ------------------------------------------------------------------
    # Atualização Principal
    # ------------------------------------------------------------------
    def update_combate(self, players, inimigos, tiros_inimigos, assets):
        for pt in self.particulas_locais[:]:
            pt["x"] += pt["vx"]
            pt["y"] += pt["vy"]
            pt["vida"] -= 1
            if pt["vida"] <= 0:
                self.particulas_locais.remove(pt)

        # Atualiza Lanças Celestiais em queda
        for lanca in self.lancas_ativas[:]:
            lanca["x"] += lanca["vx"]
            lanca["y"] += lanca["vy"]
            lanca["rect"].center = (int(lanca["x"]), int(lanca["y"]))
            if lanca["y"] > ALTURA + 90:
                self.lancas_ativas.remove(lanca)

        # Atualiza orbes dos anéis da Singularidade
        for orb in self.orbes_sing[:]:
            orb["x"] += orb["vx"]
            orb["y"] += orb["vy"]
            if (
                orb["x"] < -30
                or orb["x"] > LARGURA + 30
                or orb["y"] < -30
                or orb["y"] > ALTURA + 30
            ):
                self.orbes_sing.remove(orb)

        # Atualiza Obeliscos Orbitais ativos
        self._atualizar_pilares(players, tiros_inimigos, assets)

        self.sub_timer += 1
        fator = 1.18 if self.em_furia else 1.0

        # ==============================================================
        # FASE 0: Patrulha Astral (Rajadas em estrela)
        # ==============================================================
        if self.sub_estado == "patrulha":
            self._limpar_flags()
            t = self.anim_t * 0.46 * fator
            alvo_x = LARGURA * 0.5 + math.sin(t) * 195.0
            alvo_y = self.Y_COMBATE + math.sin(t * 2.0) * 16.0

            self.rect.centerx += int((alvo_x - self.rect.centerx) * 0.09)
            self.rect.centery += int((alvo_y - self.rect.centery) * 0.09)

            if self.sub_timer in (22, 48):
                assets.tocar_som("tiro")
                cx, cy = self.rect.centerx, self.rect.bottom - 14
                desloc = 8.0 if self.sub_timer == 48 else 0.0
                for ang_deg in (-42, -21, 0, 21, 42):
                    rad = math.radians(90 + ang_deg + desloc)
                    vel = 4.9 if self.em_furia else 4.5
                    tiros_inimigos.append(
                        Bullet(cx - 4, cy, math.cos(rad) * vel, math.sin(rad) * vel, owner="enemy")
                    )

            if self.sub_timer >= self.sub_duracao:
                self._iniciar_malha_posicionar()

        # ==============================================================
        # ATAQUE 1: Feixes Solares Radiais (3 Rajadas Alternadas — Radiance)
        # ==============================================================
        elif self.sub_estado == "malha_posicionar":
            self.rect.centerx += int((LARGURA * 0.5 - self.rect.centerx) * 0.16)
            self.rect.centery += int((116 - self.rect.centery) * 0.16)

            if self.sub_timer >= self.sub_duracao:
                self.rect.center = (LARGURA // 2, 116)
                self.malha_etapa = 0
                self.malha_etapas_total = 4 if self.em_furia else 3
                self.malha_offset_base = random.uniform(-6.0, 6.0)
                self._preparar_onda_malha(assets)

        elif self.sub_estado == "malha_prep":
            if self.sub_timer >= self.sub_duracao:
                assets.tocar_som("olho_laser")
                self.shake_request = 7
                self.aviso_malha = False
                self.malha_ativa = True
                for (_, _), (ex, ey) in self.malha_feixes:
                    self._emitir_faiscas(self.rect.centerx, self.rect.centery + 18, (255, 225, 115), qtd=3)
                self.sub_estado = "malha_exec"
                self.sub_timer = 0
                self.sub_duracao = 20

        elif self.sub_estado == "malha_exec":
            if self.sub_timer >= self.sub_duracao:
                self.malha_ativa = False
                self.malha_feixes = []
                self.malha_etapa += 1
                if self.malha_etapa < self.malha_etapas_total:
                    self._preparar_onda_malha(assets)
                else:
                    self._iniciar_chuva_lancas(assets)

        # ==============================================================
        # ATAQUE 2: Chuva de Lanças Celestiais (Sword Rain — Radiance)
        # ==============================================================
        elif self.sub_estado == "lancas_prep":
            t = self.anim_t * 0.45
            alvo_x = LARGURA * 0.5 + math.sin(t) * 140.0
            self.rect.centerx += int((alvo_x - self.rect.centerx) * 0.08)

            if self.sub_timer >= self.sub_duracao:
                assets.tocar_som("olho_laser")
                self.aviso_lancas = False
                for sx, sy, ang_rad in self.lancas_slots:
                    vel = 8.6 if self.em_furia else 7.6
                    rect = pygame.Rect(0, 0, 14, 68)
                    rect.center = (int(sx), int(sy))
                    self.lancas_ativas.append({
                        "x": float(sx),
                        "y": float(sy),
                        "vx": math.cos(ang_rad) * vel,
                        "vy": math.sin(ang_rad) * vel,
                        "ang_deg": math.degrees(ang_rad) - 90.0,
                        "rect": rect,
                    })
                    self._emitir_faiscas(sx, 22, (255, 220, 110), qtd=4)

                self.lancas_slots = []
                self.lancas_onda += 1
                if self.lancas_onda < self.lancas_ondas_total:
                    self._preparar_onda_lancas(assets)
                else:
                    self.sub_estado = "lancas_aguardar"
                    self.sub_timer = 0
                    self.sub_duracao = 46

        elif self.sub_estado == "lancas_aguardar":
            if self.sub_timer >= self.sub_duracao:
                self._iniciar_constelacao_pilares(assets)

        # ==============================================================
        # ATAQUE 3: Constelação de Obeliscos Destrutíveis
        # ==============================================================
        elif self.sub_estado == "pilares_fase":
            t = self.anim_t * 0.48 * fator
            alvo_x = LARGURA * 0.5 + math.cos(t) * 165.0
            self.rect.centerx += int((alvo_x - self.rect.centerx) * 0.09)
            self.rect.centery += int((self.Y_COMBATE - self.rect.centery) * 0.09)

            if not self.pilares and self.sub_timer > 18:
                self._iniciar_singularidade_posicionar()
            elif self.sub_timer >= self.sub_duracao:
                self._iniciar_singularidade_posicionar()

        # ==============================================================
        # ATAQUE 4: Singularidade Gravitacional (Anéis com Brecha)
        # ==============================================================
        elif self.sub_estado == "sing_posicionar":
            self.rect.centerx += int((LARGURA * 0.5 - self.rect.centerx) * 0.16)
            self.rect.centery += int((148 - self.rect.centery) * 0.16)

            if self.sub_timer >= self.sub_duracao:
                assets.tocar_som("olho_carregar")
                self.rect.center = (LARGURA // 2, 148)
                self.aviso_sing = True
                self.sub_estado = "sing_prep"
                self.sub_timer = 0
                self.sub_duracao = 40 if self.em_furia else 48

        elif self.sub_estado == "sing_prep":
            if self.sub_timer >= self.sub_duracao:
                assets.tocar_som("olho_invocar")
                self.aviso_sing = False
                self.sing_ativa = True
                self.sing_onda_idx = 0
                self.sub_estado = "sing_exec"
                self.sub_timer = 0
                self.sub_duracao = 185 if self.em_furia else 168

        elif self.sub_estado == "sing_exec":
            cx, cy = float(self.rect.centerx), float(self.rect.centery + 18)

            # Tração gravitacional calibrada
            forca_puxao = 1.90 if self.em_furia else 1.58
            for p in players:
                if not p.vivo:
                    continue
                dx = cx - p.rect.centerx
                dy = cy - p.rect.centery
                dist = math.hypot(dx, dy)
                if 95.0 < dist < 660.0:
                    p.rect.x += int(round((dx / dist) * forca_puxao))
                    p.rect.y += int(round((dy / dist) * forca_puxao * 0.85))
                    p.rect.clamp_ip(pygame.Rect(0, 0, LARGURA, ALTURA))

            cadencia_anel = 38 if self.em_furia else 46
            if self.sub_timer == 6 or (self.sub_timer > 6 and (self.sub_timer - 6) % cadencia_anel == 0):
                assets.tocar_som("tiro")
                angulos_brecha = (90.0, 122.0, 58.0, 106.0, 74.0)
                centro_brecha = angulos_brecha[self.sing_onda_idx % len(angulos_brecha)]
                self.sing_onda_idx += 1

                vel_anel = 3.95 if self.em_furia else 3.55
                qtd_orbes = 18
                for i in range(qtd_orbes):
                    ang_deg = i * (360.0 / qtd_orbes)
                    diff = abs((ang_deg - centro_brecha + 180.0) % 360.0 - 180.0)
                    # Brecha limpa de 72 graus para atravessar
                    if diff < 36.0:
                        continue
                    rad = math.radians(ang_deg)
                    self.orbes_sing.append({
                        "x": cx + math.cos(rad) * 36.0,
                        "y": cy + math.sin(rad) * 36.0,
                        "vx": math.cos(rad) * vel_anel,
                        "vy": math.sin(rad) * vel_anel,
                        "onda": self.sing_onda_idx,
                    })

            if self.sub_timer >= self.sub_duracao:
                self.sing_ativa = False
                self.ciclo += 1
                self.sub_estado = "patrulha"
                self.sub_timer = 0
                self.sub_duracao = 58 if self.em_furia else 68

    # ------------------------------------------------------------------
    # Helpers de Ataque
    # ------------------------------------------------------------------
    def _iniciar_malha_posicionar(self):
        self._limpar_flags()
        self.sub_estado = "malha_posicionar"
        self.sub_timer = 0
        self.sub_duracao = 20

    def _preparar_onda_malha(self, assets):
        assets.tocar_som("olho_carregar")
        self.aviso_malha = True
        self.malha_ativa = False
        self.malha_feixes = []

        ox, oy = float(self.rect.centerx), float(self.rect.centery + 18)
        comp = 840.0

        passo = 26.0
        shift = (self.malha_etapa % 2) * (passo * 0.5) + self.malha_offset_base
        for k in (-2, -1, 0, 1, 2):
            ang_deg = k * passo + shift
            rad = math.radians(90.0 + ang_deg)
            ex = ox + math.cos(rad) * comp
            ey = oy + math.sin(rad) * comp
            self.malha_feixes.append(((ox, oy), (ex, ey)))

        self.sub_estado = "malha_prep"
        self.sub_timer = 0
        if self.malha_etapa == 0:
            self.sub_duracao = 44 if self.em_furia else 52
        else:
            self.sub_duracao = 34 if self.em_furia else 40

    def _iniciar_chuva_lancas(self, assets):
        self._limpar_flags()
        self.lancas_onda = 0
        self.lancas_ondas_total = 3 if self.em_furia else 2
        self._preparar_onda_lancas(assets)

    def _preparar_onda_lancas(self, assets):
        assets.tocar_som("olho_carregar")
        self.aviso_lancas = True
        self.lancas_slots = []

        colunas = 8
        larg_col = (LARGURA - 80) / float(colunas)
        if self.lancas_onda % 2 == 0:
            brechas = {2, 5}
        else:
            brechas = {1, 6}

        tilt_deg = 0.0
        if self.em_furia:
            tilt_deg = 7.0 if (self.lancas_onda % 2 == 0) else -7.0
        ang_rad = math.radians(90.0 + tilt_deg)

        for c in range(colunas):
            if c in brechas:
                continue
            sx = 40.0 + (c + 0.5) * larg_col
            self.lancas_slots.append((sx, -36.0, ang_rad))

        self.sub_estado = "lancas_prep"
        self.sub_timer = 0
        self.sub_duracao = 40 if self.em_furia else 46

    def _iniciar_constelacao_pilares(self, assets):
        assets.tocar_som("olho_invocar")
        self._limpar_flags()
        self.pilares = []

        if self.em_furia:
            posicoes = [(135, 232), (310, 266), (490, 266), (665, 232)]
            vida_pilar = 14.0
        else:
            posicoes = [(175, 238), (400, 268), (625, 238)]
            vida_pilar = 13.0

        for idx, (px, py) in enumerate(posicoes):
            rect = pygame.Rect(0, 0, 38, 50)
            rect.center = (px, py)
            self.pilares.append({
                "base_x": float(px),
                "base_y": float(py),
                "x": float(px),
                "y": float(py),
                "fase": idx * 1.15,
                "vida": vida_pilar,
                "max_vida": vida_pilar,
                "flash": 0,
                "timer_tiro": 22 + idx * 13,
                "cadencia": 44 if self.em_furia else 52,
                "rect": rect,
            })

        self.sub_estado = "pilares_fase"
        self.sub_timer = 0
        self.sub_duracao = 175 if self.em_furia else 165

    def _atualizar_pilares(self, players, tiros_inimigos, assets):
        vivos = [pl for pl in players if pl.vivo]
        alvo = vivos[0] if vivos else None

        for p in self.pilares[:]:
            p["fase"] += 0.055
            p["x"] = p["base_x"] + math.sin(p["fase"]) * 20.0
            p["y"] = p["base_y"] + math.cos(p["fase"] * 1.4) * 9.0
            p["rect"].center = (int(p["x"]), int(p["y"]))
            if p["flash"] > 0:
                p["flash"] -= 1

            p["timer_tiro"] -= 1
            if p["timer_tiro"] <= 0:
                p["timer_tiro"] = p["cadencia"]
                assets.tocar_som("tiro")
                vel = 4.6 if self.em_furia else 4.1
                ang_base = math.pi * 0.5
                if alvo is not None:
                    dx = alvo.rect.centerx - p["x"]
                    dy = max(140.0, alvo.rect.centery - p["y"])
                    ang_base = math.atan2(dy, dx)

                for off_deg in (-10.0, 10.0):
                    rad = ang_base + math.radians(off_deg)
                    tiros_inimigos.append(
                        Bullet(p["x"] - 4, p["y"] + 20, math.cos(rad) * vel, math.sin(rad) * vel, owner="enemy", tipo="orbe_olho")
                    )

    def _iniciar_singularidade_posicionar(self):
        self._limpar_flags()
        self.pilares = []
        self.sub_estado = "sing_posicionar"
        self.sub_timer = 0
        self.sub_duracao = 22

    # ------------------------------------------------------------------
    # Colisões e Dano
    # ------------------------------------------------------------------
    def receber_acerto(self, tiro_rect, dano):
        if self.invulneravel:
            return False

        for p in self.pilares[:]:
            if tiro_rect.colliderect(p["rect"]):
                p["vida"] -= dano
                p["flash"] = 5
                if p["vida"] <= 0:
                    self._emitir_faiscas(p["x"], p["y"], (255, 218, 98), qtd=18)
                    self.vida = max(0.0, self.vida - 15.0)
                    self.flash = 6
                    self.shake_request = 6
                    self.pilares.remove(p)
                return True

        return super().receber_acerto(tiro_rect, dano)

    def receber_dano_area(self, area_rect, dano):
        if self.invulneravel:
            return
        for p in self.pilares[:]:
            if area_rect.colliderect(p["rect"]):
                p["vida"] -= dano * 0.85
                p["flash"] = 5
                if p["vida"] <= 0:
                    self._emitir_faiscas(p["x"], p["y"], (255, 218, 98), qtd=18)
                    self.vida = max(0.0, self.vida - 15.0)
                    self.pilares.remove(p)
        super().receber_dano_area(area_rect, dano)

    def verificar_dano_jogador(self, player_rect):
        if self.invulneravel:
            return False

        if player_rect.colliderect(self.rect.inflate(-38, -38)):
            return True

        for p in self.pilares:
            if player_rect.colliderect(p["rect"].inflate(-6, -6)):
                return True

        if self.malha_ativa:
            px, py = player_rect.center
            for (x1, y1), (x2, y2) in self.malha_feixes:
                if _dist_ponto_segmento(px, py, x1, y1, x2, y2) <= 12.0:
                    return True

        for lanca in self.lancas_ativas:
            if player_rect.colliderect(lanca["rect"]):
                return True

        for orb in self.orbes_sing:
            orb_rect = pygame.Rect(0, 0, 14, 14)
            orb_rect.center = (int(orb["x"]), int(orb["y"]))
            if player_rect.colliderect(orb_rect):
                return True

        return False

    # ------------------------------------------------------------------
    # Renderização do Corpo, Mandala Astral, Feixes e Lanças Celestiais
    # ------------------------------------------------------------------
    def _desenhar_mandala_fundo(self, tela, cx, cy, escala=1.0, rot_extra=0.0):
        """Mandala geométrica giratória atrás do Arquiteto (estética The Radiance)."""
        tam = max(64, int(340 * escala))
        mandala = pygame.Surface((tam, tam), pygame.SRCALPHA)
        mcx = mcy = tam // 2
        cor_ouro = (255, 110, 130) if self.em_furia else (255, 215, 105)
        cor_roxo = (210, 95, 255) if self.em_furia else (165, 110, 250)

        pulso = int(math.sin(self.anim_t * 1.3) * 6 * escala)
        pygame.draw.circle(mandala, (*cor_roxo, 24), (mcx, mcy), max(10, int(156 * escala) + pulso))
        pygame.draw.circle(mandala, (*cor_ouro, 58), (mcx, mcy), max(10, int(148 * escala) + pulso), 1)
        pygame.draw.circle(mandala, (*cor_roxo, 72), (mcx, mcy), max(8, int(124 * escala)), 1)

        ang_base = self.anim_t * 0.14 + rot_extra
        for i in range(12):
            a = ang_base + math.radians(i * 30)
            r_in = 104 * escala
            r_out = (152 if i % 2 == 0 else 136) * escala
            p1 = (mcx + math.cos(a) * r_in, mcy + math.sin(a) * r_in)
            p2 = (mcx + math.cos(a) * r_out, mcy + math.sin(a) * r_out)
            pygame.draw.line(mandala, (*cor_ouro, 85), p1, p2, 2 if i % 2 == 0 else 1)

        tela.blit(mandala, (cx - mcx, cy - mcy))

    def _desenhar_aneis_astrolabio(self, tela, cx, cy, escala=1.0, rot_mult=1.0):
        cor_ouro = (255, 95, 115) if self.em_furia else (248, 210, 102)
        cor_roxo = (210, 85, 255) if self.em_furia else (160, 108, 248)

        ang1 = self.anim_t * 0.28 * rot_mult
        raio1 = 100 * escala
        pts_octo = []
        for i in range(8):
            a = ang1 + math.radians(i * 45)
            px = int(cx + math.cos(a) * raio1)
            py = int(cy + math.sin(a) * raio1)
            pts_octo.append((px, py))
            if i % 2 == 0:
                pygame.draw.circle(tela, cor_ouro, (px, py), 4)
        pygame.draw.polygon(tela, cor_ouro, pts_octo, 2)

        ang2 = -self.anim_t * 0.45 * rot_mult
        raio2 = 84 * escala
        pts_losango = []
        for i in range(4):
            a = ang2 + math.radians(i * 90)
            px = int(cx + math.cos(a) * raio2)
            py = int(cy + math.sin(a) * raio2)
            pts_losango.append((px, py))
            pygame.draw.circle(tela, (255, 248, 215), (px, py), 5)
        pygame.draw.polygon(tela, cor_roxo, pts_losango, 2)

    def draw_corpo(self, tela, assets):
        cx, cy = self.rect.center
        self._desenhar_mandala_fundo(tela, cx, cy)
        self._desenhar_aneis_astrolabio(tela, cx, cy)

        img, mask = self._garantir_sprite(assets)
        tela.blit(img, img.get_rect(center=(cx, cy)))
        if self.flash > 0:
            tela.blit(mask, mask.get_rect(center=(cx, cy)))

    def _desenhar_lanca_celestial(self, fx_surf, x, y, ang_deg, alpha=255):
        """Desenha uma Lança de Luz cristalina estilo The Radiance."""
        lanca_surf = pygame.Surface((44, 96), pygame.SRCALPHA)
        lcx = 22
        cor_aura = (255, 105, 130) if self.em_furia else (255, 205, 85)
        cor_borda = (255, 235, 150)

        pygame.draw.polygon(
            lanca_surf,
            (*cor_aura, int(alpha * 0.34)),
            [(lcx, 4), (lcx + 15, 62), (lcx, 92), (lcx - 15, 62)],
        )
        pygame.draw.polygon(
            lanca_surf,
            (*cor_aura, alpha),
            [(lcx, 10), (lcx + 10, 62), (lcx, 86), (lcx - 10, 62)],
        )
        pygame.draw.polygon(
            lanca_surf,
            (255, 252, 235, alpha),
            [(lcx, 18), (lcx + 4, 62), (lcx, 78), (lcx - 4, 62)],
        )
        pygame.draw.line(lanca_surf, (*cor_borda, alpha), (lcx - 14, 24), (lcx + 14, 24), 2)
        pygame.draw.circle(lanca_surf, (255, 252, 235, alpha), (lcx, 24), 4)

        if abs(ang_deg) > 0.5:
            lanca_surf = pygame.transform.rotate(lanca_surf, -ang_deg)
        fx_surf.blit(lanca_surf, lanca_surf.get_rect(center=(int(x), int(y))))

    def draw_efeitos(self, tela, assets):
        for p in self.pilares:
            px, py = int(p["x"]), int(p["y"])
            pygame.draw.line(tela, (135, 85, 210), self.rect.center, (px, py), 1)

            prop_v = max(0.0, p["vida"] / float(max(1.0, p["max_vida"])))
            pygame.draw.circle(tela, (55, 35, 85), (px, py), 30, 2)
            if prop_v > 0:
                rect_arc = pygame.Rect(px - 30, py - 30, 60, 60)
                pygame.draw.arc(tela, (255, 215, 95), rect_arc, math.pi * 0.5, math.pi * 0.5 + math.tau * prop_v, 2)

            losango = [(px, py - 24), (px + 18, py), (px, py + 24), (px - 18, py)]
            cor_ext = (255, 245, 220) if p["flash"] > 0 else (242, 192, 68)
            cor_int = (255, 230, 150) if p["flash"] > 0 else (72, 34, 122)
            pygame.draw.polygon(tela, cor_ext, losango)
            pygame.draw.polygon(tela, cor_int, [(px, py - 15), (px + 10, py), (px, py + 15), (px - 10, py)])
            pygame.draw.circle(tela, (255, 242, 175), (px, py), 5)

            if p["timer_tiro"] <= 16:
                prog_t = 1.0 - (p["timer_tiro"] / 16.0)
                pygame.draw.circle(tela, (255, 225, 110), (px, py + 22), max(4, int(18 * (1.0 - prog_t))), 2)

        precisa_fx = (
            self.aviso_malha
            or self.malha_ativa
            or self.aviso_lancas
            or bool(self.lancas_ativas)
            or self.aviso_sing
            or self.sing_ativa
            or bool(self.orbes_sing)
        )

        if precisa_fx:
            fx_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

            if self.aviso_malha:
                prog = min(1.0, self.sub_timer / float(max(1, self.sub_duracao)))
                cor_rgb = (255, 100, 125) if self.em_furia else (255, 210, 88)
                for (x1, y1), (x2, y2) in self.malha_feixes:
                    dx, dy = x2 - x1, y2 - y1
                    comp = math.hypot(dx, dy) or 1.0
                    px, py = (-dy / comp) * 14.0, (dx / comp) * 14.0
                    poly = [
                        (x1 + px, y1 + py),
                        (x2 + px, y2 + py),
                        (x2 - px, y2 - py),
                        (x1 - px, y1 - py),
                    ]
                    pygame.draw.polygon(fx_surf, (*cor_rgb, int(26 + prog * 38)), poly)
                    pygame.draw.line(fx_surf, (*cor_rgb, int(105 + prog * 135)), poly[0], poly[1], 2)
                    pygame.draw.line(fx_surf, (*cor_rgb, int(105 + prog * 135)), poly[3], poly[2], 2)
                    pygame.draw.line(fx_surf, (255, 250, 225, int(90 + prog * 150)), (x1, y1), (x2, y2), 1)

                ox, oy = int(self.rect.centerx), int(self.rect.centery + 18)
                raio_r = max(10, int(34 * (1.0 - prog * 0.6)))
                pygame.draw.circle(fx_surf, (*cor_rgb, 220), (ox, oy), raio_r, 2)

            elif self.malha_ativa:
                cor_ext = (255, 75, 115) if self.em_furia else (248, 190, 68)
                for (x1, y1), (x2, y2) in self.malha_feixes:
                    pygame.draw.line(fx_surf, (*cor_ext, 95), (x1, y1), (x2, y2), 36)
                    pygame.draw.line(fx_surf, (*cor_ext, 238), (x1, y1), (x2, y2), 20)
                    pygame.draw.line(fx_surf, (255, 252, 235, 255), (x1, y1), (x2, y2), 7)
                ox, oy = int(self.rect.centerx), int(self.rect.centery + 18)
                pygame.draw.circle(fx_surf, (*cor_ext, 130), (ox, oy), 28)
                pygame.draw.circle(fx_surf, (255, 252, 235, 255), (ox, oy), 15)

            if self.aviso_lancas:
                prog = min(1.0, self.sub_timer / float(max(1, self.sub_duracao)))
                cor_rgb = (255, 100, 125) if self.em_furia else (255, 210, 88)
                for sx, sy, ang_rad in self.lancas_slots:
                    ex = sx + math.cos(ang_rad) * (ALTURA + 80)
                    ey = sy + math.sin(ang_rad) * (ALTURA + 80)
                    pygame.draw.line(fx_surf, (*cor_rgb, int(35 + prog * 65)), (sx, 0), (ex, ey), 18)
                    pygame.draw.line(fx_surf, (*cor_rgb, int(120 + prog * 120)), (sx, 0), (ex, ey), 2)
                    pygame.draw.circle(fx_surf, (*cor_rgb, 220), (int(sx), 22), int(12 + prog * 6), 2)
                    self._desenhar_lanca_celestial(
                        fx_surf,
                        sx,
                        28 + prog * 18,
                        math.degrees(ang_rad) - 90.0,
                        alpha=int(130 + prog * 125),
                    )

            for lanca in self.lancas_ativas:
                self._desenhar_lanca_celestial(
                    fx_surf,
                    lanca["x"],
                    lanca["y"],
                    lanca["ang_deg"],
                    alpha=255,
                )

            cx_s, cy_s = int(self.rect.centerx), int(self.rect.centery + 18)
            if self.aviso_sing:
                prog = min(1.0, self.sub_timer / float(max(1, self.sub_duracao)))
                raio_v = max(28, int(138 * (1.0 - prog * 0.72)))
                pygame.draw.circle(fx_surf, (165, 95, 255, 48), (cx_s, cy_s), raio_v)
                pygame.draw.circle(fx_surf, (248, 210, 98, 215), (cx_s, cy_s), raio_v, 2)

            elif self.sing_ativa:
                pulso = int(math.sin(self.anim_t * 2.2) * 8)
                pygame.draw.circle(fx_surf, (135, 65, 235, 36), (cx_s, cy_s), 140 + pulso)
                pygame.draw.circle(fx_surf, (175, 105, 255, 68), (cx_s, cy_s), 88 - pulso // 2)
                pygame.draw.circle(fx_surf, (255, 218, 105, 185), (cx_s, cy_s), 44, 2)

                for i in range(10):
                    ang = self.anim_t * 0.55 + math.radians(i * 36)
                    r_ext = 136 - ((self.sub_timer * 3 + i * 14) % 94)
                    r_int = max(36, r_ext - 26)
                    p1 = (cx_s + math.cos(ang) * r_ext, cy_s + math.sin(ang) * r_ext)
                    p2 = (cx_s + math.cos(ang) * r_int, cy_s + math.sin(ang) * r_int)
                    pygame.draw.line(fx_surf, (215, 165, 255, 135), p1, p2, 2)

            for idx in range(len(self.orbes_sing) - 1):
                o1 = self.orbes_sing[idx]
                o2 = self.orbes_sing[idx + 1]
                if o1.get("onda") == o2.get("onda") and math.hypot(o2["x"] - o1["x"], o2["y"] - o1["y"]) < 145:
                    pygame.draw.line(
                        fx_surf,
                        (185, 125, 255, 95),
                        (int(o1["x"]), int(o1["y"])),
                        (int(o2["x"]), int(o2["y"])),
                        2,
                    )

            for orb in self.orbes_sing:
                ox, oy = int(orb["x"]), int(orb["y"])
                pygame.draw.circle(fx_surf, (175, 95, 255, 95), (ox, oy), 15)
                pygame.draw.circle(fx_surf, (248, 198, 88, 255), (ox, oy), 9)
                pygame.draw.circle(fx_surf, (255, 252, 235, 255), (ox, oy), 4)

            tela.blit(fx_surf, (0, 0))

        for pt in self.particulas_locais:
            pygame.draw.circle(tela, pt["cor"], (int(pt["x"]), int(pt["y"])), pt["raio"])

    # ------------------------------------------------------------------
    # Animação de Derrota — Ascensão e Liberação de Luz Branca Pura
    # ------------------------------------------------------------------
    def on_iniciar_derrota(self, assets):
        self._limpar_flags()
        self.lasers.clear()
        self.lancas_ativas.clear()
        self.pilares.clear()
        self.orbes_sing.clear()
        self.derrota_ondas = [{"raio": 22.0, "alpha": 235}]
        self.shake_request = 10
        assets.tocar_som("olho_carregar")
        self._emitir_explosao_derrota(
            self.rect.centerx,
            self.rect.centery,
            [(255, 255, 255), (255, 238, 175), (200, 155, 255)],
            qtd=34,
        )

    def update_derrota(self, players, inimigos, tiros_inimigos, assets):
        t = self.timer_derrota
        prog = self.progresso_derrota

        # Move suavemente para o centro superior enquanto vibra de energia
        alvo_x = LARGURA * 0.5 + math.sin(t * 1.15) * (5.5 * (1.0 - prog))
        alvo_y = 165.0 + math.cos(t * 0.9) * (3.5 * (1.0 - prog))
        self.rect.centerx += int((alvo_x - self.rect.centerx) * 0.12)
        self.rect.centery += int((alvo_y - self.rect.centery) * 0.12)

        for onda in self.derrota_ondas[:]:
            onda["raio"] += 7.5
            onda["alpha"] = max(0, onda["alpha"] - 6)
            if onda["alpha"] <= 0:
                self.derrota_ondas.remove(onda)

        if t % 3 == 0 and prog < 0.85:
            ang = random.uniform(0, math.tau)
            dist = random.uniform(45, 135)
            px = self.rect.centerx + math.cos(ang) * dist
            py = self.rect.centery + math.sin(ang) * dist
            self._emitir_explosao_derrota(
                px, py, [(255, 255, 255), (255, 235, 165)], qtd=3
            )

        if t in (28, 56, 84, 108):
            assets.tocar_som("olho_laser" if t in (56, 108) else "explosao")
            self.flash = 8
            self.shake_request = 9 if t >= 84 else 6
            self.derrota_ondas.append({"raio": 18.0, "alpha": 250})
            self._emitir_explosao_derrota(
                self.rect.centerx,
                self.rect.centery,
                [(255, 255, 255), (255, 245, 200), (220, 185, 255)],
                qtd=16,
            )

    def draw_derrota(self, tela, assets):
        prog = self.progresso_derrota
        t = self.timer_derrota
        cx, cy = self.rect.center

        fx_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

        # 1. Feixes de Luz Branca irradiando do Arquiteto por toda a tela
        if prog > 0.04:
            intensidade = math.sin(min(1.0, prog / 0.94) * math.pi)
            qtd_feixes = 12
            rot_base = t * 0.014
            comp_feixe = 980.0
            larg_halo = int(12 + prog * 54)
            larg_branca = int(5 + prog * 28)

            for i in range(qtd_feixes):
                ang = rot_base + i * (math.tau / qtd_feixes)
                ex = cx + math.cos(ang) * comp_feixe
                ey = cy + math.sin(ang) * comp_feixe
                alpha_halo = min(220, int(90 + intensidade * 120))
                alpha_nucleo = min(255, int(140 + intensidade * 115))
                pygame.draw.line(fx_surf, (255, 242, 195, alpha_halo), (cx, cy), (ex, ey), max(2, larg_halo))
                pygame.draw.line(fx_surf, (255, 255, 255, alpha_nucleo), (cx, cy), (ex, ey), max(1, larg_branca))

        # 2. Mandala e corpo se dissolvendo em luz branca
        if prog < 0.88:
            escala_anel = 1.0 + prog * 0.7
            self._desenhar_mandala_fundo(tela, cx, cy, escala=escala_anel, rot_extra=t * 0.03)
            self._desenhar_aneis_astrolabio(tela, cx, cy, escala=escala_anel, rot_mult=2.4)

            img, mask = self._garantir_sprite(assets)
            escala_corpo = max(0.2, 1.0 - max(0.0, prog - 0.55) * 1.9)
            img_s = pygame.transform.rotozoom(img, t * 1.4, escala_corpo)
            mask_s = pygame.transform.rotozoom(mask, t * 1.4, escala_corpo)
            tela.blit(img_s, img_s.get_rect(center=(cx, cy)))

            mask_white = mask_s.copy()
            mask_white.set_alpha(min(255, int(60 + prog * 240)))
            tela.blit(mask_white, mask_white.get_rect(center=(cx, cy)))

        # 3. Ondas expansivas de luz branca
        for onda in self.derrota_ondas:
            pygame.draw.circle(
                fx_surf,
                (255, 255, 255, int(onda["alpha"])),
                (cx, cy),
                int(onda["raio"]),
                4,
            )

        # 4. Núcleo incandescente central + clarão branco de tela cheia
        if prog < 0.95:
            raio_nucleo = int(16 + (prog ** 1.4) * 230)
            alpha_halo_c = max(0, int(195 * (1.0 - max(0.0, prog - 0.78) / 0.17)))
            alpha_core_c = max(0, int(255 * (1.0 - max(0.0, prog - 0.82) / 0.13)))
            pygame.draw.circle(fx_surf, (255, 245, 210, alpha_halo_c), (cx, cy), int(raio_nucleo * 1.35))
            pygame.draw.circle(fx_surf, (255, 255, 255, alpha_core_c), (cx, cy), raio_nucleo)

        # Flash branco pleno liberado pelo Arquiteto (pico em prog ~ 0.82, dissipa suavemente)
        if 0.52 <= prog <= 1.0:
            if prog < 0.82:
                fator_flash = (prog - 0.52) / 0.30
            else:
                fator_flash = max(0.0, 1.0 - (prog - 0.82) / 0.18)
            alpha_tela = min(235, int((fator_flash ** 1.3) * 235))
            if alpha_tela > 0:
                clarão = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                clarão.fill((255, 255, 255, alpha_tela))
                fx_surf.blit(clarão, (0, 0))

        tela.blit(fx_surf, (0, 0))
        self._desenhar_particulas_derrota(tela)
