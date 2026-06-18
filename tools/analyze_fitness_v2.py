import sqlite3

conn = sqlite3.connect("data/meos_v0.3.db")
conn.row_factory = sqlite3.Row

gene = conn.execute("SELECT id FROM genes ORDER BY created_at DESC LIMIT 1").fetchone()

rows = conn.execute("""
    SELECT a.fitness_score, m.environment_small, m.environment_medium, m.environment_large
    FROM alleles a
    JOIN mutation_trials m ON m.child_allele_id = a.id
    WHERE a.gene_id = ? AND a.fitness_score IS NOT NULL AND m.environment_small IS NOT NULL
    ORDER BY a.fitness_score DESC
    LIMIT 50
""", (gene["id"],)).fetchall()

print("=== FITNESS COMPONENT SATURATION ===")
print(f"{'Rank':<6} {'Fitness':<8} {'Small':<8} {'Medium':<8} {'Large':<8} {'Spread':<8}")
print("-" * 50)

for i, r in enumerate(rows[:15]):
    fit = r["fitness_score"]
    small = r["environment_small"]
    medium = r["environment_medium"]
    large = r["environment_large"]
    spread = max(small, medium, large) - min(small, medium, large)
    marker = " <-- champ" if i == 0 else ""
    print(f"{i+1:<6} {fit:<8.4f} {small:<8.4f} {medium:<8.4f} {large:<8.4f} {spread:<8.4f}{marker}")

fits = [r["fitness_score"] for r in rows]
smalls = [r["environment_small"] for r in rows]
mediums = [r["environment_medium"] for r in rows]
larges = [r["environment_large"] for r in rows]

print()
print("=== TOP 50 SUMMARY ===")
print(f"  Fitness:    avg={sum(fits)/len(fits):.4f}  max={max(fits):.4f}  min={min(fits):.4f}")
print(f"  Small env:  avg={sum(smalls)/len(smalls):.4f}  max={max(smalls):.4f}  min={min(smalls):.4f}")
print(f"  Medium env: avg={sum(mediums)/len(mediums):.4f}  max={max(mediums):.4f}  min={min(mediums):.4f}")
print(f"  Large env:  avg={sum(larges)/len(larges):.4f}  max={max(larges):.4f}  min={min(larges):.4f}")

print()
print("=== DISTANCE FROM 1.0 ===")
print(f"  Champion fitness: {max(fits):.4f}  (gap: {1.0 - max(fits):.4f})")
print(f"  Champion small:   {max(smalls):.4f}  (gap: {1.0 - max(smalls):.4f})")
print(f"  Champion medium:  {max(mediums):.4f}  (gap: {1.0 - max(mediums):.4f})")
print(f"  Champion large:   {max(larges):.4f}  (gap: {1.0 - max(larges):.4f})")

conn.close()
