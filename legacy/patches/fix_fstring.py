filepath = r"src\core\meos_v0_3_core.py"
with open(filepath, "r") as f:
    c = f.read()
old = 'print(f"   [P5] Branched from archive allele fitness={float(alt_row[\"fitness_score\"]):.4f}")'
new = 'alt_fit = float(alt_row["fitness_score"])\n                        print(f"   [P5] Branched from archive allele fitness={alt_fit:.4f}")'
c = c.replace(old, new)
with open(filepath, "w") as f:
    f.write(c)
print("Fixed")
