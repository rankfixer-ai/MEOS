filepath = r"meos_orchestrator_connector.py"
with open(filepath, "r") as f:
    c = f.read()

old = '''genome = {
    "CYCLE_INTERVAL_MINUTES": 15,
    "SCRAPER_TIMEOUT_SECONDS": 30,
    "MAX_RETRIES": 3,
}'''

new = '''genome = {
    "parallelism": 1, "cache_enabled": False, "cache_size": 0,
    "reranking_enabled": True, "batch_size": 75, "timeout_seconds": 50,
    "max_results": 10, "scoring_strategy": "dot", "retrieval_depth": 10,
    "cache_eviction_policy": "lfu", "ranking_model_temp": 0.5,
    "CYCLE_INTERVAL_MINUTES": 15,
    "SCRAPER_TIMEOUT_SECONDS": 30,
    "MAX_RETRIES": 3,
}'''

c = c.replace(old, new)
with open(filepath, "w") as f:
    f.write(c)
print("Fixed")
