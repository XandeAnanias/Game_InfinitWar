import os
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")
AUDIO_DIR = os.path.join(BASE_DIR, "assets", "audio")

LARGURA = 800
ALTURA = 700
FPS = 60
TITULO = "Guerra No Infinito"
MAX_VOLUME_GLOBAL = 0.4

SPRITES_CONFIG = {
    "nave_p1":              {"arquivo": os.path.join(IMAGES_DIR, "nave.png"),                 "tamanho": (70, 70)},
    "nave_p2":              {"arquivo": os.path.join(IMAGES_DIR, "nave_p2.png"),              "tamanho": (70, 70)},
    "nave_interceptora":    {"arquivo": os.path.join(IMAGES_DIR, "nave_interceptora.png"),    "tamanho": (70, 70)},
    "nave_interceptora_p2": {"arquivo": os.path.join(IMAGES_DIR, "nave_interceptora_p2.png"), "tamanho": (70, 70)},
    "nave_caca":            {"arquivo": os.path.join(IMAGES_DIR, "nave_caca.png"),            "tamanho": (70, 70)},
    "nave_caca_p2":         {"arquivo": os.path.join(IMAGES_DIR, "nave_caca_p2.png"),         "tamanho": (70, 70)},
    "nave_fundo":           {"arquivo": os.path.join(IMAGES_DIR, "navefundo.png"),            "tamanho": (130, 130)},
    "inimigo_1":            {"arquivo": os.path.join(IMAGES_DIR, "inimigo1.png"),             "tamanho": (36, 36)},
    "inimigo_2":            {"arquivo": os.path.join(IMAGES_DIR, "inimigo2.png"),             "tamanho": (44, 44)},
    "inimigo_3":            {"arquivo": os.path.join(IMAGES_DIR, "inimigo3.png"),             "tamanho": (54, 54)},
    "inimigo_atirador":     {"arquivo": os.path.join(IMAGES_DIR, "nave_inimiga.png"),         "tamanho": (47, 47)},
    "inimigo_morcego":      {"arquivo": os.path.join(IMAGES_DIR, "inimigo_morcego.png"),      "tamanho": (46, 30)},
    "inimigo_peixe":        {"arquivo": os.path.join(IMAGES_DIR, "inimigo_peixe.png"),        "tamanho": (46, 38)},
    "inimigo_abelha":       {"arquivo": os.path.join(IMAGES_DIR, "inimigo_abelha.png"),       "tamanho": (52, 48)},
    "boss_squid":           {"arquivo": os.path.join(IMAGES_DIR, "boss_lula.png"),            "tamanho": (150, 175)},
    "boss_colmeia":         {"arquivo": os.path.join(IMAGES_DIR, "boss_colmeia.png"),         "tamanho": (170, 170)},
    "boss_eye":             {"arquivo": os.path.join(IMAGES_DIR, "boss_dragao.png"),          "tamanho": (180, 180)},
    "boss_final":           {"arquivo": os.path.join(IMAGES_DIR, "final_boss.png"),           "tamanho": (185, 200)},
    "boss_gemea_alfa":      {"arquivo": os.path.join(IMAGES_DIR, "boss_gemea_alfa.png"),      "tamanho": (106, 118)},
    "boss_gemea_beta":      {"arquivo": os.path.join(IMAGES_DIR, "boss_gemea_beta.png"),      "tamanho": (106, 118)},
    "boss_buraco_negro":    {"arquivo": os.path.join(IMAGES_DIR, "boss_buraco_negro.png"),    "tamanho": (176, 176)},
}

ORDEM_NAVES = ["interceptora", "cruzador", "caca_pesado"]

NAVES_CONFIG = {
    "interceptora": {
        "nome": "INTERCEPTORA",
        "subtitulo": "Alta Velocidade",
        "sprite_p1": "nave_interceptora",
        "sprite_p2": "nave_interceptora_p2",
        "velocidade": 7.1,
        "vidas": 3,
        "fator_recarga": 1.0,
        "stats": (5, 3, 3),
        "cor": (0, 235, 255),
        "desc_1": "Velocidade +22% para esquiva",
        "desc_2": "Escapa fácil de tinta e lasers",
    },
    "cruzador": {
        "nome": "CRUZADOR",
        "subtitulo": "Casco Blindado",
        "sprite_p1": "nave_p1",
        "sprite_p2": "nave_p2",
        "velocidade": 5.8,
        "vidas": 4,
        "fator_recarga": 1.0,
        "stats": (3, 5, 3),
        "cor": (75, 245, 145),
        "desc_1": "+1 Coração de Blindagem (4 HP)",
        "desc_2": "Resistência máxima nos chefes",
    },
    "caca_pesado": {
        "nome": "CAÇA TÁTICO",
        "subtitulo": "Cadência Rápida",
        "sprite_p1": "nave_caca",
        "sprite_p2": "nave_caca_p2",
        "velocidade": 6.1,
        "vidas": 3,
        "fator_recarga": 0.80,
        "stats": (3, 3, 5),
        "cor": (68, 175, 245),
        "desc_1": "Recarga 20% mais rápida",
        "desc_2": "Dano contínuo em todas as armas",
    },
}

