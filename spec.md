# Café Electrónico – Especificación

Objetivo: Activar alarma A para despertar a un estudiante si se queda dormido.

## Señales
- Q10 = 1 si hubo quietud continua ≥ 10 min
- Q30 = 1 si hubo quietud continua ≥ 30 min
- M4  = 1 si hora ≥ 04:00
- M6  = 1 si hora ≥ 06:00

## Regla principal
A = Q30 OR ( Q10 AND ( NOT M4 OR M6 ) )

## Don’t-care / combinaciones inválidas
- M6=1 y M4=0 (inconsistente)
- Q30=1 y Q10=0 (inconsistente)

## Casos de prueba mínimos
1) 02:30 (antes de 4am), quieto 12 min → A=1 (Q10 & ~M4)
2) 05:10 (entre 4 y 6), quieto 12 min → A=0 (tolerancia)
3) 05:20, quieto 31 min → A=1 (Q30 domina)

## Requisitos técnicos
- Python 3.11+
- Uso de `pytest` para tests
- Logs con `logging`
- Soporte para CLI (simular ticks de actividad)
- Extensible a sensores reales (IMU, cámara) con interfaces
