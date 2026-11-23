import pygame
from config import (
    LARGURA, ALTURA, VIDA_MAXIMA,
    PONTOS_BOSS_1, PONTOS_BOSS_2, PONTOS_BOSS_3,
    PONTOS_BOSS_4, PONTOS_BOSS_5, PONTOS_BOSS_6,
    ORDEM_NAVES, NAVES_CONFIG,
)


class UI:
    def __init__(self, assets):
        self.assets = assets
        cx = LARGURA // 2 - 140
        self.botoes_menu = {
            "1p":         pygame.Rect(cx, 230, 280, 48),
            "2p":         pygame.Rect(cx, 292, 280, 48),
            "como_jogar": pygame.Rect(cx, 354, 280, 48),
            "sons":       pygame.Rect(cx, 416, 280, 48),
            "sair":       pygame.Rect(cx, 478, 280, 48),
        }
        self.rect_vol_musica = pygame.Rect(LARGURA // 2 - 160, 255, 320, 44)
        self.rect_vol_efeitos = pygame.Rect(LARGURA // 2 - 160, 345, 320, 44)
        self.btn_voltar_sons = pygame.Rect(LARGURA // 2 - 130, 435, 260, 48)
        self.btn_voltar = pygame.Rect(cx, 582, 280, 44)
        self.btn_continuar = pygame.Rect(cx, 345, 280, 48)
        self.btn_menu_pause = pygame.Rect(cx, 410, 280, 48)

        self.cards_naves = self._criar_rects_cards_naves()
        self.btn_decolar = pygame.Rect(LARGURA // 2 + 12, 578, 220, 48)
        self.btn_voltar_nave = pygame.Rect(LARGURA // 2 - 232, 578, 220, 48)

        self._pico_cooldown = {}
        self._pico_poder = {}
        self._pico_vida_boss = {}
        self._icones_armas = self._criar_icones_armas()

    def _criar_rects_cards_naves(self):
        cards = {}
        larg_card, alt_card, gap = 232, 335, 18
        inicio_x = (LARGURA - (larg_card * 3 + gap * 2)) // 2
        for idx, chave in enumerate(ORDEM_NAVES):
            cards[chave] = pygame.Rect(inicio_x + idx * (larg_card + gap), 165, larg_card, alt_card)
        return cards

    def _criar_icones_armas(self):
        icones = {}

        surf_leve = pygame.Surface((34, 34), pygame.SRCALPHA)
        cx = 17
        pygame.draw.polygon(surf_leve, (20, 24, 34), [(cx, 2), (cx - 5, 13), (cx + 5, 13)])
        pygame.draw.polygon(surf_leve, (255, 225, 55), [(cx, 4), (cx - 4, 12), (cx + 4, 12)])
        pygame.draw.rect(surf_leve, (20, 24, 34), (cx - 5, 12, 11, 18), border_radius=2)
        pygame.draw.rect(surf_leve, (235, 195, 45), (cx - 4, 13, 9, 14), border_radius=1)
        icones["leve"] = surf_leve

        surf_pesado = pygame.Surface((34, 34), pygame.SRCALPHA)
        pygame.draw.ellipse(surf_pesado, (24, 18, 28), (cx - 8, 3, 17, 16))
        pygame.draw.rect(surf_pesado, (24, 18, 28), (cx - 8, 10, 17, 21), border_radius=3)
        pygame.draw.ellipse(surf_pesado, (235, 95, 30), (cx - 7, 4, 15, 14))
        pygame.draw.rect(surf_pesado, (215, 85, 28), (cx - 7, 11, 15, 18), border_radius=2)
        pygame.draw.rect(surf_pesado, (255, 235, 155), (cx - 2, 8, 5, 18), border_radius=2)
        icones["pesado"] = surf_pesado

        surf_bomba = pygame.Surface((34, 34), pygame.SRCALPHA)
        pygame.draw.circle(surf_bomba, (190, 50, 20), (17, 18), 11)
        pygame.draw.circle(surf_bomba, (255, 130, 45), (17, 18), 8)
        pygame.draw.circle(surf_bomba, (255, 230, 140), (15, 16), 4)
        icones["bomba"] = surf_bomba

        return icones

    def _render_texto_ajustado(self, texto, fonte_key, cor, escala=1.0):
        surf = self.assets.fontes[fonte_key].render(texto, True, cor)
        if escala != 1.0:
            w = max(1, int(round(surf.get_width() * escala)))
            h = max(1, int(round(surf.get_height() * escala)))
            surf = pygame.transform.smoothscale(surf, (w, h))
        return surf

    def _desenhar_botao(self, tela, rect, texto, mouse_pos, cor_base=(35, 42, 62), cor_hover=(60, 78, 120)):
        hover = rect.collidepoint(mouse_pos)
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cor = (*cor_hover, 235) if hover else (*cor_base, 200)
        borda = (110, 190, 255) if hover else (80, 95, 125)

        pygame.draw.rect(surf, cor, surf.get_rect(), border_radius=10)
        pygame.draw.rect(surf, borda, surf.get_rect(), 2, border_radius=10)
        tela.blit(surf, rect.topleft)

        render = self.assets.fontes["padrao"].render(texto, True, (255, 255, 255))
        tela.blit(render, render.get_rect(center=rect.center))

    def draw_menu(self, tela, mouse_pos, recorde=0):
        par_fundo = self.assets.sprites.get("nave_fundo")
        if par_fundo:
            emblema = par_fundo[0].copy()
            emblema.set_alpha(55)
            tela.blit(emblema, emblema.get_rect(center=(LARGURA // 2, 135)))

        titulo = self.assets.fontes["titulo"].render("GUERRA NO INFINITO", True, (0, 255, 150))
        subtitulo = self.assets.fontes["pequena"].render("EDIÇÃO ARCADE & CO-OP", True, (160, 190, 220))
        tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 95))
        tela.blit(subtitulo, (LARGURA // 2 - subtitulo.get_width() // 2, 158))

        if recorde > 0:
            txt_rec = self.assets.fontes["pequena"].render(f"RECORDE PESSOAL: {recorde} PTS", True, (255, 215, 90))
            tela.blit(txt_rec, (LARGURA // 2 - txt_rec.get_width() // 2, 192))

        self._desenhar_botao(tela, self.botoes_menu["1p"], "1 JOGADOR (ARCADE)", mouse_pos, (25, 95, 65), (40, 145, 95))
        self._desenhar_botao(tela, self.botoes_menu["2p"], "2 JOGADORES (CO-OP)", mouse_pos, (30, 80, 125), (45, 120, 185))
        self._desenhar_botao(tela, self.botoes_menu["como_jogar"], "COMO JOGAR", mouse_pos)
        self._desenhar_botao(tela, self.botoes_menu["sons"], "SONS", mouse_pos, (35, 65, 105), (55, 95, 150))
        self._desenhar_botao(tela, self.botoes_menu["sair"], "SAIR", mouse_pos, (100, 35, 45), (150, 50, 65))

    def _desenhar_medidor_stat(self, tela, x, y, rotulo, nivel, cor):
        lbl = self._render_texto_ajustado(rotulo, "pequena", (185, 200, 220), escala=0.76)
        tela.blit(lbl, (x, y))
        for i in range(5):
            bx = x + 88 + i * 22
            cor_seg = cor if i < nivel else (34, 42, 58)
            pygame.draw.rect(tela, cor_seg, (bx, y + 3, 18, 9), border_radius=2)

    def draw_selecao_nave(self, tela, mouse_pos, modo_jogadores, sel_p1, sel_p2):
        titulo = self._render_texto_ajustado("ESCOLHA SUA NAVE", "grande", (0, 240, 175), escala=0.78)
        tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 34))

        msg_sub = (
            "Clique na nave ou use A / D e pressione C ou ENTER para decolar"
            if modo_jogadores == 1
            else "P1: A/D ou Clique Esquerdo   •   P2: Setas ou Clique Direito"
        )
        sub = self._render_texto_ajustado(msg_sub, "pequena", (175, 198, 225), escala=0.88)
        tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 82))

        for chave in ORDEM_NAVES:
            rect = self.cards_naves[chave]
            spec = NAVES_CONFIG[chave]
            cor_tema = spec["cor"]
            selecionada_p1 = (sel_p1 == chave)
            selecionada_p2 = (modo_jogadores == 2 and sel_p2 == chave)
            hover = rect.collidepoint(mouse_pos)

            card = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            fundo_alpha = 225 if (selecionada_p1 or selecionada_p2 or hover) else 185
            pygame.draw.rect(card, (16, 22, 36, fundo_alpha), card.get_rect(), border_radius=12)

            if selecionada_p1 or selecionada_p2:
                pygame.draw.rect(card, (*cor_tema, 245), card.get_rect(), 3, border_radius=12)
            elif hover:
                pygame.draw.rect(card, (130, 170, 220, 210), card.get_rect(), 2, border_radius=12)
            else:
                pygame.draw.rect(card, (65, 80, 110, 180), card.get_rect(), 1, border_radius=12)
            tela.blit(card, rect.topleft)

            if selecionada_p1:
                b1 = self._render_texto_ajustado("P1", "pequena", (105, 255, 175), escala=0.85)
                tela.blit(b1, (rect.x + 12, rect.y + 8))
            if selecionada_p2:
                b2 = self._render_texto_ajustado("P2", "pequena", (110, 205, 255), escala=0.85)
                tela.blit(b2, (rect.right - b2.get_width() - 12, rect.y + 8))

            par = self.assets.sprites.get(spec["sprite_p1"]) or self.assets.sprites.get("nave_p1")
            if par:
                img = pygame.transform.smoothscale(par[0], (82, 82))
                pygame.draw.circle(tela, (24, 34, 54), (rect.centerx, rect.y + 72), 44)
                pygame.draw.circle(tela, cor_tema, (rect.centerx, rect.y + 72), 44, 1)
                tela.blit(img, img.get_rect(center=(rect.centerx, rect.y + 72)))

            t_nome = self._render_texto_ajustado(spec["nome"], "padrao", (255, 255, 255), escala=0.86)
            t_sub = self._render_texto_ajustado(spec["subtitulo"], "pequena", cor_tema, escala=0.84)
            tela.blit(t_nome, (rect.centerx - t_nome.get_width() // 2, rect.y + 124))
            tela.blit(t_sub, (rect.centerx - t_sub.get_width() // 2, rect.y + 149))

            vel_s, bld_s, cad_s = spec["stats"]
            self._desenhar_medidor_stat(tela, rect.x + 14, rect.y + 184, "VELOCIDADE", vel_s, cor_tema)
            self._desenhar_medidor_stat(tela, rect.x + 14, rect.y + 208, "BLINDAGEM", bld_s, cor_tema)
            self._desenhar_medidor_stat(tela, rect.x + 14, rect.y + 232, "CADÊNCIA", cad_s, cor_tema)

            d1 = self._render_texto_ajustado(spec["desc_1"], "pequena", (220, 232, 245), escala=0.75)
            d2 = self._render_texto_ajustado(spec["desc_2"], "pequena", (170, 190, 215), escala=0.73)
            tela.blit(d1, (rect.centerx - d1.get_width() // 2, rect.y + 272))
            tela.blit(d2, (rect.centerx - d2.get_width() // 2, rect.y + 294))

        self._desenhar_botao(tela, self.btn_voltar_nave, "VOLTAR (ESC)", mouse_pos)
        self._desenhar_botao(tela, self.btn_decolar, "DECOLAR!", mouse_pos, (25, 105, 70), (40, 155, 100))

    def _desenhar_barra_audio(self, tela, rect, rotulo, valor, mouse_pos, cor_preenchimento):
        pygame.draw.rect(tela, (28, 34, 48), rect, border_radius=10)
        if valor > 0:
            pygame.draw.rect(
                tela,
                cor_preenchimento,
                (rect.x, rect.y, int(rect.width * valor), rect.height),
                border_radius=10,
            )
        cor_borda = (130, 210, 255) if rect.collidepoint(mouse_pos) else (80, 95, 125)
        pygame.draw.rect(tela, cor_borda, rect, 2, border_radius=10)

        texto = f"{rotulo}: {int(round(valor * 100))}%" if valor > 0 else f"{rotulo}: MUDO"
        render = self.assets.fontes["padrao"].render(texto, True, (255, 255, 255))
        tela.blit(render, render.get_rect(center=rect.center))

    def draw_sons(self, tela, mouse_pos):
        titulo = self.assets.fontes["grande"].render("CONFIGURAÇÃO DE SONS", True, (0, 235, 180))
        sub = self.assets.fontes["pequena"].render("Clique ou arraste nas barras para ajustar", True, (170, 190, 215))
        tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 130))
        tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 188))

        self._desenhar_barra_audio(tela, self.rect_vol_musica, "MÚSICA", self.assets.volume_musica, mouse_pos, (55, 145, 220))
        self._desenhar_barra_audio(tela, self.rect_vol_efeitos, "EFEITOS", self.assets.volume_efeitos, mouse_pos, (45, 175, 115))
        self._desenhar_botao(tela, self.btn_voltar_sons, "VOLTAR", mouse_pos)

    def _desenhar_card_como_jogar(self, tela, rect, cor_borda=(75, 95, 130)):
        card = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(card, (16, 22, 36, 205), card.get_rect(), border_radius=10)
        pygame.draw.rect(card, (*cor_borda, 195), card.get_rect(), 1, border_radius=10)
        tela.blit(card, rect.topleft)

    def draw_como_jogar(self, tela, mouse_pos):
        titulo = self._render_texto_ajustado("COMO JOGAR", "grande", (0, 235, 180), escala=0.76)
        tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 24))
        pygame.draw.line(tela, (55, 85, 115), (40, 68), (LARGURA - 40, 68), 1)

        margem_x = 24
        largura_card = LARGURA - margem_x * 2

        card_ctrl = pygame.Rect(margem_x, 80, largura_card, 146)
        self._desenhar_card_como_jogar(tela, card_ctrl, (70, 170, 130))
        sec_ctrl = self._render_texto_ajustado("CONTROLES", "pequena", (105, 255, 170), escala=0.90)
        tela.blit(sec_ctrl, (card_ctrl.x + 14, card_ctrl.y + 10))

        linhas_ctrl = [
            ("1P Arcade:", (135, 235, 175), "WASD Mover  •  C Atirar (segurar)  •  Q Trocar Tiro", (225, 235, 245)),
            ("2P Co-op:", (125, 205, 255), "Setas Mover  •  ESPAÇO Atirar (segurar)", (225, 235, 245)),
            ("Sistema:", (255, 215, 100), "P / ESC Pausar  •  F11 Tela Cheia", (200, 212, 228)),
        ]
        cy = card_ctrl.y + 40
        for rotulo, cor_r, desc, cor_d in linhas_ctrl:
            tela.blit(self._render_texto_ajustado(rotulo, "pequena", cor_r, escala=0.84), (card_ctrl.x + 16, cy))
            tela.blit(self._render_texto_ajustado(desc, "pequena", cor_d, escala=0.84), (card_ctrl.x + 112, cy))
            cy += 32

        card_pod = pygame.Rect(margem_x, 238, largura_card, 238)
        self._desenhar_card_como_jogar(tela, card_pod, (185, 155, 65))
        sec_pod = self._render_texto_ajustado("PODERES & ITENS", "pequena", (255, 215, 85), escala=0.90)
        tela.blit(sec_pod, (card_pod.x + 14, card_pod.y + 10))

        itens_poder = [
            ("tiro_triplo", "Tiro Triplo:", (255, 215, 95), "Dispara 3 projéteis simultâneos em leque."),
            ("escudo", "Escudo:", (95, 240, 155), "Bloqueia dano e destrói naves ao colidir."),
            ("bomba", "Tiro Bomba:", (255, 130, 80), "Disparo explosivo em área por tempo limitado."),
            ("cura", "Coração:", (255, 110, 135), "Recupera +1 de vida (até o máximo da nave)."),
        ]

        py = card_pod.y + 38
        for chave_ic, nome_p, cor_p, desc_p in itens_poder:
            icone = self.assets.icones_poder.get(chave_ic)
            if icone:
                tela.blit(pygame.transform.smoothscale(icone, (28, 28)), (card_pod.x + 14, py + 4))
            tela.blit(self._render_texto_ajustado(nome_p, "pequena", cor_p, escala=0.86), (card_pod.x + 50, py + 1))
            tela.blit(self._render_texto_ajustado(desc_p, "pequena", (215, 225, 238), escala=0.80), (card_pod.x + 50, py + 20))
            py += 48

        card_obj = pygame.Rect(margem_x, 488, largura_card, 74)
        self._desenhar_card_como_jogar(tela, card_obj, (75, 135, 200))
        tela.blit(self._render_texto_ajustado("OBJETIVO", "pequena", (110, 205, 255), escala=0.90), (card_obj.x + 14, card_obj.y + 8))
        tela.blit(
            self._render_texto_ajustado("Encadeie abates (Combo até 4x) e enfrente os 6 Guardiões Estelares.", "pequena", (220, 230, 242), escala=0.80),
            (card_obj.x + 14, card_obj.y + 30),
        )
        tela.blit(
            self._render_texto_ajustado("DEVORADOR DAS PROFUNDEZAS • COLMEIA PROFANA • SENTINELA ESMERALDA • ARAUTO DA EXTINÇÃO • IRMÃS DO CAOS • LAMENTO DO VAZIO", 
            "pequena", (185, 205, 228), escala=0.55),
            (card_obj.x + 14, card_obj.y + 49),
        )

        self._desenhar_botao(tela, self.btn_voltar, "VOLTAR AO MENU", mouse_pos)

    def _classificar_valor_arma(self, valor, player=None):
        if isinstance(valor, bool) or valor is None:
            return None
        texto = str(valor).strip().lower()
        if "pesad" in texto:
            return "pesado"
        if "tripl" in texto:
            return "tiro_triplo"
        if "bomb" in texto:
            return "bomba"
        return "leve"

    def _obter_info_tiro(self, player):
        if getattr(player, "tempo_tiro_bomba", 0) > 0:
            return "bomba", "TIRO BOMBA", (255, 115, 65), True
        if getattr(player, "tempo_tiro_triplo", 0) > 0:
            return "tiro_triplo", "TIRO TRIPLO", (255, 210, 65), True

        chave = self._classificar_valor_arma(getattr(player, "modo_tiro", "rapido"), player)
        if chave == "pesado":
            return "pesado", "TIRO PESADO", (255, 150, 55), False
        return "leve", "TIRO LEVE", (80, 225, 255), False

    def _obter_progresso_cooldown(self, player, chave_modo):
        cd_atual = max(0.0, float(getattr(player, "cooldown_tiro", 0)))
        if cd_atual <= 0:
            return True, 1.0

        cd_max = float(getattr(player, "cooldown_max", 0) or 1.0)
        pico = max(self._pico_cooldown.get(chave_modo, cd_max), cd_atual, 1.0)
        self._pico_cooldown[chave_modo] = pico
        return False, max(0.0, min(1.0, 1.0 - (cd_atual / pico)))

    def _desenhar_painel_arcade(self, tela, player, top_y):
        chave_modo, nome_modo, cor_modo, travado = self._obter_info_tiro(player)
        pronto, prop_cd = self._obter_progresso_cooldown(player, chave_modo)

        largura_painel, altura_painel = 216, 58
        px, py = LARGURA - 16 - largura_painel, top_y

        painel = pygame.Surface((largura_painel, altura_painel), pygame.SRCALPHA)
        pygame.draw.rect(painel, (16, 22, 36, 195), painel.get_rect(), border_radius=8)
        pygame.draw.rect(painel, (*cor_modo, 190), painel.get_rect(), 1, border_radius=8)
        tela.blit(painel, (px, py))

        icone = self.assets.icones_poder.get(chave_modo) or self._icones_armas.get(chave_modo)
        if icone:
            tela.blit(icone, (px + 6, py + 6))

        tela.blit(self._render_texto_ajustado(nome_modo, "pequena", cor_modo, escala=0.88), (px + 44, py + 6))

        if travado:
            tag_lock = self._render_texto_ajustado("TRAVADO", "pequena", (255, 215, 110), escala=0.72)
            tela.blit(tag_lock, (px + largura_painel - tag_lock.get_width() - 8, py + 8))
        elif getattr(player, "pode_alternar_tiro", False):
            tag_q = self._render_texto_ajustado("[Q]", "pequena", (185, 205, 230), escala=0.88)
            tela.blit(tag_q, (px + largura_painel - tag_q.get_width() - 8, py + 6))

        barra_x, barra_y, barra_w, barra_h = px + 44, py + 31, largura_painel - 52, 10
        pygame.draw.rect(tela, (28, 34, 48), (barra_x, barra_y, barra_w, barra_h), border_radius=4)
        largura_fill = int(barra_w * prop_cd)
        if largura_fill > 0:
            cor_cd = (60, 235, 145) if pronto else (255, 165, 50)
            pygame.draw.rect(tela, cor_cd, (barra_x, barra_y, largura_fill, barra_h), border_radius=4)
        pygame.draw.rect(tela, (90, 110, 140), (barra_x, barra_y, barra_w, barra_h), 1, border_radius=4)

        status_txt = "PRONTO" if pronto else "RECARREGANDO"
        cor_status = (120, 245, 175) if pronto else (225, 185, 115)
        tela.blit(self._render_texto_ajustado(status_txt, "pequena", cor_status, escala=0.72), (barra_x, barra_y + 11))
        return py + altura_painel + 6

    def _desenhar_poderes_ativos(self, tela, player, base_y, idx_player=0):
        tempos_poderes = (
            ("tiro_triplo", getattr(player, "tempo_tiro_triplo", 0)),
            ("escudo", getattr(player, "tempo_escudo", 0)),
            ("bomba", getattr(player, "tempo_tiro_bomba", 0)),
        )

        ativos = []
        for chave, tempo in tempos_poderes:
            if tempo > 0:
                chave_pico = f"{idx_player}_{chave}"
                pico = max(self._pico_poder.get(chave_pico, tempo), tempo, 1)
                self._pico_poder[chave_pico] = pico
                ativos.append((chave, tempo / pico))

        for k, (chave_icone, prop_tempo) in enumerate(ativos):
            icone = self.assets.icones_poder.get(chave_icone) or self._icones_armas.get(chave_icone)
            if icone:
                ix = LARGURA - 50 - k * 40
                tela.blit(icone, (ix, base_y))
                pygame.draw.rect(tela, (25, 30, 42), (ix + 2, base_y + 34, 30, 4), border_radius=2)
                pygame.draw.rect(tela, (90, 235, 180), (ix + 2, base_y + 34, max(2, int(30 * prop_tempo)), 4), border_radius=2)

    def _desenhar_apresentacao_chefe_entrada(self, tela, boss):
        """Faixa elegante e estática durante a descida do chefe."""
        t = getattr(boss, "progresso_entrada", 1.0)
        # Fade-in nos primeiros 20% e fade-out nos últimos 25% da descida
        if t < 0.2:
            alpha = int((t / 0.2) * 215)
        elif t > 0.75:
            alpha = int(((1.0 - t) / 0.25) * 215)
        else:
            alpha = 215

        if alpha <= 5:
            return

        largura_box, altura_box = 430, 56
        bx = LARGURA // 2 - largura_box // 2
        by = ALTURA - 115

        painel = pygame.Surface((largura_box, altura_box), pygame.SRCALPHA)
        pygame.draw.rect(painel, (14, 20, 34, alpha), painel.get_rect(), border_radius=10)
        pygame.draw.rect(painel, (110, 195, 245, alpha), painel.get_rect(), 1, border_radius=10)

        t_sub = self._render_texto_ajustado(getattr(boss, "subtitulo", "SETOR HOSTIL"), "pequena", (140, 215, 255), escala=0.78)
        t_nome = self._render_texto_ajustado(getattr(boss, "nome", "CHEFE"), "padrao", (245, 248, 255), escala=0.88)
        t_sub.set_alpha(alpha)
        t_nome.set_alpha(alpha)

        painel.blit(t_sub, (largura_box // 2 - t_sub.get_width() // 2, 7))
        painel.blit(t_nome, (largura_box // 2 - t_nome.get_width() // 2, 26))
        tela.blit(painel, (bx, by))

    def _desenhar_barra_boss(self, tela, boss, loop_nivel=1):
        if getattr(boss, "estado", "") == "entrando":
            self._desenhar_apresentacao_chefe_entrada(tela, boss)
            return

        vida_raw = float(getattr(boss, "vida", 0))
        if vida_raw <= 0:
            return

        boss_key = id(boss)
        vida_max = getattr(boss, "vida_max", None) or getattr(boss, "max_vida", None)
        if not isinstance(vida_max, (int, float)) or vida_max <= 0:
            vida_max = max(self._pico_vida_boss.get(boss_key, vida_raw), vida_raw, 1.0)
            self._pico_vida_boss[boss_key] = vida_max
        else:
            vida_max = max(float(vida_max), vida_raw, 1.0)

        tipo = str(getattr(boss, "tipo", "")).lower()
        temas_boss = {
            "squid":        ("DEVORADOR DAS PROFUNDEZAS",  (185, 95, 245),  (225, 165, 255)),
            "colmeia":      ("COLMEIA PROFANA",          (135, 215, 70),  (205, 250, 145)),
            "eye":          ("SENTINELA ESMERALDA",      (235, 95, 75),   (255, 165, 145)),
            "final":        ("ARAUTO DA EXTINÇÃO",      (235, 180, 60),  (255, 230, 145)),
            "gemeos":       ("IRMÃS DO CAOS",   (80, 190, 245),  (185, 235, 255)),
            "arquiteto":    ("A ÚLTIMA SINGULARIDADE", (165, 115, 245), (245, 210, 135)),
        }
        nome_boss, cor_barra, cor_brilho = temas_boss.get(
            tipo,
            (str(getattr(boss, "nome", "CHEFE")).upper(), (220, 110, 80), (255, 185, 155)),
        )

        largura_box = min(LARGURA - 36, 460)
        altura_box = 42
        bx = LARGURA // 2 - largura_box // 2
        by = ALTURA - altura_box - 10

        fundo = pygame.Surface((largura_box, altura_box), pygame.SRCALPHA)
        pygame.draw.rect(fundo, (14, 16, 26, 205), fundo.get_rect(), border_radius=8)
        pygame.draw.rect(fundo, (*cor_barra, 185), fundo.get_rect(), 1, border_radius=8)
        tela.blit(fundo, (bx, by))

        txt_nome = self.assets.fontes["pequena"].render(nome_boss, True, cor_brilho)
        tela.blit(txt_nome, (bx + 10, by + 4))

        if loop_nivel >= 2:
            mut = self._render_texto_ajustado("LOOP 2+: METEOROS", "pequena", (175, 205, 235), escala=0.72)
            tela.blit(mut, (bx + largura_box - mut.get_width() - 10, by + 6))

        bar_x, bar_y, bar_w, bar_h = bx + 10, by + 24, largura_box - 20, 11
        pygame.draw.rect(tela, (32, 24, 34), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        prop = max(0.0, min(1.0, vida_raw / float(vida_max)))
        fill_w = int(bar_w * prop)
        if fill_w > 0:
            pygame.draw.rect(tela, cor_barra, (bar_x, bar_y, fill_w, bar_h), border_radius=5)
            if fill_w > 6:
                pygame.draw.rect(tela, cor_brilho, (bar_x + 2, bar_y + 2, fill_w - 4, 3), border_radius=2)

        for frac in (0.25, 0.5, 0.75):
            mx = bar_x + int(bar_w * frac)
            pygame.draw.line(tela, (22, 26, 36), (mx, bar_y + 1), (mx, bar_y + bar_h - 2), 1)

        pygame.draw.rect(tela, (115, 125, 150), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=5)

    def draw_hud(
        self,
        tela,
        players,
        pontos,
        loop_nivel=1,
        recorde=0,
        novo_recorde=False,
        alerta_recorde=0,
        boss=None,
        combo=0,
        combo_prop=0.0,
    ):
        txt_pts = self.assets.fontes["padrao"].render(f"PONTOS: {pontos}", True, (255, 255, 255))
        tela.blit(txt_pts, (16, 14))

        cor_rec = (255, 215, 70) if novo_recorde else (165, 185, 210)
        txt_rec = self.assets.fontes["pequena"].render(f"RECORDE: {recorde}", True, cor_rec)
        tela.blit(txt_rec, (16, 44))

        esq_y = 68
        if loop_nivel > 1:
            txt_loop = self.assets.fontes["pequena"].render(f"LOOP {loop_nivel}", True, (0, 240, 190))
            tela.blit(txt_loop, (16, esq_y))
            esq_y += 24

        if combo >= 2 and combo_prop > 0.0:
            mult_combo = min(4.0, 1.0 + (combo - 1) * 0.25)
            cor_combo = (255, 215, 65) if combo >= 5 else (110, 245, 195)
            txt_combo = self._render_texto_ajustado(f"COMBO {combo}x  (×{mult_combo:.2g})", "pequena", cor_combo, escala=0.88)
            tela.blit(txt_combo, (16, esq_y))
            bar_y = esq_y + 20
            pygame.draw.rect(tela, (28, 34, 48), (16, bar_y, 128, 5), border_radius=3)
            pygame.draw.rect(tela, cor_combo, (16, bar_y, max(2, int(128 * combo_prop)), 5), border_radius=3)

        if alerta_recorde > 0:
            aviso = self.assets.fontes["pequena"].render("★ NOVO RECORDE! ★", True, (255, 225, 80))
            tela.blit(aviso, (LARGURA // 2 - aviso.get_width() // 2, 16))

        if len(players) == 1:
            p = players[0]
            max_v = getattr(p, "max_vidas", VIDA_MAXIMA)
            for i in range(max_v):
                coracao = self.assets.coracao_cheio if i < p.vidas else self.assets.coracao_vazio
                tela.blit(coracao, (LARGURA - 16 - (max_v - i) * 30, 14))

            prox_y = self._desenhar_painel_arcade(tela, p, top_y=44)
            self._desenhar_poderes_ativos(tela, p, base_y=prox_y, idx_player=0)
        else:
            for idx, p in enumerate(players):
                base_y = 14 + idx * 66
                max_v = getattr(p, "max_vidas", VIDA_MAXIMA)
                for i in range(max_v):
                    coracao = self.assets.coracao_cheio if i < p.vidas else self.assets.coracao_vazio
                    tela.blit(coracao, (LARGURA - 16 - (max_v - i) * 30, base_y))

                chave_modo, _, _, _ = self._obter_info_tiro(p)
                pronto, prop_cd = self._obter_progresso_cooldown(p, f"p{idx}_{chave_modo}")
                cd_w, cd_x, cd_y = 68, LARGURA - 16 - 68, base_y + 27
                pygame.draw.rect(tela, (28, 34, 48), (cd_x, cd_y, cd_w, 6), border_radius=3)
                pygame.draw.rect(tela, (60, 235, 145) if pronto else (255, 165, 50), (cd_x, cd_y, int(cd_w * prop_cd), 6), border_radius=3)
                self._desenhar_poderes_ativos(tela, p, base_y=base_y + 35, idx_player=idx)

        if boss is not None:
            self._desenhar_barra_boss(tela, boss, loop_nivel=loop_nivel)

    def draw_pause(self, tela, mouse_pos):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        tela.blit(overlay, (0, 0))

        titulo = self.assets.fontes["grande"].render("JOGO PAUSADO", True, (255, 230, 100))
        tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 220))

        self._desenhar_botao(tela, self.btn_continuar, "CONTINUAR (P)", mouse_pos, (25, 95, 65), (40, 145, 95))
        self._desenhar_botao(tela, self.btn_menu_pause, "MENU INICIAL", mouse_pos)

    def draw_admin(self, tela, texto_input):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((10, 14, 24, 210))
        tela.blit(overlay, (0, 0))

        t1 = self.assets.fontes["padrao"].render("CONSOLE DE TESTES (F1)", True, (0, 240, 180))
        t2 = self._render_texto_ajustado(
            f"1: DEVORADOR DAS PROFUNDEZAS ({PONTOS_BOSS_1}) | 2: COLMEIA PROFANA ({PONTOS_BOSS_2}) | 3: SENTINELA ESMERALDA ({PONTOS_BOSS_3})",
            "pequena",
            (180, 200, 225),
            escala=0.85,
        )
        t2b = self._render_texto_ajustado(
            f"4: ARAUTO DA EXTINÇÃO ({PONTOS_BOSS_4}) | 5: IRMÃS DO CAOS ({PONTOS_BOSS_5}) | 6: A ÚLTIMA SINGULARIDADE ({PONTOS_BOSS_6})",
            "pequena",
            (180, 200, 225),
            escala=0.85,
        )
        t3 = self.assets.fontes["padrao"].render(f"Pontos: {texto_input}_", True, (255, 255, 255))
        t4 = self.assets.fontes["pequena"].render("ENTER para aplicar  |  ESC para cancelar", True, (150, 170, 195))

        tela.blit(t1, (LARGURA // 2 - t1.get_width() // 2, 205))
        tela.blit(t2, (LARGURA // 2 - t2.get_width() // 2, 248))
        tela.blit(t2b, (LARGURA // 2 - t2b.get_width() // 2, 272))
        tela.blit(t3, (LARGURA // 2 - t3.get_width() // 2, 315))
        tela.blit(t4, (LARGURA // 2 - t4.get_width() // 2, 365))

    def draw_vitoria(self, tela, pontos, mouse_pos, recorde=0, novo_recorde=False):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((6, 12, 24, 195))
        tela.blit(overlay, (0, 0))

        t1 = self.assets.fontes["grande"].render("VITÓRIA GALÁCTICA!", True, (0, 255, 160))
        t2 = self.assets.fontes["padrao"].render(f"Lamento do Vazio Derrotado! Pontos: {pontos}", True, (255, 255, 255))
        msg_rec = "NOVO RECORDE PESSOAL!" if novo_recorde else f"Recorde Pessoal: {recorde}"
        cor_rec = (255, 215, 70) if novo_recorde else (160, 210, 255)
        t_rec = self.assets.fontes["pequena"].render(msg_rec, True, cor_rec)
        t3 = self.assets.fontes["pequena"].render("Pressione ENTER para continuar no Modo Infinito (Loop 2+)", True, (190, 210, 230))

        tela.blit(t1, (LARGURA // 2 - t1.get_width() // 2, 165))
        tela.blit(t2, (LARGURA // 2 - t2.get_width() // 2, 222))
        tela.blit(t_rec, (LARGURA // 2 - t_rec.get_width() // 2, 254))
        tela.blit(t3, (LARGURA // 2 - t3.get_width() // 2, 282))

        self._desenhar_botao(tela, self.btn_continuar, "MODO INFINITO (ENTER)", mouse_pos, (25, 95, 65), (40, 145, 95))
        self._desenhar_botao(tela, self.btn_menu_pause, "MENU INICIAL", mouse_pos)

    def draw_game_over(self, tela, pontos, mouse_pos, recorde=0, novo_recorde=False):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        tela.blit(overlay, (0, 0))

        t1 = self.assets.fontes["grande"].render("GAME OVER", True, (255, 60, 60))
        t2 = self.assets.fontes["padrao"].render(f"Pontuação Final: {pontos}", True, (255, 255, 255))
        msg_rec = "NOVO RECORDE PESSOAL!" if novo_recorde else f"Recorde Pessoal: {recorde}"
        cor_rec = (255, 215, 70) if novo_recorde else (170, 195, 230)
        t_rec = self.assets.fontes["pequena"].render(msg_rec, True, cor_rec)
        t3 = self.assets.fontes["pequena"].render("Pressione R para jogar novamente", True, (190, 200, 215))

        tela.blit(t1, (LARGURA // 2 - t1.get_width() // 2, 185))
        tela.blit(t2, (LARGURA // 2 - t2.get_width() // 2, 250))
        tela.blit(t_rec, (LARGURA // 2 - t_rec.get_width() // 2, 284))
        tela.blit(t3, (LARGURA // 2 - t3.get_width() // 2, 322))
        self._desenhar_botao(tela, self.btn_menu_pause, "MENU INICIAL", mouse_pos)