SONS_CONFIG = {
    "tiro":          os.path.join(AUDIO_DIR, "tiro.wav"),
    "tiro_triplo":   os.path.join(AUDIO_DIR, "tiro_triplo.wav"),
    "bomba":         os.path.join(AUDIO_DIR, "bomba.wav"),
    "explosao":      os.path.join(AUDIO_DIR, "explosao.wav"),
    "dano":          os.path.join(AUDIO_DIR, "dano.wav"),
    "morte":         os.path.join(AUDIO_DIR, "morte.wav"),
    "olho_carregar": os.path.join(AUDIO_DIR, "olho_carregar.wav"),
    "olho_laser":    os.path.join(AUDIO_DIR, "olho_laser.wav"),
    "olho_invocar":  os.path.join(AUDIO_DIR, "olho_invocar.wav"),
}

VIDA_MAXIMA = 3

# Ordem dos 6 Bosses:
# 1. Lula -> 2. Colmeia -> 3. Dragão -> 4. Nave -> 5. Naves Duplas -> 6. O Arquiteto
PONTOS_BOSS_1 = 5500     # 1. Lula
PONTOS_BOSS_2 = 13000    # 2. Colmeia
PONTOS_BOSS_3 = 22000    # 3. Dragão
PONTOS_BOSS_4 = 32500    # 4. Nave (Comando de Andromeda)
PONTOS_BOSS_5 = 44500    # 5. Naves Duplas
PONTOS_BOSS_6 = 58000    # 6. O Arquiteto (Boss Final do Loop)

# Armas e Cooldowns
TIRO_RAPIDO_COOLDOWN = 15
TIRO_RAPIDO_DANO = 1
TIRO_PESADO_COOLDOWN = 45
TIRO_PESADO_DANO = 2.5

TIRO_TRIPLO_COOLDOWN = 15
TIRO_TRIPLO_DANO = 1
TIRO_TRIPLO_DURACAO = 480

TIRO_BOMBA_COOLDOWN = 58
TIRO_BOMBA_DANO_DIRETO = 1
TIRO_BOMBA_DANO_AREA_INIMIGO = 6
TIRO_BOMBA_DANO_AREA_BOSS = 10
TIRO_BOMBA_RAIO = 105
TIRO_BOMBA_DURACAO = 420

# Escalonamento
ESCALA_DANO_LOOP = 0.20
ESCALA_MULT_PROGRESSO_LOOP = 0.45
ESCALA_MULT_BONUS_LOOP = 0.35

SPAWN_INTERVALO_INICIAL = 50
SPAWN_REDUCAO_PROGRESSO = 36
SPAWN_INTERVALO_MINIMO = 22

LIMITE_INIMIGOS_LOOP1_MIN = 6
LIMITE_INIMIGOS_LOOP1_MAX = 10
LIMITE_INIMIGOS_BONUS_LOOP = 3
LIMITE_INIMIGOS_TETO_GLOBAL = 18

INIMIGO_TIRO_COOLDOWN_BASE = 80
INIMIGO_TIRO_COOLDOWN_MIN = 45
INIMIGO_TIRO_DELAY_INICIAL = (20, 55)

# Status dos 6 Bosses
LULA_VIDA = 167
LULA_VELOCIDADE = 3.4
LULA_TINTA_Y_EXPLOSAO = (360, 580)
LULA_TINTA_DURACAO_POCA = 240
FATOR_LENTIDAO_TINTA = 0.50

COLMEIA_VIDA = 180
COLMEIA_VELOCIDADE = 2.6

OLHO_VIDA = 210
OLHO_VELOCIDADE = 3.1

BOSS_FINAL_VIDA = 235
BOSS_FINAL_VIDA_COOP_EXTRA = 55
BOSS_FINAL_VELOCIDADE = 2.8
BOSS_FINAL_COOLDOWN_TIRO = 48
BOSS_FINAL_BRECHA = 205
BOSS_FINAL_LARGURA_CANHAO = 52
FATOR_LENTIDAO_CAMPO_VERDE = 0.45

GEMEOS_VIDA = 260
GEMEOS_VELOCIDADE = 3.2

ARQUITETO_VIDA = 295
ARQUITETO_VELOCIDADE = 2.1

# Chances de Drop
CHANCE_DROP_PODER = 0.10
CHANCE_DROP_CURA_NAVE = 0.22
CHANCE_DROP_MORCEGO = 0.15
