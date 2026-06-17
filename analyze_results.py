import sqlite3

conn = sqlite3.connect('data/meos_v0.3.db')
cursor = conn.cursor()

print("\n" + "=" * 70)
print("📊 MEOS V0.3 - ANALYSIS REPORT")
print("=" * 70)

# 1. Evaluation Results by Seed
print("\n📊 EVALUATION RESULTS BY SEED:")
print("-" * 50)

cursor.execute('''
SELECT
    seed,
    evaluation_result,
    COUNT(*) AS count
FROM mutation_trials
GROUP BY seed, evaluation_result
ORDER BY seed, count DESC
''')

rows = cursor.fetchall()
current_seed = None
for row in rows:
    if row[0] != current_seed:
        current_seed = row[0]
        print(f"\nSeed {current_seed}:")
    print(f"  {row[1]}: {row[2]}")

# 2. Failed Seeds Detail
print("\n" + "=" * 70)
print("📊 FAILED SEEDS (42, 9001):")
print("-" * 70)

cursor.execute('''
SELECT
    seed,
    generation,
    ROUND(fitness_before, 4) as fitness_before,
    ROUND(fitness_after, 4) as fitness_after,
    ROUND(delta, 4) as delta,
    evaluation_result
FROM mutation_trials
WHERE seed IN (42, 9001)
ORDER BY seed, generation
''')

rows = cursor.fetchall()
print(f'{"Seed":>6} | {"Gen":>4} | {"Fitness Before":>14} | {"Fitness After":>14} | {"Delta":>8} | {"Result":>20}')
print("-" * 70)

for row in rows:
    print(f'{row[0]:6} | {row[1]:4} | {row[2]:14.4f} | {row[3]:14.4f} | {row[4]:+8.4f} | {row[5]:20}')

# 3. Check if generalization_score exists
cursor.execute("PRAGMA table_info(mutation_trials)")
columns = cursor.fetchall()
has_gen_score = any(col[1] == 'generalization_score' for col in columns)

if has_gen_score:
    cursor.execute('''
    SELECT
        seed,
        generation,
        ROUND(fitness_after, 4) as fitness,
        ROUND(generalization_score, 4) as gen_score,
        evaluation_result
    FROM mutation_trials
    WHERE seed IN (42, 9001)
    ORDER BY seed, generation
    ''')
    rows = cursor.fetchall()
    print("\n📊 GENERALIZATION SCORES:")
    print("-" * 50)
    for row in rows:
        print(f'  Seed {row[0]}, Gen {row[1]}: Fitness={row[2]:.4f}, GenScore={row[3]:.4f}, Result={row[4]}')
else:
    print("\nℹ️ No generalization_score column found.")

conn.close()
