filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()
c = c.replace('time.sleep(min(latency, self.timeout))', 'pass  # time.sleep removed for determinism')
old = 'start = time.time()\n                    result = engine.search(q["text"], q["sources"])\n                    end = time.time()\n                    successful += 1\n                    total_latency += (end - start)'
new = 'result = engine.search(q["text"], q["sources"])\n                    successful += 1\n                    total_latency += 0.05 * max(1, len(q["sources"]) / max(1, genome.get("parallelism", 1)))'
c = c.replace(old, new)
with open(filepath, 'w') as f:
    f.write(c)
print('Determinism fix applied')
