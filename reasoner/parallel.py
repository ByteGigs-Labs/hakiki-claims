import multiprocessing
from collections.abc import Iterator, Sequence
from concurrent.futures import ProcessPoolExecutor

from reasoner import engine


def check_all(
    claims: Sequence[dict], priors: Sequence[Sequence[dict]], workers: int
) -> Iterator[dict]:
    if workers <= 1 or len(claims) < 2:
        yield from map(engine.check, claims, priors)
        return
    with ProcessPoolExecutor(
        max_workers=min(workers, len(claims)), mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        yield from pool.map(engine.check, claims, priors, chunksize=1)
