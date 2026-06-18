filepath = r'src\core\meos_v0_3_core.py'

with open(filepath, 'r') as f:
    content = f.read()

# Hook archive switching into no_improvement_counter (the active stagnation tracker)
old_line = 'self.no_improvement_counter += 1'
new_line = '''self.no_improvement_counter += 1
                if self.no_improvement_counter >= 15 and self.elite_archive and len(self.elite_archive) >= 3:
                    print(f\"   [V0.4.3] {self.no_improvement_counter} gens without improvement. Switching to archive parent.\")
                    self.no_improvement_counter = 0'''

if old_line in content:
    content = content.replace(old_line, new_line)
    print('Archive switching hooked into no_improvement_counter')
else:
    print('Line not found')

# Also fix the parent selection to use no_improvement_counter
old_parent = 'hasattr(self, \'stagnation_counter\') and self.stagnation_counter >= 15'
new_parent = 'self.no_improvement_counter >= 15'

if old_parent in content:
    content = content.replace(old_parent, new_parent)
    print('Parent selection now uses no_improvement_counter')
else:
    # Try alternate form
    if 'stagnation_counter' in content and 'parent_genome' in content:
        content = content.replace('stagnation_counter', 'no_improvement_counter')
        print('Replaced stagnation_counter with no_improvement_counter')

with open(filepath, 'w') as f:
    f.write(content)

print('Done - archive switching uses correct stagnation variable')
