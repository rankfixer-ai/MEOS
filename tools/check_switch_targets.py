import sqlite3, json

conn = sqlite3.connect("data/meos_v0.3.db")
conn.row_factory = sqlite3.Row

targets = ["c4c3e71c", "359a9ca6", "b5a7cc3d", "4b852c42"]

for tid in targets:
    allele = conn.execute("SELECT id, fitness_score, genome FROM alleles WHERE id LIKE ?", (tid + "%",)).fetchone()
    if allele:
        g = json.loads(allele["genome"])
        fid = allele["id"][:8]
        fit = allele["fitness_score"]
        print(f"{fid} | fitness={fit:.4f}")
        print(f"  parallelism={g['parallelism']} cache_size={g['cache_size']} batch={g['batch_size']}")
        print(f"  retrieval_depth={g['retrieval_depth']} temp={g['ranking_model_temp']}")
        print(f"  scoring={g['scoring_strategy']} eviction={g['cache_eviction_policy']}")
        print(f"  reranking={g['reranking_enabled']} cache_enabled={g['cache_enabled']}")
        print()
    else:
        print(f"{tid} not found")
        print()

print("=== PAIRWISE DIFFS ===")
genomes = {}
for tid in targets:
    allele = conn.execute("SELECT id, genome FROM alleles WHERE id LIKE ?", (tid + "%",)).fetchone()
    if allele:
        genomes[tid] = json.loads(allele["genome"])

keys = list(genomes.keys())
for i in range(len(keys)):
    for j in range(i+1, len(keys)):
        a, b = genomes[keys[i]], genomes[keys[j]]
        diffs = []
        for param in a:
            if param in b and a[param] != b[param]:
                diffs.append(f"{param}: {a[param]} -> {b[param]}")
        print(f"{keys[i][:8]} vs {keys[j][:8]}: {len(diffs)} diffs")
        for d in diffs:
            print(f"  {d}")
        print()

conn.close()
