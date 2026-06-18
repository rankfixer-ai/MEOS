filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    content = f.read()

target = '        self._set_active_allele(allele_id, evaluation_result)\n\n        self.best_ever_fitness = fitness_score\n        self.best_ever_allele_id = allele_id\n        self.best_ever_genome = initial_genome.copy()'

replacement = '        self._set_active_allele(allele_id, "baseline")\n\n        self.best_ever_fitness = fitness_score\n        self.best_ever_allele_id = allele_id\n        self.best_ever_genome = initial_genome.copy()'

if target in content:
    content = content.replace(target, replacement, 1)
    with open(filepath, 'w') as f:
        f.write(content)
    print('Fixed line 566')
else:
    print('Target not found - checking what is there...')
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '_set_active_allele(allele_id, evaluation_result)' in line:
            print(f'Line {i+1}: {repr(line)}')
