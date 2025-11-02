"""Priority entity model for biodiversity priorities."""

import polars as pl

from models.base import BaseModel


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

    def delete_with_cascade(self, priority_id: int) -> bool:
        """Delete a priority and all its relationships following cascade order.

        Cascade order (from CLAUDE.md):
        1. Delete from measure_area_priority_grant where priority_id matches
        2. Delete from measure_area_priority where priority_id matches
        3. Delete from species_area_priority where priority_id matches
        4. Finally delete from priority

        Args:
            priority_id: ID of the priority to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            Exception: If any deletion step fails
        """
        try:
            # Step 1: Delete from measure_area_priority_grant
            query1 = "DELETE FROM measure_area_priority_grant WHERE priority_id = ?"
            self.execute_raw_query(query1, [priority_id])

            # Step 2: Delete from measure_area_priority
            query2 = "DELETE FROM measure_area_priority WHERE priority_id = ?"
            self.execute_raw_query(query2, [priority_id])

            # Step 3: Delete from species_area_priority
            query3 = "DELETE FROM species_area_priority WHERE priority_id = ?"
            self.execute_raw_query(query3, [priority_id])

            # Step 4: Delete from priority
            query4 = "DELETE FROM priority WHERE priority_id = ?"
            self.execute_raw_query(query4, [priority_id])

            return True
        except Exception as e:
            print(f"Error deleting priority {priority_id} with cascade: {e}")
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
