"""
Tests de unidad para las reglas de alarma.

Casos mínimos esperados (del spec):
1) 02:30, quieto 12 min -> A=1 (Q10 & ~M4)
2) 05:10, quieto 12 min -> A=0 (tolerancia entre 4 y 6)
3) 05:20, quieto 31 min -> A=1 (Q30 domina)

TODO: Agregar tests cuando exista la API de `alarm`.
"""

