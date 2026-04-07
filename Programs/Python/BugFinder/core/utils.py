from concurrent.futures import ThreadPoolExecutor

def run_threads(function, items, threads=10):
    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = executor.map(function, items)
    return list(results)
