filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()

# Add _print_archive_summary method right before def run(self)
old = '    def run(self) -> Dict:'
new = '''    def _print_archive_summary(self):
        rows = self.db.execute(
            "SELECT COUNT(*) AS total, MAX(fitness_score) AS best_fitness, MIN(fitness_score) AS worst_fitness FROM alleles WHERE gene_id = ?",
            (self.gene_id,)
        )
        if not rows:
            return
        row = rows[0]
        print()
        print(f"   [ARCHIVE SUMMARY]")
        print(f"   Alleles recorded: {row['total']}")
        if row["best_fitness"] is not None:
            print(f"   Best fitness:  {float(row['best_fitness']):.4f}")
        if row["worst_fitness"] is not None:
            print(f"   Worst fitness: {float(row['worst_fitness']):.4f}")

    def run(self) -> Dict:'''
c = c.replace(old, new)

# Call it before the evolution complete message
old_complete = '        print("-" * 50)\n        print(f"? Evolution complete!")'
new_complete = '        self._print_archive_summary()\n        print("-" * 50)\n        print(f"? Evolution complete!")'
c = c.replace(old_complete, new_complete)

with open(filepath, 'w') as f:
    f.write(c)
print('P4-A: archive summary added')
