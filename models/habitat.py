"""Habitat entity model for habitat types."""

import polars as pl

from models.base import BaseModel


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
        """Delete a habitat and all its relationships following cascade order.

        Cascade order (from CLAUDE.md):
        1. Delete from habitat_creation_area where habitat_id matches
        2. Delete from habitat_management_area where habitat_id matches
        3. Finally delete from habitat

        Args:
            habitat_id: ID of the habitat to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            Exception: If any deletion step fails
        """
        try:
            # Step 1: Delete from habitat_creation_area
            query1 = "DELETE FROM habitat_creation_area WHERE habitat_id = ?"
            self.execute_raw_query(query1, [habitat_id])

            # Step 2: Delete from habitat_management_area
            query2 = "DELETE FROM habitat_management_area WHERE habitat_id = ?"
            self.execute_raw_query(query2, [habitat_id])

            # Step 3: Delete from habitat
            query3 = "DELETE FROM habitat WHERE habitat_id = ?"
            self.execute_raw_query(query3, [habitat_id])

            return True
        except Exception as e:
            print(f"Error deleting habitat {habitat_id} with cascade: {e}")
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
