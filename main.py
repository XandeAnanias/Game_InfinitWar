import pygame, random, os, json, sys
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))

from config import (
    LARGURA, ALTURA, FPS,
    ORDEM_NAVES,
    PONTOS_BOSS_1, PONTOS_BOSS_2, PONTOS_BOSS_3,
    PONTOS_BOSS_4, PONTOS_BOSS_5, PONTOS_BOSS_6,
    CHANCE_DROP_PODER, CHANCE_DROP_CURA_NAVE, CHANCE_DROP_MORCEGO,
    ESCALA_DANO_LOOP,
    ESCALA_MULT_PROGRESSO_LOOP, ESCALA_MULT_BONUS_LOOP,
    SPAWN_INTERVALO_INICIAL, SPAWN_REDUCAO_PROGRESSO, SPAWN_INTERVALO_MINIMO,
    LIMITE_INIMIGOS_LOOP1_MIN, LIMITE_INIMIGOS_LOOP1_MAX,
    LIMITE_INIMIGOS_BONUS_LOOP, LIMITE_INIMIGOS_TETO_GLOBAL,
    TIRO_BOMBA_RAIO, TIRO_BOMBA_DANO_AREA_INIMIGO, TIRO_BOMBA_DANO_AREA_BOSS,
)
from display_crt import DisplayCRT
from assets import AssetManager
from background import Background
from entities import (
    Player,
    Enemy,
    Boss,
    Asteroid,
    PowerUp,
    ManchaTinta,
    Particle,
    BombShockwave,
)
from ui import UI


COMBO_DURACAO_FRAMES = 180

SEQUENCIA_BOSSES = [
    ("squid",     PONTOS_BOSS_1, "boss_medio"),
    ("colmeia",   PONTOS_BOSS_2, "boss_medio"),
    ("eye",       PONTOS_BOSS_3, "boss_medio"),
    ("final",     PONTOS_BOSS_4, "boss_medio"),
    ("gemeos",    PONTOS_BOSS_5, "boss_medio"),
    ("arquiteto", PONTOS_BOSS_6, "boss_final"),
]


