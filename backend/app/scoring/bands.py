from app.difficulty import BAND_CEILING
from app.spec import LEVELS, MAIN, ROUTER, UPPER, Difficulty, round_band


def estimate_band(points: float, max_points: float, difficulty: Difficulty) -> float:
    """Difficulty-weighted band estimate: fraction correct scaled to the level's reachable band ceiling.

    Beginner tops out at 3.5, Intermediate at 5, Advanced at 6. This is an estimate, not an ETS score.
    """
    if max_points <= 0:
        return 1.0
    fraction = max(0.0, min(1.0, points / max_points))
    return round_band(1.0 + (BAND_CEILING[difficulty] - 1.0) * fraction)


def stage_band(kind: str, level: Difficulty, points: float, max_points: float) -> float:
    """Unrounded band for one stage. The band interval depends on the module's role, so routing carries information:

    router / lower / main: [1, ceiling(level)]; upper: [ceiling(level below), ceiling(level)] - reaching the upper
    module means the router was passed, so even a weak showing there sits above the router's band range.
    """
    if max_points <= 0:
        return 1.0
    fraction = max(0.0, min(1.0, points / max_points))
    top = BAND_CEILING[level]
    if kind == UPPER:
        below = LEVELS.index(level) - 1
        bottom = BAND_CEILING[LEVELS[max(below, 0)]]
        return bottom + (top - bottom) * fraction
    return 1.0 + (top - 1.0) * fraction


def adaptive_band(stages: list[tuple[str, Difficulty, float, float]]) -> float:
    """Combine (kind, level, points, max_points) stages by their point weight; round to the nearest half band."""
    total = sum(m for _, _, _, m in stages)
    if total <= 0:
        return 1.0
    return round_band(sum(stage_band(k, lv, p, m) * m for k, lv, p, m in stages) / total)


__all__ = ["MAIN", "ROUTER", "adaptive_band", "estimate_band", "stage_band"]
