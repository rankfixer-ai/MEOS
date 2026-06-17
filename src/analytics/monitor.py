"""
MEOS V0.3 - CLI Monitoring Dashboard (No Pandas Required)
"""

import sqlite3
from tabulate import tabulate
import argparse

DB_PATH = "data/meos_v0.3.db"


def get_db_connection():
    return sqlite3.connect(DB_PATH)


def show_summary():
    """Show overall promotion/rejection summary."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            evaluation_result,
            COUNT(*) as count,
            ROUND(AVG(fitness_after), 4) as avg_fitness,
            ROUND(AVG(generalization_score), 4) as avg_gen_score,
            ROUND(AVG(stability_score), 4) as avg_stability
        FROM mutation_trials
        WHERE fitness_after IS NOT NULL
        GROUP BY evaluation_result
        ORDER BY count DESC
    """)
    rows = cursor.fetchall()

    print("\n📊 PROMOTION/REJECTION SUMMARY")
    print("=" * 70)
    if rows:
        print(tabulate(rows, headers=["Result", "Count", "Avg Fitness", "Avg Gen Score", "Avg Stability"], tablefmt="psql"))
    else:
        print("  No data yet.")

    cursor.execute("""
        SELECT 
            COUNT(*) as total_trials,
            SUM(CASE WHEN evaluation_result = 'PROMOTED' THEN 1 ELSE 0 END) as promotions,
            ROUND(AVG(fitness_after), 4) as avg_fitness,
            ROUND(MAX(fitness_after), 4) as max_fitness
        FROM mutation_trials
        WHERE fitness_after IS NOT NULL
    """)
    row = cursor.fetchone()
    if row and row[0] > 0:
        print("\n📈 OVERALL STATS")
        print("=" * 70)
        print(f"  Total Trials: {row[0]}")
        print(f"  Promotions: {row[1]}")
        print(f"  Avg Fitness: {row[2]}")
        print(f"  Max Fitness: {row[3]}")

    conn.close()


def show_seed_status():
    """Show status of all seeds."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            seed,
            ROUND(baseline_fitness, 4) as baseline,
            ROUND(final_fitness, 4) as final,
            ROUND((final_fitness - baseline_fitness) / NULLIF(baseline_fitness, 0) * 100, 1) as improvement_pct,
            CASE WHEN success = 1 THEN '✅' ELSE '❌' END as status,
            plateau_generation,
            total_generations
        FROM experiment_runs
        ORDER BY seed
    """)
    rows = cursor.fetchall()

    print("\n🧬 SEED STATUS")
    print("=" * 70)
    if rows:
        print(tabulate(rows, headers=["Seed", "Baseline", "Final", "Improvement %", "Status", "Plateau", "Total Gen"], tablefmt="psql"))
    else:
        print("  No seeds run yet.")
    conn.close()


def show_recent_trials(limit=10, seed=None):
    """Show recent mutation trials."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if seed:
        cursor.execute("""
            SELECT 
                seed,
                generation,
                ROUND(fitness_after, 4) as fitness,
                ROUND(generalization_score, 4) as gen_score,
                ROUND(stability_score, 4) as stability,
                evaluation_result
            FROM mutation_trials
            WHERE seed = ?
            ORDER BY generation DESC
            LIMIT ?
        """, (seed, limit))
    else:
        cursor.execute("""
            SELECT 
                seed,
                generation,
                ROUND(fitness_after, 4) as fitness,
                ROUND(generalization_score, 4) as gen_score,
                ROUND(stability_score, 4) as stability,
                evaluation_result
            FROM mutation_trials
            ORDER BY generation DESC
            LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    print(f"\n🔍 RECENT TRIALS (Last {limit})")
    print("=" * 70)
    if rows:
        print(tabulate(rows, headers=["Seed", "Gen", "Fitness", "Gen Score", "Stability", "Result"], tablefmt="psql"))
    else:
        print("  No trials found.")
    conn.close()


