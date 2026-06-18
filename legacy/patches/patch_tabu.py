filepath = r"src\core\meos_v0_3_core.py"
with open(filepath, "r") as f:
    c = f.read()

# Add tabu list init in EvolutionLoop.__init__
old_init = "self.max_elite_size = 10"
new_init = "self.max_elite_size = 10\n        self.tabu_alleles = []  # recently visited, don't re-select"
c = c.replace(old_init, new_init)

# Modify the P5 archive query to exclude tabu alleles
old_query = '"SELECT id, genome, fitness_score FROM alleles WHERE gene_id = ? AND fitness_score < ? AND fitness_score IS NOT NULL AND id != ? ORDER BY fitness_score DESC LIMIT 15"'
new_query = '"SELECT id, genome, fitness_score FROM alleles WHERE gene_id = ? AND fitness_score < ? AND fitness_score IS NOT NULL AND id != ? AND id NOT IN ({}) ORDER BY fitness_score DESC LIMIT 15".format(\",\".join([\"?\"]*len(self.tabu_alleles))) if self.tabu_alleles else "SELECT id, genome, fitness_score FROM alleles WHERE gene_id = ? AND fitness_score < ? AND fitness_score IS NOT NULL AND id != ? ORDER BY fitness_score DESC LIMIT 15"'
c = c.replace(old_query, new_query)

# Add tabu list management after a branch is selected
old_branch = "alt_id, alt_genome_json, alt_fitness = chosen\n                        alt_genome = json.loads(alt_genome_json)\n                        self.best_ever_genome = alt_genome\n                        self._set_active_allele(alt_id, \"P5_branch\")"
new_branch = "alt_id, alt_genome_json, alt_fitness = chosen\n                        alt_genome = json.loads(alt_genome_json)\n                        self.best_ever_genome = alt_genome\n                        self._set_active_allele(alt_id, \"P5_branch\")\n                        self.tabu_alleles.append(alt_id)\n                        if len(self.tabu_alleles) > 3:\n                            self.tabu_alleles.pop(0)"

c = c.replace(old_branch, new_branch)

with open(filepath, "w") as f:
    f.write(c)
print("Tabu list added: last 3 branch targets excluded from re-selection")
