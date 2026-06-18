filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()

# Find the P5 STAGNATION block and add archive branching
old = "print(f\"   [P5] STAGNATION: {self.champion_stagnation_counter} gens. Forcing macro jump.\")\n                self.no_improvement_counter = self.stagnation_threshold"
new = "print(f\"   [P5] STAGNATION: {self.champion_stagnation_counter} gens. Switching to archive parent.\")\n                # Query top non-champion allele from archive\n                alt = self.db.execute(\n                    \"SELECT id, genome, fitness_score FROM alleles WHERE gene_id = ? AND fitness_score < ? AND fitness_score IS NOT NULL ORDER BY fitness_score DESC LIMIT 1\",\n                    (self.gene_id, self.best_ever_fitness * 0.999)\n                )\n                if alt:\n                    alt_genome = json.loads(alt[0][\"genome\"])\n                    self._set_active_allele(alt[0][\"id\"], \"P5_branch\")\n                    self.no_improvement_counter = 0\n                else:\n                    self.no_improvement_counter = self.stagnation_threshold"

c = c.replace(old, new)

with open(filepath, 'w') as f:
    f.write(c)
print('P5.1: Archive branching on stagnation')
