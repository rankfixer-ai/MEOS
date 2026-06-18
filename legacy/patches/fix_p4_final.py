filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()

old_method = """    def _print_archive_summary(self):
        rows = self.db.execute(
            "SELECT COUNT(*) AS total, MAX(fitness_score) AS best_fitness, MIN(fitness_score) AS worst_fitness FROM alleles WHERE gene_id = ?",
            (self.gene_id,)
        )
        if not rows:
            return
        row = rows[0]
        print()
        print(f\"   [ARCHIVE SUMMARY]\")
        print(f\"   Alleles recorded: {row['total']}\")
        if row[\"best_fitness\"] is not None:
            print(f\"   Best fitness:  {float(row['best_fitness']):.4f}\")
        if row[\"worst_fitness\"] is not None:
            print(f\"   Worst fitness: {float(row['worst_fitness']):.4f}\")"""

new_method = """    def _print_archive_summary(self):
        rows = self.db.execute(
            "SELECT COUNT(*), MAX(fitness_score), MIN(fitness_score) FROM alleles WHERE gene_id = ?",
            (self.gene_id,)
        )
        if not rows:
            return
        total, best, worst = rows[0]
        print()
        print(f\"   [ARCHIVE SUMMARY]\")
        print(f\"   Alleles recorded: {total}\")
        if best is not None:
            print(f\"   Best fitness:  {float(best):.4f}\")
        if worst is not None:
            print(f\"   Worst fitness: {float(worst):.4f}\")"""

if old_method in c:
    c = c.replace(old_method, new_method)
    with open(filepath, 'w') as f:
        f.write(c)
    print('Method replaced successfully')
else:
    print('Old method not found - checking what is there...')
    # Find and print the current method
    import re
    m = re.search(r'def _print_archive_summary\(self\):.*?(?=\n    def |\n\n    def |\Z)', c, re.DOTALL)
    if m:
        print(repr(m.group()))
