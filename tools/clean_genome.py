filepath = r"meos_orchestrator_connector.py"
with open(filepath, "r") as f:
    c = f.read()

old = '''genome = {
    "parallelism": 1, "cache_enabled": False, "cache_size": 0,
    "reranking_enabled": True, "batch_size": 75, "timeout_seconds": 50,
    "max_results": 10, "scoring_strategy": "dot", "retrieval_depth": 10,
    "cache_eviction_policy": "lfu", "ranking_model_temp": 0.5,
    "CYCLE_INTERVAL_MINUTES": 15,
    "SCRAPER_TIMEOUT_SECONDS": 30,
    "MAX_RETRIES": 3,
}'''

new = '''genome = {
    "CYCLE_INTERVAL_MINUTES": 15,
    "SCRAPER_TIMEOUT_SECONDS": 30,
    "MAX_RETRIES": 3,
}'''

c = c.replace(old, new)

# Update the mutation call - mutator.mutate() expects the full genome structure
# We need a custom mutate that only touches our 3 params
old_mutate = 'new_genome, _ = mutator.mutate(genome, gen)'
new_mutate = '''# Custom mutation: only mutate our 3 real parameters
    new_genome = genome.copy()
    param = mutator.random.choice(["CYCLE_INTERVAL_MINUTES", "SCRAPER_TIMEOUT_SECONDS", "MAX_RETRIES"])
    if param == "CYCLE_INTERVAL_MINUTES":
        new_genome[param] = mutator.random.choice([5, 10, 15, 20, 30, 45, 60])
    elif param == "SCRAPER_TIMEOUT_SECONDS":
        new_genome[param] = mutator.random.choice([10, 15, 30, 45, 60, 90, 120])
    else:
        new_genome[param] = mutator.random.choice([1, 2, 3, 5, 7, 10])'''
c = c.replace(old_mutate, new_mutate)

with open(filepath, "w") as f:
    f.write(c)
print("Genome reduced to 3 active parameters")
