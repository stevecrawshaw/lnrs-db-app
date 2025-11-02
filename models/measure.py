"""Measure entity model for biodiversity measures."""

import polars as pl

from models.base import BaseModel


class MeasureModel(BaseModel):
    """Model for managing measure entities."""

    @property
    def table_name(self) -> str:
        return "measure"

    @property
    def id_column(self) -> str:
        return "measure_id"

    def get_with_relationship_counts(self) -> pl.DataFrame:
        """Get all measures with relationship counts and types/stakeholders.

        Uses correlated subqueries to avoid Cartesian product performance issues.

        Returns:
            pl.DataFrame: Measures with relationship counts and aggregated types/stakeholders
        """
        query = """
            SELECT
                m.measure_id,
                m.measure,
                m.concise_measure,
                m.core_supplementary,
                m.mapped_unmapped,
                (SELECT STRING_AGG(DISTINCT mt.measure_type, ', ')
                 FROM measure_has_type mht
                 JOIN measure_type mt ON mht.measure_type_id = mt.measure_type_id
                 WHERE mht.measure_id = m.measure_id) as types,
                (SELECT STRING_AGG(DISTINCT s.stakeholder, ', ')
                 FROM measure_has_stakeholder mhs
                 JOIN stakeholder s ON mhs.stakeholder_id = s.stakeholder_id
                 WHERE mhs.measure_id = m.measure_id) as stakeholders,
                (SELECT COUNT(DISTINCT area_id)
                 FROM measure_area_priority
                 WHERE measure_id = m.measure_id) as areas,
                (SELECT COUNT(DISTINCT priority_id)
                 FROM measure_area_priority
                 WHERE measure_id = m.measure_id) as priorities,
                (SELECT COUNT(DISTINCT species_id)
                 FROM measure_has_species
                 WHERE measure_id = m.measure_id) as species,
                (SELECT COUNT(DISTINCT benefit_id)
                 FROM measure_has_benefits
                 WHERE measure_id = m.measure_id) as benefits
            FROM measure m
            ORDER BY m.measure_id
        """

        result = self.execute_raw_query(query)
        return result.pl()

    def get_types(self, measure_id: int) -> pl.DataFrame:
        """Get types for this measure.

        Args:
            measure_id: ID of the measure

        Returns:
            pl.DataFrame: Types linked to this measure
        """
        query = """
            SELECT
                mt.measure_type_id,
                mt.measure_type
            FROM measure_type mt
            JOIN measure_has_type mht ON mt.measure_type_id = mht.measure_type_id
            WHERE mht.measure_id = ?
            ORDER BY mt.measure_type
        """

        result = self.execute_raw_query(query, [measure_id])
        return result.pl()

    def get_stakeholders(self, measure_id: int) -> pl.DataFrame:
        """Get stakeholders for this measure.

        Args:
            measure_id: ID of the measure

        Returns:
            pl.DataFrame: Stakeholders linked to this measure
        """
        query = """
            SELECT
                s.stakeholder_id,
                s.stakeholder
            FROM stakeholder s
            JOIN measure_has_stakeholder mhs ON s.stakeholder_id = mhs.stakeholder_id
            WHERE mhs.measure_id = ?
            ORDER BY s.stakeholder
        """

        result = self.execute_raw_query(query, [measure_id])
        return result.pl()

    def get_related_areas(self, measure_id: int) -> pl.DataFrame:
        """Get areas linked to this measure.

        Args:
            measure_id: ID of the measure

        Returns:
            pl.DataFrame: Areas linked to this measure
        """
        query = """
            SELECT DISTINCT
                a.area_id,
                a.area_name,
                a.area_description
            FROM area a
            JOIN measure_area_priority map ON a.area_id = map.area_id
            WHERE map.measure_id = ?
            ORDER BY a.area_name
        """

        result = self.execute_raw_query(query, [measure_id])
        return result.pl()

    def get_related_priorities(self, measure_id: int) -> pl.DataFrame:
        """Get priorities linked to this measure.

        Args:
            measure_id: ID of the measure

        Returns:
            pl.DataFrame: Priorities linked to this measure
        """
        query = """
            SELECT DISTINCT
                p.priority_id,
                p.biodiversity_priority,
                p.simplified_biodiversity_priority,
                p.theme
            FROM priority p
            JOIN measure_area_priority map ON p.priority_id = map.priority_id
            WHERE map.measure_id = ?
            ORDER BY p.theme, p.biodiversity_priority
        """

        result = self.execute_raw_query(query, [measure_id])
        return result.pl()

    def get_related_grants(self, measure_id: int) -> pl.DataFrame:
        """Get grants linked to this measure.

        Args:
            measure_id: ID of the measure

        Returns:
            pl.DataFrame: Grants linked to this measure
        """
        query = """
            SELECT DISTINCT
                g.grant_id,
                g.grant_name,
                g.grant_scheme,
                g.url
            FROM grant_table g
            JOIN measure_area_priority_grant mapg ON g.grant_id = mapg.grant_id
            WHERE mapg.measure_id = ?
            ORDER BY g.grant_scheme, g.grant_name
        """

        result = self.execute_raw_query(query, [measure_id])
        return result.pl()

    def get_related_species(self, measure_id: int) -> pl.DataFrame:
        """Get species linked to this measure.

        Args:
            measure_id: ID of the measure

        Returns:
            pl.DataFrame: Species linked to this measure
        """
        query = """
            SELECT
                s.species_id,
                s.common_name,
                s.linnaean_name,
                s.assemblage,
                s.taxa
            FROM species s
            JOIN measure_has_species mhs ON s.species_id = mhs.species_id
            WHERE mhs.measure_id = ?
            ORDER BY s.common_name
        """

        result = self.execute_raw_query(query, [measure_id])
        return result.pl()

    def get_benefits(self, measure_id: int) -> pl.DataFrame:
        """Get benefits delivered by this measure.

        Args:
            measure_id: ID of the measure

        Returns:
            pl.DataFrame: Benefits linked to this measure
        """
        query = """
            SELECT
                b.benefit_id,
                b.benefit
            FROM benefits b
            JOIN measure_has_benefits mhb ON b.benefit_id = mhb.benefit_id
            WHERE mhb.measure_id = ?
            ORDER BY b.benefit
        """

        result = self.execute_raw_query(query, [measure_id])
        return result.pl()

    def get_relationship_counts(self, measure_id: int) -> dict[str, int]:
        """Get counts of all related entities for a measure.

        Args:
            measure_id: ID of the measure

        Returns:
            dict: Entity name -> count
        """
        types = self.get_types(measure_id)
        stakeholders = self.get_stakeholders(measure_id)
        areas = self.get_related_areas(measure_id)
        priorities = self.get_related_priorities(measure_id)
        grants = self.get_related_grants(measure_id)
        species = self.get_related_species(measure_id)
        benefits = self.get_benefits(measure_id)

        return {
            "types": len(types),
            "stakeholders": len(stakeholders),
            "areas": len(areas),
            "priorities": len(priorities),
            "grants": len(grants),
            "species": len(species),
            "benefits": len(benefits),
        }


