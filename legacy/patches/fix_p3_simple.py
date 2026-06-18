filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()

# The broken line is at line 566 - a _set_active_allele call with the long ternary
# We need to find and replace ALL _set_active_allele calls that have the long ternary
# and replace them with just (allele_id, "promoted")
import re

# Pattern: _set_active_allele(allele_id, "PROMOTED_CHAMPION" if ... else evaluation_result)
old = '_set_active_allele(allele_id, "PROMOTED_CHAMPION" if evaluation_result == "PROMOTED_CHAMPION" else "PROMOTED" if evaluation_result == "PROMOTED" else "SOFT_PROMOTED" if evaluation_result == "PROMOTED_SOFT" else evaluation_result)'
new = '_set_active_allele(allele_id, evaluation_result)'

count = c.count(old)
c = c.replace(old, new)
print(f'Replaced {count} occurrences')
print('_set_active_allele now passes evaluation_result directly as reason')

with open(filepath, 'w') as f:
    f.write(c)
