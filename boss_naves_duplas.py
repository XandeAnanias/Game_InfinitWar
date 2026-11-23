import math
import random
import pygame
from config import LARGURA, ALTURA, GEMEOS_VIDA, GEMEOS_VELOCIDADE, SPRITES_CONFIG
from projectiles import Bullet
from boss_basic import BossBase


class BossNavesDuplas(BossBase):
    """
    Boss 5 — Valquírias Gêmeas (Alfa & Beta).
    Inspirado em Hollow Knight (Mantis Lords / Sisters of Battle) e Cuphead.
    """

    TIPO = "gemeos"
    NOME_EXIBICAO = "IRMÃS DO CAOS"
    SUBTITULO_ENTRADA = "GUARDIÃO V  •  ESQUADRÃO CARMESIM"
    SPRITE_KEY = "boss_gemea_alfa"
    VIDA_BASE = GEMEOS_VIDA
    VELOCIDADE_BASE = GEMEOS_VELOCIDADE
    Y_COMBATE = 128

    TAMANHO_NAVE = (148, 164)
    LARGURA_CORREDOR_DASH = 68

    def __init__(self, loop_nivel=1, modo_jogadores=1):
        super().__init__(loop_nivel=loop_nivel, modo_jogadores=modo_jogadores)

        self.alfa_x = float(LARGURA // 2 - 175)
        self.alfa_y = float(self.rect.centery)
        self.beta_x = float(LARGURA // 2 + 175)
        self.beta_y = float(self.rect.centery)

        self.alfa_ang = 0.0
        self.beta_ang = 0.0

        self.alfa_rect = pygame.Rect(0, 0, 124, 138)
        self.beta_rect = pygame.Rect(0, 0, 124, 138)
        self._sincronizar_rects()

        self.alfa_flash = 0
        self.beta_flash = 0

        self._sprites_base = {}
        self._fallbacks = {}

        # Máquina de estados
        self.sub_estado = "patrulha"
        self.sub_timer = 0
        self.sub_duracao = 60
        self.ciclo = 0

        # Estado do Corte Cruzado em X (Diagonal)
        self.x_modo = "aberto"
        self.x_origem_a = (95.0, 110.0)
        self.x_destino_a = (float(LARGURA - 34), float(ALTURA - 34))
        self.x_origem_b = (float(LARGURA - 95), 110.0)
        self.x_destino_b = (34.0, float(ALTURA - 34))
        self.x_ret_ini_a = self.x_destino_a
        self.x_ret_ini_b = self.x_destino_b
        self.aviso_x_alfa = False
        self.aviso_x_beta = False

        # Estado do Corredor Móvel de Lasers + Orbes Ciano
        self.aviso_corredor = False
        self.corredor_ativo = False
        self.corredor_dir = 1
        self.corredor_vel_atual = 0.0
        self.corredor_turno = 0
        self.carga_orbe = None
        self.orbes_corredor = []

        self.particulas_locais = []

        # Estado da animação de derrota
        self.derrota_fumaca = []
        self.derrota_ondas = []
        self.derrota_colidiu = False
        self.derrota_ini_a = (self.alfa_x, self.alfa_y)
        self.derrota_ini_b = (self.beta_x, self.beta_y)
        self.derrota_ponto_choque = (float(LARGURA * 0.52), 210.0)

    def _sincronizar_rects(self):
        self.alfa_rect.center = (int(self.alfa_x), int(self.alfa_y))
        self.beta_rect.center = (int(self.beta_x), int(self.beta_y))
        if not self.invulneravel:
            self.rect.center = (
                int((self.alfa_x + self.beta_x) * 0.5),
                int((self.alfa_y + self.beta_y) * 0.5),
            )

    def on_init_combate(self):
        self.sub_estado = "patrulha"
        self.sub_timer = 0
        self.sub_duracao = 72
        self.ciclo = 0
        self.alfa_ang = 0.0
        self.beta_ang = 0.0
        self.orbes_corredor = []
        self._limpar_flags()

    def estado_inicial_combate(self):
        return "patrulha"

    def _limpar_flags(self):
        self.aviso_x_alfa = False
        self.aviso_x_beta = False
        self.aviso_corredor = False
        self.corredor_ativo = False
        self.corredor_vel_atual = 0.0
        self.carga_orbe = None

    def _emitir_faiscas(self, x, y, cor, qtd=6):
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            vel = random.uniform(1.6, 4.4)
            self.particulas_locais.append({
                "x": float(x),
                "y": float(y),
                "vx": math.cos(ang) * vel,
                "vy": math.sin(ang) * vel,
                "vida": random.randint(12, 20),
                "raio": random.randint(2, 4),
                "cor": cor,
            })

    def _carregar_base_rotacionada(self, assets, chave):
        if chave in self._sprites_base:
            return self._sprites_base[chave]

        cfg = SPRITES_CONFIG.get(chave, {})
        caminho = cfg.get("arquivo", "")
        if caminho:
            try:
                raw = pygame.image.load(caminho).convert_alpha()
                if raw.get_bounding_rect().width > 4:
                    escalada = pygame.transform.smoothscale(raw, self.TAMANHO_NAVE)
                    virada = pygame.transform.rotate(escalada, 180)
                    mask = pygame.mask.from_surface(virada).to_surface(
                        setcolor=(255, 255, 255, 195),
                        unsetcolor=(0, 0, 0, 0),
                    )
                    self._sprites_base[chave] = (virada, mask)
                    return self._sprites_base[chave]
            except Exception:
                pass

        par = assets.sprites.get(chave)
        if par:
            img, _ = par
            if img.get_bounding_rect().width > 4:
                escalada = pygame.transform.smoothscale(img, self.TAMANHO_NAVE)
                virada = pygame.transform.rotate(escalada, 180)
                mask = pygame.mask.from_surface(virada).to_surface(
                    setcolor=(255, 255, 255, 195),
                    unsetcolor=(0, 0, 0, 0),
                )
                self._sprites_base[chave] = (virada, mask)
                return self._sprites_base[chave]

        if chave not in self._fallbacks:
            w, h = self.TAMANHO_NAVE
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            cx = w // 2
            cor_casco = (205, 62, 48) if "alfa" in chave else (182, 46, 68)
            cor_escuro = (44, 34, 38)
            pygame.draw.polygon(surf, cor_casco, [(14, 12), (34, 78), (12, h - 8), (46, 98), (46, 32)])
            pygame.draw.polygon(surf, cor_casco, [(w - 14, 12), (w - 34, 78), (w - 12, h - 8), (w - 46, 98), (w - 46, 32)])
            pygame.draw.polygon(surf, cor_escuro, [(36, 58), (w - 36, 58), (w - 50, 90), (50, 90)])
            pygame.draw.polygon(surf, cor_casco, [(cx - 18, 22), (cx + 18, 22), (cx + 10, h - 24), (cx, h - 6), (cx - 10, h - 24)])
            mask = pygame.mask.from_surface(surf).to_surface(
                setcolor=(255, 255, 255, 195),
                unsetcolor=(0, 0, 0, 0),
            )
            self._fallbacks[chave] = (surf, mask)
        return self._fallbacks[chave]

    @staticmethod
    def _angulo_para_alvo(x0, y0, x1, y1):
        return math.degrees(math.atan2(x1 - x0, max(1.0, y1 - y0)))

    @staticmethod
    def _aproximar_angulo(atual, alvo, fator=0.18):
        diff = (alvo - atual + 180.0) % 360.0 - 180.0
        return atual + diff * fator

    def _posicao_canhao_corredor(self, lado):
        if lado == "alfa":
            return (self.alfa_x + 48.0, self.alfa_y + 44.0)
        return (self.beta_x - 48.0, self.beta_y + 44.0)

    # ------------------------------------------------------------------
    # Atualização Principal
    # ------------------------------------------------------------------
    def update(self, players, inimigos, tiros_inimigos, assets):
        super().update(players, inimigos, tiros_inimigos, assets)

        if self.estado == "entrando":
            progresso = min(1.0, max(0.0, (self.rect.centery + 90) / float(self.Y_COMBATE + 90)))
            abertura = 260.0 - progresso * 85.0
            self.alfa_x = LARGURA * 0.5 - abertura
            self.beta_x = LARGURA * 0.5 + abertura
            self.alfa_y = float(self.rect.centery)
            self.beta_y = float(self.rect.centery)
            self.alfa_ang = 0.0
            self.beta_ang = 0.0
            self._sincronizar_rects()

    def update_combate(self, players, inimigos, tiros_inimigos, assets):
        if self.alfa_flash > 0:
            self.alfa_flash -= 1
        if self.beta_flash > 0:
            self.beta_flash -= 1

        for pt in self.particulas_locais[:]:
            pt["x"] += pt["vx"]
            pt["y"] += pt["vy"]
            pt["vida"] -= 1
            if pt["vida"] <= 0:
                self.particulas_locais.remove(pt)

        for orb in self.orbes_corredor[:]:
            orb["y"] += orb["vy"]
            if orb["y"] > ALTURA + 24:
                self.orbes_corredor.remove(orb)

        fator = 1.12 if self.em_furia else 1.0
        self.sub_timer += 1

        # ==============================================================
        # FASE 0: Voo Sincronizado em Leque
        # ==============================================================
        if self.sub_estado == "patrulha":
            self._limpar_flags()
            t = self.anim_t * 0.45 * fator
            alvo_ax = LARGURA * 0.27 + math.sin(t) * 75.0
            alvo_bx = LARGURA * 0.73 - math.sin(t) * 75.0
            alvo_ay = self.Y_COMBATE + math.cos(t * 1.2) * 20.0
            alvo_by = self.Y_COMBATE - math.cos(t * 1.2) * 20.0

            self.alfa_x += (alvo_ax - self.alfa_x) * 0.10
            self.alfa_y += (alvo_ay - self.alfa_y) * 0.10
            self.beta_x += (alvo_bx - self.beta_x) * 0.10
            self.beta_y += (alvo_by - self.beta_y) * 0.10

            self.alfa_ang = self._aproximar_angulo(self.alfa_ang, math.cos(t) * 8.0)
            self.beta_ang = self._aproximar_angulo(self.beta_ang, -math.cos(t) * 8.0)

            if self.sub_timer in (26, 56):
                atira_alfa = (self.sub_timer == 26)
                ox = self.alfa_x if atira_alfa else self.beta_x
                oy = (self.alfa_y if atira_alfa else self.beta_y) + 64
                for ang_deg in (-28, -9, 9, 28):
                    rad = math.radians(90 + ang_deg)
                    tiros_inimigos.append(
                        Bullet(ox - 4, oy, math.cos(rad) * 4.4, math.sin(rad) * 4.4, owner="enemy")
                    )

            if self.sub_timer >= self.sub_duracao:
                self._iniciar_posicionar_x()

        # ==============================================================
        # ATAQUE 1: Corte Cruzado em X na Diagonal
        # ==============================================================
        elif self.sub_estado == "x_posicionar":
            self.alfa_x += (self.x_origem_a[0] - self.alfa_x) * 0.14
            self.alfa_y += (self.x_origem_a[1] - self.alfa_y) * 0.14
            self.beta_x += (self.x_origem_b[0] - self.beta_x) * 0.14
            self.beta_y += (self.x_origem_b[1] - self.beta_y) * 0.14

            ang_a = self._angulo_para_alvo(*self.x_origem_a, *self.x_destino_a)
            ang_b = self._angulo_para_alvo(*self.x_origem_b, *self.x_destino_b)
            self.alfa_ang = self._aproximar_angulo(self.alfa_ang, ang_a, 0.22)
            self.beta_ang = self._aproximar_angulo(self.beta_ang, ang_b, 0.22)

            if self.sub_timer >= self.sub_duracao:
                assets.tocar_som("olho_carregar")
                self.alfa_x, self.alfa_y = self.x_origem_a
                self.beta_x, self.beta_y = self.x_origem_b
                self.alfa_ang = ang_a
                self.beta_ang = ang_b
                self.aviso_x_alfa = True
                self.aviso_x_beta = True
                self.sub_estado = "x_prep"
                self.sub_timer = 0
                self.sub_duracao = 50 if self.em_furia else 60

        elif self.sub_estado == "x_prep":
            if self.sub_timer >= self.sub_duracao:
                assets.tocar_som("olho_laser")
                self.sub_timer = 0
                if self.em_furia:
                    self.aviso_x_alfa = False
                    self.aviso_x_beta = False
                    self.sub_estado = "x_simultaneo"
                    self.sub_duracao = 50
                else:
                    self.aviso_x_alfa = False
                    self.aviso_x_beta = True
                    self.sub_estado = "x_alfa"
                    self.sub_duracao = 54

        elif self.sub_estado == "x_alfa":
            prog = min(1.0, self.sub_timer / float(self.sub_duracao))
            ease = prog * prog * (3.0 - 2.0 * prog)
            self.alfa_x = self.x_origem_a[0] + (self.x_destino_a[0] - self.x_origem_a[0]) * ease
            self.alfa_y = self.x_origem_a[1] + (self.x_destino_a[1] - self.x_origem_a[1]) * ease

            if self.sub_timer % 4 == 0:
                self._emitir_faiscas(self.alfa_x, self.alfa_y, (255, 135, 65), qtd=3)

            if self.sub_timer >= self.sub_duracao:
                assets.tocar_som("olho_laser")
                self.aviso_x_beta = False
                self.sub_estado = "x_beta"
                self.sub_timer = 0
                self.sub_duracao = 54

        elif self.sub_estado == "x_beta":
            prog = min(1.0, self.sub_timer / float(self.sub_duracao))
            ease = prog * prog * (3.0 - 2.0 * prog)
            self.beta_x = self.x_origem_b[0] + (self.x_destino_b[0] - self.x_origem_b[0]) * ease
            self.beta_y = self.x_origem_b[1] + (self.x_destino_b[1] - self.x_origem_b[1]) * ease

            self.alfa_x += (665.0 - self.alfa_x) * 0.08
            self.alfa_y += (120.0 - self.alfa_y) * 0.08
            self.alfa_ang = self._aproximar_angulo(self.alfa_ang, 0.0, 0.16)

            if self.sub_timer % 4 == 0:
                self._emitir_faiscas(self.beta_x, self.beta_y, (255, 135, 65), qtd=3)

            if self.sub_timer >= self.sub_duracao:
                self.x_ret_ini_a = (self.alfa_x, self.alfa_y)
                self.x_ret_ini_b = (self.beta_x, self.beta_y)
                self.sub_estado = "x_retorno"
                self.sub_timer = 0
                self.sub_duracao = 34

        elif self.sub_estado == "x_simultaneo":
            prog = min(1.0, self.sub_timer / float(self.sub_duracao))
            ease = prog * prog * (3.0 - 2.0 * prog)

            self.alfa_x = self.x_origem_a[0] + (self.x_destino_a[0] - self.x_origem_a[0]) * ease
            self.alfa_y = self.x_origem_a[1] + (self.x_destino_a[1] - self.x_origem_a[1]) * ease
            self.beta_x = self.x_origem_b[0] + (self.x_destino_b[0] - self.x_origem_b[0]) * ease
            self.beta_y = self.x_origem_b[1] + (self.x_destino_b[1] - self.x_origem_b[1]) * ease

            if self.sub_timer % 4 == 0:
                self._emitir_faiscas(self.alfa_x, self.alfa_y, (255, 95, 75), qtd=3)
                self._emitir_faiscas(self.beta_x, self.beta_y, (255, 95, 75), qtd=3)

            if self.sub_timer >= self.sub_duracao:
                self.x_ret_ini_a = (self.alfa_x, self.alfa_y)
                self.x_ret_ini_b = (self.beta_x, self.beta_y)
                self.sub_estado = "x_retorno"
                self.sub_timer = 0
                self.sub_duracao = 34

        elif self.sub_estado == "x_retorno":
            prog = min(1.0, self.sub_timer / float(self.sub_duracao))
            ease = 1.0 - (1.0 - prog) * (1.0 - prog)

            self.alfa_x = self.x_ret_ini_a[0] + (620.0 - self.x_ret_ini_a[0]) * ease
            self.alfa_y = self.x_ret_ini_a[1] + (self.Y_COMBATE - self.x_ret_ini_a[1]) * ease
            self.beta_x = self.x_ret_ini_b[0] + (180.0 - self.x_ret_ini_b[0]) * ease
            self.beta_y = self.x_ret_ini_b[1] + (self.Y_COMBATE - self.x_ret_ini_b[1]) * ease

            self.alfa_ang = self._aproximar_angulo(self.alfa_ang, 0.0, 0.22)
            self.beta_ang = self._aproximar_angulo(self.beta_ang, 0.0, 0.22)

            if self.sub_timer >= self.sub_duracao:
                self._iniciar_corredor_posicionar()

        # ==============================================================
        # ATAQUE 2: Corredor Móvel de Lasers + Orbes Ciano Telegráficos
        # ==============================================================
        elif self.sub_estado == "corredor_posicionar":
            meia_largura = 144.0 if self.em_furia else 160.0
            alvo_ax = LARGURA * 0.5 - meia_largura
            alvo_bx = LARGURA * 0.5 + meia_largura
            alvo_y = 132.0

            self.alfa_x += (alvo_ax - self.alfa_x) * 0.14
            self.alfa_y += (alvo_y - self.alfa_y) * 0.14
            self.beta_x += (alvo_bx - self.beta_x) * 0.14
            self.beta_y += (alvo_y - self.beta_y) * 0.14
            self.alfa_ang = self._aproximar_angulo(self.alfa_ang, 0.0, 0.22)
            self.beta_ang = self._aproximar_angulo(self.beta_ang, 0.0, 0.22)

            if self.sub_timer >= self.sub_duracao:
                assets.tocar_som("olho_carregar")
                self.alfa_x, self.alfa_y = alvo_ax, alvo_y
                self.beta_x, self.beta_y = alvo_bx, alvo_y
                self.alfa_ang = 0.0
                self.beta_ang = 0.0
                self.aviso_corredor = True
                self.sub_estado = "corredor_prep"
                self.sub_timer = 0
                self.sub_duracao = 46 if self.em_furia else 54

        elif self.sub_estado == "corredor_prep":
            if self.sub_timer >= self.sub_duracao:
                assets.tocar_som("olho_laser")
                self.aviso_corredor = False
                self.corredor_ativo = True
                self.corredor_turno = 0
                self.carga_orbe = None
                self.sub_estado = "corredor_exec"
                self.sub_timer = 0
                self.sub_duracao = 190 if self.em_furia else 215

        elif self.sub_estado == "corredor_exec":
            prog = self.sub_timer / float(self.sub_duracao)
            meia_largura = 144.0 if self.em_furia else 160.0
            amplitude = 155.0

            centro_ant = (self.alfa_x + self.beta_x) * 0.5
            centro = LARGURA * 0.5 + math.sin(prog * math.tau) * amplitude * self.corredor_dir
            self.corredor_vel_atual = centro - centro_ant

            self.alfa_x = centro - meia_largura
            self.beta_x = centro + meia_largura
            self.alfa_y = 132.0
            self.beta_y = 132.0

            cadencia = 42 if self.em_furia else 50
            if (
                self.carga_orbe is None
                and self.sub_timer >= 14
                and self.sub_timer <= self.sub_duracao - 36
                and (self.sub_timer - 14) % cadencia == 0
            ):
                lado = "alfa" if (self.corredor_turno % 2 == 0) else "beta"
                self.corredor_turno += 1
                self.carga_orbe = {
                    "lado": lado,
                    "timer": 0,
                    "duracao": 20,
                }

            if self.carga_orbe is not None:
                self.carga_orbe["timer"] += 1
                if self.carga_orbe["timer"] >= self.carga_orbe["duracao"]:
                    assets.tocar_som("tiro")
                    ox, oy = self._posicao_canhao_corredor(self.carga_orbe["lado"])
                    self.orbes_corredor.append({
                        "x": ox,
                        "y": oy + 10.0,
                        "vy": 3.7 if self.em_furia else 3.4,
                    })
                    self.carga_orbe = None

            if self.sub_timer >= self.sub_duracao:
                self.corredor_ativo = False
                self.corredor_vel_atual = 0.0
                self.carga_orbe = None
                self.corredor_dir *= -1
                self.ciclo += 1
                self.sub_estado = "patrulha"
                self.sub_timer = 0
                self.sub_duracao = 64 if self.em_furia else 76

        self._sincronizar_rects()

    def _iniciar_posicionar_x(self):
        self._limpar_flags()
        self.x_modo = "fechado" if (self.ciclo % 2 == 1) else "aberto"

        self.x_origem_a = (95.0, 110.0)
        self.x_origem_b = (float(LARGURA - 95), 110.0)
        if self.x_modo == "aberto":
            self.x_destino_a = (float(LARGURA - 34), float(ALTURA - 34))
            self.x_destino_b = (34.0, float(ALTURA - 34))
        else:
            self.x_destino_a = (LARGURA * 0.5 + 85.0, 645.0)
            self.x_destino_b = (LARGURA * 0.5 - 85.0, 645.0)

        self.sub_estado = "x_posicionar"
        self.sub_timer = 0
        self.sub_duracao = 26

    def _iniciar_corredor_posicionar(self):
        self._limpar_flags()
        self.sub_estado = "corredor_posicionar"
        self.sub_timer = 0
        self.sub_duracao = 26

    # ------------------------------------------------------------------
    # Colisões e Dano Compartilhado
    # ------------------------------------------------------------------
    def _aplicar_dano_compartilhado(self, alvo_nome, dano):
        self.vida = max(0.0, self.vida - dano)
        if alvo_nome == "alfa":
            self.alfa_flash = 5
        else:
            self.beta_flash = 5

        if self.vida <= 0:
            self._emitir_faiscas(self.alfa_x, self.alfa_y, (255, 190, 80), qtd=22)
            self._emitir_faiscas(self.beta_x, self.beta_y, (255, 190, 80), qtd=22)

    def receber_acerto(self, tiro_rect, dano):
        if self.invulneravel:
            return False

        if tiro_rect.colliderect(self.alfa_rect):
            self._aplicar_dano_compartilhado("alfa", dano)
            return True

        if tiro_rect.colliderect(self.beta_rect):
            self._aplicar_dano_compartilhado("beta", dano)
            return True

        return False

    def receber_dano_area(self, area_rect, dano):
        if self.invulneravel:
            return
        acertou_a = area_rect.colliderect(self.alfa_rect)
        acertou_b = area_rect.colliderect(self.beta_rect)
        if acertou_a and acertou_b:
            self.vida = max(0.0, self.vida - dano * 1.3)
            self.alfa_flash = 6
            self.beta_flash = 6
        elif acertou_a:
            self._aplicar_dano_compartilhado("alfa", dano)
        elif acertou_b:
            self._aplicar_dano_compartilhado("beta", dano)

    def verificar_dano_jogador(self, player_rect):
        if self.invulneravel:
            return False

        if player_rect.colliderect(self.alfa_rect.inflate(-52, -46)):
            return True
        if player_rect.colliderect(self.beta_rect.inflate(-52, -46)):
            return True

        if self.corredor_ativo:
            feixe_a = pygame.Rect(int(self.alfa_x - 9), int(self.alfa_y + 42), 18, ALTURA)
            feixe_b = pygame.Rect(int(self.beta_x - 9), int(self.beta_y + 42), 18, ALTURA)
            if player_rect.colliderect(feixe_a) or player_rect.colliderect(feixe_b):
                return True

        for orb in self.orbes_corredor:
            orb_rect = pygame.Rect(0, 0, 16, 16)
            orb_rect.center = (int(orb["x"]), int(orb["y"]))
            if player_rect.colliderect(orb_rect):
                return True

        return False

    # ------------------------------------------------------------------
    # Renderização das Naves, Traçados, Lasers e Orbes Ciano
    # ------------------------------------------------------------------
    def _desenhar_nave(self, tela, assets, chave, cx, cy, angulo, flash, cor_propulsor):
        rad = math.radians(angulo)
        tx = cx - math.sin(rad) * 66
        ty = cy - math.cos(rad) * 66
        chama = 18 + int(abs(math.sin(self.anim_t * 2.6)) * 11)
        px = tx - math.sin(rad) * chama
        py = ty - math.cos(rad) * chama
        perp_x = math.cos(rad) * 9
        perp_y = -math.sin(rad) * 9

        pygame.draw.polygon(
            tela,
            cor_propulsor,
            [(int(tx - perp_x), int(ty - perp_y)), (int(tx + perp_x), int(ty + perp_y)), (int(px), int(py))],
        )
        pygame.draw.circle(tela, (255, 245, 210), (int(tx), int(ty)), 6)

        img_base, mask_base = self._carregar_base_rotacionada(assets, chave)
        if abs(angulo) > 0.5:
            img_rot = pygame.transform.rotate(img_base, angulo)
            rect_rot = img_rot.get_rect(center=(int(cx), int(cy)))
            tela.blit(img_rot, rect_rot)
            if flash > 0:
                mask_rot = pygame.transform.rotate(mask_base, angulo)
                tela.blit(mask_rot, mask_rot.get_rect(center=(int(cx), int(cy))))
        else:
            rect = img_base.get_rect(center=(int(cx), int(cy)))
            tela.blit(img_base, rect)
            if flash > 0:
                tela.blit(mask_base, mask_base.get_rect(center=(int(cx), int(cy))))

    def _desenhar_trilha_diagonal(self, fx_surf, origem, destino, cor_rgb, progresso):
        x0, y0 = origem
        x1, y1 = destino
        dx = x1 - x0
        dy = y1 - y0
        comp = math.hypot(dx, dy)
        if comp <= 1.0:
            return

        ux, uy = dx / comp, dy / comp
        px, py = -uy, ux
        meia_w = self.LARGURA_CORREDOR_DASH * 0.5

        poly = [
            (x0 + px * meia_w, y0 + py * meia_w),
            (x1 + px * meia_w, y1 + py * meia_w),
            (x1 - px * meia_w, y1 - py * meia_w),
            (x0 - px * meia_w, y0 - py * meia_w),
        ]

        pulso = 0.5 + 0.5 * math.sin(self.anim_t * 2.2)
        alpha_fill = int(26 + progresso * 28 + pulso * 12)
        alpha_borda = int(95 + progresso * 120)

        pygame.draw.polygon(fx_surf, (*cor_rgb, alpha_fill), poly)
        pygame.draw.line(fx_surf, (*cor_rgb, alpha_borda), poly[0], poly[1], 2)
        pygame.draw.line(fx_surf, (*cor_rgb, alpha_borda), poly[3], poly[2], 2)
        pygame.draw.line(fx_surf, (255, 240, 200, int(70 + progresso * 110)), (x0, y0), (x1, y1), 1)

        espaco = 58.0
        desloc = (self.anim_t * 14.0) % espaco
        dist = desloc + 35.0
        while dist < comp - 28.0:
            cx = x0 + ux * dist
            cy = y0 + uy * dist
            ponta = (cx + ux * 11.0, cy + uy * 11.0)
            asa_e = (cx - ux * 7.0 + px * 14.0, cy - uy * 7.0 + py * 14.0)
            asa_d = (cx - ux * 7.0 - px * 14.0, cy - uy * 7.0 - py * 14.0)
            pygame.draw.lines(fx_surf, (255, 235, 175, int(115 + progresso * 120)), False, [asa_e, ponta, asa_d], 2)
            dist += espaco

        raio_mira = int(26 - progresso * 12)
        losango = [
            (x1, y1 - raio_mira),
            (x1 + raio_mira, y1),
            (x1, y1 + raio_mira),
            (x1 - raio_mira, y1),
        ]
        pygame.draw.polygon(fx_surf, (*cor_rgb, 210), losango, 2)
        pygame.draw.circle(fx_surf, (255, 240, 190, 220), (int(x1), int(y1)), 4)

    def draw_corpo(self, tela, assets):
        cor_prop_a = (255, 70, 95) if self.em_furia else (255, 145, 50)
        cor_prop_b = (255, 70, 95) if self.em_furia else (245, 110, 65)

        self._desenhar_nave(
            tela, assets, "boss_gemea_alfa",
            self.alfa_x, self.alfa_y, self.alfa_ang, self.alfa_flash, cor_prop_a,
        )
        self._desenhar_nave(
            tela, assets, "boss_gemea_beta",
            self.beta_x, self.beta_y, self.beta_ang, self.beta_flash, cor_prop_b,
        )

    def draw_efeitos(self, tela, assets):
        precisa_fx = (
            self.aviso_x_alfa
            or self.aviso_x_beta
            or self.aviso_corredor
            or self.corredor_ativo
            or (self.carga_orbe is not None)
            or bool(self.orbes_corredor)
        )

        if precisa_fx:
            fx_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

            if self.aviso_x_alfa:
                prog = min(1.0, self.sub_timer / float(max(1, self.sub_duracao)))
                self._desenhar_trilha_diagonal(
                    fx_surf, self.x_origem_a, self.x_destino_a, (255, 85, 65), prog
                )
            if self.aviso_x_beta:
                prog = min(1.0, self.sub_timer / float(max(1, self.sub_duracao))) if self.sub_estado == "x_prep" else 0.75
                self._desenhar_trilha_diagonal(
                    fx_surf, self.x_origem_b, self.x_destino_b, (255, 145, 55), prog
                )

            if self.aviso_corredor:
                prog = min(1.0, self.sub_timer / float(max(1, self.sub_duracao)))
                larg = max(6, int(34 * (1.0 - prog * 0.7)))
                y0 = int(self.alfa_y + 42)
                for lx in (int(self.alfa_x), int(self.beta_x)):
                    pygame.draw.rect(fx_surf, (255, 180, 65, int(45 + prog * 90)), (lx - larg // 2, y0, larg, ALTURA - y0))
                    pygame.draw.line(fx_surf, (255, 235, 160, 210), (lx, y0), (lx, ALTURA), 2)

            elif self.corredor_ativo:
                cor_ext = (255, 55, 95) if self.em_furia else (255, 130, 45)
                y0 = int(self.alfa_y + 42)
                for lx in (int(self.alfa_x), int(self.beta_x)):
                    pygame.draw.rect(fx_surf, (*cor_ext, 85), (lx - 22, y0, 44, ALTURA - y0))
                    pygame.draw.rect(fx_surf, (*cor_ext, 235), (lx - 11, y0, 22, ALTURA - y0))
                    pygame.draw.rect(fx_surf, (255, 245, 215, 255), (lx - 4, y0, 8, ALTURA - y0))
                    pygame.draw.circle(fx_surf, (255, 245, 215, 255), (lx, y0), 12)
                    pygame.draw.ellipse(fx_surf, (*cor_ext, 190), (lx - 24, ALTURA - 14, 48, 14))

                if abs(self.corredor_vel_atual) > 0.35:
                    sinal = 1 if self.corredor_vel_atual > 0 else -1
                    cx_corr = int((self.alfa_x + self.beta_x) * 0.5)
                    for cy_s in (340, 490):
                        pts = [
                            (cx_corr + sinal * 14, cy_s),
                            (cx_corr - sinal * 6, cy_s - 10),
                            (cx_corr - sinal * 6, cy_s + 10),
                        ]
                        pygame.draw.polygon(fx_surf, (255, 230, 150, 95), pts)

            if self.carga_orbe is not None:
                cx_c, cy_c = self._posicao_canhao_corredor(self.carga_orbe["lado"])
                prog_c = min(1.0, self.carga_orbe["timer"] / float(max(1, self.carga_orbe["duracao"])))
                raio_anel = max(6, int(24 * (1.0 - prog_c * 0.65)))
                pygame.draw.circle(fx_surf, (70, 235, 255, 220), (int(cx_c), int(cy_c)), raio_anel, 2)
                pygame.draw.circle(fx_surf, (235, 255, 255, 240), (int(cx_c), int(cy_c)), int(3 + prog_c * 5))

            for orb in self.orbes_corredor:
                ox, oy = int(orb["x"]), int(orb["y"])
                pygame.draw.polygon(
                    fx_surf,
                    (65, 225, 255, 70),
                    [(ox - 8, oy), (ox + 8, oy), (ox, oy - 26)],
                )
                pygame.draw.circle(fx_surf, (55, 225, 255, 85), (ox, oy), 18)
                pygame.draw.circle(fx_surf, (65, 238, 255, 255), (ox, oy), 11)
                pygame.draw.circle(fx_surf, (245, 255, 255, 255), (ox, oy), 5)

            tela.blit(fx_surf, (0, 0))

        for pt in self.particulas_locais:
            pygame.draw.circle(tela, pt["cor"], (int(pt["x"]), int(pt["y"])), pt["raio"])

    # ------------------------------------------------------------------
    # Animação de Derrota — Alfa solta fumaça, bate na Beta e explodem saindo da tela
    # ------------------------------------------------------------------
    def _emitir_fumaca_derrota(self, x, y, qtd=2, intensa=False):
        for _ in range(qtd):
            tom = random.randint(36, 78) if intensa else random.randint(52, 96)
            self.derrota_fumaca.append({
                "x": float(x + random.uniform(-16, 16)),
                "y": float(y + random.uniform(-14, 14)),
                "vx": random.uniform(-1.1, 1.1),
                "vy": random.uniform(-2.4, -0.8),
                "raio": random.uniform(9.0, 15.0) if intensa else random.uniform(7.0, 12.0),
                "vida": random.randint(24, 38),
                "max_vida": 38,
                "cor": (tom, tom, tom + 6),
            })

    def on_iniciar_derrota(self, assets):
        self._limpar_flags()
        self.lasers.clear()
        self.orbes_corredor.clear()
        self.derrota_fumaca = []
        self.derrota_ondas = []
        self.derrota_colidiu = False

        # Garante que Alfa fique à esquerda e Beta à direita para a colisão visual
        if self.alfa_x > self.beta_x:
            self.alfa_x, self.beta_x = self.beta_x, self.alfa_x
            self.alfa_y, self.beta_y = self.beta_y, self.alfa_y

        self.derrota_ini_a = (float(self.alfa_x), float(self.alfa_y))
        self.derrota_ini_b = (float(self.beta_x), float(self.beta_y))
        self.derrota_ponto_choque = (float(LARGURA * 0.54), 215.0)

        self.alfa_flash = 8
        self.beta_flash = 0
        self.shake_request = 8
        self._emitir_fumaca_derrota(self.alfa_x, self.alfa_y, qtd=7, intensa=True)
        self._emitir_explosao_derrota(
            self.alfa_x,
            self.alfa_y,
            [(55, 55, 65), (255, 145, 45), (255, 220, 110)],
            qtd=22,
        )

    def update_derrota(self, players, inimigos, tiros_inimigos, assets):
        t = self.timer_derrota
        prog = self.progresso_derrota

        if self.alfa_flash > 0:
            self.alfa_flash -= 1
        if self.beta_flash > 0:
            self.beta_flash -= 1

        for fm in self.derrota_fumaca[:]:
            fm["x"] += fm["vx"]
            fm["y"] += fm["vy"]
            fm["vy"] -= 0.03
            fm["raio"] += 0.30
            fm["vida"] -= 1
            if fm["vida"] <= 0:
                self.derrota_fumaca.remove(fm)

        for onda in self.derrota_ondas[:]:
            onda["raio"] += 8.0
            onda["alpha"] = max(0, onda["alpha"] - 11)
            if onda["alpha"] <= 0:
                self.derrota_ondas.remove(onda)

        cx_choque, cy_choque = self.derrota_ponto_choque

        # ETAPA 1 (0.0 -> 0.40): Alfa começa a soltar fumaça preta, perde controle e vai em direção à Beta
        if prog < 0.40:
            p1 = prog / 0.40
            ease = p1 * p1
            alvo_a_x = cx_choque - 24.0
            alvo_a_y = cy_choque - 6.0
            alvo_b_x = cx_choque + 26.0
            alvo_b_y = cy_choque + 6.0

            oscilacao = math.sin(t * 0.65) * 16.0 * (1.0 - p1 * 0.5)
            self.alfa_x = self.derrota_ini_a[0] + (alvo_a_x - self.derrota_ini_a[0]) * ease
            self.alfa_y = self.derrota_ini_a[1] + (alvo_a_y - self.derrota_ini_a[1]) * ease + oscilacao
            self.alfa_ang = -38.0 * p1 + math.sin(t * 0.75) * 14.0

            self.beta_x = self.derrota_ini_b[0] + (alvo_b_x - self.derrota_ini_b[0]) * (p1 * 0.85)
            self.beta_y = self.derrota_ini_b[1] + (alvo_b_y - self.derrota_ini_b[1]) * (p1 * 0.85)
            self.beta_ang = math.sin(t * 0.35) * 8.0

            if t % 2 == 0:
                self._emitir_fumaca_derrota(self.alfa_x, self.alfa_y, qtd=2, intensa=True)
                self._emitir_explosao_derrota(
                    self.alfa_x + random.randint(-12, 12),
                    self.alfa_y + random.randint(-12, 12),
                    [(255, 130, 40), (255, 200, 80)],
                    qtd=2,
                )

        # ETAPA 2 (prog >= 0.40): Colisão entre as duas naves + explosões em cadeia saindo da tela!
        else:
            if not self.derrota_colidiu:
                self.derrota_colidiu = True
                self.alfa_flash = 10
                self.beta_flash = 10
                self.shake_request = 14
                assets.tocar_som("explosao")
                self.derrota_ondas.append({"raio": 20.0, "alpha": 250})
                self._emitir_fumaca_derrota(cx_choque, cy_choque, qtd=12, intensa=True)
                self._emitir_explosao_derrota(
                    cx_choque,
                    cy_choque,
                    [(255, 245, 185), (255, 135, 45), (255, 55, 65), (60, 60, 70)],
                    qtd=44,
                )

            p2 = min(1.0, (prog - 0.40) / 0.60)
            impulso = p2 ** 1.32
            # Saem girando e explodindo pela diagonal inferior-direita para fora da tela
            centro_x = cx_choque + impulso * (LARGURA * 0.72)
            centro_y = cy_choque + impulso * (ALTURA * 0.88)

            sep = 22.0
            ang_orb = t * 0.24
            self.alfa_x = centro_x - math.cos(ang_orb) * sep
            self.alfa_y = centro_y - math.sin(ang_orb) * sep
            self.beta_x = centro_x + math.cos(ang_orb) * sep
            self.beta_y = centro_y + math.sin(ang_orb) * sep

            self.alfa_ang += 9.5
            self.beta_ang -= 8.0

            if t % 2 == 0:
                self._emitir_fumaca_derrota(self.alfa_x, self.alfa_y, qtd=2, intensa=True)
                self._emitir_fumaca_derrota(self.beta_x, self.beta_y, qtd=2, intensa=True)
                self._emitir_explosao_derrota(
                    centro_x + random.randint(-28, 28),
                    centro_y + random.randint(-28, 28),
                    [(255, 155, 50), (255, 70, 60), (255, 230, 140)],
                    qtd=4,
                )

            if t % 14 == 0:
                assets.tocar_som("explosao")
                self.alfa_flash = 5
                self.beta_flash = 5
                self.shake_request = 7
                self.derrota_ondas.append({"raio": 16.0, "alpha": 220})
                self._emitir_explosao_derrota(
                    centro_x,
                    centro_y,
                    [(255, 235, 160), (255, 115, 45), (255, 55, 65)],
                    qtd=18,
                )

        self.alfa_rect.center = (int(self.alfa_x), int(self.alfa_y))
        self.beta_rect.center = (int(self.beta_x), int(self.beta_y))
        self.rect.center = (
            int((self.alfa_x + self.beta_x) * 0.5),
            int((self.alfa_y + self.beta_y) * 0.5),
        )

    def draw_derrota(self, tela, assets):
        # 1. Plumas de fumaça preta/cinza das naves avariadas
        if self.derrota_fumaca:
            smoke_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            for fm in self.derrota_fumaca:
                alpha = max(0, min(210, int((fm["vida"] / float(fm["max_vida"])) * 210)))
                pygame.draw.circle(
                    smoke_surf,
                    (*fm["cor"], alpha),
                    (int(fm["x"]), int(fm["y"])),
                    int(fm["raio"]),
                )
            tela.blit(smoke_surf, (0, 0))

        # 2. As duas naves gêmeas enquanto ainda estiverem visíveis na tela
        margem = 220
        if -margem <= self.alfa_x <= LARGURA + margem and -margem <= self.alfa_y <= ALTURA + margem:
            self._desenhar_nave(
                tela, assets, "boss_gemea_alfa",
                self.alfa_x, self.alfa_y, self.alfa_ang, self.alfa_flash, (255, 95, 45),
            )
        if -margem <= self.beta_x <= LARGURA + margem and -margem <= self.beta_y <= ALTURA + margem:
            self._desenhar_nave(
                tela, assets, "boss_gemea_beta",
                self.beta_x, self.beta_y, self.beta_ang, self.beta_flash, (255, 70, 95),
            )

        # 3. Ondas de choque da colisão e explosões
        if self.derrota_ondas:
            onda_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            cx_o, cy_o = self.rect.center
            for onda in self.derrota_ondas:
                pygame.draw.circle(
                    onda_surf,
                    (255, 200, 110, int(onda["alpha"])),
                    (cx_o, cy_o),
                    int(onda["raio"]),
                    3,
                )
            tela.blit(onda_surf, (0, 0))

        self._desenhar_particulas_derrota(tela)