class TextoFlutuante:
    def __init__(self, x, y, texto, cor, fonte):
        self.x = float(x)
        self.y = float(y)
        self.vy = -1.1
        self.vida = 48
        self.vida_max = 48
        self.surf = fonte.render(texto, True, cor)

    def update(self):
        self.y += self.vy
        self.vy *= 0.96
        self.vida -= 1

    def draw(self, tela):
        if self.vida <= 0:
            return
        alpha = min(255, int((self.vida / self.vida_max) * 300))
        self.surf.set_alpha(alpha)
        tela.blit(self.surf, (int(self.x - self.surf.get_width() // 2), int(self.y)))


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.init()

        self.tela_jogo = pygame.Surface((LARGURA, ALTURA))
        self.display = DisplayCRT()
        self.clock = pygame.time.Clock()

        self.assets = AssetManager()
        self.bg = Background()
        self.ui = UI(self.assets)

        self.estado = "MENU"
        self.modo_jogadores = 1
        self.nave_p1 = "cruzador"
        self.nave_p2 = "interceptora"
        self.input_admin = ""
        self.rodando = True

        self.shake_timer = 0
        self.shake_intensidade = 0
        self.loop_nivel = 1
        self.pontos_inicio_loop = 0
        self.limiares_boss = [b[1] for b in SEQUENCIA_BOSSES]
        self.bosses_spawned = [False] * len(SEQUENCIA_BOSSES)
        self.espera_asteroide_boss = 0

        self.arquivo_recorde = "recorde.json"
        self.recorde = self._carregar_recorde()
        self.novo_recorde = False
        self.usou_admin = False
        self.alerta_recorde = 0
        self.bloqueio_tela_fim = 0

        self.combo = 0
        self.combo_timer = 0
        self.textos_flutuantes = []

        self.resetar_partida(1)
        self.assets.tocar_musica("menu")

    def aplicar_shake(self, frames=8, intensidade=4):
        self.shake_timer = max(self.shake_timer, frames)
        self.shake_intensidade = max(self.shake_intensidade, intensidade)

    def _adicionar_texto_flutuante(self, x, y, texto, cor=(255, 255, 255)):
        self.textos_flutuantes.append(
            TextoFlutuante(x, y, texto, cor, self.assets.fontes["pequena"])
        )

    def _carregar_recorde(self):
        try:
            if os.path.exists(self.arquivo_recorde):
                with open(self.arquivo_recorde, "r", encoding="utf-8") as f:
                    return max(0, int(json.load(f).get("recorde", 0)))
        except Exception:
            pass
        return 0

    def _salvar_recorde(self):
        try:
            with open(self.arquivo_recorde, "w", encoding="utf-8") as f:
                json.dump({"recorde": self.recorde}, f, indent=2)
        except Exception:
            pass

    def _verificar_recorde(self):
        if not self.usou_admin and self.pontos > self.recorde:
            if not self.novo_recorde and self.recorde > 0:
                self.alerta_recorde = 140
            self.recorde = self.pontos
            self.novo_recorde = True
            self._salvar_recorde()

    def _ciclar_nave(self, atual, delta):
        idx = ORDEM_NAVES.index(atual) if atual in ORDEM_NAVES else 0
        return ORDEM_NAVES[(idx + delta) % len(ORDEM_NAVES)]

    def resetar_partida(self, num_jogadores):
        self.modo_jogadores = num_jogadores
        self.pontos = 0
        self.pontos_inicio_loop = 0
        self.loop_nivel = 1
        self.limiares_boss = [b[1] for b in SEQUENCIA_BOSSES]
        self.bosses_spawned = [False] * len(SEQUENCIA_BOSSES)
        self.boss = None
        self.novo_recorde = False
        self.usou_admin = False
        self.alerta_recorde = 0
        self.bloqueio_tela_fim = 0
        self.espera_asteroide_boss = 0

        self.combo = 0
        self.combo_timer = 0
        self.textos_flutuantes = []

        self.espera_inimigos = 0
        self.espera_asteroides = 0
        self.shake_timer = 0
        self.shake_intensidade = 0

        self.inimigos = []
        self.asteroides = []
        self.tiros_aliados = []
        self.tiros_inimigos = []
        self.poderes = []
        self.particulas = []
        self.ondas_bomba = []
        self.manchas_tinta = []

        if num_jogadores == 1:
            self.players = [
                Player(0, LARGURA // 2 - 20, ALTURA - 75, "nave_p1", pode_alternar_tiro=True, nave_tipo=self.nave_p1)
            ]
        else:
            self.players = [
                Player(0, LARGURA // 2 - 70, ALTURA - 75, "nave_p1", pode_alternar_tiro=False, nave_tipo=self.nave_p1),
                Player(1, LARGURA // 2 + 30, ALTURA - 75, "nave_p2", pode_alternar_tiro=False, nave_tipo=self.nave_p2),
            ]

    def iniciar_modo_infinito(self):
        self.loop_nivel += 1
        self.pontos_inicio_loop = self.pontos
        self.boss = None
        self.bosses_spawned = [False] * len(SEQUENCIA_BOSSES)
        self.espera_asteroide_boss = 0
        self.limiares_boss = [self.pontos + b[1] for b in SEQUENCIA_BOSSES]
        for p in self.players:
            p.vidas = min(p.max_vidas, p.vidas + 2) if p.vivo else min(p.max_vidas, 2)
            p.invencivel = 120

        self.estado = "JOGANDO"
        self.assets.tocar_musica("fase")

    def aplicar_pontos_admin(self, valor):
        self.usou_admin = True
        self.pontos = max(0, valor)
        self.loop_nivel = 1
        self.pontos_inicio_loop = 0
        self.limiares_boss = [b[1] for b in SEQUENCIA_BOSSES]
        self.boss = None
        self.inimigos.clear()
        self.tiros_inimigos.clear()
        self.manchas_tinta.clear()

        self.bosses_spawned = [False] * len(SEQUENCIA_BOSSES)
        ultimo_atingido = -1
        for idx, limiar in enumerate(self.limiares_boss):
            if self.pontos >= limiar:
                ultimo_atingido = idx
        for idx in range(ultimo_atingido):
            self.bosses_spawned[idx] = True

        self.assets.tocar_musica("fase")

    def _invocar_chefe(self, tipo, musica_chave):
        for ini in self.inimigos:
            ini.vy = max(float(getattr(ini, "vy", 3.0)), 6.0)
            ini.cooldown_tiro = 999999

        self.boss = Boss(tipo, loop_nivel=self.loop_nivel, modo_jogadores=self.modo_jogadores)
        self.espera_asteroide_boss = 0
        self.assets.tocar_musica(musica_chave)

    def _fator_dano_loop(self):
        return 1.0 + (self.loop_nivel - 1) * ESCALA_DANO_LOOP

    def _balancear_tiro_aliado(self, tiro):
        if getattr(tiro, "_balanceado", False):
            return
        tiro._balanceado = True
        dano_base = float(getattr(tiro, "dano", 1))
        tiro.dano = round(dano_base * self._fator_dano_loop(), 2)

    def _disparar_jogador(self, player):
        qtd_antes = len(self.tiros_aliados)
        player.atirar(self.tiros_aliados, self.assets)
        for novo_tiro in self.tiros_aliados[qtd_antes:]:
            self._balancear_tiro_aliado(novo_tiro)

    def _aplicar_dano_jogador(self, player):
        if player.receber_dano(self.assets):
            self.aplicar_shake(10, 5)
            if self.combo >= 2:
                self._adicionar_texto_flutuante(player.rect.centerx, player.rect.top - 10, "COMBO QUEBRADO", (255, 115, 115))
            self.combo = 0
            self.combo_timer = 0
            return True
        return False

    def criar_explosao(self, x, y, cor, qtd=12):
        for _ in range(qtd):
            self.particulas.append(Particle(x, y, cor))

    def explodir_projetil_tinta(self, x, y):
        self.assets.tocar_som("lula_tinta")
        self.criar_explosao(x, y, (170, 70, 240), qtd=14)
        self.ondas_bomba.append(BombShockwave(x, y, raio=52, cor=(175, 75, 245)))
        self.manchas_tinta.append(ManchaTinta(x, y, self.assets))

    def detonar_bomba(self, x, y):
        self.assets.tocar_som("bomba")
        self.aplicar_shake(8, 4)
        raio = TIRO_BOMBA_RAIO
        area = pygame.Rect(0, 0, raio * 2, raio * 2)
        area.center = (x, y)
        self.ondas_bomba.append(BombShockwave(x, y, raio))

        fator = self._fator_dano_loop()
        dano_inimigo = round(TIRO_BOMBA_DANO_AREA_INIMIGO * fator, 2)
        dano_boss = round(TIRO_BOMBA_DANO_AREA_BOSS * fator, 2)

        for ini in self.inimigos[:]:
            if area.colliderect(ini.rect):
                ini.vida -= dano_inimigo
                ini.flash = 6
                if ini.vida <= 0:
                    self.abater_inimigo(ini)

        for ast in self.asteroides[:]:
            if area.colliderect(ast.rect):
                self.criar_explosao(ast.rect.centerx, ast.rect.centery, (165, 160, 155), qtd=10)
                self.asteroides.remove(ast)

        if self.boss and self.boss.vida > 0:
            self.boss.receber_dano_area(area, dano_boss)

    def abater_inimigo(self, ini):
        if ini not in self.inimigos:
            return
        self.inimigos.remove(ini)

        self.combo += 1
        self.combo_timer = COMBO_DURACAO_FRAMES
        mult_combo = min(4.0, 1.0 + (self.combo - 1) * 0.15)
        pontos_ganhos = int(round(ini.pontos * mult_combo))

        self.pontos += pontos_ganhos
        self._verificar_recorde()
        self.criar_explosao(ini.rect.centerx, ini.rect.centery, (255, 155, 50))
        self.assets.tocar_som("explosao")

        if self.combo >= 2:
            cor_pts = (255, 225, 85) if self.combo >= 5 else (130, 245, 200)
            self._adicionar_texto_flutuante(ini.rect.centerx, ini.rect.top, f"+{pontos_ganhos} (x{mult_combo:.2g})", cor_pts)

        if ini.tipo == "atirador" and random.random() < CHANCE_DROP_CURA_NAVE:
            self.poderes.append(PowerUp(ini.rect.centerx, ini.rect.centery, "cura"))
        elif ini.tipo in ("morcego", "abelha") and random.random() < CHANCE_DROP_MORCEGO:
            self.poderes.append(PowerUp(ini.rect.centerx, ini.rect.centery, random.choice(["tiro_triplo", "escudo", "bomba"])))
        elif ini.especial:
            self.poderes.append(PowerUp(ini.rect.centerx, ini.rect.centery, random.choice(["tiro_triplo", "escudo", "bomba"])))

    def _iniciar_partida_escolhida(self):
        self.resetar_partida(self.modo_jogadores)
        self.estado = "JOGANDO"
        self.assets.tocar_musica("fase")

    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
                continue

            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_F11:
                self.display.configurar(tela_cheia=not self.display.tela_cheia)
                continue

            pos_virtual = self.display.obter_pos_mouse_jogo()

            if self.estado == "MENU":
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.ui.botoes_menu["1p"].collidepoint(pos_virtual):
                        self.modo_jogadores = 1
                        self.estado = "SELECAO_NAVE"
                    elif self.ui.botoes_menu["2p"].collidepoint(pos_virtual):
                        self.modo_jogadores = 2
                        self.estado = "SELECAO_NAVE"
                    elif self.ui.botoes_menu["como_jogar"].collidepoint(pos_virtual):
                        self.estado = "COMO_JOGAR"
                    elif self.ui.botoes_menu["sons"].collidepoint(pos_virtual):
                        self.estado = "SONS"
                    elif self.ui.botoes_menu["sair"].collidepoint(pos_virtual):
                        self.rodando = False

            elif self.estado == "SELECAO_NAVE":
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        self.estado = "MENU"
                    elif evento.key == pygame.K_a:
                        self.nave_p1 = self._ciclar_nave(self.nave_p1, -1)
                        self.assets.tocar_som("tiro")
                    elif evento.key == pygame.K_d:
                        self.nave_p1 = self._ciclar_nave(self.nave_p1, 1)
                        self.assets.tocar_som("tiro")
                    elif evento.key == pygame.K_LEFT:
                        if self.modo_jogadores == 2:
                            self.nave_p2 = self._ciclar_nave(self.nave_p2, -1)
                        else:
                            self.nave_p1 = self._ciclar_nave(self.nave_p1, -1)
                        self.assets.tocar_som("tiro")
                    elif evento.key == pygame.K_RIGHT:
                        if self.modo_jogadores == 2:
                            self.nave_p2 = self._ciclar_nave(self.nave_p2, 1)
                        else:
                            self.nave_p1 = self._ciclar_nave(self.nave_p1, 1)
                        self.assets.tocar_som("tiro")
                    elif evento.key in (pygame.K_RETURN, pygame.K_c, pygame.K_SPACE):
                        self._iniciar_partida_escolhida()

                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1:
                        if self.ui.btn_voltar_nave.collidepoint(pos_virtual):
                            self.estado = "MENU"
                        elif self.ui.btn_decolar.collidepoint(pos_virtual):
                            self._iniciar_partida_escolhida()
                        else:
                            for chave, rect in self.ui.cards_naves.items():
                                if rect.collidepoint(pos_virtual):
                                    self.nave_p1 = chave
                                    self.assets.tocar_som("tiro")
                                    break
                    elif evento.button == 3 and self.modo_jogadores == 2:
                        for chave, rect in self.ui.cards_naves.items():
                            if rect.collidepoint(pos_virtual):
                                self.nave_p2 = chave
                                self.assets.tocar_som("tiro")
                                break

            elif self.estado == "COMO_JOGAR":
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    self.estado = "MENU"
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.ui.btn_voltar.collidepoint(pos_virtual):
                        self.estado = "MENU"

            elif self.estado == "SONS":
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    self.estado = "MENU"
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.ui.rect_vol_musica.collidepoint(pos_virtual):
                        rel = (pos_virtual[0] - self.ui.rect_vol_musica.x) / self.ui.rect_vol_musica.width
                        self.assets.ajustar_volume_musica(rel)
                    elif self.ui.rect_vol_efeitos.collidepoint(pos_virtual):
                        rel = (pos_virtual[0] - self.ui.rect_vol_efeitos.x) / self.ui.rect_vol_efeitos.width
                        self.assets.ajustar_volume_efeitos(rel)
                        self.assets.tocar_som("powerup")
                    elif self.ui.btn_voltar_sons.collidepoint(pos_virtual):
                        self.estado = "MENU"

            elif self.estado == "PAUSADO":
                if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_p, pygame.K_ESCAPE):
                    self.estado = "JOGANDO"
                    self.assets.retomar_musica()
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.ui.btn_continuar.collidepoint(pos_virtual):
                        self.estado = "JOGANDO"
                        self.assets.retomar_musica()
                    elif self.ui.btn_menu_pause.collidepoint(pos_virtual):
                        self.estado = "MENU"
                        self.assets.tocar_musica("menu")

            elif self.estado == "ADMIN":
                if evento.type == pygame.KEYDOWN:
                    if evento.key in (pygame.K_ESCAPE, pygame.K_F1):
                        self.estado = "JOGANDO"
                    elif evento.key == pygame.K_RETURN:
                        if self.input_admin.isdigit():
                            self.aplicar_pontos_admin(int(self.input_admin))
                        self.estado = "JOGANDO"
                    elif evento.key == pygame.K_BACKSPACE:
                        self.input_admin = self.input_admin[:-1]
                    elif evento.unicode.isdigit() and len(self.input_admin) < 7:
                        self.input_admin += evento.unicode

            elif self.estado == "VITORIA":
                if self.bloqueio_tela_fim <= 0:
                    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_RETURN:
                        self.iniciar_modo_infinito()
                    elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                        if self.ui.btn_continuar.collidepoint(pos_virtual):
                            self.iniciar_modo_infinito()
                        elif self.ui.btn_menu_pause.collidepoint(pos_virtual):
                            self.estado = "MENU"
                            self.assets.tocar_musica("menu")

            elif self.estado == "GAME_OVER":
                if self.bloqueio_tela_fim <= 0:
                    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_r:
                        self.resetar_partida(self.modo_jogadores)
                        self.estado = "JOGANDO"
                        self.assets.tocar_musica("fase")
                    elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                        if self.ui.btn_menu_pause.collidepoint(pos_virtual):
                            self.estado = "MENU"
                            self.assets.tocar_musica("menu")

            elif self.estado == "JOGANDO":
                if evento.type == pygame.KEYDOWN:
                    if evento.key in (pygame.K_p, pygame.K_ESCAPE):
                        self.estado = "PAUSADO"
                        self.assets.pausar_musica()
                    elif evento.key == pygame.K_F1:
                        self.input_admin = ""
                        self.estado = "ADMIN"
                    elif evento.key == pygame.K_q and self.modo_jogadores == 1:
                        self.players[0].alternar_modo_tiro()
                    elif evento.key == pygame.K_c:
                        self._disparar_jogador(self.players[0])
                    elif evento.key == pygame.K_SPACE and self.modo_jogadores == 2:
                        self._disparar_jogador(self.players[1])

        if self.estado == "SONS" and pygame.mouse.get_pressed()[0]:
            mx, my = self.display.obter_pos_mouse_jogo()
            if self.ui.rect_vol_musica.collidepoint((mx, my)):
                rel = (mx - self.ui.rect_vol_musica.x) / self.ui.rect_vol_musica.width
                self.assets.ajustar_volume_musica(rel)
            elif self.ui.rect_vol_efeitos.collidepoint((mx, my)):
                rel = (mx - self.ui.rect_vol_efeitos.x) / self.ui.rect_vol_efeitos.width
                self.assets.ajustar_volume_efeitos(rel)

    def _calcular_escalonamento(self):
        bonus_loop = max(0, self.loop_nivel - 1)
        ponto_final_loop = self.limiares_boss[-1] if self.limiares_boss else PONTOS_BOSS_6
        span_loop = max(1, ponto_final_loop - self.pontos_inicio_loop)
        pontos_no_loop = max(0, self.pontos - self.pontos_inicio_loop)
        progresso_loop = min(1.0, pontos_no_loop / float(span_loop))

        multiplicador = 1.0 + progresso_loop * ESCALA_MULT_PROGRESSO_LOOP + bonus_loop * ESCALA_MULT_BONUS_LOOP
        intervalo = max(
            SPAWN_INTERVALO_MINIMO,
            int(round(SPAWN_INTERVALO_INICIAL - progresso_loop * SPAWN_REDUCAO_PROGRESSO)) - bonus_loop * 6,
        )
        limite_base_loop1 = int(round(
            LIMITE_INIMIGOS_LOOP1_MIN + progresso_loop * (LIMITE_INIMIGOS_LOOP1_MAX - LIMITE_INIMIGOS_LOOP1_MIN)
        ))
        limite_inimigos = min(LIMITE_INIMIGOS_TETO_GLOBAL, limite_base_loop1 + bonus_loop * LIMITE_INIMIGOS_BONUS_LOOP)
        chance_atirador = min(0.45, 0.24 + progresso_loop * 0.08 + bonus_loop * 0.06)
        chance_dupla = 0.0 if bonus_loop == 0 else min(0.60, 0.30 + (bonus_loop - 1) * 0.15 + progresso_loop * 0.10)
        intervalo_ast = max(75, int(round(125 - progresso_loop * 20)) - bonus_loop * 12)
        limite_ast = min(7, 4 + bonus_loop)

        return {
            "multiplicador": multiplicador,
            "intervalo": intervalo,
            "limite_inimigos": limite_inimigos,
            "chance_atirador": chance_atirador,
            "chance_dupla": chance_dupla,
            "intervalo_ast": intervalo_ast,
            "limite_ast": limite_ast,
        }

    def _spawnar_inimigo_unico(self, multiplicador, chance_atirador=0.28, x_forcado=None):
        x = x_forcado if x_forcado is not None else random.randint(24, LARGURA - 64)
        if random.random() < chance_atirador:
            self.inimigos.append(Enemy(x, tipo="atirador", multiplicador=multiplicador))
        else:
            tam = random.choice([1, 2, 3])
            esp = (self.pontos >= 150) and (random.random() < CHANCE_DROP_PODER) and (len(self.poderes) == 0)
            self.inimigos.append(Enemy(x, tipo="normal", tamanho_idx=tam, especial=esp, multiplicador=multiplicador))

    def _boss_derrota_concluida(self, boss):
        return (
            getattr(boss, "derrota_concluida", False)
            or getattr(boss, "morto", False)
            or getattr(boss, "finalizado", False)
            or getattr(boss, "estado", "") in ("morto", "finalizado", "derrota_concluida")
            or getattr(boss, "progresso_derrota", 1.0) >= 1.0
        )

    def atualizar_jogo(self):
        self.bg.update()
        if self.shake_timer > 0:
            self.shake_timer -= 1
            if self.shake_timer == 0:
                self.shake_intensidade = 0

        if self.alerta_recorde > 0:
            self.alerta_recorde -= 1

        if self.bloqueio_tela_fim > 0:
            self.bloqueio_tela_fim -= 1

        if self.estado != "JOGANDO":
            return

        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo = 0

        for p in self.players:
            p.lento_tinta = any(m.contem_nave(p.rect) for m in self.manchas_tinta)
            p.lento_campo_verde = bool(self.boss and self.boss.vida > 0 and self.boss.verificar_lentidao_jogador(p.rect))

        teclas = pygame.key.get_pressed()
        limites = self.tela_jogo.get_rect()
        for p in self.players:
            p.update(teclas, limites)

        if teclas[pygame.K_c] and self.players[0].vivo:
            self._disparar_jogador(self.players[0])
        if self.modo_jogadores == 2 and teclas[pygame.K_SPACE] and self.players[1].vivo:
            self._disparar_jogador(self.players[1])

        if not any(p.vivo for p in self.players):
            self._verificar_recorde()
            self.bloqueio_tela_fim = 45
            self.estado = "GAME_OVER"
            self.assets.tocar_musica("menu")
            return

        escala = self._calcular_escalonamento()
        multiplicador = escala["multiplicador"]

        if not self.boss:
            for idx in range(len(SEQUENCIA_BOSSES) - 1, -1, -1):
                if self.pontos >= self.limiares_boss[idx] and not self.bosses_spawned[idx]:
                    tipo_b, _, mus_b = SEQUENCIA_BOSSES[idx]
                    self._invocar_chefe(tipo_b, mus_b)
                    for prev in range(idx + 1):
                        self.bosses_spawned[prev] = True
                    break

        if not self.boss:
            self.espera_inimigos += 1
            if self.espera_inimigos >= escala["intervalo"] and len(self.inimigos) < escala["limite_inimigos"]:
                self.espera_inimigos = 0
                qtd_onda = 2 if (escala["chance_dupla"] > 0 and len(self.inimigos) + 1 < escala["limite_inimigos"] and random.random() < escala["chance_dupla"]) else 1

                if qtd_onda == 1:
                    self._spawnar_inimigo_unico(multiplicador, chance_atirador=escala["chance_atirador"])
                else:
                    meio = LARGURA // 2
                    x1 = random.randint(24, max(60, meio - 55))
                    x2 = random.randint(min(LARGURA - 100, meio + 15), LARGURA - 64)
                    self._spawnar_inimigo_unico(multiplicador, chance_atirador=escala["chance_atirador"], x_forcado=x1)
                    self._spawnar_inimigo_unico(multiplicador, chance_atirador=escala["chance_atirador"], x_forcado=x2)

            self.espera_asteroides += 1
            if self.espera_asteroides >= escala["intervalo_ast"] and len(self.asteroides) < escala["limite_ast"]:
                self.espera_asteroides = 0
                self.asteroides.append(Asteroid(random.randint(20, LARGURA - 70), random.randint(20, 34), self.assets))

        if self.boss and self.boss.vida > 0 and self.boss.estado != "entrando" and self.loop_nivel >= 2:
            self.espera_asteroide_boss += 1
            cd_mut = max(95, 165 - (self.loop_nivel - 2) * 18)
            if self.espera_asteroide_boss >= cd_mut and len(self.asteroides) < 3:
                self.espera_asteroide_boss = 0
                self.asteroides.append(Asteroid(random.randint(30, LARGURA - 80), random.randint(18, 28), self.assets))

        if self.boss:
            self.boss.update(self.players, self.inimigos, self.tiros_inimigos, self.assets)
            if self.boss.shake_request > 0:
                self.aplicar_shake(self.boss.shake_request, 5)
                self.boss.shake_request = 0

            if self.boss.vida > 0:
                for p in self.players:
                    if p.vivo and self.boss.verificar_dano_jogador(p.rect) and p.tempo_escudo == 0:
                        self._aplicar_dano_jogador(p)

            if self.boss.vida <= 0:
                if not getattr(self.boss, "_derrota_iniciada_main", False):
                    self.boss._derrota_iniciada_main = True
                    self.tiros_inimigos.clear()
                    if hasattr(self.boss, "iniciar_derrota"):
                        self.boss.iniciar_derrota(self.assets)
                    else:
                        self.boss.estado = "derrotado"
                        self.assets.tocar_som("explosao")
                        self.aplicar_shake(14, 6)
                if self._boss_derrota_concluida(self.boss):
                    tipo_derrotado = self.boss.tipo
                    bx = max(110, min(LARGURA - 110, self.boss.rect.centerx))
                    by = max(120, min(ALTURA - 160, self.boss.rect.centery))
                    y_cura = min(by, 200)
                    eh_boss_final = tipo_derrotado == "arquiteto"
                    bonus_boss = 800 if eh_boss_final else 350

                    self.criar_explosao(bx, by, (255, 220, 100), qtd=45 if eh_boss_final else 35)
                    self.assets.tocar_som("explosao")
                    self.aplicar_shake(16, 6)
                    self.pontos += bonus_boss
                    self._adicionar_texto_flutuante(bx, by - 16, f"+{bonus_boss} GUARDIÃO DERROTADO", (255, 230, 95))
                    self._verificar_recorde()
                    self.poderes.append(PowerUp(bx - 18, y_cura, "cura"))
                    self.boss = None
                    self.tiros_inimigos.clear()

                    if eh_boss_final and self.loop_nivel == 1:
                        self.poderes.append(PowerUp(bx + 18, y_cura, random.choice(["tiro_triplo", "escudo", "bomba"])))
                        self.bloqueio_tela_fim = 60
                        self.estado = "VITORIA"
                        self.assets.tocar_musica("menu")
                        return
                    else:
                        self.assets.tocar_musica("fase")

        for ini in self.inimigos[:]:
            ini.update(self.tiros_inimigos)
            if ini.rect.top > ALTURA:
                self.inimigos.remove(ini)
                continue

            for p in self.players:
                if p.vivo and getattr(ini, "emergindo", 0) <= 0 and p.rect.colliderect(ini.rect):
                    if p.tempo_escudo > 0:
                        self.abater_inimigo(ini)
                    else:
                        if self._aplicar_dano_jogador(p):
                            self.inimigos.remove(ini)
                    break

        for ast in self.asteroides[:]:
            ast.update()
            if ast.rect.top > ALTURA:
                self.asteroides.remove(ast)
                continue

            for p in self.players:
                if p.vivo and p.rect.colliderect(ast.rect):
                    if p.tempo_escudo > 0:
                        self.criar_explosao(ast.rect.centerx, ast.rect.centery, (0, 255, 140))
                        self.assets.tocar_som("explosao")
                        self.asteroides.remove(ast)
                    else:
                        if self._aplicar_dano_jogador(p):
                            self.asteroides.remove(ast)
                    break

        for tiro in self.tiros_aliados[:]:
            self._balancear_tiro_aliado(tiro)
            tiro.update()
            if tiro.tipo == "bomba" and tiro.tempo <= 0:
                self.detonar_bomba(tiro.rect.centerx, tiro.rect.centery)
                self.tiros_aliados.remove(tiro)
                continue

            if tiro.fora_da_tela():
                self.tiros_aliados.remove(tiro)
                continue

            if any(tiro.rect.colliderect(ast.rect) for ast in self.asteroides):
                if tiro.tipo == "bomba":
                    self.detonar_bomba(tiro.rect.centerx, tiro.rect.centery)
                else:
                    self.criar_explosao(tiro.rect.centerx, tiro.rect.top, (180, 175, 170), qtd=4)
                self.tiros_aliados.remove(tiro)
                continue

            if self.boss and self.boss.vida > 0:
                if self.boss.invulneravel and tiro.rect.colliderect(self.boss.rect):
                    self.criar_explosao(tiro.rect.centerx, tiro.rect.top, (140, 215, 255), qtd=4)
                    self.tiros_aliados.remove(tiro)
                    continue
                if self.boss.receber_acerto(tiro.rect, tiro.dano):
                    if tiro.tipo == "bomba":
                        self.detonar_bomba(tiro.rect.centerx, tiro.rect.centery)
                    self.tiros_aliados.remove(tiro)
                    continue

            for ini in self.inimigos[:]:
                if tiro.rect.colliderect(ini.rect):
                    if tiro.tipo == "bomba":
                        self.detonar_bomba(tiro.rect.centerx, tiro.rect.centery)
                    else:
                        ini.vida -= tiro.dano
                        ini.flash = 5
                        if ini.vida <= 0:
                            self.abater_inimigo(ini)
                    self.tiros_aliados.remove(tiro)
                    break

        for tiro in self.tiros_inimigos[:]:
            tiro.update()
            if tiro.fora_da_tela():
                self.tiros_inimigos.remove(tiro)
                continue

            if any(tiro.rect.colliderect(ast.rect) for ast in self.asteroides):
                self.criar_explosao(tiro.rect.centerx, tiro.rect.bottom, (180, 175, 170), qtd=4)
                self.tiros_inimigos.remove(tiro)
                continue

            acertou_jogador = False
            for p in self.players:
                if p.vivo and tiro.rect.colliderect(p.rect):
                    if p.tempo_escudo == 0:
                        self._aplicar_dano_jogador(p)
                    if tiro.tipo == "tinta":
                        self.criar_explosao(tiro.rect.centerx, tiro.rect.centery, (170, 70, 240), qtd=10)
                    self.tiros_inimigos.remove(tiro)
                    acertou_jogador = True
                    break

            if acertou_jogador:
                continue

            if tiro.atingiu_ponto_explosao_tinta():
                self.explodir_projetil_tinta(tiro.rect.centerx, tiro.rect.centery)
                self.tiros_inimigos.remove(tiro)

        rotulos_poder = {
            "tiro_triplo": ("TIRO TRIPLO", (0, 235, 255)),
            "escudo": ("ESCUDO ATIVO", (70, 250, 145)),
            "bomba": ("TIRO BOMBA", (255, 175, 55)),
            "cura": ("+1 VIDA", (255, 95, 125)),
        }
        for pod in self.poderes[:]:
            pod.update()
            if pod.rect.top > ALTURA:
                self.poderes.remove(pod)
                continue
            for p in self.players:
                if p.vivo and p.rect.colliderect(pod.rect):
                    p.aplicar_poder(pod.tipo, self.assets)
                    txt_p, cor_p = rotulos_poder.get(pod.tipo, ("PODER", (255, 255, 255)))
                    self._adicionar_texto_flutuante(p.rect.centerx, p.rect.top - 12, txt_p, cor_p)
                    self.poderes.remove(pod)
                    break

        for mancha in self.manchas_tinta[:]:
            mancha.update()
            if mancha.vida <= 0:
                self.manchas_tinta.remove(mancha)

        for part in self.particulas[:]:
            part.update()
            if part.vida <= 0:
                self.particulas.remove(part)

        for onda in self.ondas_bomba[:]:
            onda.update()
            if onda.vida <= 0:
                self.ondas_bomba.remove(onda)

        for txt_f in self.textos_flutuantes[:]:
            txt_f.update()
            if txt_f.vida <= 0:
                self.textos_flutuantes.remove(txt_f)

    def desenhar(self):
        mouse_pos = self.display.obter_pos_mouse_jogo()
        canvas = self.tela_jogo
        self.bg.draw(canvas)

        if self.estado == "MENU":
            self.ui.draw_menu(canvas, mouse_pos, self.recorde)
        elif self.estado == "SELECAO_NAVE":
            self.ui.draw_selecao_nave(canvas, mouse_pos, self.modo_jogadores, self.nave_p1, self.nave_p2)
        elif self.estado == "COMO_JOGAR":
            self.ui.draw_como_jogar(canvas, mouse_pos)
        elif self.estado == "SONS":
            self.ui.draw_sons(canvas, mouse_pos)
        else:
            for mancha in self.manchas_tinta:
                mancha.draw(canvas)
            for ast in self.asteroides:
                ast.draw(canvas)
            for pod in self.poderes:
                pod.draw(canvas, self.assets)
            for ini in self.inimigos:
                ini.draw(canvas, self.assets)
            if self.boss:
                self.boss.draw(canvas, self.assets)
            for tiro in self.tiros_aliados:
                tiro.draw(canvas)
            for tiro in self.tiros_inimigos:
                tiro.draw(canvas)
            for p in self.players:
                p.draw(canvas, self.assets, mostrar_tag=(self.modo_jogadores == 2))
            for part in self.particulas:
                part.draw(canvas)
            for onda in self.ondas_bomba:
                onda.draw(canvas)
            for txt_f in self.textos_flutuantes:
                txt_f.draw(canvas)

            combo_prop = self.combo_timer / float(COMBO_DURACAO_FRAMES) if self.combo >= 2 else 0.0
            self.ui.draw_hud(
                canvas,
                self.players,
                self.pontos,
                self.loop_nivel,
                recorde=self.recorde,
                novo_recorde=self.novo_recorde,
                alerta_recorde=self.alerta_recorde,
                boss=self.boss,
                combo=self.combo,
                combo_prop=combo_prop,
            )

            if self.estado == "PAUSADO":
                self.ui.draw_pause(canvas, mouse_pos)
            elif self.estado == "ADMIN":
                self.ui.draw_admin(canvas, self.input_admin)
            elif self.estado == "VITORIA":
                self.ui.draw_vitoria(canvas, self.pontos, mouse_pos, self.recorde, self.novo_recorde)
            elif self.estado == "GAME_OVER":
                self.ui.draw_game_over(canvas, self.pontos, mouse_pos, self.recorde, self.novo_recorde)

        offset_x, offset_y = 0, 0
        if self.shake_timer > 0 and self.shake_intensidade > 0:
            offset_x = random.randint(-self.shake_intensidade, self.shake_intensidade)
            offset_y = random.randint(-self.shake_intensidade, self.shake_intensidade)

        self.display.renderizar(canvas, offset_x, offset_y)

    def run(self):
        while self.rodando:
            self.clock.tick(FPS)
            self.processar_eventos()
            self.atualizar_jogo()
            self.desenhar()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
