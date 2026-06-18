filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()

# Fix engine seeding: use hash of genome + env instead of random allele_id
old = 'engine = SearchEngine(genome, seed=hash(allele_id + env_name) % 10000)'
new = 'engine = SearchEngine(genome, seed=hash(str(genome.get("parallelism",1)) + env_name) % 10000)'
c = c.replace(old, new)

with open(filepath, 'w') as f:
    f.write(c)
print('Engine seed now derived from genome + env, not random UUID')
