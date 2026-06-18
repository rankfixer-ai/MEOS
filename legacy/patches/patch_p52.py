filepath = r"src\core\meos_v0_3_core.py"
with open(filepath, "r") as f:
    c = f.read()

old = 'alt = self.db.execute(\n                        "SELECT id, genome, fitness_score FROM alleles WHERE gene_id = ? AND fitness_score < ? AND fitness_score IS NOT NULL ORDER BY fitness_score DESC LIMIT 1",\n                        (self.gene_id, self.best_ever_fitness * 0.999)\n                    )'
new = 'alt = self.db.execute(\n                        "SELECT id, genome, fitness_score FROM alleles WHERE gene_id = ? AND fitness_score < ? AND fitness_score IS NOT NULL ORDER BY fitness_score DESC LIMIT 10",\n                        (self.gene_id, self.best_ever_fitness * 0.999)\n                    )'

c = c.replace(old, new)

old2 = 'if alt:\n                        alt_id, alt_genome_json, alt_fitness = alt[0]'
new2 = 'if alt:\n                        import random as _random\n                        alt_id, alt_genome_json, alt_fitness = _random.choice(alt)'

c = c.replace(old2, new2)

with open(filepath, "w") as f:
    f.write(c)
print("P5.2: Random selection from top 10 archive alleles")
