import logging
from pathlib import Path


LOG_BESTAND = Path("huizenzoeker.log")


def maak_logger():
    logger = logging.getLogger("huizenzoeker")
    logger.setLevel(logging.INFO)

    # Voorkomt dubbele regels wanneer de logger vaker wordt geladen
    if logger.handlers:
        return logger

    opmaak = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    bestand_handler = logging.FileHandler(
        LOG_BESTAND,
        encoding="utf-8"
    )
    bestand_handler.setFormatter(opmaak)

    scherm_handler = logging.StreamHandler()
    scherm_handler.setFormatter(opmaak)

    logger.addHandler(bestand_handler)
    logger.addHandler(scherm_handler)

    return logger


logger = maak_logger()