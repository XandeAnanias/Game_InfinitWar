import os
import math
import wave
import struct
import random

SAMPLE_RATE = 44100
PASTA_SAIDA = os.path.join("assets", "audio")
random.seed(42)


def envelope(t, duracao, ataque=0.01, release=0.05):
    if t < ataque:
        return t / max(1e-6, ataque)
    if t > duracao - release:
        return max(0.0, (duracao - t) / max(1e-6, release))
    return 1.0


def salvar_wav(nome_arquivo, amostras):
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    caminho = os.path.join(PASTA_SAIDA, nome_arquivo)

    pico = max((abs(s) for s in amostras), default=1.0) or 1.0
    escala = (32767 * 0.85) / pico  # Normaliza para -1.4 dB sem clipar

    with wave.open(caminho, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for s in amostras:
            val = max(-32768, min(32767, int(s * escala)))
            frames.extend(struct.pack("<h", val))
        wav.writeframes(frames)
    print(f"[OK] {caminho}")


def gerar_boss_final_campo():
    """1.0s — Zumbido gravitacional grave com pulso elétrico."""
    dur = 1.0
    total = int(SAMPLE_RATE * dur)
    amostras = []
    f1 = f2 = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        prog = t / dur
        freq_base = 62.0 + 18.0 * math.sin(2 * math.pi * 6.5 * t)
        sweep = 380.0 * ((1.0 - prog) ** 2.2) + 85.0
        f1 += 2 * math.pi * freq_base / SAMPLE_RATE
        f2 += 2 * math.pi * sweep / SAMPLE_RATE

        onda = 0.65 * math.sin(f1) + 0.35 * math.sin(f2)
        onda = math.tanh(onda * 1.6)  # Saturação suave sci-fi
        amostras.append(onda * envelope(t, dur, 0.04, 0.12))
    salvar_wav("boss_final_campo.wav", amostras)


def gerar_boss_final_frota():
    """0.55s — Comporta metálica abrindo + dois pulsos de teletransporte."""
    dur = 0.55
    total = int(SAMPLE_RATE * dur)
    amostras = []
    fc = fm = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        if t < 0.22:
            # Impacto metálico FM
            fc += 2 * math.pi * 175.0 / SAMPLE_RATE
            fm += 2 * math.pi * 268.0 / SAMPLE_RATE
            mod = math.sin(fm) * (3.2 * (1.0 - t / 0.22))
            sinal = math.sin(fc + mod)
        else:
            # Dois chirps rápidos de spawn
            t_local = (t - 0.22) % 0.165
            prog = t_local / 0.165
            freq = 320.0 + 680.0 * prog
            fc += 2 * math.pi * freq / SAMPLE_RATE
            sinal = 0.7 * math.sin(fc) * (1.0 - prog * 0.5)
        amostras.append(sinal * envelope(t, dur, 0.008, 0.04))
    salvar_wav("boss_final_frota.wav", amostras)


def gerar_boss_final_carregar():
    """0.90s — Turbina subindo de tom (sincronizada com os 55 frames de carga)."""
    dur = 0.90
    total = int(SAMPLE_RATE * dur)
    amostras = []
    f1 = f2 = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        prog = t / dur
        freq = 115.0 + 1080.0 * (prog ** 2.1)
        f1 += 2 * math.pi * freq / SAMPLE_RATE
        f2 += 2 * math.pi * (freq * 1.5) / SAMPLE_RATE

        pulso = 0.75 + 0.25 * math.sin(2 * math.pi * (8.0 + 22.0 * prog) * t)
        ruido = random.uniform(-0.15, 0.15) * (prog ** 1.5)
        sinal = (0.65 * math.sin(f1) + 0.35 * math.sin(f2)) * pulso + ruido
        amostras.append(sinal * envelope(t, dur, 0.03, 0.02))
    salvar_wav("boss_final_carregar.wav", amostras)


def gerar_boss_final_laser():
    """0.78s — Disparo do raio laser azul gigante com sub-grave e feixe elétrico."""
    dur = 0.78
    total = int(SAMPLE_RATE * dur)
    amostras = []
    f_sub = f_beam = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        prog = t / dur
        freq_sub = 155.0 * math.exp(-t * 14.0) + 46.0
        freq_beam = 130.0 + 25.0 * math.sin(2 * math.pi * 28.0 * t)
        f_sub += 2 * math.pi * freq_sub / SAMPLE_RATE
        f_beam += 2 * math.pi * freq_beam / SAMPLE_RATE

        dente_serra = 2.0 * ((f_beam / (2 * math.pi)) % 1.0) - 1.0
        ruido = random.uniform(-0.35, 0.35) * math.exp(-t * 4.5)
        sinal = 0.55 * math.sin(f_sub) + 0.35 * dente_serra + ruido
        sinal = math.tanh(sinal * 1.4) * (1.0 - 0.35 * prog)
        amostras.append(sinal * envelope(t, dur, 0.005, 0.08))
    salvar_wav("boss_final_laser.wav", amostras)


def gerar_boss_alerta():
    """1.25s — Sirene dupla de emergência na entrada dos chefes."""
    dur = 1.25
    total = int(SAMPLE_RATE * dur)
    amostras = []
    fase = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        ciclo = (t % 0.625) / 0.625
        freq = 440.0 + 420.0 * math.sin(math.pi * ciclo)
        fase += 2 * math.pi * freq / SAMPLE_RATE
        sinal = 0.65 * math.sin(fase) + 0.25 * (1.0 if math.sin(fase) >= 0 else -1.0)
        amostras.append(sinal * envelope(t, dur, 0.015, 0.06))
    salvar_wav("boss_alerta.wav", amostras)


def gerar_lula_dash():
    """0.42s — Impulso aquático/espacial da investida da Lula."""
    dur = 0.42
    total = int(SAMPLE_RATE * dur)
    amostras = []
    fase = 0.0
    ruido_filt = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        prog = t / dur
        freq = 640.0 * ((1.0 - prog) ** 1.6) + 140.0 + 30.0 * math.sin(2 * math.pi * 22.0 * t)
        fase += 2 * math.pi * freq / SAMPLE_RATE
        ruido_filt = 0.75 * ruido_filt + 0.25 * random.uniform(-1.0, 1.0)
        sinal = 0.55 * math.sin(fase) + 0.45 * ruido_filt * math.sin(math.pi * prog)
        amostras.append(sinal * envelope(t, dur, 0.01, 0.06))
    salvar_wav("lula_dash.wav", amostras)


def gerar_lula_tinta():
    """0.45s — Estouro líquido formando a poça de lentidão."""
    dur = 0.45
    total = int(SAMPLE_RATE * dur)
    amostras = []
    f1 = f2 = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        prog = t / dur
        # Bolha grave + gotículas agudas
        freq_bolha = 120.0 + 240.0 * math.sin(math.pi * min(1.0, prog * 2.2))
        freq_gota = 520.0 + 380.0 * ((prog * 3.0) % 1.0)
        f1 += 2 * math.pi * freq_bolha / SAMPLE_RATE
        f2 += 2 * math.pi * freq_gota / SAMPLE_RATE
        sinal = 0.7 * math.sin(f1) + 0.3 * math.sin(f2) * (1.0 - prog)
        amostras.append(sinal * envelope(t, dur, 0.008, 0.07))
    salvar_wav("lula_tinta.wav", amostras)


def gerar_powerup():
    """0.36s — Arpejo arcade ascendente para coleta de armas/escudo."""
    notas = [523.25, 659.25, 783.99, 1046.50]  # Dó5, Mi5, Sol5, Dó6
    dur_nota = 0.09
    dur = dur_nota * len(notas)
    total = int(SAMPLE_RATE * dur)
    amostras = []
    fase = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        idx = min(len(notas) - 1, int(t / dur_nota))
        t_local = t - idx * dur_nota
        fase += 2 * math.pi * notas[idx] / SAMPLE_RATE
        sinal = 0.7 * math.sin(fase) + 0.3 * math.sin(fase * 2.0)
        amostras.append(sinal * envelope(t_local, dur_nota, 0.005, 0.02))
    salvar_wav("powerup.wav", amostras)


def gerar_cura():
    """0.42s — Acorde brilhante suave ao recuperar vida."""
    notas = [698.46, 1046.50]  # Fá5 -> Dó6
    dur_nota = 0.21
    dur = dur_nota * len(notas)
    total = int(SAMPLE_RATE * dur)
    amostras = []
    f1 = f2 = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        idx = min(len(notas) - 1, int(t / dur_nota))
        t_local = t - idx * dur_nota
        f1 += 2 * math.pi * notas[idx] / SAMPLE_RATE
        f2 += 2 * math.pi * (notas[idx] * 1.5) / SAMPLE_RATE
        sinal = 0.75 * math.sin(f1) + 0.25 * math.sin(f2)
        amostras.append(sinal * envelope(t_local, dur_nota, 0.01, 0.06))
    salvar_wav("cura.wav", amostras)


if __name__ == "__main__":
    gerar_boss_final_campo()
    gerar_boss_final_frota()
    gerar_boss_final_carregar()
    gerar_boss_final_laser()
    gerar_boss_alerta()
    gerar_lula_dash()
    gerar_lula_tinta()
    gerar_powerup()
    gerar_cura()
    print("\nTodos os 9 efeitos sonoros foram gerados em assets/audio/!")