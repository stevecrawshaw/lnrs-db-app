"""Measure entity model for biodiversity measures."""

import logging

import duckdb
import polars as pl
import streamlit as st

from config.database import db, with_snapshot
from config.monitoring import monitor_performance
from models.base import BaseModel

logger = logging.getLogger(__name__)


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

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_all_measure_types(_self) -> pl.DataFrame:
        """Get all available measure types for multi-select dropdown.

        Cached for 1 hour as this reference data rarely changes.

        Returns:
            pl.DataFrame: All measure types
        """
        query = "SELECT measure_type_id, measure_type FROM measure_type ORDER BY measure_type"
        result = _self.execute_raw_query(query)
        return result.pl()

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_all_stakeholders(_self) -> pl.DataFrame:
        """Get all available stakeholders for multi-select dropdown.

        Cached for 1 hour as this reference data rarely changes.

        Returns:
            pl.DataFrame: All stakeholders
        """
        query = "SELECT stakeholder_id, stakeholder FROM stakeholder ORDER BY stakeholder"
        result = _self.execute_raw_query(query)
        return result.pl()

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_all_benefits(_self) -> pl.DataFrame:
        """Get all available benefits for multi-select dropdown.

        Cached for 1 hour as this reference data rarely changes.

        Returns:
            pl.DataFrame: All benefits
        """
        query = "SELECT benefit_id, benefit FROM benefits ORDER BY benefit"
        result = _self.execute_raw_query(query)
        return result.pl()

    @monitor_performance("measure_delete_cascade")
    @with_snapshot("delete", "measure")
    def delete_with_cascade(self, measure_id: int) -> bool:
        """Delete a measure and all its relationships.

        NOTE: This operation is NOT atomic due to DuckDB FK constraint limitations.
        DuckDB checks FK constraints immediately after each statement, even within
        transactions. The composite FK from measure_area_priority_grant to
        measure_area_priority prevents atomic deletion.

        Sequential cascade order (from CLAUDE.md):
        1. Delete from measure_has_type where measure_id matches
        2. Delete from measure_has_stakeholder where measure_id matches
        3. Delete from measure_area_priority_grant where measure_id matches
        4. Delete from measure_area_priority where measure_id matches
        5. Delete from measure_has_benefits where measure_id matches
        6. Delete from measure_has_species where measure_id matches
        7. Finally delete from measure

        Each step is executed sequentially and committed immediately.
        If a later step fails, earlier deletions are already committed.

        Args:
            measure_id: ID of the measure to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            duckdb.Error: If any deletion step fails
        """
        conn = db.get_connection()

        # Get relationship counts for logging
        type_count = conn.execute(
            "SELECT COUNT(*) FROM measure_has_type WHERE measure_id = ?",
            [measure_id],
        ).fetchone()[0]
        stakeholder_count = conn.execute(
            "SELECT COUNT(*) FROM measure_has_stakeholder WHERE measure_id = ?",
            [measure_id],
        ).fetchone()[0]
        grant_count = conn.execute(
            "SELECT COUNT(*) FROM measure_area_priority_grant WHERE measure_id = ?",
            [measure_id],
        ).fetchone()[0]
        map_count = conn.execute(
            "SELECT COUNT(*) FROM measure_area_priority WHERE measure_id = ?",
            [measure_id],
        ).fetchone()[0]
        benefit_count = conn.execute(
            "SELECT COUNT(*) FROM measure_has_benefits WHERE measure_id = ?",
            [measure_id],
        ).fetchone()[0]
        species_count = conn.execute(
            "SELECT COUNT(*) FROM measure_has_species WHERE measure_id = ?",
            [measure_id],
        ).fetchone()[0]

        logger.info(
            f"Deleting measure {measure_id} with relationships: "
            f"{type_count} types, {stakeholder_count} stakeholders, "
            f"{grant_count} grants, {map_count} area-priority links, "
            f"{benefit_count} benefits, {species_count} species"
        )

        try:
            # Step 1: Delete measure types
            logger.debug(f"Step 1/7: Deleting {type_count} types")
            conn.execute(
                "DELETE FROM measure_has_type WHERE measure_id = ?",
                [measure_id],
            )

            # Step 2: Delete stakeholders
            logger.debug(f"Step 2/7: Deleting {stakeholder_count} stakeholders")
            conn.execute(
                "DELETE FROM measure_has_stakeholder WHERE measure_id = ?",
                [measure_id],
            )

            # Step 3: Delete grant links (grandchild - must come before MAP)
            logger.debug(f"Step 3/7: Deleting {grant_count} grant links")
            conn.execute(
                "DELETE FROM measure_area_priority_grant WHERE measure_id = ?",
                [measure_id],
            )

            # Step 4: Delete measure_area_priority (child - after grants)
            logger.debug(f"Step 4/7: Deleting {map_count} area-priority links")
            conn.execute(
                "DELETE FROM measure_area_priority WHERE measure_id = ?",
                [measure_id],
            )

            # Step 5: Delete benefits
            logger.debug(f"Step 5/7: Deleting {benefit_count} benefits")
            conn.execute(
                "DELETE FROM measure_has_benefits WHERE measure_id = ?",
                [measure_id],
            )

            # Step 6: Delete species links
            logger.debug(f"Step 6/7: Deleting {species_count} species")
            conn.execute(
                "DELETE FROM measure_has_species WHERE measure_id = ?",
                [measure_id],
            )

            # Step 7: Delete the measure itself
            logger.debug(f"Step 7/7: Deleting measure {measure_id}")
            conn.execute(
                "DELETE FROM measure WHERE measure_id = ?",
                [measure_id],
            )

            logger.info(
                f"Successfully deleted measure {measure_id} with cascade "
                f"(total: {type_count + stakeholder_count + grant_count + map_count + benefit_count + species_count} child records)"
            )
            return True
        except duckdb.Error as e:
            logger.error(
                f"Failed to delete measure {measure_id}: {e}\n"
                f"Note: This operation is NOT atomic due to DuckDB FK constraint limitations. "
                f"Some deletions may have succeeded before this error.",
                exc_info=True,
            )
            raise

    def add_measure_types(self, measure_id: int, type_ids: list[int]) -> None:
        """Add types to a measure atomically.

        Args:
            measure_id: ID of the measure
            type_ids: List of measure_type_ids to link

        Raises:
            duckdb.Error: If transaction fails
        """
        if not type_ids:
            return

        queries = [
            ("INSERT INTO measure_has_type (measure_id, measure_type_id) VALUES (?, ?)",
             [measure_id, type_id])
            for type_id in type_ids
        ]

        try:
            db.execute_transaction(queries)
            logger.debug(f"Added {len(type_ids)} types to measure {measure_id}")
        except duckdb.Error as e:
            logger.error(f"Failed to add types to measure {measure_id}: {e}")
            raise

    def add_stakeholders(self, measure_id: int, stakeholder_ids: list[int]) -> None:
        """Add stakeholders to a measure atomically.

        Args:
            measure_id: ID of the measure
            stakeholder_ids: List of stakeholder_ids to link

        Raises:
            duckdb.Error: If transaction fails
        """
        if not stakeholder_ids:
            return

        queries = [
            ("INSERT INTO measure_has_stakeholder (measure_id, stakeholder_id) VALUES (?, ?)",
             [measure_id, stakeholder_id])
            for stakeholder_id in stakeholder_ids
        ]

        try:
            db.execute_transaction(queries)
            logger.debug(f"Added {len(stakeholder_ids)} stakeholders to measure {measure_id}")
        except duckdb.Error as e:
            logger.error(f"Failed to add stakeholders to measure {measure_id}: {e}")
            raise

    def add_benefits(self, measure_id: int, benefit_ids: list[int]) -> None:
        """Add benefits to a measure atomically.

        Args:
            measure_id: ID of the measure
            benefit_ids: List of benefit_ids to link

        Raises:
            duckdb.Error: If transaction fails
        """
        if not benefit_ids:
            return

        queries = [
            ("INSERT INTO measure_has_benefits (measure_id, benefit_id) VALUES (?, ?)",
             [measure_id, benefit_id])
            for benefit_id in benefit_ids
        ]

        try:
            db.execute_transaction(queries)
            logger.debug(f"Added {len(benefit_ids)} benefits to measure {measure_id}")
        except duckdb.Error as e:
            logger.error(f"Failed to add benefits to measure {measure_id}: {e}")
            raise

    def update_with_relationships(
        self,
        measure_id: int,
        measure_data: dict,
        measure_types: list[int] | None = None,
        stakeholders: list[int] | None = None,
        benefits: list[int] | None = None
    ) -> bool:
        """Update measure and all relationships atomically.

        All operations are executed in a single transaction - either all succeed
        or all are rolled back automatically on failure.

        Args:
            measure_id: ID of the measure to update
            measure_data: Dictionary of measure fields to update
            measure_types: List of measure_type_ids (replaces existing)
            stakeholders: List of stakeholder_ids (replaces existing)
            benefits: List of benefit_ids (replaces existing)

        Returns:
            bool: True if update was successful

        Raises:
            duckdb.Error: If any operation fails (all changes rolled back)
        """
        queries = []

        # 1. Update measure record
        if measure_data:
            set_clause = ", ".join([f"{k} = ?" for k in measure_data.keys()])
            values = list(measure_data.values()) + [measure_id]
            queries.append((
                f"UPDATE measure SET {set_clause} WHERE measure_id = ?",
                values
            ))

        # 2. Delete existing relationships
        queries.extend([
            ("DELETE FROM measure_has_type WHERE measure_id = ?", [measure_id]),
            ("DELETE FROM measure_has_stakeholder WHERE measure_id = ?", [measure_id]),
            ("DELETE FROM measure_has_benefits WHERE measure_id = ?", [measure_id]),
        ])

        # 3. Insert new relationships
        if measure_types:
            for type_id in measure_types:
                queries.append((
                    "INSERT INTO measure_has_type (measure_id, measure_type_id) VALUES (?, ?)",
                    [measure_id, type_id]
                ))

        if stakeholders:
            for stakeholder_id in stakeholders:
                queries.append((
                    "INSERT INTO measure_has_stakeholder (measure_id, stakeholder_id) VALUES (?, ?)",
                    [measure_id, stakeholder_id]
                ))

        if benefits:
            for benefit_id in benefits:
                queries.append((
                    "INSERT INTO measure_has_benefits (measure_id, benefit_id) VALUES (?, ?)",
                    [measure_id, benefit_id]
                ))

        try:
            db.execute_transaction(queries)
            logger.info(f"Updated measure {measure_id} with {len(queries)} operations")
            return True
        except duckdb.Error as e:
            logger.error(f"Failed to update measure {measure_id}: {e}", exc_info=True)
            raise


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
