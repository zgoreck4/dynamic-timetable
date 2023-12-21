import random


def randomize_map_coordinates(limit: int | float) -> tuple[float, float]:
    return round(random.random() * limit), round(random.random() * limit)