"""
MEOS V0.2 - Database Verification
Check actual stored values for all experiments.
"""

import sqlite3
import json
import os

def verify():
    db_path = "data/meos_v0.2.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("📊 MEOS V0.2 - EXPERIMENT VERIFICATION")
    print("=" * 80)

    # 1. Experiment Summary
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
        ORDER BY seed
    ''')
    
    rows = cursor.fetchall()
    
    print("\n📊 EXPERIMENTS")
    print("-" * 80)
    print(f'{"Seed":>6} | {"Baseline":>8} | {"Final":>8} | {"Improvement":>10} | {"Stability":>8} | {"Gen Score":>8} | {"Success":>6}')
    print("-" * 80)
    
    for row in rows:
        seed = row[0]
        baseline = row[1] if row[1] is not None else 0.0
        final = row[2] if row[2] is not None else None
        improvement = row[3] * 100 if row[3] is not None else 0
        stability = row[4] if row[4] is not None else 0.0
        gen_score = row[5] if row[5] is not None else 0.0
        success = "✅" if row[6] == 1 else "❌" if row[6] == 0 else "⏳"
        
        # Check threshold - only if final is not None
        if final is not None:
            pass_threshold = final > 0.95
            threshold_str = "(PASS)" if pass_threshold else "(FAIL)"
        else:
            threshold_str = "(PENDING)"
        
        # Format final fitness string
        final_str = f"{final:8.4f}" if final is not None else "   PENDING"
        
        print(f'{seed:6} | {baseline:8.4f} | {final_str:>8} | {improvement:9.1f}% | {stability:8.4f} | {gen_score:8.4f} | {success:6} {threshold_str}')

    # 2. Champion Genomes
    print("\n🏆 CHAMPION GENOMES")
    print("-" * 80)
    
    cursor.execute('''
        SELECT 
            experiments.seed,
            alleles.fitness_score,
            alleles.genome
        FROM alleles
        JOIN experiments ON alleles.gene_id = experiments.gene_id
        WHERE alleles.fitness_score >= 0.90
        ORDER BY alleles.fitness_score DESC
        LIMIT 10
    ''')
    
    rows = cursor.fetchall()
    
    if rows:
        for row in rows:
            seed = row[0]
            fitness = row[1]
            genome = json.loads(row[2])
            
            print(f"\nSeed {seed} (fitness: {fitness:.4f}):")
            print(f"  cache_enabled: {genome.get('cache_enabled', False)}")
            print(f"  reranking_enabled: {genome.get('reranking_enabled', False)}")
            print(f"  parallelism: {genome.get('parallelism', 1)}")
            print(f"  cache_size: {genome.get('cache_size', 0)}")
            print(f"  batch_size: {genome.get('batch_size', 10)}")
            print(f"  timeout_seconds: {genome.get('timeout_seconds', 30)}")
            print(f"  max_results: {genome.get('max_results', 50)}")
    else:
        print("  No champions found yet.")

    # 3. Gene Effects
    print("\n🧬 GENE EFFECTS")
    print("-" * 80)
    
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
    
    if rows:
        print(f'{"Parameter":>20} | {"Mutations":>10} | {"Positive":>10} | {"Negative":>10} | {"Pos Rate":>10} | {"Avg Delta":>10}')
        print("-" * 80)
        
        for row in rows:
            param = row[0]
            total = row[1] if row[1] is not None else 0
            positive = row[2] if row[2] is not None else 0
            negative = row[3] if row[3] is not None else 0
            avg_delta = row[4] if row[4] is not None else 0
            pos_rate = positive / total if total > 0 else 0
            
            print(f'{param:>20} | {total:>10} | {positive:>10} | {negative:>10} | {pos_rate:>9.1%} | {avg_delta:>10.4f}')
    else:
        print("  No gene effects data yet.")

    # 4. Validation Score (Check 0.945 vs 0.95)
    print("\n🔍 THRESHOLD CHECK")
    print("-" * 80)
    
    cursor.execute('''
        SELECT 
            seed,
            final_fitness,
            CASE WHEN final_fitness > 0.95 THEN 'PASS' ELSE 'FAIL' END as threshold_check,
            success
        FROM experiments
        WHERE final_fitness IS NOT NULL
        ORDER BY seed
    ''')
    
    rows = cursor.fetchall()
    
    print(f'{"Seed":>6} | {"Final Fitness":>12} | {"Threshold (0.95)":>15} | {"Success Flag":>12} | {"Match":>6}')
    print("-" * 80)
    
    for row in rows:
        seed = row[0]
        final = row[1] if row[1] is not None else 0
        threshold = row[2]
        success_flag = "✅" if row[3] == 1 else "❌" if row[3] == 0 else "⏳"
        
        # Check if threshold and success flag match
        if (threshold == "PASS" and row[3] == 1) or (threshold == "FAIL" and row[3] == 0):
            match = "✅"
        else:
            match = "⚠️"
        
        print(f'{seed:6} | {final:12.4f} | {threshold:>15} | {success_flag:>12} | {match:>6}')

    conn.close()

if __name__ == "__main__":
    verify()