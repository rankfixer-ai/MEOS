filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()

# Fix 1: Seed the soft promotion coin flip (line 635)
old_soft = "if random.random() < 0.25:"
new_soft = "if random.Random(hashlib.md5(f'{self.seed}:{gen}:soft'.encode()).hexdigest()[:8]).random() < 0.25:"
c = c.replace(old_soft, new_soft)

# Fix 2: Replace bare random.choice in parent selection with self.mutation_engine.random.choice
# (MutationEngine already has a seeded self.random instance)
c = c.replace(
    'parent_genome = random.choice(alt_elites)[\'genome\']',
    'parent_genome = self.mutation_engine.random.choice(alt_elites)[\'genome\']'
)
c = c.replace(
    'parent_genome = random.choice(self.elite_archive)[\'genome\']',
    'parent_genome = self.mutation_engine.random.choice(self.elite_archive)[\'genome\']'
)
# The second and third instances are identical text, so they all get replaced

with open(filepath, 'w') as f:
    f.write(c)
print('All 5 bare random.* calls now use seeded RNGs')
