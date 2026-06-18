filepath = r'src\core\meos_v0_3_core.py'

with open(filepath, 'r') as f:
    content = f.read()

# Find the broken parent selection block and replace it entirely
old_block = '''            if hasattr(self, "elite_archive") and self.elite_archive:
                if self.no_improvement_counter >= 3:
                    parent_genome = random.choice(self.elite_archive)["genome"]
                elif random.random() < 0.3:
                    parent_genome = random.choice(self.elite_archive)["genome"]
                else:
                    if self.no_improvement_counter >= 15 and self.elite_archive and len(self.elite_archive) >= 2:
                parent_genome = random.choice([e for e in self.elite_archive if e['fitness'] < self.best_ever_fitness * 0.995])['genome']
            else:
                parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome
            else:
                if self.no_improvement_counter >= 15 and self.elite_archive and len(self.elite_archive) >= 2:
                parent_genome = random.choice([e for e in self.elite_archive if e['fitness'] < self.best_ever_fitness * 0.995])['genome']
            else:
                parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome'''

new_block = '''            if hasattr(self, "elite_archive") and self.elite_archive:
                if self.no_improvement_counter >= 15:
                    alt_elites = [e for e in self.elite_archive if e['fitness'] < self.best_ever_fitness * 0.995]
                    if alt_elites:
                        parent_genome = random.choice(alt_elites)['genome']
                    else:
                        parent_genome = random.choice(self.elite_archive)['genome']
                elif self.no_improvement_counter >= 3:
                    parent_genome = random.choice(self.elite_archive)['genome']
                elif random.random() < 0.3:
                    parent_genome = random.choice(self.elite_archive)['genome']
                else:
                    parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome
            else:
                parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print('Parent selection block replaced cleanly')
else:
    print('Exact block not found - trying partial replacement')
    # Fallback: find and remove duplicate/indented lines
    lines = content.split('\n')
    clean_lines = []
    skip_next = False
    for i, line in enumerate(lines):
        if 'parent_genome = random.choice([e for e in self.elite_archive if' in line and not line.strip().startswith('parent_genome = random.choice([e for e in self.elite_archive'):
            # This is the incorrectly indented duplicate - skip it
            continue
        clean_lines.append(line)
    content = '\n'.join(clean_lines)
    print('Removed indented duplicates')

with open(filepath, 'w') as f:
    f.write(content)

print('Parent selection should now be clean')
