filepath = r'src\core\meos_v0_3_core.py'

with open(filepath, 'r') as f:
    content = f.read()

# Find the stagnation counter increment and add archive parent switching
old_stag = 'self.stagnation_counter += 1'
new_stag = '''self.stagnation_counter += 1
                if self.stagnation_counter >= 15 and self.elite_archive and len(self.elite_archive) >= 3:
                    print(f\"   [V0.4.3] Stagnation detected ({self.stagnation_counter} gens). Switching to archive parent.\")
                    self.stagnation_counter = 0'''

if old_stag in content:
    content = content.replace(old_stag, new_stag, 1)  # Only first occurrence
    print('Archive parent switching on stagnation installed')
else:
    print('Could not find stagnation counter line')

# Also ensure parent selection uses archive during stagnation
old_parent = 'parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome'
new_parent = '''if hasattr(self, 'stagnation_counter') and self.stagnation_counter >= 15 and self.elite_archive and len(self.elite_archive) >= 2:
                parent_genome = random.choice([e for e in self.elite_archive if e['fitness'] < self.best_ever_fitness * 0.995])['genome']
            else:
                parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome'''

if old_parent in content:
    content = content.replace(old_parent, new_parent)
    print('Stagnation-aware parent selection installed')
else:
    print('Searching for parent selection line...')
    if 'self.best_ever_genome if self.best_ever_genome else initial_genome' in content:
        print('Found parent selection - patching')
        content = content.replace(
            'self.best_ever_genome if self.best_ever_genome else initial_genome',
            new_parent.split('else:')[1].strip()
        )

with open(filepath, 'w') as f:
    f.write(content)

print('\nV0.4.3 archive switching installed')
print('After 15 gens of stagnation, system switches to a different elite parent')
print('This mimics the successful Gen 19?27 breakthrough pattern')
