"""Priority entity model for biodiversity priorities."""

import logging

import duckdb
import polars as pl

from config.database import db, with_snapshot
from models.base import BaseModel

logger = logging.getLogger(__name__)


class PriorityModel(BaseModel):
    """Model for managing biodiversity priority entities."""

    @property
    def table_name(self) -> str:
        return "priority"

    @property
    def id_column(self) -> str:
        return "priority_id"

    def get_by_theme(self) -> dict[str, pl.DataFrame]:
        """Get priorities grouped by theme.

        Returns:
            dict: Theme name -> DataFrame of priorities in that theme
        """
        all_priorities = self.get_all(order_by="theme, biodiversity_priority")

        # Group by theme
        themes = all_priorities["theme"].unique().sort()
        grouped = {}

        for theme in themes:
            theme_data = all_priorities.filter(pl.col("theme") == theme)
            grouped[theme] = theme_data

        return grouped

    def get_related_measures(self, priority_id: int) -> pl.DataFrame:
        """Get measures linked to this priority.

        Args:
            priority_id: ID of the priority

        Returns:
            pl.DataFrame: Measures linked to this priority
        """
        query = """
            SELECT DISTINCT
                m.measure_id,
                m.measure,
                m.concise_measure,
                m.core_supplementary
            FROM measure m
            JOIN measure_area_priority map ON m.measure_id = map.measure_id
            WHERE map.priority_id = ?
            ORDER BY m.measure_id
        """

        result = self.execute_raw_query(query, [priority_id])
        return result.pl()

    def get_related_areas(self, priority_id: int) -> pl.DataFrame:
        """Get areas linked to this priority.

        Args:
            priority_id: ID of the priority

        Returns:
            pl.DataFrame: Areas linked to this priority
        """
        query = """
            SELECT DISTINCT
                a.area_id,
                a.area_name,
                a.area_description
            FROM area a
            JOIN measure_area_priority map ON a.area_id = map.area_id
            WHERE map.priority_id = ?
            ORDER BY a.area_name
        """

        result = self.execute_raw_query(query, [priority_id])
        return result.pl()

    def get_related_species(self, priority_id: int) -> pl.DataFrame:
        """Get species linked to this priority.

        Args:
            priority_id: ID of the priority

        Returns:
            pl.DataFrame: Species linked to this priority
        """
        query = """
            SELECT DISTINCT
                s.species_id,
                s.common_name,
                s.linnaean_name,
                s.assemblage
            FROM species s
            JOIN species_area_priority sap ON s.species_id = sap.species_id
            WHERE sap.priority_id = ?
            ORDER BY s.common_name
        """

        result = self.execute_raw_query(query, [priority_id])
        return result.pl()

    def get_relationship_counts(self, priority_id: int) -> dict[str, int]:
        """Get counts of related entities.

        Args:
            priority_id: ID of the priority

        Returns:
            dict: Entity name -> count
        """
        measures = self.get_related_measures(priority_id)
        areas = self.get_related_areas(priority_id)
        species = self.get_related_species(priority_id)

        return {
            "measures": len(measures),
            "areas": len(areas),
            "species": len(species),
        }

    @with_snapshot("delete", "priority")
    def delete_with_cascade(self, priority_id: int) -> bool:
        """Delete a priority and all its relationships.

        NOTE: This operation is NOT atomic due to DuckDB FK constraint limitations.
        DuckDB checks FK constraints immediately after each statement, even within
        transactions. The composite FK from measure_area_priority_grant to
        measure_area_priority prevents atomic deletion.

        Sequential cascade order (from CLAUDE.md):
        1. Delete from measure_area_priority_grant where priority_id matches
        2. Delete from measure_area_priority where priority_id matches
        3. Delete from species_area_priority where priority_id matches
        4. Finally delete from priority

        Each step is executed sequentially and committed immediately.
        If a later step fails, earlier deletions are already committed.

        Args:
            priority_id: ID of the priority to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            duckdb.Error: If any deletion step fails
        """
        conn = db.get_connection()

        # Get relationship counts for logging
        grant_count = conn.execute(
            "SELECT COUNT(*) FROM measure_area_priority_grant WHERE priority_id = ?",
            [priority_id],
        ).fetchone()[0]
        map_count = conn.execute(
            "SELECT COUNT(*) FROM measure_area_priority WHERE priority_id = ?",
            [priority_id],
        ).fetchone()[0]
        species_count = conn.execute(
            "SELECT COUNT(*) FROM species_area_priority WHERE priority_id = ?",
            [priority_id],
        ).fetchone()[0]

        logger.info(
            f"Deleting priority {priority_id} with relationships: "
            f"{grant_count} grants, {map_count} measure-area-priority, "
            f"{species_count} species"
        )

        try:
            # Step 1: Delete grant links (grandchild - must come first)
            logger.debug(f"Step 1/4: Deleting {grant_count} grant links")
            conn.execute(
                "DELETE FROM measure_area_priority_grant WHERE priority_id = ?",
                [priority_id],
            )

            # Step 2: Delete measure_area_priority (child - after grants)
            logger.debug(f"Step 2/4: Deleting {map_count} measure-area-priority links")
            conn.execute(
                "DELETE FROM measure_area_priority WHERE priority_id = ?",
                [priority_id],
            )

            # Step 3: Delete species_area_priority
            logger.debug(f"Step 3/4: Deleting {species_count} species links")
            conn.execute(
                "DELETE FROM species_area_priority WHERE priority_id = ?",
                [priority_id],
            )

            # Step 4: Delete the priority itself
            logger.debug(f"Step 4/4: Deleting priority {priority_id}")
            conn.execute(
                "DELETE FROM priority WHERE priority_id = ?",
                [priority_id],
            )

            logger.info(
                f"Successfully deleted priority {priority_id} with cascade "
                f"(total: {grant_count + map_count + species_count} child records)"
            )
            return True
        except duckdb.Error as e:
            logger.error(
                f"Failed to delete priority {priority_id}: {e}\n"
                f"Note: This operation is NOT atomic due to DuckDB FK constraint limitations. "
                f"Some deletions may have succeeded before this error.",
                exc_info=True,
            )
            raise


# %%
if __name__ == "__main__":
    """Test the Priority model."""
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    print("Testing Priority Model\n")

    model = PriorityModel()

    # Test count
    print(f"1. Total priorities: {model.count()}")

    # Test get by theme
    print("\n2. Priorities by theme:")
    by_theme = model.get_by_theme()
    for theme, priorities in by_theme.items():
        print(f"   {theme}: {len(priorities)} priorities")

    # Test get by ID
    print("\n3. Testing get_by_id(1):")
    priority = model.get_by_id(1)
    if priority:
        print(f"   Priority: {priority['biodiversity_priority']}")
        print(f"   Theme: {priority['theme']}")

    # Test related measures
    print("\n4. Related entities for priority 1:")
    counts = model.get_relationship_counts(1)
    for entity, count in counts.items():
        print(f"   {entity.title()}: {count}")

    # Test get all
    print("\n5. Getting all priorities:")
    all_priorities = model.get_all()
    print(f"   Retrieved {len(all_priorities)} priorities")

    print("\n✓ All Priority model tests completed!")
