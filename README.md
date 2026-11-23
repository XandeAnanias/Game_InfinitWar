# Guerra No Infinito — Edição Arcade & Co-op

Jogo de nave 2D estilo *shoot 'em up* arcade desenvolvido em **Python** com **Pygame**, com suporte para **1 Jogador (Arcade)** e **2 Jogadores (Co-op Local)**, três chefes com padrões únicos de ataque, zonas de lentidão táticas e sistema modular dividido por responsabilidades.

---

## Como Executar

1. Certifique-se de ter o **Python 3.10+** e o **Pygame** instalados:
   ```bash
   pip install pygame
   ```
2. Na pasta raiz do projeto, execute:
   ```bash
   python main.py
   ```

---

## Arquitetura Modular do Projeto

O código foi segmentado em camadas independentes para facilitar a manutenção e o ajuste rápido de mecânicas:

| Arquivo | Responsabilidade |
| :--- | :--- |
| `config.py` | **Central de Balanceamento:** resolução, caminhos de sprites/áudios, vida, cooldowns, danos, velocidades e fatores de lentidão. |
| `boss_movesets.py` | **Movesets dos Chefes:** lógica isolada das fases, timers, ataques e telegráfos visuais de cada chefe (`MovesetLula`, `MovesetOlho`, `MovesetNaveComandante`). |
| `boss.py` | **Classe Base dos Chefes:** gerencia vida, hitbox, flash de dano, ajuste de co-op e delega os ataques para `boss_movesets.py`. |
| `player.py` | **Jogador:** movimentação 1P/2P, alternância de tiro (Rápido/Pesado), power-ups, escudo e redução de velocidade sob lentidão. |
| `enemies.py` | **Inimigos Comuns:** comportamento e cadência de tiro de naves normais, atiradores, morcegos e peixes. |
| `projectiles.py` | **Projéteis & Objetos de Arena:** `Bullet` (incluindo detonação aérea da tinta), `ManchaTinta` (poça de lentidão), `Asteroid`, `PowerUp`, `Particle` e `BombShockwave`. |
| `entities.py` | **Agregador:** reexporta todas as entidades para manter imports simples e organizados. |
| `assets.py` | **Gerenciador de Mídia:** carregamento de PNGs/WAVs e geração procedural automática caso algum arquivo opcional falte. |
| `background.py` | **Cenário Espacial:** campo de estrelas em paralaxe e planetas proceduralmente gerados. |
| `ui.py` | **Interface e HUD:** menus, tela "Como Jogar", barra de vida dos chefes, indicadores de recarga, status de lentidão e Console Admin (`F1`). |
| `main.py` | **Loop Principal:** máquina de estados do jogo, colisões, ondas de inimigos e progressão de pontuação. |

---

## Controles

* **Jogador 1 (Arcade & Co-op):**
  * Mover: `W`, `A`, `S`, `D`
  * Atirar: `C`
  * Alternar Tiro Rápido / Pesado (modo 1P): `Q`
* **Jogador 2 (Co-op):**
  * Mover: `Setas Direcionais`
  * Atirar: `Espaço`
* **Atalhos Gerais:**
  * Pausar / Continuar: `P` ou `ESC`
  * Console Admin (definir pontuação para testar chefes): `F1`
  * Reiniciar no Game Over: `R`

---

## Chefes e Mecânicas Especiais

1. **Lula Cósmica (`700 pts`):**
   * Dispara 3 projéteis roxos de tinta que percorrem a tela até uma altura sorteada: se acertarem a nave antes, causam dano; se explodirem no ar sem acertar, não causam dano e criam uma **poça de tinta** que reduz a velocidade da nave em `50%`.
   * Invoca peixes e executa investidas (*dash*) telegrafadas.
2. **Olho Dracônico (`1.500 pts`):**
   * Dispara pares de orbes, carrega e dispara um raio laser vermelho contínuo e invoca morcegos em formação.
3. **Nave Comandante (`2.500 pts` — Boss Final):**
   * Dispara rajadas de 3 tiros (asas + tiro mirado).
   * Projeta um **Campo Gravitacional Verde** na arena que reduz a velocidade da nave em `55%` dentro da área enquanto invoca uma frota de naves menores com corredor de passagem.
   * Carrega e dispara um **raio laser azul gigante** de dano imediato acompanhado de projéteis pesados laterais.