# %%
if __name__ == "__main__":
    """Test the Measure model."""
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    print("Testing Measure Model\n")

    model = MeasureModel()

    # Test count
    print(f"1. Total measures: {model.count()}")

    # Test get with relationship counts
    print("\n2. First 3 measures with relationship counts:")
    measures_with_counts = model.get_with_relationship_counts()
    print(measures_with_counts.select([
        "measure_id",
        "concise_measure",
        "core_supplementary",
        "types",
        "stakeholders",
        "areas",
        "priorities",
        "species"
    ]).head(3))

    # Test get by ID
    print("\n3. Testing get_by_id(2):")
    measure = model.get_by_id(2)
    if measure:
        print(f"   Measure: {measure['concise_measure'][:80]}...")
        print(f"   Type: {measure['core_supplementary']}")

    # Test related entities
    print("\n4. Related entities for measure 2:")
    counts = model.get_relationship_counts(2)
    for entity, count in counts.items():
        print(f"   {entity.capitalize()}: {count}")

    # Test get types
    print("\n5. Testing get_types(2):")
    types = model.get_types(2)
    print(f"   Found {len(types)} types")
    if len(types) > 0:
        for i in range(len(types)):
            print(f"   - {types[i, 'measure_type']}")

    # Test get stakeholders
    print("\n6. Testing get_stakeholders(2):")
    stakeholders = model.get_stakeholders(2)
    print(f"   Found {len(stakeholders)} stakeholders")
    if len(stakeholders) > 0:
        for i in range(len(stakeholders)):
            print(f"   - {stakeholders[i, 'stakeholder']}")

    print("\n✓ All Measure model tests completed!")
