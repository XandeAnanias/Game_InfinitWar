import random
import pygame
from config import LARGURA, ALTURA, TITULO


class DisplayCRT:
    """Gerencia a janela estilo console Atari-2600 e o filtro CRT permanente."""

    def __init__(self):
        self.tela_cheia = False
        self.escala = 1.0
        self.rect_tela_interna = pygame.Rect(0, 0, LARGURA, ALTURA)
        self.tela = None
        self.tela_jogo_escalada = None
        self.overlay_crt = None
        self.moldura_atari = None

        self.configurar(tela_cheia=False)
        pygame.display.set_caption(TITULO)

    def _criar_overlay_crt(self, tamanho):
        w, h = tamanho
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Scanlines horizontais sutis
        for y in range(0, h, 3):
            pygame.draw.line(surf, (0, 0, 0, 38), (0, y), (w, y), 1)

        # Vinheta suave nas bordas para simular curvatura de TV de tubo
        for i in range(18):
            alpha = int((18 - i) * 2.2)
            rect_v = pygame.Rect(i, i, w - i * 2, h - i * 2)
            if rect_v.width > 0 and rect_v.height > 0:
                pygame.draw.rect(surf, (0, 0, 0, alpha), rect_v, 1, border_radius=12)

        return surf

    def configurar(self, tela_cheia=False):
        self.tela_cheia = tela_cheia
        info = pygame.display.Info()
        mon_w = info.current_w if info.current_w > 0 else 1280
        mon_h = info.current_h if info.current_h > 0 else 800

        if tela_cheia:
            win_w, win_h = mon_w, mon_h
            margem_v = max(84, int(win_h * 0.11))
            margem_h_min = max(160, int(win_w * 0.14))
            escala_h = (win_h - margem_v) / ALTURA
            escala_w = (win_w - margem_h_min * 2) / LARGURA
            self.escala = max(1.0, min(escala_h, escala_w))

            larg_interna = int(round(LARGURA * self.escala))
            alt_interna = int(round(ALTURA * self.escala))
            off_x = (win_w - larg_interna) // 2
            off_y = (win_h - alt_interna) // 2
            self.rect_tela_interna = pygame.Rect(off_x, off_y, larg_interna, alt_interna)
            self.tela = pygame.display.set_mode((win_w, win_h), pygame.FULLSCREEN)
        else:
            alvo_alt_interna = min(int(ALTURA * 1.28), max(ALTURA, mon_h - 155))
            alvo_larg_interna = min(int(LARGURA * 1.28), max(LARGURA, mon_w - 380))
            self.escala = max(1.0, min(alvo_alt_interna / ALTURA, alvo_larg_interna / LARGURA))

            larg_interna = int(round(LARGURA * self.escala))
            alt_interna = int(round(ALTURA * self.escala))

            lateral_atari = max(145, int(larg_interna * 0.27))
            topo_atari = 42
            base_atari = 54

            win_w = larg_interna + lateral_atari * 2
            win_h = alt_interna + topo_atari + base_atari
            self.rect_tela_interna = pygame.Rect(lateral_atari, topo_atari, larg_interna, alt_interna)
            self.tela = pygame.display.set_mode((win_w, win_h))

        self.tela_jogo_escalada = pygame.Surface(self.rect_tela_interna.size)
        self.overlay_crt = self._criar_overlay_crt(self.rect_tela_interna.size)
        self.moldura_atari = self._construir_moldura_atari(win_w, win_h, self.rect_tela_interna)

    def _construir_moldura_atari(self, win_w, win_h, tela_rect):
        surf = pygame.Surface((win_w, win_h))
        rng = random.Random(2600)

        surf.fill((96, 54, 26))
        for y in range(0, win_h, 2):
            variacao = rng.randint(-12, 12)
            cor_veio = (
                max(45, min(145, 96 + variacao)),
                max(24, min(88, 54 + int(variacao * 0.65))),
                max(10, min(48, 26 + int(variacao * 0.4))),
            )
            pygame.draw.line(surf, cor_veio, (0, y), (win_w, y), 2)

        for x in range(0, win_w, 5):
            if rng.random() < 0.45:
                tom = rng.choice([(76, 40, 18), (114, 66, 33), (64, 33, 14)])
                pygame.draw.line(surf, tom, (x, 0), (x, win_h), 1)

        pad_console = 22
        console_rect = pygame.Rect(
            max(12, tela_rect.left - pad_console),
            max(8, tela_rect.top - 34),
            min(win_w - 24, tela_rect.width + pad_console * 2),
            min(win_h - 16, tela_rect.height + 80),
        )
        pygame.draw.rect(surf, (24, 24, 28), console_rect, border_radius=14)
        pygame.draw.rect(surf, (58, 58, 66), console_rect, 2, border_radius=14)

        for lado_x in (console_rect.left - 86, console_rect.right + 14):
            if 10 <= lado_x <= win_w - 82:
                for i in range(9):
                    ry = tela_rect.top + 35 + i * 16
                    if ry < tela_rect.bottom - 35:
                        pygame.draw.rect(surf, (38, 22, 12), (lado_x, ry, 72, 6), border_radius=3)
                        pygame.draw.line(surf, (128, 76, 40), (lado_x + 1, ry + 6), (lado_x + 70, ry + 6), 1)

        borda_laranja = tela_rect.inflate(16, 16)
        pygame.draw.rect(surf, (214, 102, 28), borda_laranja, 4, border_radius=10)
        borda_interna = tela_rect.inflate(6, 6)
        pygame.draw.rect(surf, (14, 14, 18), borda_interna, 3, border_radius=6)

        fonte_badge = pygame.font.SysFont("consolas", 14, bold=True)
        txt_topo = fonte_badge.render("ATARI-2600  //  GUERRA NO INFINITO  //  F11 TELA CHEIA", True, (235, 175, 85))
        surf.blit(txt_topo, (tela_rect.centerx - txt_topo.get_width() // 2, max(10, tela_rect.top - 26)))

        # LED Power estático
        led_x = tela_rect.left + 12
        led_y = max(17, tela_rect.top - 19)
        pygame.draw.circle(surf, (220, 50, 50), (led_x, led_y), 4)
        pygame.draw.circle(surf, (255, 170, 170), (led_x - 1, led_y - 1), 1)

        deck_y = tela_rect.bottom + 12
        if deck_y + 30 <= win_h:
            switches = ["TV: COLOR", "DIFF: A", "SELECT", "RESET"]
            espacamento = min(115, max(82, tela_rect.width // 4))
            inicio_x = tela_rect.centerx - ((len(switches) - 1) * espacamento) // 2
            fonte_sw = pygame.font.SysFont("consolas", 11, bold=True)

            for idx, nome_sw in enumerate(switches):
                sx = inicio_x + idx * espacamento
                pygame.draw.rect(surf, (44, 46, 54), (sx - 18, deck_y + 2, 36, 14), border_radius=3)
                pygame.draw.rect(surf, (195, 200, 210), (sx - 4, deck_y - 3, 8, 16), border_radius=2)
                pygame.draw.line(surf, (245, 248, 255), (sx - 2, deck_y - 2), (sx - 2, deck_y + 11), 1)
                lbl = fonte_sw.render(nome_sw, True, (218, 130, 55))
                surf.blit(lbl, (sx - lbl.get_width() // 2, deck_y + 19))

        return surf

    def obter_pos_mouse_jogo(self):
        mx, my = pygame.mouse.get_pos()
        vx = int((mx - self.rect_tela_interna.x) / self.escala)
        vy = int((my - self.rect_tela_interna.y) / self.escala)
        return (vx, vy)

    def renderizar(self, canvas, offset_x=0, offset_y=0):
        self.tela.blit(self.moldura_atari, (0, 0))

        pygame.transform.smoothscale(canvas, self.rect_tela_interna.size, self.tela_jogo_escalada)
        self.tela.set_clip(self.rect_tela_interna)
        pos_blit = (self.rect_tela_interna.x + offset_x, self.rect_tela_interna.y + offset_y)
        self.tela.blit(self.tela_jogo_escalada, pos_blit)

        # Filtro CRT sempre aplicado
        self.tela.blit(self.overlay_crt, self.rect_tela_interna.topleft)

        pygame.draw.rect(self.tela, (10, 12, 16), self.rect_tela_interna, 2)
        self.tela.set_clip(None)
        pygame.display.flip()