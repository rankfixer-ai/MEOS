"""
MEOS V0.3 - Analytics Exporter
Extracts and displays evolutionary metrics from the database.
"""

import sqlite3
import os
from datetime import datetime

def export_metrics():
    db_path = os.path.join("data", "meos_v0.3.db")
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 MEOS EVOLUTIONARY METRICS EXPORTER")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Get all seeds
        cursor.execute("SELECT DISTINCT seed FROM mutation_trials")
        seeds = [row[0] for row in cursor.fetchall() if row[0] is not None]
        
        for seed in seeds:
            print(f"\n🌱 Metrics Summary for Seed: {seed}")
            print("-" * 70)
            print(f"{'Gen':<6}{'Fitness':<12}{'Stability':<12}{'Result':<25}")
            print("-" * 70)
            
            cursor.execute("""
                SELECT generation, fitness_score, stability_score, evaluation_result 
                FROM mutation_trials 
                WHERE seed = ?
                ORDER BY generation ASC
            """, (seed,))
            
            gen_counter = 0
            for row in cursor.fetchall():
                gen = row[0] if row[0] is not None else 0
                fit = row[1] if row[1] is not None else 0.0
                stab = row[2] if row[2] is not None else 0.0
                res = row[3] if row[3] is not None else "UNKNOWN"
                print(f"{gen:<6}{fit:<12.4f}{stab:<12.4f}{res:<25}")
                gen_counter += 1
            
            # Get best for this seed
            cursor.execute("""
                SELECT MAX(fitness_score), MAX(stability_score) 
                FROM mutation_trials 
                WHERE seed = ?
            """, (seed,))
            best = cursor.fetchone()
            print("-" * 70)
            print(f"🏆 Best Fitness: {best[0]:.4f} | Best Stability: {best[1]:.4f}")
        
        # Overall summary
        print("\n" + "=" * 60)
        print("📊 OVERALL SUMMARY")
        print("-" * 60)
        
        cursor.execute("""
            SELECT 
                seed,
                COUNT(*) as trials,
                MAX(fitness_score) as best_fit,
                AVG(stability_score) as avg_stab
            FROM mutation_trials 
            GROUP BY seed
            ORDER BY best_fit DESC
        """)
        
        print(f"{'Seed':<8}{'Trials':<10}{'Best Fitness':<15}{'Avg Stability':<15}")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"{row[0]:<8}{row[1]:<10}{row[2]:<15.4f}{row[3]:<15.4f}")
            
    except Exception as e:
        print(f"⚠️ Error: {e}")
    finally:
        conn.close()
        print("\n✅ Export complete!")

if __name__ == "__main__":
    export_metrics()
