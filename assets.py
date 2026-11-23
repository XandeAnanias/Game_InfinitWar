import os
import json
import pygame
import random
import math
import threading
from config import SPRITES_CONFIG, SONS_CONFIG, MAX_VOLUME_GLOBAL


class SomNulo:
    """Evita crashes caso algum arquivo .wav seja removido."""
    def play(self): pass
    def set_volume(self, v): pass


class AssetManager:
    # Mapeia novos efeitos para sons existentes caso os .wav ainda não estejam em assets/audio/
    SONS_RESERVA = {
        "olho_carregar":       "tiro_triplo",
        "olho_laser":          "bomba",
        "olho_invocar":        "tiro",
        "boss_final_campo":    "tiro_triplo",
        "boss_final_frota":    "olho_invocar",
        "boss_final_carregar": "olho_carregar",
        "boss_final_laser":    "olho_laser",
        "boss_alerta":         "tiro_triplo",
        "lula_dash":           "tiro",
        "lula_tinta":          "bomba",
        "colmeia_enxame":      "olho_invocar",
        "gemeos_arco":         "olho_laser",
        "buraco_negro_pulso":  "boss_final_campo",
        "buraco_negro_feixe":  "olho_laser",
        "powerup":             "tiro_triplo",
        "cura":                "tiro_triplo",
    }

    SONS_EXTRAS_PADRAO = {
        "boss_final_campo":    "assets/audio/boss_final_campo.wav",
        "boss_final_frota":    "assets/audio/boss_final_frota.wav",
        "boss_final_carregar": "assets/audio/boss_final_carregar.wav",
        "boss_final_laser":    "assets/audio/boss_final_laser.wav",
        "boss_alerta":         "assets/audio/boss_alerta.wav",
        "lula_dash":           "assets/audio/lula_dash.wav",
        "lula_tinta":          "assets/audio/lula_tinta.wav",
        "colmeia_enxame":      "assets/audio/colmeia_enxame.wav",
        "gemeos_arco":         "assets/audio/gemeos_arco.wav",
        "buraco_negro_pulso":  "assets/audio/buraco_negro_pulso.wav",
        "buraco_negro_feixe":  "assets/audio/buraco_negro_feixe.wav",
        "powerup":             "assets/audio/powerup.wav",
        "cura":                "assets/audio/cura.wav",
    }

    MUSICAS_PADRAO = {
        "menu": [
            "assets/audio/musica_menu.ogg",
            "assets/audio/musica_menu.mid",
        ],
        "fase": [
            "assets/audio/musica_fase.ogg",
            "assets/audio/musica_fase.mp3",
        ],
        "boss_medio": [
            "assets/audio/musica_boss.ogg",
            "assets/audio/musica_boss.mp3",
        ],
        "boss_final": [
            "assets/audio/musica_boss_final.ogg",
            "assets/audio/musica_boss_final.mp3",
            "assets/audio/musica_boss.ogg",
            "assets/audio/musica_boss.mp3",
        ],
        "boss_final_furia": [
            "assets/audio/musica_boss_final_furia.ogg",
            "assets/audio/musica_boss_final_furia.mp3",
            "assets/audio/musica_boss_final.ogg",
            "assets/audio/musica_boss_final.mp3",
        ],
    }

    def __init__(self):
        self.sprites = {}
        self.sons = {}
        self.arquivo_config_audio = "config_audio.json"
        self.volume_musica = 0.5
        self.volume_efeitos = 0.5
        self.musica_atual = None
        self.musica_arquivo_atual = None
        self._musica_lock = threading.Lock()
        self._musica_req_id = 0
        self._cache_musicas = {}

        self._carregar_config_audio()

        self.fontes = {
            "pequena": pygame.font.SysFont("segoeui", 17, True),
            "padrao":  pygame.font.SysFont("segoeui", 23, True),
            "grande":  pygame.font.SysFont("segoeui", 46, True),
            "titulo":  pygame.font.SysFont("segoeui", 54, True),
        }

        self._mapear_musicas()
        self._carregar_sons()
        self._carregar_sprites()
        self.coracao_cheio = self._criar_coracao((255, 40, 60), (255, 180, 190))
        self.coracao_vazio = self._criar_coracao((60, 60, 75), (95, 95, 110))
        self.icones_poder = self._criar_icones_poder()

    @property
    def volume_atual(self):
        return max(self.volume_musica, self.volume_efeitos)

    def _carregar_config_audio(self):
        try:
            if os.path.exists(self.arquivo_config_audio):
                with open(self.arquivo_config_audio, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.volume_musica = max(0.0, min(1.0, float(dados.get("musica", 0.5))))
                    self.volume_efeitos = max(0.0, min(1.0, float(dados.get("efeitos", 0.5))))
        except Exception:
            pass

    def _salvar_config_audio(self):
        try:
            with open(self.arquivo_config_audio, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "musica": round(self.volume_musica, 2),
                        "efeitos": round(self.volume_efeitos, 2),
                    },
                    f,
                    indent=2,
                )
        except Exception:
            pass

    def _resolver_caminho_reserva(self, chave, mapa_sons):
        visitados = set()
        atual = self.SONS_RESERVA.get(chave)
        while atual and atual not in visitados:
            visitados.add(atual)
            caminho = mapa_sons.get(atual)
            if caminho and os.path.exists(caminho):
                return caminho
            atual = self.SONS_RESERVA.get(atual)
        return None

    def _carregar_sons(self):
        mapa_completo = {**self.SONS_EXTRAS_PADRAO, **SONS_CONFIG}
        for chave, caminho in mapa_completo.items():
            try:
                self.sons[chave] = pygame.mixer.Sound(caminho)
            except Exception:
                caminho_reserva = self._resolver_caminho_reserva(chave, mapa_completo)
                try:
                    self.sons[chave] = pygame.mixer.Sound(caminho_reserva) if caminho_reserva else SomNulo()
                except Exception:
                    self.sons[chave] = SomNulo()
        self.ajustar_volume_efeitos(self.volume_efeitos, salvar=False)
        self.ajustar_volume_musica(self.volume_musica, salvar=False)

    def tocar_som(self, nome):
        if nome in self.sons:
            self.sons[nome].play()

    def _mapear_musicas(self):
        """Localiza todos os arquivos de trilha sonora uma única vez ao abrir o jogo."""
        chaves = ("menu", "fase", "boss_medio", "boss_final", "boss_final_furia")
        pasta_audio = os.path.join("assets", "audio")
        arquivos_pasta = sorted(os.listdir(pasta_audio)) if os.path.isdir(pasta_audio) else []
        extensoes_aceitas = (".ogg", ".mp3", ".wav", ".mid")

        for chave in chaves:
            encontrado = None
            for caminho in self.MUSICAS_PADRAO.get(chave, []):
                if os.path.exists(caminho):
                    encontrado = caminho
                    break

            if not encontrado and arquivos_pasta:
                nomes_aceitos = {f"musica_{chave}".lower(), chave.lower()}
                for arquivo in arquivos_pasta:
                    nome_base, ext = os.path.splitext(arquivo)
                    if nome_base.lower() in nomes_aceitos and ext.lower() in extensoes_aceitas:
                        encontrado = os.path.join(pasta_audio, arquivo)
                        break

            self._cache_musicas[chave] = encontrado

    def ajustar_volume_musica(self, novo_volume, salvar=True):
        self.volume_musica = max(0.0, min(1.0, novo_volume))
        vol_real = self.volume_musica * MAX_VOLUME_GLOBAL
        if self._musica_lock.acquire(blocking=False):
            try:
                pygame.mixer.music.set_volume(vol_real * 0.65)
            except Exception:
                pass
            finally:
                self._musica_lock.release()
        if salvar:
            self._salvar_config_audio()

    def ajustar_volume_efeitos(self, novo_volume, salvar=True):
        self.volume_efeitos = max(0.0, min(1.0, novo_volume))
        vol_real = self.volume_efeitos * MAX_VOLUME_GLOBAL
        for som in self.sons.values():
            som.set_volume(vol_real)
        if salvar:
            self._salvar_config_audio()

    def ajustar_volume(self, novo_volume):
        self.ajustar_volume_musica(novo_volume, salvar=False)
        self.ajustar_volume_efeitos(novo_volume, salvar=True)

    def _worker_tocar_musica(self, caminho_valido, fade_ms, req_id):
        with self._musica_lock:
            if req_id != self._musica_req_id:
                return
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(caminho_valido)
                pygame.mixer.music.set_volume(self.volume_musica * MAX_VOLUME_GLOBAL * 0.65)
                pygame.mixer.music.play(-1, fade_ms=fade_ms)
            except Exception as erro:
                print(f"[ÁUDIO] Falha ao reproduzir '{caminho_valido}': {erro}")

    def tocar_musica(self, chave, fade_ms=450):
        caminho_valido = self._cache_musicas.get(chave)
        if not caminho_valido:
            return

        if caminho_valido == self.musica_arquivo_atual and pygame.mixer.music.get_busy():
            return

        self.musica_atual = chave
        self.musica_arquivo_atual = caminho_valido
        self._musica_req_id += 1
        req_id = self._musica_req_id

        threading.Thread(
            target=self._worker_tocar_musica,
            args=(caminho_valido, fade_ms, req_id),
            daemon=True,
        ).start()

    def pausar_musica(self):
        with self._musica_lock:
            try:
                pygame.mixer.music.pause()
            except Exception:
                pass

    def retomar_musica(self):
        with self._musica_lock:
            try:
                pygame.mixer.music.unpause()
            except Exception:
                pass

    def _gerar_mascara_branca(self, surf):
        mascara = pygame.mask.from_surface(surf)
        return mascara.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))

    def _carregar_sprites(self):
        for chave, info in SPRITES_CONFIG.items():
            tamanho = info["tamanho"]
            img = None
            caminhos_tentativa = [info["arquivo"]]
            if " " in info["arquivo"]:
                caminhos_tentativa.append(info["arquivo"].replace(" ", "_"))

            for caminho in caminhos_tentativa:
                try:
                    img = pygame.image.load(caminho).convert_alpha()
                    img = pygame.transform.scale(img, tamanho)
                    break
                except Exception:
                    img = None

            if img is None:
                img = self._gerar_sprite_fallback(chave, tamanho)

            if img is None:
                img = pygame.Surface(tamanho, pygame.SRCALPHA)

            self.sprites[chave] = (img, self._gerar_mascara_branca(img))

    def _salvar_sprite_gerado(self, chave, surf):
        info = SPRITES_CONFIG.get(chave)
        if not info:
            return
        caminho = info["arquivo"]
        pasta = os.path.dirname(caminho)
        if os.path.isdir(pasta) and not os.path.exists(caminho):
            try:
                pygame.image.save(surf, caminho)
            except Exception:
                pass

    def _gerar_sprite_fallback(self, chave, tamanho):
        """Gera texturas detalhadas caso o PNG customizado ainda não exista em assets/images/."""
        w, h = tamanho
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        if chave == "nave_p2" and "nave_p1" in self.sprites:
            base = self.sprites["nave_p1"][0].copy()
            base.fill((120, 200, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
            return base

        if chave == "nave_interceptora":
            # Interceptora -> "Lança-Vórtice" (70x70): diapasão duplo + asas forward-swept + jato único ciano
            cx = w // 2

            # Único jato traseiro longo em ciano elétrico (#00EBFF)
            pygame.draw.polygon(surf, (0, 165, 235, 190), [(cx - 7, h - 18), (cx, h - 1), (cx + 7, h - 18)])
            pygame.draw.polygon(surf, (0, 235, 255), [(cx - 5, h - 18), (cx, h - 3), (cx + 5, h - 18)])
            pygame.draw.polygon(surf, (225, 255, 255), [(cx - 2, h - 18), (cx, h - 8), (cx + 2, h - 18)])
            pygame.draw.rect(surf, (22, 36, 58), (cx - 6, h - 21, 12, 5), border_radius=2)
            pygame.draw.line(surf, (124, 232, 255), (cx - 5, h - 20), (cx + 5, h - 20), 1)

            # Estabilizadores traseiros curtos
            pygame.draw.polygon(surf, (24, 42, 72), [(cx - 9, 46), (17, 56), (19, 60), (cx - 7, 55)])
            pygame.draw.polygon(surf, (24, 42, 72), [(cx + 9, 46), (w - 17, 56), (w - 19, 60), (cx + 7, 55)])
            pygame.draw.line(surf, (124, 232, 255), (18, 56), (cx - 8, 48), 1)
            pygame.draw.line(surf, (124, 232, 255), (w - 18, 56), (cx + 8, 48), 1)

            # Asas curtas anguladas para frente (forward-swept)
            asa_esq_ext = [(cx - 9, 32), (6, 23), (4, 30), (14, 44), (cx - 9, 47)]
            asa_dir_ext = [(cx + 9, 32), (w - 6, 23), (w - 4, 30), (w - 14, 44), (cx + 9, 47)]
            pygame.draw.polygon(surf, (20, 36, 62), asa_esq_ext)
            pygame.draw.polygon(surf, (20, 36, 62), asa_dir_ext)

            asa_esq_int = [(cx - 9, 34), (9, 26), (8, 30), (16, 42), (cx - 9, 45)]
            asa_dir_int = [(cx + 9, 34), (w - 9, 26), (w - 8, 30), (w - 16, 42), (cx + 9, 45)]
            pygame.draw.polygon(surf, (124, 232, 255), asa_esq_int)
            pygame.draw.polygon(surf, (124, 232, 255), asa_dir_int)

            pygame.draw.polygon(surf, (32, 92, 168), [(cx - 10, 37), (14, 32), (18, 41), (cx - 10, 43)])
            pygame.draw.polygon(surf, (32, 92, 168), [(cx + 10, 37), (w - 14, 32), (w - 18, 41), (cx + 10, 43)])
            pygame.draw.lines(surf, (235, 252, 255), False, [(14, 44), (4, 30), (6, 23), (cx - 9, 32)], 2)
            pygame.draw.lines(surf, (235, 252, 255), False, [(w - 14, 44), (w - 4, 30), (w - 6, 23), (cx + 9, 32)], 2)

            # Bico duplo afilado em formato de diapasão (branco-prateado e azul-gelo #7CE8FF)
            haste_esq_ext = [(cx - 5, 4), (cx - 9, 22), (cx - 10, 50), (cx - 3, 52), (cx - 3, 20)]
            haste_esq_luz = [(cx - 5, 7), (cx - 7, 23), (cx - 8, 48), (cx - 4, 49), (cx - 4, 20)]
            haste_dir_ext = [(cx + 5, 4), (cx + 9, 22), (cx + 10, 50), (cx + 3, 52), (cx + 3, 20)]
            haste_dir_luz = [(cx + 5, 7), (cx + 7, 23), (cx + 8, 48), (cx + 4, 49), (cx + 4, 20)]

            pygame.draw.polygon(surf, (22, 40, 68), haste_esq_ext)
            pygame.draw.polygon(surf, (22, 40, 68), haste_dir_ext)
            pygame.draw.polygon(surf, (224, 238, 250), haste_esq_luz)
            pygame.draw.polygon(surf, (224, 238, 250), haste_dir_luz)
            pygame.draw.line(surf, (124, 232, 255), (cx - 5, 6), (cx - 8, 24), 2)
            pygame.draw.line(surf, (124, 232, 255), (cx + 5, 6), (cx + 8, 24), 2)

            # Núcleo de energia ciano brilhando no vão central do diapasão
            pygame.draw.line(surf, (0, 235, 255), (cx, 9), (cx, 25), 3)
            pygame.draw.circle(surf, (0, 235, 255), (cx, 22), 4)
            pygame.draw.circle(surf, (255, 255, 255), (cx, 22), 2)

            # Fuselagem central e cockpit em azul-safira escuro
            pygame.draw.polygon(surf, (22, 40, 68), [(cx - 8, 25), (cx + 8, 25), (cx + 9, 52), (cx - 9, 52)])
            pygame.draw.polygon(surf, (195, 218, 240), [(cx - 6, 26), (cx + 6, 26), (cx + 7, 50), (cx - 7, 50)])
            cockpit = [(cx, 27), (cx - 4, 34), (cx - 3, 44), (cx, 47), (cx + 3, 44), (cx + 4, 34)]
            pygame.draw.polygon(surf, (14, 38, 86), cockpit)
            pygame.draw.polygon(surf, (28, 78, 158), [(cx, 29), (cx - 3, 35), (cx - 2, 43), (cx + 2, 43), (cx + 3, 35)])
            pygame.draw.line(surf, (165, 245, 255), (cx - 1, 30), (cx - 1, 41), 1)
            self._salvar_sprite_gerado(chave, surf)
            return surf

        if chave == "nave_interceptora_p2" and "nave_interceptora" in self.sprites:
            base = self.sprites["nave_interceptora"][0].copy()
            base.fill((145, 255, 195, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self._salvar_sprite_gerado(chave, base)
            return base

        if chave == "nave_caca":
            # Caça Tático -> "Falcão Catamarã" (70x70): fuselagem dupla paralela + canhões duplos + aletas em X
            cx = w // 2

            # Propulsores duplos nos dois cascos paralelos
            for lado in (-1, 1):
                px = cx + lado * 12
                pygame.draw.polygon(surf, (43, 108, 176), [(px - 5, h - 14), (px, h - 2), (px + 5, h - 14)])
                pygame.draw.polygon(surf, (92, 225, 230), [(px - 3, h - 14), (px, h - 4), (px + 3, h - 14)])
                pygame.draw.polygon(surf, (235, 255, 255), [(px - 1, h - 14), (px, h - 7), (px + 1, h - 14)])
                pygame.draw.rect(surf, (22, 34, 54), (px - 5, h - 17, 10, 4), border_radius=1)

            # Quatro aletas estabilizadoras em "X" fechado
            aleta_tras_esq = [(cx - 15, 43), (5, 53), (7, 58), (cx - 14, 52)]
            aleta_tras_dir = [(cx + 15, 43), (w - 5, 53), (w - 7, 58), (cx + 14, 52)]
            aleta_frente_esq = [(cx - 15, 34), (7, 24), (9, 20), (cx - 14, 27)]
            aleta_frente_dir = [(cx + 15, 34), (w - 7, 24), (w - 9, 20), (cx + 14, 27)]

            for aleta in (aleta_tras_esq, aleta_tras_dir, aleta_frente_esq, aleta_frente_dir):
                pygame.draw.polygon(surf, (20, 36, 62), aleta)
                pygame.draw.polygon(surf, (68, 175, 245), aleta, 1)

            # Detalhes em azul-celeste (#44AFF5) nas aletas
            pygame.draw.polygon(surf, (68, 175, 245), [(cx - 15, 45), (8, 53), (cx - 15, 50)])
            pygame.draw.polygon(surf, (68, 175, 245), [(cx + 15, 45), (w - 8, 53), (cx + 15, 50)])
            pygame.draw.polygon(surf, (68, 175, 245), [(cx - 15, 32), (10, 24), (cx - 15, 29)])
            pygame.draw.polygon(surf, (68, 175, 245), [(cx + 15, 32), (w - 10, 24), (cx + 15, 29)])

            # Ponte central blindada unindo os dois cascos
            pygame.draw.rect(surf, (20, 34, 58), (cx - 10, 26, 20, 22), border_radius=3)
            pygame.draw.rect(surf, (43, 108, 176), (cx - 8, 28, 16, 18), border_radius=2)
            pygame.draw.rect(surf, (24, 48, 86), (cx - 5, 31, 10, 12), border_radius=2)
            pygame.draw.circle(surf, (92, 225, 230), (cx, 37), 3)
            pygame.draw.circle(surf, (235, 255, 255), (cx, 37), 1)

            # Fuselagem dupla paralela + dois canhões frontais salientes com pontas ciano-neon (#5CE1E6)
            for lado in (-1, 1):
                fx = cx + lado * 12

                pygame.draw.rect(surf, (24, 38, 60), (fx - 2, 4, 4, 15), border_radius=1)
                pygame.draw.rect(surf, (130, 165, 205), (fx - 1, 6, 2, 12))
                pygame.draw.circle(surf, (92, 225, 230), (fx, 4), 3)
                pygame.draw.circle(surf, (245, 255, 255), (fx, 4), 1)

                casco_ext = [(fx, 14), (fx - 6, 22), (fx - 6, 53), (fx + 6, 53), (fx + 6, 22)]
                casco_cob = [(fx, 16), (fx - 4, 23), (fx - 4, 51), (fx + 4, 51), (fx + 4, 23)]
                pygame.draw.polygon(surf, (18, 32, 54), casco_ext)
                pygame.draw.polygon(surf, (43, 108, 176), casco_cob)

                pygame.draw.rect(surf, (68, 175, 245), (fx - 2, 23, 4, 24), border_radius=1)
                pygame.draw.rect(surf, (14, 36, 74), (fx - 2, 26, 4, 9), border_radius=1)
                pygame.draw.line(surf, (165, 245, 255), (fx - 1, 27), (fx - 1, 33), 1)

            self._salvar_sprite_gerado(chave, surf)
            return surf

        if chave == "nave_caca_p2" and "nave_caca" in self.sprites:
            base = self.sprites["nave_caca"][0].copy()
            base.fill((140, 245, 205, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self._salvar_sprite_gerado(chave, base)
            return base

        if chave == "nave_fundo" and "nave_p1" in self.sprites:
            return pygame.transform.scale(self.sprites["nave_p1"][0], tamanho)

        if chave == "inimigo_1":
            cx = w // 2
            asa_sup_esq = [(cx - 3, int(h * 0.42)), (1, int(h * 0.24)), (3, int(h * 0.54)), (cx - 5, int(h * 0.58))]
            asa_sup_dir = [(cx + 3, int(h * 0.42)), (w - 1, int(h * 0.24)), (w - 3, int(h * 0.54)), (cx + 5, int(h * 0.58))]
            asa_inf_esq = [(cx - 4, int(h * 0.56)), (5, int(h * 0.62)), (8, int(h * 0.78)), (cx - 4, int(h * 0.68))]
            asa_inf_dir = [(cx + 4, int(h * 0.56)), (w - 5, int(h * 0.62)), (w - 8, int(h * 0.78)), (cx + 4, int(h * 0.68))]

            for asa in (asa_sup_esq, asa_sup_dir, asa_inf_esq, asa_inf_dir):
                pygame.draw.polygon(surf, (12, 42, 28), asa)
            for asa in (asa_sup_esq, asa_sup_dir):
                pygame.draw.polygon(surf, (42, 210, 128), asa)
                pygame.draw.polygon(surf, (155, 255, 195), asa, 1)
            for asa in (asa_inf_esq, asa_inf_dir):
                pygame.draw.polygon(surf, (28, 165, 105), asa)
                pygame.draw.polygon(surf, (110, 240, 175), asa, 1)

            pygame.draw.line(surf, (190, 255, 130), (cx - 5, int(h * 0.46)), (4, int(h * 0.34)), 1)
            pygame.draw.line(surf, (190, 255, 130), (cx + 5, int(h * 0.46)), (w - 4, int(h * 0.34)), 1)

            pygame.draw.ellipse(surf, (16, 46, 20), (cx - 7, 2, 14, int(h * 0.44)))
            pygame.draw.ellipse(surf, (115, 230, 52), (cx - 6, 3, 12, int(h * 0.40)))
            for y_faixa in (6, 10, 14):
                pygame.draw.line(surf, (22, 68, 22), (cx - 5, y_faixa), (cx + 5, y_faixa), 2)
            pygame.draw.line(surf, (215, 255, 110), (cx - 2, 4), (cx - 2, 14), 1)

            pygame.draw.ellipse(surf, (14, 44, 24), (cx - 8, int(h * 0.36), 16, int(h * 0.34)))
            pygame.draw.ellipse(surf, (44, 155, 68), (cx - 7, int(h * 0.38), 14, int(h * 0.30)))
            pygame.draw.ellipse(surf, (115, 238, 98), (cx - 4, int(h * 0.40), 8, int(h * 0.18)))

            pygame.draw.polygon(surf, (24, 65, 32), [(cx - 4, int(h * 0.72)), (cx - 7, h - 5), (cx - 2, int(h * 0.78))])
            pygame.draw.polygon(surf, (24, 65, 32), [(cx + 4, int(h * 0.72)), (cx + 7, h - 5), (cx + 2, int(h * 0.78))])
            pygame.draw.polygon(surf, (32, 36, 44), [(cx - 4, int(h * 0.74)), (cx, h - 1), (cx + 4, int(h * 0.74))])
            pygame.draw.polygon(surf, (255, 225, 70), [(cx - 2, int(h * 0.75)), (cx, h - 2), (cx + 2, int(h * 0.75))])

            pygame.draw.ellipse(surf, (18, 48, 28), (cx - 7, int(h * 0.58), 14, int(h * 0.22)))
            pygame.draw.ellipse(surf, (62, 185, 82), (cx - 6, int(h * 0.60), 12, int(h * 0.18)))

            for lado in (-1, 1):
                ex = cx + lado * 4
                ey = int(h * 0.69)
                pygame.draw.circle(surf, (255, 55, 50), (ex, ey), 3)
                pygame.draw.circle(surf, (255, 235, 210), (ex - lado, ey - 1), 1)

            return surf

        if chave == "inimigo_2":
            cx = w // 2
            for lado in (-1, 1):
                patas = [
                    [(cx + lado * 11, 12), (cx + lado * 19, 7), (cx + lado * 21, 13)],
                    [(cx + lado * 13, 20), (cx + lado * 21, 19), (cx + lado * 20, 26)],
                    [(cx + lado * 11, 28), (cx + lado * 19, 31), (cx + lado * 17, 37)],
                ]
                for p_pts in patas:
                    pygame.draw.lines(surf, (44, 14, 72), False, p_pts, 4)
                    pygame.draw.lines(surf, (215, 75, 205), False, p_pts, 2)

            pinca_esq = [(cx - 8, 32), (cx - 12, 39), (cx - 4, h - 2), (cx - 5, 36)]
            pinca_dir = [(cx + 8, 32), (cx + 12, 39), (cx + 4, h - 2), (cx + 5, 36)]
            pygame.draw.polygon(surf, (38, 12, 62), pinca_esq)
            pygame.draw.polygon(surf, (38, 12, 62), pinca_dir)
            pygame.draw.lines(surf, (255, 130, 235), False, [(cx - 7, 34), (cx - 10, 39), (cx - 4, h - 2)], 2)
            pygame.draw.lines(surf, (255, 130, 235), False, [(cx + 7, 34), (cx + 10, 39), (cx + 4, h - 2)], 2)

            casco_ext = [
                (cx, 3), (cx - 13, 9), (cx - 16, 22), (cx - 11, 32),
                (cx + 11, 32), (cx + 16, 22), (cx + 13, 9),
            ]
            pygame.draw.polygon(surf, (34, 10, 56), casco_ext)

            elitro_esq = [(cx - 1, 5), (cx - 11, 10), (cx - 14, 21), (cx - 9, 29), (cx - 1, 28)]
            elitro_dir = [(cx + 1, 5), (cx + 11, 10), (cx + 14, 21), (cx + 9, 29), (cx + 1, 28)]
            pygame.draw.polygon(surf, (168, 36, 152), elitro_esq)
            pygame.draw.polygon(surf, (138, 28, 132), elitro_dir)
            pygame.draw.lines(surf, (245, 115, 225), False, [(cx - 11, 10), (cx - 1, 5), (cx + 11, 10)], 2)

            pygame.draw.line(surf, (0, 240, 220), (cx, 6), (cx, 28), 2)
            for lado in (-1, 1):
                pygame.draw.circle(surf, (255, 120, 235), (cx + lado * 7, 15), 2)
                pygame.draw.circle(surf, (0, 235, 215), (cx + lado * 6, 23), 2)

            pygame.draw.ellipse(surf, (42, 14, 68), (cx - 10, 26, 20, 11))
            pygame.draw.ellipse(surf, (105, 32, 145), (cx - 9, 27, 18, 9))
            for lado in (-1, 1):
                ex = cx + lado * 5
                pygame.draw.circle(surf, (255, 205, 55), (ex, 32), 3)
                pygame.draw.circle(surf, (255, 250, 210), (ex - lado, 31), 1)

            return surf

        if chave == "inimigo_3":
            cx = w // 2
            for lado in (-1, 1):
                px = cx + lado * 11
                pygame.draw.polygon(surf, (35, 195, 255), [(px - 4, 9), (px, 1), (px + 4, 9)])
                pygame.draw.polygon(surf, (225, 252, 255), [(px - 2, 9), (px, 3), (px + 2, 9)])
                pygame.draw.rect(surf, (36, 42, 56), (px - 5, 8, 10, 6), border_radius=2)

            asa_sombra = [
                (cx - 16, 13), (2, 24), (4, 37), (14, 41),
                (cx + 14, 41), (w - 4, 37), (w - 2, 24), (cx + 16, 13),
            ]
            asa_aco = [
                (cx - 15, 15), (5, 25), (6, 35), (15, 39),
                (cx + 13, 39), (w - 6, 35), (w - 5, 25), (cx + 15, 15),
            ]
            pygame.draw.polygon(surf, (18, 20, 30), asa_sombra)
            pygame.draw.polygon(surf, (68, 78, 102), asa_aco)

            placa_esq = [(cx - 13, 18), (9, 26), (11, 34), (cx - 11, 36)]
            placa_dir = [(cx + 13, 18), (w - 9, 26), (w - 11, 34), (cx + 11, 36)]
            pygame.draw.polygon(surf, (172, 34, 52), placa_esq)
            pygame.draw.polygon(surf, (172, 34, 52), placa_dir)
            pygame.draw.lines(surf, (150, 168, 200), False, [(5, 25), (cx - 15, 15), (cx + 15, 15), (w - 5, 25)], 1)

            for lado in (-1, 1):
                gx = cx + lado * 20
                pygame.draw.rect(surf, (28, 32, 44), (gx - 3, 23, 6, 17), border_radius=2)
                pygame.draw.rect(surf, (130, 145, 175), (gx - 2, 24, 4, 13), border_radius=1)
                pygame.draw.circle(surf, (255, 145, 45), (gx, 40), 2)

            casco_ext = [
                (cx - 11, 10), (cx + 11, 10), (cx + 15, 24), (cx + 12, 43),
                (cx, h - 2), (cx - 12, 43), (cx - 15, 24),
            ]
            casco_med = [
                (cx - 9, 12), (cx + 9, 12), (cx + 12, 25), (cx + 10, 41),
                (cx, h - 5), (cx - 10, 41), (cx - 12, 25),
            ]
            couraca_frontal = [
                (cx - 7, 17), (cx + 7, 17), (cx + 9, 32), (cx, h - 8), (cx - 9, 32),
            ]
            pygame.draw.polygon(surf, (16, 18, 28), casco_ext)
            pygame.draw.polygon(surf, (46, 54, 72), casco_med)
            pygame.draw.polygon(surf, (214, 46, 66), couraca_frontal)
            pygame.draw.lines(surf, (255, 125, 135), False, [(cx - 7, 17), (cx + 7, 17), (cx + 9, 32)], 1)

            pygame.draw.circle(surf, (22, 26, 38), (cx, 27), 7)
            pygame.draw.circle(surf, (255, 155, 35), (cx, 27), 5)
            pygame.draw.circle(surf, (255, 248, 195), (cx, 27), 2)

            pygame.draw.polygon(surf, (0, 235, 255), [(cx - 5, 39), (cx + 5, 39), (cx + 3, 43), (cx - 3, 43)])
            pygame.draw.line(surf, (220, 255, 255), (cx - 3, 40), (cx + 3, 40), 1)
            return surf

        if chave == "inimigo_atirador":
            pygame.draw.polygon(surf, (185, 30, 45), [(w // 2, h), (0, h // 3), (w // 4, 0), (w * 3 // 4, 0), (w, h // 3)])
            pygame.draw.polygon(surf, (240, 75, 85), [(w // 2, h - 6), (w // 4, h // 3), (w * 3 // 4, h // 3)])
            pygame.draw.ellipse(surf, (255, 220, 80), (w // 2 - 5, h // 3, 10, 14))
            return surf

        if chave == "inimigo_morcego":
            asa_esq = [(w // 2, h // 2), (8, 4), (0, h * 2 // 3), (10, h - 4), (16, h * 2 // 3)]
            asa_dir = [(w // 2, h // 2), (w - 8, 4), (w, h * 2 // 3), (w - 10, h - 4), (w - 16, h * 2 // 3)]
            pygame.draw.polygon(surf, (95, 35, 145), asa_esq)
            pygame.draw.polygon(surf, (95, 35, 145), asa_dir)
            pygame.draw.polygon(surf, (155, 70, 220), asa_esq, 2)
            pygame.draw.polygon(surf, (155, 70, 220), asa_dir, 2)
            pygame.draw.ellipse(surf, (55, 20, 85), (w // 2 - 8, 5, 16, h - 8))
            pygame.draw.polygon(surf, (130, 50, 190), [(w // 2 - 6, 8), (w // 2 - 9, 0), (w // 2 - 2, 6)])
            pygame.draw.polygon(surf, (130, 50, 190), [(w // 2 + 6, 8), (w // 2 + 9, 0), (w // 2 + 2, 6)])
            pygame.draw.circle(surf, (255, 50, 80), (w // 2 - 3, h // 2), 2)
            pygame.draw.circle(surf, (255, 50, 80), (w // 2 + 3, h // 2), 2)
            return surf

        if chave == "inimigo_peixe":
            cx = w // 2
            cauda_esq = [(cx, int(h * 0.25)), (int(cx - w * 0.26), 2), (int(cx - w * 0.11), int(h * 0.25))]
            cauda_dir = [(cx, int(h * 0.25)), (int(cx + w * 0.26), 2), (int(cx + w * 0.11), int(h * 0.25))]
            pygame.draw.polygon(surf, (115, 45, 195), cauda_esq)
            pygame.draw.polygon(surf, (115, 45, 195), cauda_dir)
            pygame.draw.line(surf, (0, 235, 210), cauda_esq[2], cauda_esq[1], 2)
            pygame.draw.line(surf, (0, 235, 210), cauda_dir[2], cauda_dir[1], 2)

            asa_esq = [(int(cx - w * 0.17), int(h * 0.38)), (2, int(h * 0.56)), (int(w * 0.11), int(h * 0.74)), (int(cx - w * 0.20), int(h * 0.60))]
            asa_dir = [(int(cx + w * 0.17), int(h * 0.38)), (w - 2, int(h * 0.56)), (int(w * 0.89), int(h * 0.74)), (int(cx + w * 0.20), int(h * 0.60))]
            pygame.draw.polygon(surf, (30, 125, 210), asa_esq)
            pygame.draw.polygon(surf, (30, 125, 210), asa_dir)
            pygame.draw.lines(surf, (115, 235, 255), False, asa_esq[:3], 2)
            pygame.draw.lines(surf, (115, 235, 255), False, asa_dir[:3], 2)

            corpo_ext = [
                (cx, int(h * 0.15)), (int(cx - w * 0.26), int(h * 0.42)),
                (int(cx - w * 0.22), int(h * 0.72)), (cx, h - 3),
                (int(cx + w * 0.22), int(h * 0.72)), (int(cx + w * 0.26), int(h * 0.42)),
            ]
            corpo_med = [
                (cx, int(h * 0.22)), (int(cx - w * 0.20), int(h * 0.45)),
                (int(cx - w * 0.16), int(h * 0.68)), (cx, h - 6),
                (int(cx + w * 0.16), int(h * 0.68)), (int(cx + w * 0.20), int(h * 0.45)),
            ]
            crista = [
                (cx, int(h * 0.26)), (int(cx - w * 0.08), int(h * 0.50)),
                (cx, int(h * 0.76)), (int(cx + w * 0.08), int(h * 0.50)),
            ]
            pygame.draw.polygon(surf, (20, 48, 112), corpo_ext)
            pygame.draw.polygon(surf, (46, 138, 232), corpo_med)
            pygame.draw.polygon(surf, (110, 215, 255), crista)

            pygame.draw.line(surf, (0, 245, 215), (int(cx - w * 0.16), int(h * 0.42)), (int(cx - w * 0.14), int(h * 0.56)), 2)
            pygame.draw.line(surf, (0, 245, 215), (int(cx + w * 0.16), int(h * 0.42)), (int(cx + w * 0.14), int(h * 0.56)), 2)

            for lado in (-1, 1):
                ex = cx + lado * int(w * 0.14)
                ey = int(h * 0.64)
                pygame.draw.circle(surf, (255, 220, 70), (ex, ey), 4)
                pygame.draw.circle(surf, (14, 18, 36), (ex, ey + 1), 2)
            pygame.draw.circle(surf, (0, 250, 220), (cx, h - 4), 2)
            return surf

        if chave == "boss_squid":
            cx = w // 2
            for lado in (-1, 1):
                pts_tras = [
                    (cx + lado * 22, 96), (cx + lado * 56, 124),
                    (cx + lado * 48, 156), (cx + lado * 62, 170),
                ]
                pygame.draw.lines(surf, (62, 20, 108), False, pts_tras, 10)
                pygame.draw.circle(surf, (130, 45, 200), pts_tras[-1], 5)

            manto_sombra = [(cx, 2), (8, 56), (26, 82), (w - 26, 82), (w - 8, 56)]
            manto_medio = [(cx, 6), (16, 54), (32, 76), (w - 32, 76), (w - 16, 54)]
            manto_crista = [(cx, 10), (cx - 22, 52), (cx, 68), (cx + 22, 52)]
            pygame.draw.polygon(surf, (58, 18, 102), manto_sombra)
            pygame.draw.polygon(surf, (118, 42, 188), manto_medio)
            pygame.draw.polygon(surf, (165, 72, 235), manto_crista)
            pygame.draw.lines(surf, (215, 130, 255), False, [(16, 54), (cx, 6), (w - 16, 54)], 2)

            pygame.draw.lines(surf, (0, 240, 210), False, [(cx - 18, 42), (cx, 28), (cx + 18, 42)], 2)
            pygame.draw.lines(surf, (0, 240, 210), False, [(cx - 12, 54), (cx, 44), (cx + 12, 54)], 2)

            tentaculos = [
                (-34, -46, -28, 158, 9), (-14, -22, -10, 171, 11),
                (14, 22, 10, 171, 11), (34, 46, 28, 158, 9),
            ]
            for ox_topo, ox_meio, ox_ponta, y_fim, esp in tentaculos:
                p0 = (cx + ox_topo // 2, 104)
                p1 = (cx + ox_meio, 132)
                p2 = (cx + ox_ponta, y_fim)
                pygame.draw.lines(surf, (88, 28, 148), False, [p0, p1, p2], esp + 3)
                pygame.draw.lines(surf, (155, 62, 225), False, [p0, p1, p2], max(4, esp - 2))
                pygame.draw.circle(surf, (0, 245, 210), p1, 3)
                pygame.draw.circle(surf, (255, 110, 220), p2, 4)

            pygame.draw.ellipse(surf, (72, 24, 125), (cx - 42, 34, 84, 86))
            pygame.draw.ellipse(surf, (132, 48, 202), (cx - 36, 38, 72, 76))
            pygame.draw.ellipse(surf, (175, 82, 242), (cx - 24, 42, 48, 44))

            pygame.draw.polygon(surf, (48, 14, 85), [(cx - 36, 70), (cx - 8, 78), (cx - 12, 66)])
            pygame.draw.polygon(surf, (48, 14, 85), [(cx + 36, 70), (cx + 8, 78), (cx + 12, 66)])

            for lado in (-1, 1):
                ex = cx + lado * 19
                ey = 86
                pygame.draw.ellipse(surf, (14, 8, 26), (ex - 11, ey - 13, 22, 26))
                pygame.draw.ellipse(surf, (0, 235, 200), (ex - 8, ey - 10, 16, 20))
                pygame.draw.rect(surf, (12, 10, 24), (ex - 7, ey - 2, 14, 5), border_radius=2)
                pygame.draw.circle(surf, (255, 255, 255), (ex - 3, ey - 5), 2)

            return surf

        if chave == "boss_colmeia":
            # Colmeia-Mãe / Núcleo Parasita (170x170): organismo biomecânico quitinoso com núcleo verde-tóxico
            cx, cy = w // 2, h // 2 - 4

            # Tentáculos/ovipositores inferiores
            for ox, comp, esp in [(-38, 42, 7), (-18, 52, 9), (0, 58, 10), (18, 52, 9), (38, 42, 7)]:
                p0 = (cx + ox, cy + 36)
                p1 = (cx + int(ox * 1.15), cy + 36 + comp // 2)
                p2 = (cx + int(ox * 0.85), cy + 36 + comp)
                pygame.draw.lines(surf, (46, 26, 58), False, [p0, p1, p2], esp + 3)
                pygame.draw.lines(surf, (125, 175, 42), False, [p0, p1, p2], max(3, esp - 3))
                pygame.draw.circle(surf, (195, 255, 75), p2, 4)

            # Garras biomecânicas laterais
            for lado in (-1, 1):
                garra = [
                    (cx + lado * 48, cy - 12),
                    (cx + lado * 78, cy - 30),
                    (cx + lado * 82, cy + 8),
                    (cx + lado * 62, cy + 34),
                    (cx + lado * 44, cy + 16),
                ]
                pygame.draw.polygon(surf, (38, 22, 48), garra)
                pygame.draw.lines(surf, (165, 225, 65), False, garra[1:4], 3)

            # Carapaça quitinosa hexagonal externa
            casco = [
                (cx, 12), (cx - 46, 28), (cx - 64, cy),
                (cx - 44, cy + 46), (cx + 44, cy + 46),
                (cx + 64, cy), (cx + 46, 28),
            ]
            pygame.draw.polygon(surf, (44, 24, 56), casco)
            pygame.draw.polygon(surf, (86, 48, 92), [
                (cx, 18), (cx - 40, 32), (cx - 56, cy),
                (cx - 38, cy + 40), (cx + 38, cy + 40),
                (cx + 56, cy), (cx + 40, 32),
            ])
            pygame.draw.polygon(surf, (150, 215, 65), casco, 2)

            # Alvéolos / favos bioluminescentes na carapaça
            for ax, ay, ar in [(-32, -22, 11), (32, -22, 11), (-36, 16, 10), (36, 16, 10), (0, -38, 12)]:
                pygame.draw.circle(surf, (32, 58, 24), (cx + ax, cy + ay), ar + 2)
                pygame.draw.circle(surf, (125, 235, 65), (cx + ax, cy + ay), ar)
                pygame.draw.circle(surf, (220, 255, 145), (cx + ax - 3, cy + ay - 3), max(2, ar // 3))

            # Núcleo Parasita central pulsante
            pygame.draw.circle(surf, (24, 48, 22), (cx, cy + 2), 30)
            pygame.draw.circle(surf, (95, 225, 55), (cx, cy + 2), 25)
            pygame.draw.circle(surf, (195, 255, 110), (cx, cy + 2), 16)
            pygame.draw.ellipse(surf, (24, 34, 20), (cx - 5, cy - 10, 10, 24))
            pygame.draw.circle(surf, (255, 255, 220), (cx - 7, cy - 7), 4)
            return surf

        if chave == "boss_eye":
            cx, cy = w // 2, h // 2 + 6
            chifre_esq_base = [(52, 54), (20, 32), (6, 4), (36, 16), (68, 42)]
            chifre_esq_luz = [(50, 48), (22, 28), (10, 8), (34, 18), (64, 42)]
            pygame.draw.polygon(surf, (36, 26, 44), chifre_esq_base)
            pygame.draw.polygon(surf, (150, 115, 55), chifre_esq_luz)
            pygame.draw.lines(surf, (240, 205, 120), False, [(10, 8), (34, 18), (64, 42)], 2)

            chifre_dir_base = [(w - 52, 54), (w - 20, 32), (w - 6, 4), (w - 36, 16), (w - 68, 42)]
            chifre_dir_luz = [(w - 50, 48), (w - 22, 28), (w - 10, 8), (w - 34, 18), (w - 64, 42)]
            pygame.draw.polygon(surf, (36, 26, 44), chifre_dir_base)
            pygame.draw.polygon(surf, (150, 115, 55), chifre_dir_luz)
            pygame.draw.lines(surf, (240, 205, 120), False, [(w - 10, 8), (w - 34, 18), (w - 64, 42)], 2)

            pygame.draw.polygon(surf, (24, 90, 50), [(66, 42), (60, 14), (78, 36)])
            pygame.draw.polygon(surf, (58, 185, 105), [(66, 40), (62, 18), (74, 36)])
            pygame.draw.polygon(surf, (24, 90, 50), [(w - 66, 42), (w - 60, 14), (w - 78, 36)])
            pygame.draw.polygon(surf, (58, 185, 105), [(w - 66, 40), (w - 62, 18), (w - 74, 36)])

            asa_esq = [(32, 72), (2, 58), (12, 92), (2, 120), (34, 116)]
            asa_dir = [(w - 32, 72), (w - 2, 58), (w - 12, 92), (w - 2, 120), (w - 34, 116)]
            pygame.draw.polygon(surf, (14, 58, 34), asa_esq)
            pygame.draw.polygon(surf, (14, 58, 34), asa_dir)
            pygame.draw.polygon(surf, (34, 140, 76), [(32, 75), (8, 64), (16, 92), (34, 96)])
            pygame.draw.polygon(surf, (34, 140, 76), [(w - 32, 75), (w - 8, 64), (w - 16, 92), (w - 34, 96)])
            pygame.draw.lines(surf, (80, 225, 135), False, [(32, 72), (2, 58), (12, 92)], 2)
            pygame.draw.lines(surf, (80, 225, 135), False, [(w - 32, 72), (w - 2, 58), (w - 12, 92)], 2)

            pygame.draw.polygon(surf, (22, 68, 40), [(54, 136), (44, 176), (72, 152)])
            pygame.draw.polygon(surf, (22, 68, 40), [(w - 54, 136), (w - 44, 176), (w - 72, 152)])
            pygame.draw.polygon(surf, (185, 155, 95), [(56, 142), (48, 172), (68, 152)])
            pygame.draw.polygon(surf, (185, 155, 95), [(w - 56, 142), (w - 48, 172), (w - 68, 152)])
            pygame.draw.polygon(surf, (235, 215, 165), [(72, 150), (76, 168), (82, 152)])
            pygame.draw.polygon(surf, (235, 215, 165), [(w - 72, 150), (w - 76, 168), (w - 82, 152)])

            casco_sombra = [
                (cx - 34, 38), (cx + 34, 38), (w - 24, 68), (w - 22, 118),
                (cx + 38, 154), (cx - 38, 154), (22, 118), (24, 68),
            ]
            casco_medio = [
                (cx - 31, 42), (cx + 31, 42), (w - 28, 70), (w - 27, 115),
                (cx + 35, 149), (cx - 35, 149), (27, 115), (28, 70),
            ]
            casco_topo_luz = [(cx - 31, 42), (cx + 31, 42), (w - 28, 70), (cx, 62), (28, 70)]
            casco_base_sombra = [(cx - 35, 149), (cx + 35, 149), (cx + 22, 134), (cx - 22, 134)]
            pygame.draw.polygon(surf, (12, 48, 28), casco_sombra)
            pygame.draw.polygon(surf, (26, 118, 64), casco_medio)
            pygame.draw.polygon(surf, (46, 175, 96), casco_topo_luz)
            pygame.draw.polygon(surf, (16, 72, 40), casco_base_sombra)
            pygame.draw.lines(surf, (95, 235, 145), False, [(28, 70), (cx - 31, 42), (cx + 31, 42), (w - 28, 70)], 2)
            pygame.draw.lines(surf, (10, 35, 20), False, [(24, 118), (cx - 38, 154), (cx + 38, 154), (w - 24, 118)], 3)

            for ox, oy, esc_w, esc_h in [(0, 46, 26, 16), (-22, 52, 20, 14), (22, 52, 20, 14)]:
                px, py = cx + ox, oy
                pygame.draw.polygon(surf, (12, 45, 26), [(px, py + esc_h + 3), (px - esc_w // 2, py + 3), (px, py - 3), (px + esc_w // 2, py + 3)])
                pygame.draw.polygon(surf, (42, 165, 88), [(px, py + esc_h), (px - esc_w // 2, py), (px, py - 5), (px + esc_w // 2, py)])
                pygame.draw.lines(surf, (110, 245, 160), False, [(px - esc_w // 2, py), (px, py - 5), (px + esc_w // 2, py)], 2)

            for lado in (-1, 1):
                v1 = (cx + lado * 44, cy + 16)
                v2 = (cx + lado * 56, cy + 28)
                v3 = (cx + lado * 46, cy + 42)
                pygame.draw.lines(surf, (140, 20, 30), False, [v1, v2, v3], 4)
                pygame.draw.lines(surf, (255, 95, 65), False, [v1, v2, v3], 2)

            pygame.draw.ellipse(surf, (10, 24, 16), (cx - 54, cy - 36, 108, 72))
            pygame.draw.ellipse(surf, (205, 175, 125), (cx - 47, cy - 30, 94, 60))
            pygame.draw.ellipse(surf, (245, 225, 180), (cx - 42, cy - 26, 84, 52))
            pygame.draw.ellipse(surf, (255, 248, 225), (cx - 32, cy - 18, 64, 36))

            pygame.draw.circle(surf, (155, 20, 20), (cx, cy), 25)
            pygame.draw.circle(surf, (225, 45, 30), (cx, cy), 21)
            for ang in range(0, 360, 30):
                rad = math.radians(ang)
                ix1, iy1 = cx + int(math.cos(rad) * 10), cy + int(math.sin(rad) * 10)
                ix2, iy2 = cx + int(math.cos(rad) * 20), cy + int(math.sin(rad) * 20)
                pygame.draw.line(surf, (255, 145, 45), (ix1, iy1), (ix2, iy2), 2)
            pygame.draw.circle(surf, (255, 180, 60), (cx, cy), 12, 2)

            pupila = [(cx, cy - 21), (cx + 7, cy), (cx, cy + 21), (cx - 7, cy)]
            pygame.draw.polygon(surf, (10, 6, 16), pupila)
            pygame.draw.polygon(surf, (255, 110, 40), pupila, 1)

            sombra_palpebra = pygame.Surface((96, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(sombra_palpebra, (15, 20, 25, 115), (0, -10, 96, 32))
            surf.blit(sombra_palpebra, (cx - 48, cy - 31))

            pygame.draw.circle(surf, (255, 255, 255), (cx - 10, cy - 10), 4)
            pygame.draw.circle(surf, (255, 230, 190), (cx + 10, cy + 9), 2)

            brow_esq = [(34, cy - 22), (cx - 4, cy - 12), (cx - 10, cy - 30), (42, cy - 38)]
            brow_dir = [(w - 34, cy - 22), (cx + 4, cy - 12), (cx + 10, cy - 30), (w - 42, cy - 38)]
            pygame.draw.polygon(surf, (10, 32, 18), [(p[0], p[1] + 4) for p in brow_esq])
            pygame.draw.polygon(surf, (10, 32, 18), [(p[0], p[1] + 4) for p in brow_dir])
            pygame.draw.polygon(surf, (34, 145, 78), brow_esq)
            pygame.draw.polygon(surf, (34, 145, 78), brow_dir)
            pygame.draw.lines(surf, (105, 245, 155), False, [(42, cy - 38), (cx - 10, cy - 30), (cx - 4, cy - 12)], 2)
            pygame.draw.lines(surf, (105, 245, 155), False, [(w - 42, cy - 38), (cx + 10, cy - 30), (cx + 4, cy - 12)], 2)
            return surf

        if chave in ("boss_gemea_alfa", "boss_gemea_beta"):
            # Naves Irmãs do Colosso Gêmeo (106x118): Alfa (Ciano/Prata) e Beta (Magenta/Violeta)
            eh_alfa = (chave == "boss_gemea_alfa")
            cor_prim = (35, 175, 235) if eh_alfa else (210, 55, 185)
            cor_luz = (155, 245, 255) if eh_alfa else (255, 165, 245)
            cor_esc = (22, 46, 82) if eh_alfa else (68, 22, 68)
            cx, cy = w // 2, h // 2

            # Propulsores superiores
            for ox in (-16, 16):
                pygame.draw.polygon(surf, cor_prim, [(cx + ox - 5, 14), (cx + ox, 2), (cx + ox + 5, 14)])
                pygame.draw.polygon(surf, (255, 255, 255), [(cx + ox - 2, 14), (cx + ox, 5), (cx + ox + 2, 14)])

            # Asas angulares de combate
            asa = [
                (cx, 14), (8, 42), (12, 82), (cx - 18, 96),
                (cx, h - 6), (cx + 18, 96), (w - 12, 82), (w - 8, 42),
            ]
            pygame.draw.polygon(surf, cor_esc, asa)
            pygame.draw.polygon(surf, cor_prim, [
                (cx, 20), (16, 44), (20, 78), (cx - 14, 90),
                (cx, h - 12), (cx + 14, 90), (w - 20, 78), (w - 16, 44),
            ])
            pygame.draw.polygon(surf, cor_luz, asa, 2)

            # Núcleo reator central
            pygame.draw.polygon(surf, (38, 44, 62), [(cx, 26), (cx - 14, 52), (cx, 84), (cx + 14, 52)])
            pygame.draw.circle(surf, cor_luz, (cx, cy + 2), 13)
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy + 2), 6)

            # Bobinas elétricas nas laterais
            for lado in (-1, 1):
                bx = cx + lado * 36
                pygame.draw.rect(surf, (42, 48, 66), (bx - 4, cy - 12, 8, 24), border_radius=2)
                pygame.draw.circle(surf, cor_luz, (bx, cy), 5)
            return surf

        if chave == "boss_buraco_negro":
            # Arquiteto Estelar / Buraco Negro (176x176): singularidade com disco de acreção cósmico
            cx, cy = w // 2, h // 2

            # Anéis gravitacionais externos
            pygame.draw.circle(surf, (85, 45, 165), (cx, cy), 82, 2)
            pygame.draw.circle(surf, (145, 85, 245), (cx, cy), 72, 1)

            # Disco de acreção inclinado (elipses luminosas douradas/laranja/violeta)
            for rot_w, rot_h, cor_disco, esp in [
                (166, 52, (135, 55, 215), 6),
                (152, 42, (235, 115, 35), 5),
                (136, 30, (255, 215, 95), 3),
            ]:
                pygame.draw.ellipse(surf, cor_disco, (cx - rot_w // 2, cy - rot_h // 2, rot_w, rot_h), esp)

            # Estruturas geométricas do Arquiteto Estelar (4 pilares orbitais)
            for ang_deg in (45, 135, 225, 315):
                rad = math.radians(ang_deg)
                px = cx + int(math.cos(rad) * 58)
                py = cy + int(math.sin(rad) * 58)
                pygame.draw.circle(surf, (42, 34, 68), (px, py), 10)
                pygame.draw.circle(surf, (255, 195, 75), (px, py), 10, 2)
                pygame.draw.circle(surf, (130, 235, 255), (px, py), 4)

            # Horizonte de eventos (esfera negra com borda incandescente)
            pygame.draw.circle(surf, (255, 165, 55), (cx, cy), 39)
            pygame.draw.circle(surf, (255, 240, 175), (cx, cy), 36)
            pygame.draw.circle(surf, (8, 6, 16), (cx, cy), 33)
            pygame.draw.arc(surf, (185, 120, 255), (cx - 28, cy - 28, 56, 56), 0.3, 2.5, 2)
            return surf

        if chave == "boss_final":
            cx, cy = w // 2, h // 2
            asa_ext = [(cx, 10), (8, cy + 18), (24, h - 22), (cx - 28, h - 10), (cx + 28, h - 10), (w - 24, h - 22), (w - 8, cy + 18)]
            asa_int = [(cx, 22), (28, cy + 16), (42, h - 24), (w - 42, h - 24), (w - 28, cy + 16)]
            pygame.draw.polygon(surf, (45, 52, 72), asa_ext)
            pygame.draw.polygon(surf, (82, 94, 125), asa_int)
            pygame.draw.polygon(surf, (255, 90, 70), asa_ext, 2)
            for lx in (44, w - 44):
                pygame.draw.rect(surf, (150, 165, 195), (lx - 6, cy + 8, 12, 34), border_radius=3)
                pygame.draw.circle(surf, (255, 190, 60), (lx, cy + 40), 4)
            pygame.draw.polygon(surf, (125, 32, 48), [(cx, 6), (cx - 32, cy), (cx - 22, h - 12), (cx + 22, h - 12), (cx + 32, cy)])
            pygame.draw.rect(surf, (35, 40, 52), (cx - 14, cy + 12, 28, h - cy - 12), border_radius=4)
            pygame.draw.circle(surf, (0, 235, 255), (cx, cy - 4), 16)
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy - 4), 7)
            return surf

        return surf

    def criar_textura_asteroide(self, raio):
        tamanho = raio * 2 + 8
        centro = tamanho // 2
        surf = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        pontos = []

        for angulo in range(0, 360, 30):
            rad = math.radians(angulo)
            r_var = raio + random.randint(-raio // 4, raio // 5)
            px = centro + int(math.cos(rad) * r_var)
            py = centro + int(math.sin(rad) * r_var)
            pontos.append((px, py))

        pygame.draw.polygon(surf, (115, 110, 105), pontos)
        pygame.draw.polygon(surf, (70, 68, 65), pontos, 3)

        for _ in range(max(4, raio // 4)):
            cx = centro + random.randint(-raio // 2, raio // 2)
            cy = centro + random.randint(-raio // 2, raio // 2)
            cr = random.randint(3, max(4, raio // 4))
            pygame.draw.circle(surf, (80, 76, 72), (cx, cy), cr)
            pygame.draw.circle(surf, (135, 130, 125), (cx - 1, cy - 1), cr, 1)

        return surf

    def criar_mancha_tinta(self):
        surf = pygame.Surface((260, 260))
        surf.fill((0, 0, 0))
        surf.set_colorkey((0, 0, 0))
        cx, cy = 130, 130
        pygame.draw.circle(surf, (28, 12, 48), (cx, cy), 68)
        for _ in range(14):
            ang = random.uniform(0, math.pi * 2)
            dist = random.randint(35, 95)
            bx = cx + int(math.cos(ang) * dist)
            by = cy + int(math.sin(ang) * dist)
            br = random.randint(12, 34)
            pygame.draw.circle(surf, (24, 10, 42), (bx, by), br)
        return surf

    def _criar_coracao(self, cor_principal, cor_brilho):
        desenho = [
            ".RR...RR.",
            "RWRR.RRRR",
            "RRRRRRRRR",
            "RRRRRRRRR",
            ".RRRRRRR.",
            "..RRRRR..",
            "...RRR...",
            "....R....",
        ]
        sup = pygame.Surface((9, 8), pygame.SRCALPHA)
        for y, linha in enumerate(desenho):
            for x, px in enumerate(linha):
                if px == "R":
                    sup.set_at((x, y), cor_principal)
                elif px == "W":
                    sup.set_at((x, y), cor_brilho)
        return pygame.transform.scale(sup, (27, 24))

    def _criar_icones_poder(self):
        icones = {}

        surf_b = pygame.Surface((34, 34), pygame.SRCALPHA)
        pygame.draw.circle(surf_b, (15, 18, 24), (16, 20), 11)
        pygame.draw.circle(surf_b, (44, 50, 66), (16, 20), 10)
        pygame.draw.circle(surf_b, (72, 82, 106), (14, 18), 7)
        pygame.draw.circle(surf_b, (220, 235, 255), (12, 16), 2)
        pygame.draw.circle(surf_b, (255, 130, 45), (16, 20), 10, 1)
        pygame.draw.rect(surf_b, (20, 24, 32), (13, 8, 7, 4), border_radius=1)
        pygame.draw.rect(surf_b, (150, 160, 180), (14, 8, 5, 3), border_radius=1)
        pygame.draw.lines(surf_b, (225, 190, 120), False, [(16, 8), (19, 4), (24, 4)], 2)
        pygame.draw.circle(surf_b, (255, 85, 20), (25, 4), 5)
        pygame.draw.circle(surf_b, (255, 215, 60), (25, 4), 3)
        pygame.draw.line(surf_b, (255, 255, 255), (21, 4), (29, 4), 1)
        pygame.draw.line(surf_b, (255, 255, 255), (25, 0), (25, 8), 1)
        icones["bomba"] = surf_b

        surf_t = pygame.Surface((34, 34), pygame.SRCALPHA)

        def desenhar_bala(bx, by_topo, altura_corpo):
            ogiva_ext = [(bx, by_topo - 1), (bx - 4, by_topo + 6), (bx + 4, by_topo + 6)]
            pygame.draw.polygon(surf_t, (20, 24, 34), ogiva_ext)
            pygame.draw.rect(surf_t, (20, 24, 34), (bx - 4, by_topo + 5, 9, altura_corpo + 2), border_radius=1)

            ogiva = [(bx, by_topo), (bx - 3, by_topo + 5), (bx + 3, by_topo + 5)]
            pygame.draw.polygon(surf_t, (255, 165, 45), ogiva)
            pygame.draw.line(surf_t, (255, 235, 150), (bx, by_topo + 1), (bx - 2, by_topo + 5), 1)

            pygame.draw.rect(surf_t, (225, 170, 40), (bx - 3, by_topo + 6, 7, altura_corpo - 2))
            pygame.draw.line(surf_t, (255, 235, 130), (bx - 2, by_topo + 6), (bx - 2, by_topo + 3 + altura_corpo), 1)
            pygame.draw.line(surf_t, (155, 105, 20), (bx + 2, by_topo + 6), (bx + 2, by_topo + 3 + altura_corpo), 1)

            y_base = by_topo + 4 + altura_corpo
            pygame.draw.line(surf_t, (120, 80, 15), (bx - 3, y_base), (bx + 3, y_base), 1)
            pygame.draw.rect(surf_t, (245, 195, 65), (bx - 3, y_base + 1, 7, 2))

        desenhar_bala(8, 11, 14)
        desenhar_bala(26, 11, 14)
        desenhar_bala(17, 6, 15)
        icones["tiro_triplo"] = surf_t

        surf_e = pygame.Surface((34, 34), pygame.SRCALPHA)
        escudo_borda = [(17, 2), (29, 7), (27, 19), (17, 31), (7, 19), (5, 7)]
        escudo_esq = [(17, 4), (7, 8), (9, 18), (17, 29)]
        escudo_dir = [(17, 4), (27, 8), (25, 18), (17, 29)]

        pygame.draw.polygon(surf_e, (10, 62, 34), escudo_borda)
        pygame.draw.polygon(surf_e, (42, 215, 115), escudo_esq)
        pygame.draw.polygon(surf_e, (24, 165, 85), escudo_dir)
        pygame.draw.polygon(surf_e, (165, 255, 205), escudo_borda, 2)
        pygame.draw.line(surf_e, (215, 255, 230), (17, 7), (17, 25), 2)
        pygame.draw.line(surf_e, (215, 255, 230), (11, 14), (23, 14), 2)
        icones["escudo"] = surf_e

        surf_c = pygame.Surface((34, 34), pygame.SRCALPHA)
        surf_c.blit(self.coracao_cheio, (3, 5))
        icones["cura"] = surf_c

        return icones