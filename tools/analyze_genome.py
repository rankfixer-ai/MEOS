import sqlite3, json

conn = sqlite3.connect("data/meos_v0.3.db")
conn.row_factory = sqlite3.Row

gene = conn.execute("SELECT id FROM genes ORDER BY created_at DESC LIMIT 1").fetchone()
alleles = conn.execute(
    "SELECT genome, fitness_score FROM alleles WHERE gene_id = ? AND fitness_score IS NOT NULL ORDER BY fitness_score DESC LIMIT 100",
    (gene["id"],)
).fetchall()

genomes = [(json.loads(a["genome"]), a["fitness_score"]) for a in alleles]
params = ["parallelism", "cache_enabled", "cache_size", "reranking_enabled",
          "batch_size", "timeout_seconds", "max_results", "scoring_strategy",
          "retrieval_depth", "cache_eviction_policy", "ranking_model_temp"]

print(f"{'Parameter':<25} {'Unique':>7} {'Variance':>9} {'Fitness Corr':>12} {'Status'}")
print("-" * 70)

for p in params:
    vals = []
    for g, _ in genomes:
        v = g.get(p)
        if isinstance(v, bool):
            vals.append(1 if v else 0)
        elif isinstance(v, str):
            vals.append(hash(v) % 1000)
        else:
            vals.append(float(v))
    
    unique = len(set(str(g.get(p)) for g, _ in genomes))
    
    mean_v = sum(vals) / len(vals)
    variance = sum((v - mean_v)**2 for v in vals) / len(vals)
    
    fits = [f for _, f in genomes]
    mean_f = sum(fits) / len(fits)
    cov = sum((vals[i] - mean_v) * (fits[i] - mean_f) for i in range(len(vals))) / len(vals)
    corr = cov / (variance**0.5 * (sum((f - mean_f)**2 for f in fits)/len(fits))**0.5) if variance > 0 else 0
    
    if unique == 1:
        status = "FROZEN"
    elif variance < 0.01:
        status = "NEAR-FIXED"
    elif abs(corr) < 0.05:
        status = "LOW IMPACT"
    elif corr > 0.1:
        status = "INFLUENTIAL +"
    elif corr < -0.1:
        status = "INFLUENTIAL -"
    else:
        status = "MODERATE"
    
    print(f"{p:<25} {unique:>7} {variance:>9.4f} {corr:>12.4f} {status}")

conn.close()
