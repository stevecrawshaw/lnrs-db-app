"""Habitat entity model for habitat types."""

import logging

import duckdb
import polars as pl

from config.database import db
from models.base import BaseModel

logger = logging.getLogger(__name__)


class HabitatModel(BaseModel):
    """Model for managing habitat entities."""

    @property
    def table_name(self) -> str:
        return "habitat"

    @property
    def id_column(self) -> str:
        return "habitat_id"

    def get_creation_areas(self, habitat_id: int) -> pl.DataFrame:
        """Get areas where this habitat is suitable for creation.

        Args:
            habitat_id: ID of the habitat

        Returns:
            pl.DataFrame: Areas linked for habitat creation
        """
        query = """
            SELECT
                a.area_id,
                a.area_name,
                a.area_description
            FROM area a
            JOIN habitat_creation_area hca ON a.area_id = hca.area_id
            WHERE hca.habitat_id = ?
            ORDER BY a.area_name
        """

        result = self.execute_raw_query(query, [habitat_id])
        return result.pl()

    def get_management_areas(self, habitat_id: int) -> pl.DataFrame:
        """Get areas where this habitat requires management.

        Args:
            habitat_id: ID of the habitat

        Returns:
            pl.DataFrame: Areas linked for habitat management
        """
        query = """
            SELECT
                a.area_id,
                a.area_name,
                a.area_description
            FROM area a
            JOIN habitat_management_area hma ON a.area_id = hma.area_id
            WHERE hma.habitat_id = ?
            ORDER BY a.area_name
        """

        result = self.execute_raw_query(query, [habitat_id])
        return result.pl()

    def get_with_area_counts(self) -> pl.DataFrame:
        """Get all habitats with counts of creation and management areas.

        Returns:
            pl.DataFrame: Habitats with area counts
        """
        query = """
            SELECT
                h.habitat_id,
                h.habitat,
                COUNT(DISTINCT hca.area_id) as creation_areas,
                COUNT(DISTINCT hma.area_id) as management_areas
            FROM habitat h
            LEFT JOIN habitat_creation_area hca ON h.habitat_id = hca.habitat_id
            LEFT JOIN habitat_management_area hma ON h.habitat_id = hma.habitat_id
            GROUP BY h.habitat_id, h.habitat
            ORDER BY h.habitat
        """

        result = self.execute_raw_query(query)
        return result.pl()

    def get_relationship_counts(self, habitat_id: int) -> dict[str, int]:
        """Get counts of related entities.

        Args:
            habitat_id: ID of the habitat

        Returns:
            dict: Entity name -> count
        """
        creation_areas = self.get_creation_areas(habitat_id)
        management_areas = self.get_management_areas(habitat_id)

        return {
            "creation_areas": len(creation_areas),
            "management_areas": len(management_areas),
        }

    def delete_with_cascade(self, habitat_id: int) -> bool:
        """Delete a habitat and all its relationships.

        NOTE: This operation is NOT atomic due to DuckDB FK constraint limitations.
        DuckDB checks FK constraints immediately after each statement, even within
        transactions, preventing atomic deletion of parent records.

        Sequential cascade order (from CLAUDE.md):
        1. Delete from habitat_creation_area where habitat_id matches
        2. Delete from habitat_management_area where habitat_id matches
        3. Finally delete from habitat

        Each step is executed sequentially and committed immediately.
        If a later step fails, earlier deletions are already committed.

        Args:
            habitat_id: ID of the habitat to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            duckdb.Error: If any deletion step fails
        """
        conn = db.get_connection()

        # Get relationship counts for logging
        creation_count = conn.execute(
            "SELECT COUNT(*) FROM habitat_creation_area WHERE habitat_id = ?",
            [habitat_id],
        ).fetchone()[0]
        management_count = conn.execute(
            "SELECT COUNT(*) FROM habitat_management_area WHERE habitat_id = ?",
            [habitat_id],
        ).fetchone()[0]

        logger.info(
            f"Deleting habitat {habitat_id} with relationships: "
            f"{creation_count} creation areas, {management_count} management areas"
        )

        try:
            # Step 1: Delete habitat_creation_area
            logger.debug(f"Step 1/3: Deleting {creation_count} creation area links")
            conn.execute(
                "DELETE FROM habitat_creation_area WHERE habitat_id = ?",
                [habitat_id],
            )

            # Step 2: Delete habitat_management_area
            logger.debug(f"Step 2/3: Deleting {management_count} management area links")
            conn.execute(
                "DELETE FROM habitat_management_area WHERE habitat_id = ?",
                [habitat_id],
            )

            # Step 3: Delete the habitat itself
            logger.debug(f"Step 3/3: Deleting habitat {habitat_id}")
            conn.execute(
                "DELETE FROM habitat WHERE habitat_id = ?",
                [habitat_id],
            )

            logger.info(
                f"Successfully deleted habitat {habitat_id} with cascade "
                f"(total: {creation_count + management_count} child records)"
            )
            return True
        except duckdb.Error as e:
            logger.error(
                f"Failed to delete habitat {habitat_id}: {e}\n"
                f"Note: This operation is NOT atomic due to DuckDB FK constraint limitations. "
                f"Some deletions may have succeeded before this error.",
                exc_info=True,
            )
            raise


# %%
if __name__ == "__main__":
    """Test the Habitat model."""
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    print("Testing Habitat Model\n")

    model = HabitatModel()

    # Test count
    print(f"1. Total habitats: {model.count()}")

    # Test get with area counts
    print("\n2. Habitats with area counts:")
    habitats_with_counts = model.get_with_area_counts()
    print(habitats_with_counts.head(5))

    # Test get by ID
    print("\n3. Testing get_by_id(1):")
    habitat = model.get_by_id(1)
    if habitat:
        print(f"   Habitat: {habitat['habitat']}")

    # Test related areas
    print("\n4. Related areas for habitat 1:")
    counts = model.get_relationship_counts(1)
    for entity, count in counts.items():
        print(f"   {entity.replace('_', ' ').title()}: {count}")

    print("\n✓ All Habitat model tests completed!")
