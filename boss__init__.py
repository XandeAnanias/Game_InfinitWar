from boss_lula import BossLula
from boss_comeia import BossColmeia
from boss_dragao import BossDragao
from boss_nave_comandante import BossNaveAndromeda
from boss_naves_duplas import BossNavesDuplas
from boss_arquiteto import BossArquiteto

CLASSES_BOSSES = {
    "squid":        BossLula,
    "colmeia":      BossColmeia,
    "eye":          BossDragao,
    "final":        BossNaveAndromeda,
    "gemeos":       BossNavesDuplas,
    "arquiteto":    BossArquiteto,
    "buraco_negro": BossArquiteto,
}


def criar_boss(tipo, loop_nivel=1, modo_jogadores=1):
    cls = CLASSES_BOSSES.get(tipo, BossLula)
    return cls(loop_nivel=loop_nivel, modo_jogadores=modo_jogadores)