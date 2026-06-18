with open(r'src\core\meos_v0_3_core.py') as f:
    c = f.read()
checks = [
    'self.elite_archive = []',
    'self.max_elite_size = 10',
    'random.choice(self.elite_archive)',
    'self.elite_archive.append',
    'self.elite_archive.sort'
]
for check in checks:
    status = 'OK' if check in c else 'MISSING'
    print(f'  [{status}] {check}')
print(f'')
print(f'Total elite_archive references: {c.count("elite_archive")}')
