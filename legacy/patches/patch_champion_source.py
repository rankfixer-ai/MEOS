filepath = r"src\core\meos_v0_3_core.py"
with open(filepath, "r") as f:
    c = f.read()

# Add champion source tracking
old = 'self.best_ever_genome = new_genome.copy()\n                self.best_ever_allele_id = allele_id\n                self.champion_stagnation_counter = 0\n                self.no_improvement_counter = 0\n                print(f"   NEW CHAMPION: {fitness_score:.4f}")'
new = 'self.best_ever_genome = new_genome.copy()\n                self.best_ever_allele_id = allele_id\n                self.champion_stagnation_counter = 0\n                self.no_improvement_counter = 0\n                source = "branch" if "P5_branch" in locals() else "direct"\n                print(f"   NEW CHAMPION: {fitness_score:.4f} [{source}]")'
c = c.replace(old, new)

with open(filepath, "w") as f:
    f.write(c)
print("Champion source tracking added: [direct] or [branch]")
