filepath = r'src\core\meos_v0_3_core.py'

with open(filepath, 'r') as f:
    content = f.read()

old_floor = 'stability_score > 0.95 and fitness_delta > -0.02'
new_floor = 'stability_score > 0.98 and fitness_delta > -0.005'

if old_floor in content:
    content = content.replace(old_floor, new_floor)
    print('Parent drift floor tightened: -0.02 -> -0.005, stability 0.95 -> 0.98')
else:
    print('Searching for alternate pattern...')
    if 'fitness_delta > -0.02' in content:
        content = content.replace('fitness_delta > -0.02', 'fitness_delta > -0.005')
        print('Found and replaced fitness_delta threshold')
    else:
        print('Could not find threshold line - check the file manually')

with open(filepath, 'w') as f:
    f.write(content)
