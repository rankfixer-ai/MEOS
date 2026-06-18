filepath = r"src\core\meos_v0_3_core.py"
with open(filepath, "r") as f:
    c = f.read()

old = 'alt_genome = json.loads(alt_genome_json)\n                        self.best_ever_genome = alt_genome\n                        self._set_active_allele(alt_id, "P5_branch")\n                        self.no_improvement_counter = 0\n                        self.champion_stagnation_counter = 0'

new = 'alt_genome = json.loads(alt_genome_json)\n                        crossed = self._crossover(self.best_ever_genome, alt_genome)\n                        self.best_ever_genome = crossed\n                        self._set_active_allele(alt_id, "P5_crossover")\n                        self.no_improvement_counter = 0\n                        self.champion_stagnation_counter = 0\n                        print(f"   [P5] Crossover: champion x archive -> new parent")'

if old in c:
    c = c.replace(old, new)
    with open(filepath, "w") as f:
        f.write(c)
    print("Crossover inserted")
else:
    print("Old block not found")
    # Show what's actually at that location
    import re
    m = re.search(r'alt_genome = json\.loads\(alt_genome_json\).*?champion_stagnation_counter = 0', c, re.DOTALL)
    if m:
        print(repr(m.group()))
