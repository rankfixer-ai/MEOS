filepath = r'src\core\meos_v0_3_core.py'

with open(filepath, 'r') as f:
    content = f.read()

# Find the WRONG placement (before new_genome is defined) and remove it
# The bad block is right before the loop starts - it has no new_genome variable
old_bad_block = '''fitness_score = results["fitness"]
        if not hasattr(self, "elite_archive"):
            self.elite_archive = []
        self.elite_archive.append({"genome": new_genome.copy(), "fitness": fitness_score})
        self.elite_archive.sort(key=lambda x: x["fitness"], reverse=True)
        if len(self.elite_archive) > 10:
            self.elite_archive = self.elite_archive[:10]
        stability_score = results["stability"]'''

new_good_block = '''fitness_score = results["fitness"]
        stability_score = results["stability"]'''

content = content.replace(old_bad_block, new_good_block)

# Now add archive maintenance at the CORRECT location (inside the loop, after new_genome exists)
old_loop_fitness = '''results = self.benchmark_runner.run_multi_env_benchmark(allele_id, new_genome)
        fitness_score = results["fitness"]
        stability_score = results["stability"]'''

new_loop_fitness = '''results = self.benchmark_runner.run_multi_env_benchmark(allele_id, new_genome)
        fitness_score = results["fitness"]
        stability_score = results["stability"]
        if not hasattr(self, "elite_archive"):
            self.elite_archive = []
        self.elite_archive.append({"genome": new_genome.copy(), "fitness": fitness_score})
        self.elite_archive.sort(key=lambda x: x["fitness"], reverse=True)
        if len(self.elite_archive) > 10:
            self.elite_archive = self.elite_archive[:10]'''

content = content.replace(old_loop_fitness, new_loop_fitness)

with open(filepath, 'w') as f:
    f.write(content)

print("Archive maintenance moved to correct location inside the evolution loop")
