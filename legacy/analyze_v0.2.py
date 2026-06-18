"""
MEOS V0.2 - Analysis Script
Run this after experiments to analyze results.
"""

import sqlite3
import json
import os

def analyze():
    db_path = "data/meos_v0.2.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("   Run MEOS V0.2 first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Experiment Summary
    print("📊 MEOS V0.2 - Experiment Summary")
    print("=" * 70)
    
    cursor.execute('''
        SELECT 
            seed,
            baseline_fitness,
            final_fitness,
            improvement,
            stability,
            generalization_score,
            success
        FROM experiments
    ''')
    rows = cursor.fetchall()
    
    print(f'{"Seed":>6} | {"Baseline":>8} | {"Final":>8} | {"Improvement":>10} | {"Stability":>8} | {"Gen Score":>8} | {"Pass":>4}')
    print("-" * 80)
    
    for row in rows:
        print(f'{row[0]:6} | {row[1]:8.4f} | {row[2]:8.4f} | {row[3]*100:9.1f}% | {row[4]:8.3f} | {row[5]:8.3f} | {"✅" if row[6]==1 else "❌"}')

    # 2. Champion Genomes
    print("\n🏆 Champion Genomes")
    print("=" * 70)
    
    cursor.execute('''
        SELECT 
            alleles.genome,
            alleles.fitness_score,
            experiments.seed
        FROM alleles
        JOIN experiments ON alleles.gene_id = experiments.gene_id
        WHERE alleles.fitness_score >= 0.95
        ORDER BY alleles.fitness_score DESC
        LIMIT 10
    ''')
    
    rows = cursor.fetchall()
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

    # 3. Gene Effects
    print("\n🧬 Gene Effects Analysis")
    print("=" * 70)
    
    cursor.execute('''
        SELECT 
            parameter_name,
            SUM(mutation_count) as total,
            SUM(positive_count) as positive,
            SUM(negative_count) as negative,
            AVG(avg_delta) as avg_delta
        FROM gene_effects
        GROUP BY parameter_name
        ORDER BY avg_delta DESC
    ''')
    
    rows = cursor.fetchall()
    print(f'{"Parameter":>20} | {"Mutations":>10} | {"Positive Rate":>14} | {"Avg Delta":>10}')
    print("-" * 70)
    
    for row in rows:
        positive_rate = row[2] / row[1] if row[1] > 0 else 0
        print(f'{row[0]:>20} | {row[1]:>10} | {positive_rate:>14.2%} | {row[4]:>10.4f}')

    conn.close()

if __name__ == "__main__":
    analyze()