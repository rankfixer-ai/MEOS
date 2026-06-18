"""
MEOS V0.1 - Champion Genome Analysis
Run this to analyze the best genomes found during evolution.
"""

import sqlite3
import json
import os

# Make sure database exists
db_path = "data/meos.db"
if not os.path.exists(db_path):
    print(f"❌ Database not found at {db_path}")
    print("   Run MEOS first to generate data.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ============================================================
# 1. Top 10 Champion Alleles
# ============================================================

print("🏆 Top 10 Champion Alleles")
print("=" * 70)

cursor.execute('''
    SELECT 
        id,
        fitness_score,
        genome,
        gene_id,
        generation,
        random_seed
    FROM alleles
    WHERE fitness_score IS NOT NULL
    ORDER BY fitness_score DESC
    LIMIT 10
''')

rows = cursor.fetchall()

print(f'{"Fitness":>8} | {"Seed":>6} | {"Gen":>4} | Genome')
print("-" * 70)

for row in rows:
    fitness = row[1]
    seed = row[5]
    gen = row[4]
    genome = json.loads(row[2])
    
    genome_str = (
        f"p:{genome.get('parallelism',1)} "
        f"c:{genome.get('cache_enabled',False)} "
        f"cs:{genome.get('cache_size',0)} "
        f"r:{genome.get('reranking_enabled',False)} "
        f"b:{genome.get('batch_size',10)} "
        f"t:{genome.get('timeout_seconds',30)} "
        f"m:{genome.get('max_results',50)}"
    )
    
    print(f'{fitness:8.4f} | {seed:6} | {gen:4} | {genome_str}')

print()
print()

# ============================================================
# 2. Seed Summary
# ============================================================

print("📊 Seed Summary")
print("=" * 70)

cursor.execute('''
    SELECT 
        seed,
        baseline_fitness,
        final_fitness,
        improvement,
        success,
        notes
    FROM experiments
''')

rows = cursor.fetchall()

print(f'{"Seed":>6} | {"Baseline":>8} | {"Final":>8} | {"Improvement":>10} | {"Pass":>4}')
print("-" * 70)

for row in rows:
    seed = row[0]
    baseline = row[1]
    final = row[2] if row[2] is not None else 0.0
    improvement = row[3] if row[3] is not None else 0.0
    passed = '✅' if row[4] == 1 else '⏳' if row[4] is None else '❌'
    
    print(f'{seed:6} | {baseline:8.4f} | {final:8.4f} | {improvement*100:9.1f}% | {passed:4}')

print()
print()

# ============================================================
# 3. Promotions per Seed
# ============================================================

print("📈 Promotions per Seed")
print("=" * 70)

cursor.execute('''
    SELECT 
        random_seed,
        COUNT(*) as promotions,
        MAX(fitness_delta) as max_delta,
        AVG(fitness_delta) as avg_delta
    FROM lineage
    WHERE selection_reason = 'promoted'
    GROUP BY random_seed
''')

rows = cursor.fetchall()

print(f'{"Seed":>6} | {"Promotions":>10} | {"Max Delta":>10} | {"Avg Delta":>10}')
print("-" * 70)

for row in rows:
    seed = row[0]
    count = row[1]
    max_delta = row[2] if row[2] is not None else 0
    avg_delta = row[3] if row[3] is not None else 0
    print(f'{seed:6} | {count:10} | {max_delta:10.4f} | {avg_delta:10.4f}')

print()
print()

# ============================================================
# 4. Champion Genome Analysis
# ============================================================

print("🧬 Champion Genome Analysis")
print("=" * 70)

cursor.execute('''
    SELECT 
        genome,
        fitness_score,
        random_seed
    FROM alleles
    WHERE fitness_score >= 0.95
    ORDER BY fitness_score DESC
''')

rows = cursor.fetchall()

if rows:
    print("Champion genomes found (>0.95 fitness):")
    for row in rows:
        genome = json.loads(row[0])
        fitness = row[1]
        seed = row[2]
        print(f"\nSeed {seed} (fitness: {fitness:.4f}):")
        print(f"  parallelism: {genome.get('parallelism', 1)}")
        print(f"  cache_enabled: {genome.get('cache_enabled', False)}")
        print(f"  cache_size: {genome.get('cache_size', 0)}")
        print(f"  reranking_enabled: {genome.get('reranking_enabled', False)}")
        print(f"  batch_size: {genome.get('batch_size', 10)}")
        print(f"  timeout_seconds: {genome.get('timeout_seconds', 30)}")
        print(f"  max_results: {genome.get('max_results', 50)}")
else:
    print("No champion genomes found (>0.95 fitness)")

conn.close()

print()
print("✅ Analysis complete!")