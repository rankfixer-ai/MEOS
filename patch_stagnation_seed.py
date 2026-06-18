filepath = r'src\core\meos_v0_3_core.py'

with open(filepath, 'r') as f:
    content = f.read()

# Replace the parent selection line with stagnation-aware version
old_parent = "parent_genome = random.choice(self.elite_archive)[\"genome\"] if hasattr(self, \"elite_archive\") and self.elite_archive and random.random() < 0.3 else self.best_ever_genome if self.best_ever_genome else initial_genome"

new_parent = '''# V0.4: Stagnation-aware parent selection
            if hasattr(self, "elite_archive") and self.elite_archive:
                if self.no_improvement_counter >= 3:
                    parent_genome = random.choice(self.elite_archive)["genome"]
                elif random.random() < 0.3:
                    parent_genome = random.choice(self.elite_archive)["genome"]
                else:
                    parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome
            else:
                parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome'''

content = content.replace(old_parent, new_parent)

with open(filepath, 'w') as f:
    f.write(content)

print("Stagnation-aware archive seeding patched - forces elite parents after 3 failures")
