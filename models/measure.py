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

    def get_all_measure_types(self) -> pl.DataFrame:
        """Get all available measure types for multi-select dropdown.

        Returns:
            pl.DataFrame: All measure types
        """
        query = "SELECT measure_type_id, measure_type FROM measure_type ORDER BY measure_type"
        result = self.execute_raw_query(query)
        return result.pl()

    def get_all_stakeholders(self) -> pl.DataFrame:
        """Get all available stakeholders for multi-select dropdown.

        Returns:
            pl.DataFrame: All stakeholders
        """
        query = "SELECT stakeholder_id, stakeholder FROM stakeholder ORDER BY stakeholder"
        result = self.execute_raw_query(query)
        return result.pl()

    def get_all_benefits(self) -> pl.DataFrame:
        """Get all available benefits for multi-select dropdown.

        Returns:
            pl.DataFrame: All benefits
        """
        query = "SELECT benefit_id, benefit FROM benefits ORDER BY benefit"
        result = self.execute_raw_query(query)
        return result.pl()

    def delete_with_cascade(self, measure_id: int) -> bool:
        """Delete a measure and all its relationships following cascade order.

        Cascade order (from CLAUDE.md):
        1. Delete from measure_has_type where measure_id matches
        2. Delete from measure_has_stakeholder where measure_id matches
        3. Delete from measure_area_priority_grant where measure_id matches
        4. Delete from measure_area_priority where measure_id matches
        5. Delete from measure_has_benefits where measure_id matches
        6. Delete from measure_has_species where measure_id matches
        7. Finally delete from measure

        Args:
            measure_id: ID of the measure to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            Exception: If any deletion step fails
        """
        try:
            # Step 1: Delete from measure_has_type
            query1 = "DELETE FROM measure_has_type WHERE measure_id = ?"
            self.execute_raw_query(query1, [measure_id])

            # Step 2: Delete from measure_has_stakeholder
            query2 = "DELETE FROM measure_has_stakeholder WHERE measure_id = ?"
            self.execute_raw_query(query2, [measure_id])

            # Step 3: Delete from measure_area_priority_grant
            query3 = "DELETE FROM measure_area_priority_grant WHERE measure_id = ?"
            self.execute_raw_query(query3, [measure_id])

            # Step 4: Delete from measure_area_priority
            query4 = "DELETE FROM measure_area_priority WHERE measure_id = ?"
            self.execute_raw_query(query4, [measure_id])

            # Step 5: Delete from measure_has_benefits
            query5 = "DELETE FROM measure_has_benefits WHERE measure_id = ?"
            self.execute_raw_query(query5, [measure_id])

            # Step 6: Delete from measure_has_species
            query6 = "DELETE FROM measure_has_species WHERE measure_id = ?"
            self.execute_raw_query(query6, [measure_id])

            # Step 7: Delete from measure
            query7 = "DELETE FROM measure WHERE measure_id = ?"
            self.execute_raw_query(query7, [measure_id])

            return True
        except Exception as e:
            print(f"Error deleting measure {measure_id} with cascade: {e}")
            raise

    def add_measure_types(self, measure_id: int, type_ids: list[int]) -> None:
        """Add types to a measure.

        Args:
            measure_id: ID of the measure
            type_ids: List of measure_type_ids to link
        """
        for type_id in type_ids:
            query = "INSERT INTO measure_has_type (measure_id, measure_type_id) VALUES (?, ?)"
            self.execute_raw_query(query, [measure_id, type_id])

    def add_stakeholders(self, measure_id: int, stakeholder_ids: list[int]) -> None:
        """Add stakeholders to a measure.

        Args:
            measure_id: ID of the measure
            stakeholder_ids: List of stakeholder_ids to link
        """
        for stakeholder_id in stakeholder_ids:
            query = "INSERT INTO measure_has_stakeholder (measure_id, stakeholder_id) VALUES (?, ?)"
            self.execute_raw_query(query, [measure_id, stakeholder_id])

    def add_benefits(self, measure_id: int, benefit_ids: list[int]) -> None:
        """Add benefits to a measure.

        Args:
            measure_id: ID of the measure
            benefit_ids: List of benefit_ids to link
        """
        for benefit_id in benefit_ids:
            query = "INSERT INTO measure_has_benefits (measure_id, benefit_id) VALUES (?, ?)"
            self.execute_raw_query(query, [measure_id, benefit_id])


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