def show_stagnation_detector(seed=None):
    """Detect if a seed is stagnating."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if seed:
        cursor.execute("""
            SELECT 
                generation,
                ROUND(fitness_after, 4) as fitness,
                ROUND(LAG(fitness_after, 10) OVER (ORDER BY generation), 4) as fitness_10_ago,
                ROUND(fitness_after - LAG(fitness_after, 10) OVER (ORDER BY generation), 4) as delta_10_gen
            FROM mutation_trials
            WHERE seed = ?
            ORDER BY generation DESC
            LIMIT 5
        """, (seed,))
    else:
        cursor.execute("""
            SELECT 
                seed,
                generation,
                ROUND(fitness_after, 4) as fitness,
                ROUND(LAG(fitness_after, 10) OVER (PARTITION BY seed ORDER BY generation), 4) as fitness_10_ago,
                ROUND(fitness_after - LAG(fitness_after, 10) OVER (PARTITION BY seed ORDER BY generation), 4) as delta_10_gen
            FROM mutation_trials
            ORDER BY generation DESC
            LIMIT 10
        """)

    rows = cursor.fetchall()
    print("\n📉 STAGNATION DETECTOR")
    print("=" * 70)
    if rows:
        print(tabulate(rows, headers=["Seed", "Gen", "Fitness", "10 Gen Ago", "Delta"], tablefmt="psql"))
    else:
        print("  Not enough data yet (need at least 10 generations).")
    conn.close()


def show_promotion_audit(seed=None):
    """Show all promotions."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if seed:
        cursor.execute("""
            SELECT 
                generation,
                parameter,
                mutation_type,
                old_value,
                new_value,
                ROUND(attributed_delta, 4) as delta
            FROM promotion_audit
            WHERE seed = ?
            ORDER BY generation
        """, (seed,))
    else:
        cursor.execute("""
            SELECT 
                seed,
                generation,
                parameter,
                mutation_type,
                old_value,
                new_value,
                ROUND(attributed_delta, 4) as delta
            FROM promotion_audit
            ORDER BY seed, generation
        """)

    rows = cursor.fetchall()
    print("\n🏆 PROMOTION AUDIT")
    print("=" * 70)
    if rows:
        if seed:
            print(tabulate(rows, headers=["Gen", "Parameter", "Type", "Old", "New", "Delta"], tablefmt="psql"))
        else:
            print(tabulate(rows, headers=["Seed", "Gen", "Parameter", "Type", "Old", "New", "Delta"], tablefmt="psql"))
    else:
        print("  No promotions yet.")
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="MEOS V0.3 CLI Monitor")
    parser.add_argument("--seed", type=int, help="Filter by seed")
    parser.add_argument("--limit", type=int, default=10, help="Limit for recent trials")
    parser.add_argument("--summary", action="store_true", help="Show summary")
    parser.add_argument("--seeds", action="store_true", help="Show seed status")
    parser.add_argument("--recent", action="store_true", help="Show recent trials")
    parser.add_argument("--stagnation", action="store_true", help="Show stagnation detector")
    parser.add_argument("--promotions", action="store_true", help="Show promotion audit")
    parser.add_argument("--all", action="store_true", help="Show all reports")

    args = parser.parse_args()

    if not any(vars(args).values()):
        args.summary = True
        args.recent = True

    if args.all:
        args.summary = args.seeds = args.recent = args.stagnation = args.promotions = True

    if args.seed:
        print(f"\n🧬 MEOS V0.3 Monitor - Seed: {args.seed}")
        print("=" * 70)

    if args.seeds:
        show_seed_status()

    if args.summary:
        show_summary()

    if args.recent:
        show_recent_trials(args.limit, args.seed)

    if args.stagnation:
        show_stagnation_detector(args.seed)

    if args.promotions:
        show_promotion_audit(args.seed)


if __name__ == "__main__":
    main()
