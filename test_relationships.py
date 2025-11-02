"""Test script for relationship (bridge table) operations."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.relationship import RelationshipModel

print("=" * 80)
print("TESTING RELATIONSHIP MODEL OPERATIONS")
print("=" * 80)

relationship_model = RelationshipModel()

# ==============================================================================
# TEST 1: MEASURE-AREA-PRIORITY OPERATIONS
# ==============================================================================

print("\n" + "=" * 80)
print("TEST 1: MEASURE-AREA-PRIORITY OPERATIONS")
print("=" * 80)

# Get initial count
initial_links = relationship_model.get_all_measure_area_priority()
print(f"\n✓ Initial link count: {len(initial_links):,}")

# Test case: Create a new link
# Use measure_id=1, area_id=1, priority_id=1 as test (should be safe)
test_measure_id = 1
test_area_id = 1
test_priority_id = 1

print(f"\n→ Testing link: Measure {test_measure_id} - Area {test_area_id} - Priority {test_priority_id}")

# Check if link already exists
link_exists = relationship_model.link_exists_measure_area_priority(
    test_measure_id, test_area_id, test_priority_id
)
print(f"   Link already exists: {link_exists}")

if link_exists:
    print("   ⚠️  Link exists - will test duplicate prevention")

    # Test duplicate prevention
    try:
        relationship_model.create_measure_area_priority_link(
            test_measure_id, test_area_id, test_priority_id
        )
        print("   ❌ ERROR: Duplicate link was allowed (should have been prevented)")
    except ValueError as e:
        print(f"   ✓ Duplicate prevention works: {e}")

    # Test delete
    print("\n→ Testing delete operation...")
    try:
        relationship_model.delete_measure_area_priority_link(
            test_measure_id, test_area_id, test_priority_id
        )
        print("   ✓ Link deleted successfully")

        # Verify deletion
        still_exists = relationship_model.link_exists_measure_area_priority(
            test_measure_id, test_area_id, test_priority_id
        )
        if not still_exists:
            print("   ✓ Verified: Link no longer exists")
        else:
            print("   ❌ ERROR: Link still exists after deletion")

        # Recreate the link for next test
        print("\n→ Recreating the link...")
        relationship_model.create_measure_area_priority_link(
            test_measure_id, test_area_id, test_priority_id
        )
        print("   ✓ Link recreated")

    except Exception as e:
        print(f"   ❌ ERROR during delete: {e}")

else:
    print("   Link does not exist - will test creation")

    # Test create
    try:
        relationship_model.create_measure_area_priority_link(
            test_measure_id, test_area_id, test_priority_id
        )
        print("   ✓ Link created successfully")

        # Verify creation
        now_exists = relationship_model.link_exists_measure_area_priority(
            test_measure_id, test_area_id, test_priority_id
        )
        if now_exists:
            print("   ✓ Verified: Link now exists")
        else:
            print("   ❌ ERROR: Link does not exist after creation")

        # Test duplicate prevention
        print("\n→ Testing duplicate prevention...")
        try:
            relationship_model.create_measure_area_priority_link(
                test_measure_id, test_area_id, test_priority_id
            )
            print("   ❌ ERROR: Duplicate link was allowed (should have been prevented)")
        except ValueError as e:
            print(f"   ✓ Duplicate prevention works: {e}")

    except Exception as e:
        print(f"   ❌ ERROR during create: {e}")

# Test filtering methods
print("\n→ Testing get_areas_for_measure(1)...")
areas_for_measure = relationship_model.get_areas_for_measure(1)
print(f"   ✓ Found {len(areas_for_measure)} area-priority combinations for measure 1")

print("\n→ Testing get_measures_for_area(1)...")
measures_for_area = relationship_model.get_measures_for_area(1)
print(f"   ✓ Found {len(measures_for_area)} measures for area 1")

print("\n→ Testing get_measures_for_priority(1)...")
measures_for_priority = relationship_model.get_measures_for_priority(1)
print(f"   ✓ Found {len(measures_for_priority)} measures for priority 1")

# ==============================================================================
# TEST 2: GRANT FUNDING OPERATIONS
# ==============================================================================

print("\n" + "=" * 80)
print("TEST 2: GRANT FUNDING OPERATIONS")
print("=" * 80)

# Get unfunded links
unfunded_links = relationship_model.get_unfunded_measure_area_priority_links()
print(f"\n✓ Found {len(unfunded_links):,} unfunded links")

# Get grant-funded links
grant_links = relationship_model.get_all_measure_area_priority_grants()
print(f"✓ Found {len(grant_links):,} grant-funded links")

# Test adding a grant to a link (if there are unfunded links)
if len(unfunded_links) > 0:
    # Use the first unfunded link
    test_link = unfunded_links.row(0, named=True)
    test_grant_id = 1  # Assume grant 1 exists

    print(f"\n→ Testing add grant to link: M{test_link['measure_id']}-A{test_link['area_id']}-P{test_link['priority_id']} + Grant {test_grant_id}")

    try:
        relationship_model.add_grant_to_link(
            test_link['measure_id'],
            test_link['area_id'],
            test_link['priority_id'],
            test_grant_id
        )
        print("   ✓ Grant added successfully")

        # Test duplicate prevention
        print("\n→ Testing duplicate grant prevention...")
        try:
            relationship_model.add_grant_to_link(
                test_link['measure_id'],
                test_link['area_id'],
                test_link['priority_id'],
                test_grant_id
            )
            print("   ❌ ERROR: Duplicate grant was allowed")
        except ValueError as e:
            print(f"   ✓ Duplicate prevention works: {e}")

        # Remove the grant (cleanup)
        print("\n→ Removing grant (cleanup)...")
        relationship_model.remove_grant_from_link(
            test_link['measure_id'],
            test_link['area_id'],
            test_link['priority_id'],
            test_grant_id
        )
        print("   ✓ Grant removed")

    except Exception as e:
        print(f"   ⚠️  Note: {e}")
else:
    print("\n⚠️  No unfunded links available for testing")

# ==============================================================================
# TEST 3: SPECIES-AREA-PRIORITY OPERATIONS
# ==============================================================================

print("\n" + "=" * 80)
print("TEST 3: SPECIES-AREA-PRIORITY OPERATIONS")
print("=" * 80)

# Get all species links
species_links = relationship_model.get_all_species_area_priority()
print(f"\n✓ Total species-area-priority links: {len(species_links):,}")

# Test create/delete with species_id=1, area_id=1, priority_id=1
test_species_id = 1
test_species_area_id = 1
test_species_priority_id = 1

print(f"\n→ Testing species link: Species {test_species_id} - Area {test_species_area_id} - Priority {test_species_priority_id}")

# Check if exists
species_link_exists = len(species_links.filter(
    (species_links["species_id"] == test_species_id) &
    (species_links["area_id"] == test_species_area_id) &
    (species_links["priority_id"] == test_species_priority_id)
)) > 0

print(f"   Link exists: {species_link_exists}")

if species_link_exists:
    print("   Testing delete...")
    try:
        relationship_model.delete_species_area_priority_link(
            test_species_id, test_species_area_id, test_species_priority_id
        )
        print("   ✓ Species link deleted")

        # Recreate it
        print("   Recreating...")
        relationship_model.create_species_area_priority_link(
            test_species_id, test_species_area_id, test_species_priority_id
        )
        print("   ✓ Species link recreated")
    except Exception as e:
        print(f"   ⚠️  {e}")
else:
    print("   Testing create...")
    try:
        relationship_model.create_species_area_priority_link(
            test_species_id, test_species_area_id, test_species_priority_id
        )
        print("   ✓ Species link created")

        # Test duplicate
        print("   Testing duplicate prevention...")
        try:
            relationship_model.create_species_area_priority_link(
                test_species_id, test_species_area_id, test_species_priority_id
            )
            print("   ❌ ERROR: Duplicate allowed")
        except ValueError as e:
            print(f"   ✓ Duplicate prevention works")

    except Exception as e:
        print(f"   ⚠️  {e}")

# ==============================================================================
# TEST 4: HABITAT CREATION OPERATIONS
# ==============================================================================

print("\n" + "=" * 80)
print("TEST 4: HABITAT CREATION OPERATIONS")
print("=" * 80)

habitat_creation_links = relationship_model.get_all_habitat_creation_areas()
print(f"\n✓ Total habitat creation links: {len(habitat_creation_links):,}")

# Test with habitat_id=1, area_id=1
test_habitat_id = 1
test_habitat_area_id = 1

print(f"\n→ Testing habitat creation link: Habitat {test_habitat_id} - Area {test_habitat_area_id}")

habitat_creation_exists = len(habitat_creation_links.filter(
    (habitat_creation_links["habitat_id"] == test_habitat_id) &
    (habitat_creation_links["area_id"] == test_habitat_area_id)
)) > 0

print(f"   Link exists: {habitat_creation_exists}")

if habitat_creation_exists:
    print("   Testing delete...")
    try:
        relationship_model.delete_habitat_creation_link(test_habitat_id, test_habitat_area_id)
        print("   ✓ Habitat creation link deleted")

        # Recreate
        print("   Recreating...")
        relationship_model.create_habitat_creation_link(test_habitat_id, test_habitat_area_id)
        print("   ✓ Habitat creation link recreated")
    except Exception as e:
        print(f"   ⚠️  {e}")
else:
    print("   Testing create...")
    try:
        relationship_model.create_habitat_creation_link(test_habitat_id, test_habitat_area_id)
        print("   ✓ Habitat creation link created")

        # Test duplicate
        print("   Testing duplicate prevention...")
        try:
            relationship_model.create_habitat_creation_link(test_habitat_id, test_habitat_area_id)
            print("   ❌ ERROR: Duplicate allowed")
        except ValueError as e:
            print(f"   ✓ Duplicate prevention works")
    except Exception as e:
        print(f"   ⚠️  {e}")

# ==============================================================================
# TEST 5: HABITAT MANAGEMENT OPERATIONS
# ==============================================================================

print("\n" + "=" * 80)
print("TEST 5: HABITAT MANAGEMENT OPERATIONS")
print("=" * 80)

habitat_management_links = relationship_model.get_all_habitat_management_areas()
print(f"\n✓ Total habitat management links: {len(habitat_management_links):,}")

print(f"\n→ Testing habitat management link: Habitat {test_habitat_id} - Area {test_habitat_area_id}")

habitat_management_exists = len(habitat_management_links.filter(
    (habitat_management_links["habitat_id"] == test_habitat_id) &
    (habitat_management_links["area_id"] == test_habitat_area_id)
)) > 0

print(f"   Link exists: {habitat_management_exists}")

if habitat_management_exists:
    print("   Testing delete...")
    try:
        relationship_model.delete_habitat_management_link(test_habitat_id, test_habitat_area_id)
        print("   ✓ Habitat management link deleted")

        # Recreate
        print("   Recreating...")
        relationship_model.create_habitat_management_link(test_habitat_id, test_habitat_area_id)
        print("   ✓ Habitat management link recreated")
    except Exception as e:
        print(f"   ⚠️  {e}")
else:
    print("   Testing create...")
    try:
        relationship_model.create_habitat_management_link(test_habitat_id, test_habitat_area_id)
        print("   ✓ Habitat management link created")

        # Test duplicate
        print("   Testing duplicate prevention...")
        try:
            relationship_model.create_habitat_management_link(test_habitat_id, test_habitat_area_id)
            print("   ❌ ERROR: Duplicate allowed")
        except ValueError as e:
            print(f"   ✓ Duplicate prevention works")
    except Exception as e:
        print(f"   ⚠️  {e}")

# ==============================================================================
# FINAL SUMMARY
# ==============================================================================

print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)

# Get final counts
final_map_links = relationship_model.get_all_measure_area_priority()
final_grant_links = relationship_model.get_all_measure_area_priority_grants()
final_species_links = relationship_model.get_all_species_area_priority()
final_habitat_creation = relationship_model.get_all_habitat_creation_areas()
final_habitat_management = relationship_model.get_all_habitat_management_areas()

print(f"""
Bridge Table Statistics:
- Measure-Area-Priority: {len(final_map_links):,} links
- Grant Funding: {len(final_grant_links):,} links
- Species-Area-Priority: {len(final_species_links):,} links
- Habitat Creation: {len(final_habitat_creation):,} links
- Habitat Management: {len(final_habitat_management):,} links

Total Relationships: {len(final_map_links) + len(final_grant_links) + len(final_species_links) + len(final_habitat_creation) + len(final_habitat_management):,}
""")

print("=" * 80)
print("✓ ALL TESTS COMPLETED")
print("=" * 80)
