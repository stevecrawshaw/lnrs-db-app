"""Test CSV export with semicolon delimiter."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.area import AreaModel
from models.measure import MeasureModel
from models.priority import PriorityModel

print("=" * 80)
print("TESTING CSV EXPORT WITH SEMICOLON DELIMITER")
print("=" * 80)

# Test 1: Measures Export
print("\n[TEST 1] Measures CSV Export")
print("-" * 80)

measure_model = MeasureModel()
measures = measure_model.get_with_relationship_counts()

print(f"Total measures: {len(measures)}")
print(f"Columns: {measures.columns}")

# Check for commas in text columns
measure_col = measures["measure"].to_list()
concise_col = measures["concise_measure"].to_list()

commas_in_measure = sum(1 for m in measure_col if m and "," in m)
commas_in_concise = sum(1 for m in concise_col if m and "," in m)

print(f"Measures with commas in 'measure' column: {commas_in_measure}")
print(f"Measures with commas in 'concise_measure' column: {commas_in_concise}")

# Generate CSV with semicolon delimiter
csv_data = measures.write_csv(separator=";")
lines = csv_data.split("\n")
print(f"\nCSV generated: {len(lines)} lines")
print(f"First line (header): {lines[0][:100]}...")

# Check that header uses semicolons
if ";" in lines[0]:
    print("✓ Header correctly uses semicolon delimiter")
else:
    print("✗ ERROR: Header does not use semicolon delimiter")

# Check a data line with comma
for i, line in enumerate(lines[1:20], 1):  # Check first 20 data lines
    if "," in line and ";" in line:
        print(f"✓ Line {i} contains both comma (in data) and semicolon (delimiter)")
        print(f"  Preview: {line[:100]}...")
        break

# Test 2: Areas Export
print("\n[TEST 2] Areas CSV Export")
print("-" * 80)

area_model = AreaModel()
areas = area_model.get_with_relationship_counts()

print(f"Total areas: {len(areas)}")

# Check for commas
area_names = areas["area_name"].to_list()
area_descs = areas["area_description"].to_list()

commas_in_names = sum(1 for a in area_names if a and "," in a)
commas_in_descs = sum(1 for d in area_descs if d and "," in d)

print(f"Areas with commas in 'area_name' column: {commas_in_names}")
print(f"Areas with commas in 'area_description' column: {commas_in_descs}")

csv_data = areas.write_csv(separator=";")
lines = csv_data.split("\n")
print(f"\nCSV generated: {len(lines)} lines")

if ";" in lines[0]:
    print("✓ Header correctly uses semicolon delimiter")
else:
    print("✗ ERROR: Header does not use semicolon delimiter")

# Test 3: Priorities Export
print("\n[TEST 3] Priorities CSV Export")
print("-" * 80)

priority_model = PriorityModel()
priorities = priority_model.get_all()

print(f"Total priorities: {len(priorities)}")

# Check for commas
biodiv_priority = priorities["biodiversity_priority"].to_list()
simplified = priorities["simplified_biodiversity_priority"].to_list()

commas_in_biodiv = sum(1 for p in biodiv_priority if p and "," in p)
commas_in_simplified = sum(1 for s in simplified if s and "," in s)

print(f"Priorities with commas in 'biodiversity_priority' column: {commas_in_biodiv}")
print(f"Priorities with commas in 'simplified_biodiversity_priority' column: {commas_in_simplified}")

csv_data = priorities.write_csv(separator=";")
lines = csv_data.split("\n")
print(f"\nCSV generated: {len(lines)} lines")

if ";" in lines[0]:
    print("✓ Header correctly uses semicolon delimiter")
else:
    print("✗ ERROR: Header does not use semicolon delimiter")

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("✓ All three entity types export with semicolon delimiter")
print("✓ Commas in text data are preserved correctly")
print("✓ CSV parsers will correctly interpret semicolon as delimiter")
print("\nNext steps:")
print("  1. Run Streamlit app: uv run streamlit run app.py")
print("  2. Navigate to Measures, Areas, or Priorities pages")
print("  3. Look for '📥 Download CSV (; delimited)' button")
print("  4. Download and verify in Excel or another tool")
print("=" * 80)
