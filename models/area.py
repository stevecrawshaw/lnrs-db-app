"""Area entity model for priority areas."""

import logging

import duckdb
import polars as pl

from config.database import db
from models.base import BaseModel

logger = logging.getLogger(__name__)


class AreaModel(BaseModel):
    """Model for managing area entities."""

    @property
    def table_name(self) -> str:
        return "area"

    @property
    def id_column(self) -> str:
        return "area_id"

    def get_with_relationship_counts(self) -> pl.DataFrame:
        """Get all areas with counts of related entities.

        Returns:
            pl.DataFrame: Areas with relationship counts
        """
        query = """
            SELECT
                a.area_id,
                a.area_name,
                a.area_description,
                a.area_link,
                (SELECT COUNT(DISTINCT measure_id)
                 FROM measure_area_priority
                 WHERE area_id = a.area_id) as measures,
                (SELECT COUNT(DISTINCT priority_id)
                 FROM measure_area_priority
                 WHERE area_id = a.area_id) as priorities,
                (SELECT COUNT(DISTINCT species_id)
                 FROM species_area_priority
                 WHERE area_id = a.area_id) as species,
                (SELECT COUNT(DISTINCT habitat_id)
                 FROM habitat_creation_area
                 WHERE area_id = a.area_id) as creation_habitats,
                (SELECT COUNT(DISTINCT habitat_id)
                 FROM habitat_management_area
                 WHERE area_id = a.area_id) as management_habitats,
                (SELECT COUNT(*)
                 FROM area_funding_schemes
                 WHERE area_id = a.area_id) as funding_schemes
            FROM area a
            ORDER BY a.area_name
        """

        result = self.execute_raw_query(query)
        return result.pl()

    def get_measures(self, area_id: int) -> pl.DataFrame:
        """Get measures linked to this area.

        Args:
            area_id: ID of the area

        Returns:
            pl.DataFrame: Measures linked to this area
        """
        query = """
            SELECT DISTINCT
                m.measure_id,
                m.measure,
                m.concise_measure,
                m.core_supplementary
            FROM measure m
            JOIN measure_area_priority map ON m.measure_id = map.measure_id
            WHERE map.area_id = ?
            ORDER BY m.measure_id
        """

        result = self.execute_raw_query(query, [area_id])
        return result.pl()

    def get_priorities(self, area_id: int) -> pl.DataFrame:
        """Get priorities linked to this area.

        Args:
            area_id: ID of the area

        Returns:
            pl.DataFrame: Priorities linked to this area
        """
        query = """
            SELECT DISTINCT
                p.priority_id,
                p.biodiversity_priority,
                p.simplified_biodiversity_priority,
                p.theme
            FROM priority p
            JOIN measure_area_priority map ON p.priority_id = map.priority_id
            WHERE map.area_id = ?
            ORDER BY p.theme, p.biodiversity_priority
        """

        result = self.execute_raw_query(query, [area_id])
        return result.pl()

    def get_species(self, area_id: int) -> pl.DataFrame:
        """Get species linked to this area.

        Args:
            area_id: ID of the area

        Returns:
            pl.DataFrame: Species linked to this area
        """
        query = """
            SELECT DISTINCT
                s.species_id,
                s.common_name,
                s.linnaean_name,
                s.assemblage,
                s.usage_key
            FROM species s
            JOIN species_area_priority sap ON s.species_id = sap.species_id
            WHERE sap.area_id = ?
            ORDER BY s.common_name
        """

        result = self.execute_raw_query(query, [area_id])
        return result.pl()

    def get_creation_habitats(self, area_id: int) -> pl.DataFrame:
        """Get habitats designated for creation in this area.

        Args:
            area_id: ID of the area

        Returns:
            pl.DataFrame: Habitats for creation
        """
        query = """
            SELECT
                h.habitat_id,
                h.habitat
            FROM habitat h
            JOIN habitat_creation_area hca ON h.habitat_id = hca.habitat_id
            WHERE hca.area_id = ?
            ORDER BY h.habitat
        """

        result = self.execute_raw_query(query, [area_id])
        return result.pl()

    def get_management_habitats(self, area_id: int) -> pl.DataFrame:
        """Get habitats requiring management in this area.

        Args:
            area_id: ID of the area

        Returns:
            pl.DataFrame: Habitats for management
        """
        query = """
            SELECT
                h.habitat_id,
                h.habitat
            FROM habitat h
            JOIN habitat_management_area hma ON h.habitat_id = hma.habitat_id
            WHERE hma.area_id = ?
            ORDER BY h.habitat
        """

        result = self.execute_raw_query(query, [area_id])
        return result.pl()

    def get_funding_schemes(self, area_id: int) -> pl.DataFrame:
        """Get funding schemes available in this area.

        Args:
            area_id: ID of the area

        Returns:
            pl.DataFrame: Funding schemes for this area
        """
        query = """
            SELECT
                id,
                area_name,
                local_funding_schemes
            FROM area_funding_schemes
            WHERE area_id = ?
            ORDER BY area_name
        """

        result = self.execute_raw_query(query, [area_id])
        return result.pl()

    def get_relationship_counts(self, area_id: int) -> dict[str, int]:
        """Get counts of all related entities for an area.

        Args:
            area_id: ID of the area

        Returns:
            dict: Entity name -> count
        """
        measures = self.get_measures(area_id)
        priorities = self.get_priorities(area_id)
        species = self.get_species(area_id)
        creation_habitats = self.get_creation_habitats(area_id)
        management_habitats = self.get_management_habitats(area_id)
        funding_schemes = self.get_funding_schemes(area_id)

        return {
            "measures": len(measures),
            "priorities": len(priorities),
            "species": len(species),
            "creation_habitats": len(creation_habitats),
            "management_habitats": len(management_habitats),
            "funding_schemes": len(funding_schemes),
        }

    def delete_with_cascade(self, area_id: int) -> bool:
        """Delete an area and all its relationships atomically.

        All deletes are executed in a single transaction - either all succeed
        or all are rolled back automatically on failure.

        Cascade order (from CLAUDE.md):
        1. Delete from measure_area_priority_grant where area_id matches
        2. Delete from measure_area_priority where area_id matches
        3. Delete from species_area_priority where area_id matches
        4. Delete from area_funding_schemes where area_id matches
        5. Delete from habitat_creation_area where area_id matches
        6. Delete from habitat_management_area where area_id matches
        7. Finally delete from area

        Args:
            area_id: ID of the area to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            duckdb.Error: If any deletion step fails (all changes rolled back)
        """
        queries = [
            ("DELETE FROM measure_area_priority_grant WHERE area_id = ?", [area_id]),
            ("DELETE FROM measure_area_priority WHERE area_id = ?", [area_id]),
            ("DELETE FROM species_area_priority WHERE area_id = ?", [area_id]),
            ("DELETE FROM area_funding_schemes WHERE area_id = ?", [area_id]),
            ("DELETE FROM habitat_creation_area WHERE area_id = ?", [area_id]),
            ("DELETE FROM habitat_management_area WHERE area_id = ?", [area_id]),
            ("DELETE FROM area WHERE area_id = ?", [area_id]),
        ]

        try:
            db.execute_transaction(queries)
            logger.info(f"Successfully deleted area {area_id} with cascade")
            return True
        except duckdb.Error as e:
            logger.error(f"Failed to delete area {area_id}: {e}", exc_info=True)
            raise


# %%
if __name__ == "__main__":
    """Test the Area model."""
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    print("Testing Area Model\n")

    model = AreaModel()

    # Test count
    print(f"1. Total areas: {model.count()}")

    # Test get with relationship counts
    print("\n2. Areas with relationship counts:")
    areas_with_counts = model.get_with_relationship_counts()
    print(areas_with_counts.head(5))

    # Test get by ID
    print("\n3. Testing get_by_id(1):")
    area = model.get_by_id(1)
    if area:
        print(f"   Area: {area['area_name']}")
        print(f"   Description: {area['area_description'][:80]}...")

    # Test related entities
    print("\n4. Related entities for area 1:")
    counts = model.get_relationship_counts(1)
    for entity, count in counts.items():
        print(f"   {entity.replace('_', ' ').title()}: {count}")

    # Test get measures
    print("\n5. Testing get_measures(1):")
    measures = model.get_measures(1)
    print(f"   Found {len(measures)} measures")
    if len(measures) > 0:
        print(f"   First measure: {measures[0, 'measure'][:60]}...")

    print("\n✓ All Area model tests completed!")
