"""Species entity model for biodiversity species."""

import logging

import duckdb
import polars as pl

from config.database import db
from models.base import BaseModel

logger = logging.getLogger(__name__)


class SpeciesModel(BaseModel):
    """Model for managing species entities."""

    @property
    def table_name(self) -> str:
        return "species"

    @property
    def id_column(self) -> str:
        return "species_id"

    def get_related_measures(self, species_id: int) -> pl.DataFrame:
        """Get measures linked to this species.

        Args:
            species_id: ID of the species

        Returns:
            pl.DataFrame: Measures linked to this species
        """
        query = """
            SELECT DISTINCT
                m.measure_id,
                m.measure,
                m.concise_measure,
                m.core_supplementary
            FROM measure m
            JOIN measure_has_species mhs ON m.measure_id = mhs.measure_id
            WHERE mhs.species_id = ?
            ORDER BY m.measure_id
        """

        result = self.execute_raw_query(query, [species_id])
        return result.pl()

    def get_related_areas(self, species_id: int) -> pl.DataFrame:
        """Get areas linked to this species.

        Args:
            species_id: ID of the species

        Returns:
            pl.DataFrame: Areas linked to this species
        """
        query = """
            SELECT DISTINCT
                a.area_id,
                a.area_name,
                a.area_description
            FROM area a
            JOIN species_area_priority sap ON a.area_id = sap.area_id
            WHERE sap.species_id = ?
            ORDER BY a.area_name
        """

        result = self.execute_raw_query(query, [species_id])
        return result.pl()

    def get_related_priorities(self, species_id: int) -> pl.DataFrame:
        """Get priorities linked to this species.

        Args:
            species_id: ID of the species

        Returns:
            pl.DataFrame: Priorities linked to this species
        """
        query = """
            SELECT DISTINCT
                p.priority_id,
                p.biodiversity_priority,
                p.simplified_biodiversity_priority,
                p.theme
            FROM priority p
            JOIN species_area_priority sap ON p.priority_id = sap.priority_id
            WHERE sap.species_id = ?
            ORDER BY p.theme, p.biodiversity_priority
        """

        result = self.execute_raw_query(query, [species_id])
        return result.pl()

    def get_relationship_counts(self, species_id: int) -> dict[str, int]:
        """Get counts of all related entities for a species.

        Args:
            species_id: ID of the species

        Returns:
            dict: Entity name -> count
        """
        measures = self.get_related_measures(species_id)
        areas = self.get_related_areas(species_id)
        priorities = self.get_related_priorities(species_id)

        return {
            "measures": len(measures),
            "areas": len(areas),
            "priorities": len(priorities),
        }

    def delete_with_cascade(self, species_id: int) -> bool:
        """Delete a species and all its relationships atomically.

        All deletes are executed in a single transaction - either all succeed
        or all are rolled back automatically on failure.

        Cascade order (from CLAUDE.md):
        1. Delete from species_area_priority where species_id matches
        2. Delete from measure_has_species where species_id matches
        3. Finally delete from species

        Args:
            species_id: ID of the species to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            duckdb.Error: If any deletion step fails (all changes rolled back)
        """
        queries = [
            ("DELETE FROM species_area_priority WHERE species_id = ?", [species_id]),
            ("DELETE FROM measure_has_species WHERE species_id = ?", [species_id]),
            ("DELETE FROM species WHERE species_id = ?", [species_id]),
        ]

        try:
            db.execute_transaction(queries)
            logger.info(f"Successfully deleted species {species_id} with cascade")
            return True
        except duckdb.Error as e:
            logger.error(f"Failed to delete species {species_id}: {e}", exc_info=True)
            raise


# %%
if __name__ == "__main__":
    """Test the Species model."""
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    print("Testing Species Model\n")

    model = SpeciesModel()

    # Test count
    print(f"1. Total species: {model.count()}")

    # Test get all
    print("\n2. First 5 species:")
    all_species = model.get_all(order_by="common_name")
    print(all_species.select([
        "species_id",
        "common_name",
        "linnaean_name",
        "assemblage",
        "taxa"
    ]).head(5))

    # Test get by ID
    print("\n3. Testing get_by_id(1):")
    species = model.get_by_id(1)
    if species:
        print(f"   Common Name: {species['common_name']}")
        print(f"   Scientific: {species['scientific_name']}")
        print(f"   Assemblage: {species['assemblage']}")
        print(f"   Taxa: {species['taxa']}")

    # Test related entities
    print("\n4. Related entities for species 1:")
    counts = model.get_relationship_counts(1)
    for entity, count in counts.items():
        print(f"   {entity.capitalize()}: {count}")

    # Test get measures
    print("\n5. Testing get_related_measures(1):")
    measures = model.get_related_measures(1)
    print(f"   Found {len(measures)} measures")
    if len(measures) > 0:
        print(f"   First measure: {measures[0, 'measure'][:60]}...")

    # Test get areas
    print("\n6. Testing get_related_areas(1):")
    areas = model.get_related_areas(1)
    print(f"   Found {len(areas)} areas")
    if len(areas) > 0:
        print(f"   First area: {areas[0, 'area_name']}")

    print("\n✓ All Species model tests completed!")
