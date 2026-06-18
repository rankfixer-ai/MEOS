filepath = r"src\core\meos_v0_3_core.py"
with open(filepath, "r") as f:
    c = f.read()
old = "alt_row = alt[0]\n                        alt_genome = json.loads(alt_row[\"genome\"])"
new = "alt_id, alt_genome_json, alt_fitness = alt[0]\n                        alt_genome = json.loads(alt_genome_json)"
c = c.replace(old, new)
old2 = 'self._set_active_allele(alt_row["id"], "P5_branch")'
new2 = 'self._set_active_allele(alt_id, "P5_branch")'
c = c.replace(old2, new2)
old3 = 'alt_fit = float(alt_row["fitness_score"])'
new3 = 'alt_fit = float(alt_fitness)'
c = c.replace(old3, new3)
with open(filepath, "w") as f:
    f.write(c)
print("Fixed tuple unpacking")
