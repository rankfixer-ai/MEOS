filepath = r"src\core\meos_v0_3_core.py"
with open(filepath, "r") as f:
    c = f.read()

old = 'print(f"   [P5] STAGNATION: {self.champion_stagnation_counter} gens. Forcing macro jump.")\n                self.no_improvement_counter = self.stagnation_threshold'

new = """print(f"   [P5] STAGNATION: {self.champion_stagnation_counter} gens. Switching to archive parent.")
                alt = self.db.execute(
                    "SELECT id, genome, fitness_score FROM alleles WHERE gene_id = ? AND fitness_score < ? AND fitness_score IS NOT NULL ORDER BY fitness_score DESC LIMIT 1",
                    (self.gene_id, self.best_ever_fitness * 0.999)
                )
                if alt:
                    alt_row = alt[0]
                    alt_genome = json.loads(alt_row["genome"])
                    self.best_ever_genome = alt_genome
                    self._set_active_allele(alt_row["id"], "P5_branch")
                    self.no_improvement_counter = 0
                    self.champion_stagnation_counter = 0
                    print(f"   [P5] Branched from archive allele fitness={float(alt_row['fitness_score']):.4f}")
                else:
                    self.no_improvement_counter = self.stagnation_threshold"""

c = c.replace(old, new)
with open(filepath, "w") as f:
    f.write(c)
print("P5.1 applied")
