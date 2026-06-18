filepath = r"src\core\meos_v0_3_core.py"
with open(filepath, "r") as f:
    lines = f.readlines()
lines[730] = '                    print(f"   [P5] STAGNATION: {self.champion_stagnation_counter} gens. Switching to archive parent.")\n'
lines[731] = '                    alt = self.db.execute(\n'
lines.insert(732, '                        "SELECT id, genome, fitness_score FROM alleles WHERE gene_id = ? AND fitness_score < ? AND fitness_score IS NOT NULL ORDER BY fitness_score DESC LIMIT 1",\n')
lines.insert(733, '                        (self.gene_id, self.best_ever_fitness * 0.999)\n')
lines.insert(734, '                    )\n')
lines.insert(735, '                    if alt:\n')
lines.insert(736, '                        alt_row = alt[0]\n')
lines.insert(737, '                        alt_genome = json.loads(alt_row["genome"])\n')
lines.insert(738, '                        self.best_ever_genome = alt_genome\n')
lines.insert(739, '                        self._set_active_allele(alt_row["id"], "P5_branch")\n')
lines.insert(740, '                        self.no_improvement_counter = 0\n')
lines.insert(741, '                        self.champion_stagnation_counter = 0\n')
lines.insert(742, '                        print(f"   [P5] Branched from archive allele fitness={float(alt_row[\"fitness_score\"]):.4f}")\n')
lines.insert(743, '                    else:\n')
lines.insert(744, '                        self.no_improvement_counter = self.stagnation_threshold\n')
with open(filepath, "w") as f:
    f.writelines(lines)
print("P5.1 applied")
