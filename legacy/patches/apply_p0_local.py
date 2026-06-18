filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()

# Fix 1: Remove time.sleep for determinism
c = c.replace('time.sleep(min(latency, self.timeout))', 'pass  # time.sleep removed')

# Fix 2: Replace wall-clock latency with computed latency
old_lat = 'start = time.time()\n                    result = engine.search(q["text"], q["sources"])\n                    end = time.time()\n                    successful += 1\n                    total_latency += (end - start)'
new_lat = 'result = engine.search(q["text"], q["sources"])\n                    successful += 1\n                    total_latency += 0.05 * max(1, len(q["sources"]) / max(1, genome.get("parallelism", 1)))'
c = c.replace(old_lat, new_lat)

# Fix 3: Unfreeze reranking_enabled
c = c.replace('"reranking_enabled": [True]', '"reranking_enabled": [True, False]')

with open(filepath, 'w') as f:
    f.write(c)
print('P0 applied: sleep removed, latency computed, reranking unfrozen')
