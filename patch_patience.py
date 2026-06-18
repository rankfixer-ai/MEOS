filepath = r'src\core\meos_v0_3_core.py'

with open(filepath, 'r') as f:
    content = f.read()

# Replace rigid plateau detection with stability-aware version
old_plateau = 'if generations_since_improvement >= self.plateau_generations:'
new_plateau = '''current_parent = self._get_active_allele()
            parent_stability = current_parent.get("stability_score", 0) if current_parent else 0
            if generations_since_improvement >= self.plateau_generations and parent_stability < 0.98:'''

if old_plateau in content:
    content = content.replace(old_plateau, new_plateau)
    print('Stability-gated plateau detection installed')
    print('Plateau only triggers if parent stability < 0.98')
    print('High-stability parents get unlimited search time')
else:
    print('Could not find plateau detection line')

with open(filepath, 'w') as f:
    f.write(content)
