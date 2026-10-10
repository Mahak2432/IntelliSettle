import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--record",
        action="store_true",
        help="Call the live services (Open-Meteo, Earth Engine, Gemini) and save their responses for replay.",
    )
