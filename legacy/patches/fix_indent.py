filepath = r'src\core\meos_v0_3_core.py'

with open(filepath, 'r') as f:
    lines = f.readlines()

# Find and fix the indentation around line 588-589
for i, line in enumerate(lines):
    if 'if hasattr(self, ' in line and 'no_improvement_counter' in line and 'parent_genome' not in line:
        # This is the if statement at line 588
        # Next line should be indented
        if i+1 < len(lines) and not lines[i+1].startswith('                '):
            lines[i+1] = '                ' + lines[i+1].lstrip()
            print(f'Fixed indentation at line {i+2}')
    if 'parent_genome = random.choice([e for e in self.elite_archive' in line:
        # Ensure proper indentation
        if not line.startswith('                '):
            lines[i] = '                ' + line.lstrip()
            print(f'Fixed parent_genome indentation at line {i+1}')

with open(filepath, 'w') as f:
    f.writelines(lines)

print('Indentation fixed')
