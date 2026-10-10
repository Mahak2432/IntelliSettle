import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--record",
        action="store_true",
        help="Call live services (Open-Meteo, Earth Engine, Gemini) for responses not saved yet, and save them.",
    )
    parser.addoption(
        "--refresh",
        action="store_true",
        help="Call live services for every response and overwrite the saved ones.",
    )
