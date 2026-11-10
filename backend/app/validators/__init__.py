def word_count(text: str) -> int:
    return len(text.split())


def in_range(n: int, rng: tuple[int, int]) -> bool:
    return rng[0] <= n <= rng[1]
