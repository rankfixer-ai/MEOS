import re

filepath = r'src\core\meos_v0_3_core.py'

with open(filepath, 'r') as f:
    content = f.read()

# Patch 1: Add elite archive initialization
old_init = 'self.champion_stagnation_threshold = 10'
new_init = '''self.champion_stagnation_threshold = 10
        self.elite_archive = []
        self.max_elite_size = 10'''
content = content.replace(old_init, new_init)

# Patch 2: Update parent selection
old_parent = 'parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome'
new_parent = 'parent_genome = random.choice(self.elite_archive)["genome"] if hasattr(self, "elite_archive") and self.elite_archive and random.random() < 0.3 else self.best_ever_genome if self.best_ever_genome else initial_genome'
content = content.replace(old_parent, new_parent)

# Patch 3: Add archive maintenance after fitness calculation
old_fitness = 'fitness_score = results["fitness"]'
new_fitness = '''fitness_score = results["fitness"]
        if not hasattr(self, "elite_archive"):
            self.elite_archive = []
        self.elite_archive.append({"genome": new_genome.copy(), "fitness": fitness_score})
        self.elite_archive.sort(key=lambda x: x["fitness"], reverse=True)
        if len(self.elite_archive) > 10:
            self.elite_archive = self.elite_archive[:10]'''
content = content.replace(old_fitness, new_fitness, 1)  # Only first occurrence

with open(filepath, 'w') as f:
    f.write(content)

print("V0.4 Elite Archive patched successfully")
