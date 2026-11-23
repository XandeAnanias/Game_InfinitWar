import pygame
import random
from config import LARGURA, ALTURA


class Background:
    CORES_PLANETAS = [
        ((45, 65, 115), (28, 42, 78)),   # Azul profundo
        ((115, 55, 45), (78, 34, 28)),   # Marte avermelhado
        ((85, 50, 110), (55, 30, 75)),   # Gigante roxo
        ((50, 100, 88), (32, 65, 55)),   # Esmeralda espacial
    ]

    def __init__(self):
        self.estrelas = [
            [random.randint(0, LARGURA), random.randint(0, ALTURA), random.choice([1, 2, 3])]
            for _ in range(70)
        ]
        self.planeta = self._novo_planeta(y_inicial=-90.0)

    def _novo_planeta(self, y_inicial=None):
        cor, sombra = random.choice(self.CORES_PLANETAS)
        raio = random.randint(28, 48)
        return {
            "x": random.randint(60, LARGURA - 60),
            "y": y_inicial if y_inicial is not None else float(-random.randint(150, 350)),
            "raio": raio,
            "cor": cor,
            "sombra": sombra,
            "anel": random.choice([True, False]),
        }

    def update(self):
        for estrela in self.estrelas:
            estrela[1] += estrela[2]
            if estrela[1] > ALTURA:
                estrela[1] = 0
                estrela[0] = random.randint(0, LARGURA)

        self.planeta["y"] += 0.45
        if self.planeta["y"] - self.planeta["raio"] > ALTURA + 20:
            self.planeta = self._novo_planeta()

    def draw(self, tela):
        tela.fill((6, 9, 18))

        for x, y, vel in self.estrelas:
            cor = (90, 95, 115) if vel == 1 else (170, 180, 200) if vel == 2 else (255, 255, 255)
            pygame.draw.rect(tela, cor, (x, y, 2, 2))

        px = self.planeta["x"]
        py = int(self.planeta["y"])
        pr = self.planeta["raio"]

        pygame.draw.circle(tela, self.planeta["cor"], (px, py), pr)
        pygame.draw.circle(tela, self.planeta["sombra"], (px + pr // 4, py + pr // 4), int(pr * 0.62))
        if self.planeta["anel"]:
            pygame.draw.ellipse(tela, (125, 130, 155), (px - pr - 16, py - 6, (pr + 16) * 2, 12), 2)
