import os

filepath = r'src\core\meos_v0_3_core.py'

with open(filepath, 'r') as f:
    content = f.read()

# The exact signature found in your file
old_sig = 'def run_evolutionary_loop(seed: int, generations: int, selector: SelectionEngine,'
new_sig = 'def run_evolutionary_loop(seed: int, generations: int, selector: SelectionEngine, db_name: str = "meos_v0.3.db",'

if old_sig in content:
    content = content.replace(old_sig, new_sig)
    # We also update the database connection line. 
    # Adjust the target string below if your code uses a different variable name than 'conn'
    content = content.replace("sqlite3.connect('meos_v0.3.db')", "sqlite3.connect(db_name)")
    
    with open(filepath, 'w') as f:
        f.write(content)
    print("Patch applied successfully: db_name support enabled.")
else:
    print("Error: Could not find exact signature. Check indentation or spacing.")
