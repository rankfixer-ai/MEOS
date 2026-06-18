import sqlite3, json

conn = sqlite3.connect("data/meos_v0.3.db")
conn.row_factory = sqlite3.Row

gene = conn.execute("SELECT id FROM genes ORDER BY created_at DESC LIMIT 1").fetchone()

# Scoring strategy breakdown
print("=== SCORING STRATEGY ===")
rows = conn.execute("""
    SELECT 
        json_extract(genome, '$.scoring_strategy') as strategy,
        COUNT(*) as count,
        AVG(fitness_score) as avg_fit,
        MAX(fitness_score) as max_fit,
        MIN(fitness_score) as min_fit
    FROM alleles 
    WHERE gene_id = ? AND fitness_score IS NOT NULL
    GROUP BY strategy
    ORDER BY max_fit DESC
""", (gene["id"],)).fetchall()

for r in rows:
    print(f"  {r['strategy']:<10} count={r['count']:>4}  avg={r['avg_fit']:.4f}  max={r['max_fit']:.4f}  min={r['min_fit']:.4f}")

# Ranking model temp breakdown into bands
print()
print("=== RANKING MODEL TEMP ===")
rows = conn.execute("""
    SELECT 
        CAST(json_extract(genome, '$.ranking_model_temp') AS REAL) as temp,
        fitness_score
    FROM alleles 
    WHERE gene_id = ? AND fitness_score IS NOT NULL
    ORDER BY fitness_score DESC
    LIMIT 100
""", (gene["id"],)).fetchall()

# Top 20 vs bottom 20
top20 = rows[:20]
bot20 = rows[-20:]
top_temps = [r["temp"] for r in top20]
bot_temps = [r["temp"] for r in bot20]
print(f"  Top 20 avg temp: {sum(top_temps)/len(top_temps):.2f}  (range: {min(top_temps):.1f}-{max(top_temps):.1f})")
print(f"  Bot 20 avg temp: {sum(bot_temps)/len(bot_temps):.2f}  (range: {min(bot_temps):.1f}-{max(bot_temps):.1f})")

# Temp distribution in top 100
bands = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
print()
print("  Temp distribution (top 100 alleles):")
for lo, hi in bands:
    count = sum(1 for r in rows if lo <= r["temp"] < hi)
    avg = sum(r["fitness_score"] for r in rows if lo <= r["temp"] < hi)
    if count > 0:
        avg /= count
    print(f"    {lo:.1f}-{hi:.1f}: {count:>3} alleles  avg fitness={avg:.4f}")

# Top 10 champion temps
champions = conn.execute("""
    SELECT DISTINCT 
        CAST(json_extract(genome, '$.ranking_model_temp') AS REAL) as temp,
        fitness_score
    FROM alleles 
    WHERE gene_id = ? AND fitness_score IS NOT NULL
    ORDER BY fitness_score DESC
    LIMIT 10
""", (gene["id"],)).fetchall()

print()
print("  Top 10 champions:")
for c in champions:
    print(f"    temp={c['temp']:.1f}  fitness={c['fitness_score']:.4f}")

conn.close()
