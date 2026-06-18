filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()

# Fix bare random.sample
c = c.replace(
    'sources = random.sample(source_pool, num_sources)',
    'sources = random.Random(42).sample(source_pool, num_sources)'
)

# Fix bare random.choice
c = c.replace(
    'queries.append({"text": random.choice(query_texts), "sources": sources})',
    'queries.append({"text": random.Random(42).choice(query_texts), "sources": sources})'
)

with open(filepath, 'w') as f:
    f.write(c)
print('Query generation seeded with fixed seed 42')
