import sqlite3

conn = sqlite3.connect('data/meos_v0.3.db')
cursor = conn.cursor()
cursor.execute('''
SELECT 
    generation,
    parameter,
    mutation_type,
    old_value,
    new_value,
    ROUND(fitness_before, 4) as fitness_before,
    ROUND(fitness_after, 4) as fitness_after,
    ROUND(delta, 4) as delta,
    evaluation_result
FROM promotion_audit
ORDER BY generation
''')
rows = cursor.fetchall()
print('\n📊 PROMOTION AUDIT:')
print('=' * 80)
if rows:
    print(f'{"Gen":>4} | {"Parameter":>18} | {"Change":>20} | {"Fitness Before":>14} | {"Fitness After":>14} | {"Delta":>8}')
    print('-' * 80)
    for row in rows:
        change = f"{row[3]} → {row[4]}"
        print(f'{row[0]:4} | {row[1]:18} | {change:20} | {row[5]:14.4f} | {row[6]:14.4f} | {row[7]:+8.4f}')
else:
    print('  No promotions found')
conn.close()
