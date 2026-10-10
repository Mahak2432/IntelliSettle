from claims_api.domain.models import Peril, Signal
from claims_api.evidence.weather import interpret, summarise


def hourly(rain: list[float], codes: list[int] | None = None) -> dict:
    n = len(rain)
    return {
        "latitude": 26.1,
        "longitude": 86.2,
        "hourly": {
            "time": [f"2024-09-29T{h % 24:02d}:00" for h in range(n)],
            "precipitation": rain,
            "weather_code": codes or [3] * n,
            "wind_gusts_10m": [20.0] * n,
        },
        "daily": {"time": ["2024-09-29"], "precipitation_sum": [sum(rain)]},
    }


def test_rolling_24h_maximum_spans_midnight():
    rain = [0.0] * 20 + [10.0] * 10 + [0.0] * 20  # 100 mm across hours 20-29
    m = summarise(hourly(rain))
    assert m["max_24h_mm"] == 100.0
    assert m["window_total_mm"] == 100.0


def test_excess_rain_signals():
    assert interpret(Peril.EXCESS_RAIN, summarise(hourly([5.0] * 24)))[0] == Signal.SUPPORTS
    assert interpret(Peril.EXCESS_RAIN, summarise(hourly([0.1] * 24)))[0] == Signal.CONTRADICTS
    assert interpret(Peril.EXCESS_RAIN, summarise(hourly([2.0] * 24)))[0] == Signal.INCONCLUSIVE


def test_low_local_rain_does_not_contradict_a_river_flood():
    assert interpret(Peril.FLOOD, summarise(hourly([0.0] * 24)))[0] == Signal.INCONCLUSIVE


def test_thunderstorm_codes_support_hail():
    m = summarise(hourly([1.0] * 24, codes=[3] * 20 + [96] * 4))
    assert m["hail_code_hours"] == 4
    assert interpret(Peril.HAILSTORM, m)[0] == Signal.SUPPORTS
