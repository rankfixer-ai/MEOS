import sqlite3

conn = sqlite3.connect('data/meos_v0.3.db')
cursor = conn.cursor()

print('\n📊 SEED 42 WITH METRICS:')
print('=' * 80)

cursor.execute('''
SELECT 
    generation,
    ROUND(fitness_after, 4) as fitness,
    ROUND(generalization_score, 4) as gen_score,
    ROUND(stability_score, 4) as stability,
    ROUND(environment_small, 4) as small,
    ROUND(environment_medium, 4) as medium,
    ROUND(environment_large, 4) as large,
    evaluation_result
FROM mutation_trials
WHERE seed = 42
ORDER BY generation
''')

rows = cursor.fetchall()

if not rows:
    print('No data found for Seed 42.')
    print('The run may have completed but no mutation trials were recorded.')
    conn.close()
    exit()

print(f'{"Gen":>4} | {"Fitness":>8} | {"Gen Score":>10} | {"Stability":>10} | {"Small":>8} | {"Medium":>8} | {"Large":>8} | {"Result":>20}')
print('-' * 80)

for row in rows:
    gen = row[0]
    fitness = row[1] if row[1] is not None else 0.0
    gen_score = row[2] if row[2] is not None else 0.0
    stability = row[3] if row[3] is not None else 0.0
    small = row[4] if row[4] is not None else 0.0
    medium = row[5] if row[5] is not None else 0.0
    large = row[6] if row[6] is not None else 0.0
    result = row[7] if row[7] else 'UNKNOWN'
    print(f'{gen:4} | {fitness:8.4f} | {gen_score:10.4f} | {stability:10.4f} | {small:8.4f} | {medium:8.4f} | {large:8.4f} | {result:20}')

# Summary
print('\n' + '=' * 80)
print('📊 SUMMARY:')
print('=' * 80)

cursor.execute('''
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN evaluation_result = "REJECTED_GENERALIZATION" THEN 1 ELSE 0 END) as rejected_gen,
    AVG(generalization_score) as avg_gen_score,
    AVG(fitness_after) as avg_fitness,
    MAX(fitness_after) as max_fitness
FROM mutation_trials
WHERE seed = 42
''')
row = cursor.fetchone()

print(f'Total Trials: {row[0]}')
print(f'REJECTED_GENERALIZATION: {row[1]}')
print(f'Avg Gen Score: {row[2]:.4f}' if row[2] else 'Avg Gen Score: N/A')
print(f'Avg Fitness: {row[3]:.4f}' if row[3] else 'Avg Fitness: N/A')
print(f'Max Fitness: {row[4]:.4f}' if row[4] else 'Max Fitness: N/A')

conn.close()
