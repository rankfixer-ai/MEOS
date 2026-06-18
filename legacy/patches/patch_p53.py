filepath = r"src\core\meos_v0_3_core.py"
with open(filepath, "r") as f:
    c = f.read()

# Replace uniform random choice with fitness-weighted selection
old = "if alt:\n                        alt_id, alt_genome_json, alt_fitness = self.mutation_engine.random.choice(alt)"
new = """if alt:
                        # Weighted selection: higher fitness = higher chance
                        weights = [max(0.001, float(row[2]) - 0.7) for row in alt]
                        total = sum(weights)
                        r = self.mutation_engine.random.random() * total
                        cumulative = 0
                        chosen = alt[0]
                        for row, w in zip(alt, weights):
                            cumulative += w
                            if r <= cumulative:
                                chosen = row
                                break
                        alt_id, alt_genome_json, alt_fitness = chosen"""

c = c.replace(old, new)

with open(filepath, "w") as f:
    f.write(c)
print("P5.3: Fitness-weighted archive selection")
