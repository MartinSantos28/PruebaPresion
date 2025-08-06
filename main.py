from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import bisect

app = FastAPI(title="Phase Change Diagram API (with interpolation)")

class PhaseChange(BaseModel):
    specific_volume_liquid: float
    specific_volume_vapor: float

# Sólo dos puntos «de ancla» extraídos de tu croquis:
#  - Saturación a 0.05 MPa
#  - Punto crítico a 10 MPa
PHASE_DATA = {
    0.05:  (0.00105, 30.00),
    10.00: (0.00350,  0.0035),
}

# Lista ordenada de presiones
PRESSURES = sorted(PHASE_DATA.keys())

def interpolate(pressure: float) -> tuple[float, float]:
    # Fuera de rango → error
    p_min, p_max = PRESSURES[0], PRESSURES[-1]
    if not (p_min <= pressure <= p_max):
        raise HTTPException(
            status_code=404,
            detail=f"Pressure {pressure} MPa out of range [{p_min}–{p_max}]"
        )
    # Exact match?
    if pressure in PHASE_DATA:
        return PHASE_DATA[pressure]
    # Busca el segmento donde cae ‘pressure’
    idx = bisect.bisect_right(PRESSURES, pressure)
    p1, p2 = PRESSURES[idx-1], PRESSURES[idx]
    v1_liq, v1_vap = PHASE_DATA[p1]
    v2_liq, v2_vap = PHASE_DATA[p2]
    t = (pressure - p1) / (p2 - p1)
    v_liq = v1_liq + t * (v2_liq - v1_liq)
    v_vap = v1_vap + t * (v2_vap - v1_vap)
    return v_liq, v_vap

@app.get("/phase-change-diagram", response_model=PhaseChange)
def get_phase_change(pressure: float = Query(..., ge=0.05, description="Presión en MPa (≥0.05)")):
    """
    Devuelve por interpolación lineal los volúmenes específico líquido y vapor
    para cualquier presión en [0.05, 10] MPa.
    """
    v_liq, v_vap = interpolate(pressure)
    return PhaseChange(
        specific_volume_liquid=round(v_liq, 6),
        specific_volume_vapor=round(v_vap, 6)
    )

@app.get("/healthz")
def health():
    return {"status": "ok"}
    