"""
MEOS V0.3 - Verification Queries
Run after a test experiment to verify Sprint 1 success.
"""

import sqlite3
import os

def verify():
    db_path = "data/meos_v0.3.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🧬 MEOS V0.3 - Sprint 1 Verification")
    print("=" * 70)

    # 1. Check tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")
    tables = cursor.fetchall()
    print("\n📊 Tables and Views:")
    for table in tables:
        print(f"  ✅ {table[0]}")

    # 2. Check trials vs promotions
    cursor.execute('''
        SELECT
            COUNT(*) AS trials,
            SUM(CASE WHEN evaluation_result='PROMOTED' THEN 1 ELSE 0 END) AS promotions
        FROM mutation_trials
    ''')
    row = cursor.fetchone()
    if row:
        print(f"\n📈 Mutation Trials: {row[0]}")
        print(f"   Promotions: {row[1]}")

    # 3. Check mutation events per parameter
    cursor.execute('''
        SELECT
            parameter,
            COUNT(*) AS events,
            COUNT(DISTINCT trial_id) AS trials
        FROM mutation_events
        GROUP BY parameter
        ORDER BY events DESC
    ''')
    rows = cursor.fetchall()
    print("\n📊 Mutation Events by Parameter:")
    print(f'{"Parameter":>20} | {"Events":>10} | {"Trials":>10}')
    print("-" * 45)
    for row in rows:
        print(f'{row[0]:>20} | {row[1]:>10} | {row[2]:>10}')

    # 4. Check attribution consistency
    cursor.execute('''
        SELECT
            SUM(positive) as total_positive,
            SUM(negative) as total_negative,
            SUM(neutral) as total_neutral,
            SUM(positive) + SUM(negative) + SUM(neutral) as sum_total
        FROM gene_effects
    ''')
    row = cursor.fetchone()
    if row and row[0] is not None:
        total = row[3]
        print(f"\n📊 Attribution Consistency:")
        print(f"   Positive: {row[0]}")
        print(f"   Negative: {row[1]}")
        print(f"   Neutral: {row[2]}")
        print(f"   Total: {total}")

    # 5. Champion reconstruction test
    cursor.execute('''
        SELECT 
            mt.seed,
            MAX(mt.fitness_after) as champion_fitness
        FROM mutation_trials mt
        WHERE mt.evaluation_result = 'PROMOTED'
        GROUP BY mt.seed
        ORDER BY champion_fitness DESC
        LIMIT 1
    ''')
    row = cursor.fetchone()
    if row:
        print(f"\n🏆 Champion:")
        print(f"   Seed: {row[0]}")
        print(f"   Fitness: {row[1]:.4f}")

    conn.close()

if __name__ == "__main__":
    verify()