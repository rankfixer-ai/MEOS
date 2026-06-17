import sqlite3

conn = sqlite3.connect('data/meos_v0.3.db')
c = conn.cursor()

# Get the latest gene_id
c.execute('SELECT id FROM genes ORDER BY created_at DESC LIMIT 1')
gene_id = c.fetchone()[0]
print(f'Gene ID: {gene_id}')

# Check active allele
c.execute('''
    SELECT id, generation, fitness_score, is_active 
    FROM alleles 
    WHERE gene_id = ? 
    ORDER BY fitness_score DESC 
    LIMIT 5
''', (gene_id,))
rows = c.fetchall()

print('\n📊 TOP 5 ALLELES BY FITNESS:')
print('-' * 50)
print(f'{"ID":>10} | {"Gen":>4} | {"Fitness":>8} | {"Active":>6}')
print('-' * 50)
for row in rows:
    print(f'{row[0]:>10} | {row[1]:>4} | {row[2]:>8.4f} | {row[3]:>6}')

conn.close()
