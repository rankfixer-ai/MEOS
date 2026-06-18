filepath = r"src\core\meos_v0_3_core.py"
with open(filepath, "r") as f:
    c = f.read()

# Add crossover method to EvolutionLoop
old_method = 'def _print_archive_summary(self):'
new_method = '''def _crossover(self, genome_a, genome_b):
        """Uniform crossover: each parameter randomly from either parent."""
        child = {}
        for key in genome_a:
            if key in genome_b:
                child[key] = genome_a[key] if self.mutation_engine.random.random() < 0.5 else genome_b[key]
            else:
                child[key] = genome_a[key]
        return child

    def _print_archive_summary(self):'''

c = c.replace(old_method, new_method)

# In P5 STAGNATION block, replace "mutate archive parent" with "crossover + mutate"
old_branch = 'alt_id, alt_genome_json, alt_fitness = chosen\n                        alt_genome = json.loads(alt_genome_json)\n                        self.best_ever_genome = alt_genome\n                        self._set_active_allele(alt_id, "P5_branch")'
new_branch = '''alt_id, alt_genome_json, alt_fitness = chosen
                        alt_genome = json.loads(alt_genome_json)
                        # Crossover: blend champion with archive parent, then mutate
                        crossed = self._crossover(self.best_ever_genome, alt_genome)
                        self.best_ever_genome = crossed
                        self._set_active_allele(alt_id, "P5_crossover")
                        print(f"   [P5] Crossover: champion x archive[{alt_fitness:.4f}] -> new parent")'''

c = c.replace(old_branch, new_branch)

with open(filepath, "w") as f:
    f.write(c)
print("Crossover added: champion x archive parent on P5 stagnation")
