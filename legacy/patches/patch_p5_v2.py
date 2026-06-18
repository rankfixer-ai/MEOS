filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'self.champion_stagnation_counter += 1' in line and 'status' in lines[i+1]:
        indent = line[:len(line) - len(line.lstrip())]
        lines[i] = indent + 'if self.champion_stagnation_counter >= self.champion_stagnation_threshold:\n'
        lines.insert(i+1, indent + '    print(f\"   [P5] STAGNATION: {self.champion_stagnation_counter} gens. Forcing macro jump.\")\n')
        lines.insert(i+2, indent + '    self.no_improvement_counter = self.stagnation_threshold\n')
        lines.insert(i+3, indent + 'elif self.champion_stagnation_counter >= 8:\n')
        lines.insert(i+4, indent + '    print(f\"   [P5] EXPLORE: {self.champion_stagnation_counter} gens. Boosting mutation.\")\n')
        lines.insert(i+5, indent + '    self.no_improvement_counter = self.stagnation_threshold\n')
        lines.insert(i+6, line)
        break
with open(filepath, 'w') as f:
    f.writelines(lines)
print('P5 inserted')
