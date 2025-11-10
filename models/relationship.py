"""Relationship model for managing bridge table relationships."""

import logging

import duckdb
import polars as pl

from config.database import db
from models.base import BaseModel

logger = logging.getLogger(__name__)


class RelationshipModel(BaseModel):
    """Model for managing many-to-many relationship bridge tables."""

    @property
    def table_name(self) -> str:
        """Not used for relationship model as it handles multiple tables."""
        return ""

    @property
    def id_column(self) -> str:
        """Not used for relationship model."""
        return ""

    # ============================================================================
    # MEASURE-AREA-PRIORITY RELATIONSHIPS
    # ============================================================================

    def get_all_measure_area_priority(self) -> pl.DataFrame:
        """Get all measure-area-priority relationships with names.

        Returns:
            pl.DataFrame: All links with measure, area, and priority names
        """
        query = """
            SELECT
                map.measure_id,
                m.concise_measure,
                m.measure,
                map.area_id,
                a.area_name,
                map.priority_id,
                p.simplified_biodiversity_priority,
                p.biodiversity_priority,
                p.theme
            FROM measure_area_priority map
            JOIN measure m ON map.measure_id = m.measure_id
            JOIN area a ON map.area_id = a.area_id
            JOIN priority p ON map.priority_id = p.priority_id
            ORDER BY p.theme, a.area_name, m.measure_id
        """

        result = self.execute_raw_query(query)
        return result.pl()

    def link_exists_measure_area_priority(
        self, measure_id: int, area_id: int, priority_id: int
    ) -> bool:
        """Check if a measure-area-priority link already exists.

        Args:
            measure_id: ID of the measure
            area_id: ID of the area
            priority_id: ID of the priority

        Returns:
            bool: True if link exists, False otherwise
        """
        query = """
            SELECT COUNT(*) as count
            FROM measure_area_priority
            WHERE measure_id = ? AND area_id = ? AND priority_id = ?
        """

        result = self.execute_raw_query(query, [measure_id, area_id, priority_id])
        count = result.fetchone()[0]
        return count > 0

    def create_measure_area_priority_link(
        self, measure_id: int, area_id: int, priority_id: int
    ) -> bool:
        """Create a new measure-area-priority link.

        Args:
            measure_id: ID of the measure
            area_id: ID of the area
            priority_id: ID of the priority

        Returns:
            bool: True if link was created successfully

        Raises:
            ValueError: If link already exists
            duckdb.Error: If foreign keys are invalid or creation fails
        """
        # Check if link already exists
        if self.link_exists_measure_area_priority(measure_id, area_id, priority_id):
            error_msg = f"Link already exists: M{measure_id}-A{area_id}-P{priority_id}"
            logger.warning(error_msg)
            raise ValueError(error_msg)

        # Create the link
        query = """
            INSERT INTO measure_area_priority (measure_id, area_id, priority_id)
            VALUES (?, ?, ?)
        """

        try:
            self.execute_raw_query(query, [measure_id, area_id, priority_id])
            logger.info(f"Created MAP link: M{measure_id}-A{area_id}-P{priority_id}")
            return True
        except duckdb.Error as e:
            logger.error(
                f"Failed to create MAP link M{measure_id}-A{area_id}-P{priority_id}: {e}",
                exc_info=True,
            )
            raise

    def delete_measure_area_priority_link(
        self, measure_id: int, area_id: int, priority_id: int
    ) -> bool:
        """Delete a measure-area-priority link and cascade to grants.

        NOTE: This operation is NOT atomic due to DuckDB FK constraint limitations.
        DuckDB checks FK constraints immediately after each statement, even within
        transactions. This prevents atomic deletion when child tables reference
        the parent table.

        This will also delete any grants linked to this measure-area-priority
        combination from measure_area_priority_grant.

        Deletions are executed sequentially:
        1. Delete from measure_area_priority_grant (child)
        2. Delete from measure_area_priority (parent)

        Each step is committed immediately. If step 2 fails, step 1 is already committed.

        Args:
            measure_id: ID of the measure
            area_id: ID of the area
            priority_id: ID of the priority

        Returns:
            bool: True if link was deleted successfully

        Raises:
            duckdb.Error: If deletion fails
        """
        conn = db.get_connection()

        # Get grant count for logging
        grant_count = conn.execute(
            """SELECT COUNT(*) FROM measure_area_priority_grant
               WHERE measure_id = ? AND area_id = ? AND priority_id = ?""",
            [measure_id, area_id, priority_id],
        ).fetchone()[0]

        logger.info(
            f"Deleting MAP link M{measure_id}-A{area_id}-P{priority_id} "
            f"with {grant_count} grants"
        )

        try:
            # Step 1: Delete from measure_area_priority_grant (child - must come first)
            logger.debug(f"Step 1/2: Deleting {grant_count} grants")
            conn.execute(
                "DELETE FROM measure_area_priority_grant WHERE measure_id = ? AND area_id = ? AND priority_id = ?",
                [measure_id, area_id, priority_id],
            )

            # Step 2: Delete from measure_area_priority (parent - after grants)
            logger.debug(f"Step 2/2: Deleting MAP link")
            conn.execute(
                "DELETE FROM measure_area_priority WHERE measure_id = ? AND area_id = ? AND priority_id = ?",
                [measure_id, area_id, priority_id],
            )

            logger.info(
                f"Successfully deleted MAP link M{measure_id}-A{area_id}-P{priority_id} "
                f"({grant_count} grants cascaded)"
            )
            return True
        except duckdb.Error as e:
            logger.error(
                f"Failed to delete MAP link M{measure_id}-A{area_id}-P{priority_id}: {e}\n"
                f"Note: This operation is NOT atomic due to DuckDB FK constraint limitations. "
                f"Some deletions may have succeeded before this error.",
                exc_info=True,
            )
            raise

    def get_areas_for_measure(self, measure_id: int) -> pl.DataFrame:
        """Get all area-priority combinations for a measure.

        Args:
            measure_id: ID of the measure

        Returns:
            pl.DataFrame: Areas and priorities linked to this measure
        """
        query = """
            SELECT
                map.area_id,
                a.area_name,
                map.priority_id,
                p.simplified_biodiversity_priority,
                p.biodiversity_priority,
                p.theme
            FROM measure_area_priority map
            JOIN area a ON map.area_id = a.area_id
            JOIN priority p ON map.priority_id = p.priority_id
            WHERE map.measure_id = ?
            ORDER BY p.theme, a.area_name
        """

        result = self.execute_raw_query(query, [measure_id])
        return result.pl()

    def get_measures_for_area(self, area_id: int) -> pl.DataFrame:
        """Get all measures linked to an area.

        Args:
            area_id: ID of the area

        Returns:
            pl.DataFrame: Measures linked to this area with their priorities
        """
        query = """
            SELECT DISTINCT
                map.measure_id,
                m.concise_measure,
                m.measure,
                m.core_supplementary
            FROM measure_area_priority map
            JOIN measure m ON map.measure_id = m.measure_id
            WHERE map.area_id = ?
            ORDER BY m.measure_id
        """

        result = self.execute_raw_query(query, [area_id])
        return result.pl()

    def get_measures_for_priority(self, priority_id: int) -> pl.DataFrame:
        """Get all measures linked to a priority.

        Args:
            priority_id: ID of the priority

        Returns:
            pl.DataFrame: Measures linked to this priority with their areas
        """
        query = """
            SELECT DISTINCT
                map.measure_id,
                m.concise_measure,
                m.measure,
                m.core_supplementary
            FROM measure_area_priority map
            JOIN measure m ON map.measure_id = m.measure_id
            WHERE map.priority_id = ?
            ORDER BY m.measure_id
        """

        result = self.execute_raw_query(query, [priority_id])
        return result.pl()

    # ============================================================================
    # MEASURE-AREA-PRIORITY-GRANT RELATIONSHIPS
    # ============================================================================

    def get_all_measure_area_priority_grants(self) -> pl.DataFrame:
        """Get all grant-funded measure-area-priority relationships.

        Returns:
            pl.DataFrame: All grant-funded links with full details
        """
        query = """
            SELECT
                mapg.measure_id,
                m.concise_measure,
                mapg.area_id,
                a.area_name,
                mapg.priority_id,
                p.simplified_biodiversity_priority,
                p.theme,
                mapg.grant_id,
                g.grant_name,
                g.grant_scheme,
                g.url
            FROM measure_area_priority_grant mapg
            JOIN measure m ON mapg.measure_id = m.measure_id
            JOIN area a ON mapg.area_id = a.area_id
            JOIN priority p ON mapg.priority_id = p.priority_id
            JOIN grant_table g ON mapg.grant_id = g.grant_id
            ORDER BY g.grant_scheme, p.theme, a.area_name
        """

        result = self.execute_raw_query(query)
        return result.pl()

    def add_grant_to_link(
        self, measure_id: int, area_id: int, priority_id: int, grant_id: int
    ) -> bool:
        """Add grant funding to an existing measure-area-priority link.

        Args:
            measure_id: ID of the measure
            area_id: ID of the area
            priority_id: ID of the priority
            grant_id: ID of the grant

        Returns:
            bool: True if grant was added successfully

        Raises:
            Exception: If measure-area-priority link doesn't exist or grant add fails
        """
        # Verify the base link exists
        if not self.link_exists_measure_area_priority(measure_id, area_id, priority_id):
            raise ValueError(
                f"Measure-area-priority link does not exist: "
                f"measure_id={measure_id}, area_id={area_id}, priority_id={priority_id}"
            )

        # Check if grant already linked to this combination
        query_check = """
            SELECT COUNT(*) as count
            FROM measure_area_priority_grant
            WHERE measure_id = ? AND area_id = ? AND priority_id = ? AND grant_id = ?
        """
        result = self.execute_raw_query(
            query_check, [measure_id, area_id, priority_id, grant_id]
        )
        if result.fetchone()[0] > 0:
            raise ValueError("Grant already linked to this measure-area-priority combination")

        # Add the grant
        query = """
            INSERT INTO measure_area_priority_grant (measure_id, area_id, priority_id, grant_id)
            VALUES (?, ?, ?, ?)
        """

        try:
            self.execute_raw_query(query, [measure_id, area_id, priority_id, grant_id])
            return True
        except Exception as e:
            logger.error(f"Failed to add grant to MAP link: {e}", exc_info=True)
            raise

    def remove_grant_from_link(
        self, measure_id: int, area_id: int, priority_id: int, grant_id: int
    ) -> bool:
        """Remove grant funding from a measure-area-priority link.

        Args:
            measure_id: ID of the measure
            area_id: ID of the area
            priority_id: ID of the priority
            grant_id: ID of the grant

        Returns:
            bool: True if grant was removed successfully
        """
        query = """
            DELETE FROM measure_area_priority_grant
            WHERE measure_id = ? AND area_id = ? AND priority_id = ? AND grant_id = ?
        """

        try:
            self.execute_raw_query(query, [measure_id, area_id, priority_id, grant_id])
            return True
        except Exception as e:
            logger.error(f"Failed to remove grant from MAP link: {e}", exc_info=True)
            raise

    def get_unfunded_measure_area_priority_links(self) -> pl.DataFrame:
        """Get measure-area-priority links that have no grant funding.

        Returns:
            pl.DataFrame: Links without any grants attached
        """
        query = """
            SELECT
                map.measure_id,
                m.concise_measure,
                map.area_id,
                a.area_name,
                map.priority_id,
                p.simplified_biodiversity_priority,
                p.theme
            FROM measure_area_priority map
            JOIN measure m ON map.measure_id = m.measure_id
            JOIN area a ON map.area_id = a.area_id
            JOIN priority p ON map.priority_id = p.priority_id
            LEFT JOIN measure_area_priority_grant mapg
                ON map.measure_id = mapg.measure_id
                AND map.area_id = mapg.area_id
                AND map.priority_id = mapg.priority_id
            WHERE mapg.grant_id IS NULL
            ORDER BY p.theme, a.area_name, m.measure_id
        """

        result = self.execute_raw_query(query)
        return result.pl()

    # ============================================================================
    # SPECIES-AREA-PRIORITY RELATIONSHIPS
    # ============================================================================

    def get_all_species_area_priority(self) -> pl.DataFrame:
        """Get all species-area-priority relationships.

        Returns:
            pl.DataFrame: All species-area-priority links with full details
        """
        query = """
            SELECT
                sap.species_id,
                s.common_name,
                s.linnaean_name,
                s.assemblage,
                s.taxa,
                s.image_url,
                sap.area_id,
                a.area_name,
                sap.priority_id,
                p.simplified_biodiversity_priority,
                p.theme
            FROM species_area_priority sap
            JOIN species s ON sap.species_id = s.species_id
            JOIN area a ON sap.area_id = a.area_id
            JOIN priority p ON sap.priority_id = p.priority_id
            ORDER BY s.common_name, p.theme, a.area_name
        """

        result = self.execute_raw_query(query)
        return result.pl()

    def create_species_area_priority_link(
        self, species_id: int, area_id: int, priority_id: int
    ) -> bool:
        """Create a new species-area-priority link.

        Args:
            species_id: ID of the species
            area_id: ID of the area
            priority_id: ID of the priority

        Returns:
            bool: True if link was created successfully

        Raises:
            ValueError: If link already exists
            duckdb.Error: If creation fails
        """
        # Check if link already exists
        query_check = """
            SELECT COUNT(*) as count
            FROM species_area_priority
            WHERE species_id = ? AND area_id = ? AND priority_id = ?
        """
        result = self.execute_raw_query(query_check, [species_id, area_id, priority_id])
        if result.fetchone()[0] > 0:
            error_msg = f"Link already exists: S{species_id}-A{area_id}-P{priority_id}"
            logger.warning(error_msg)
            raise ValueError(error_msg)

        # Create the link
        query = """
            INSERT INTO species_area_priority (species_id, area_id, priority_id)
            VALUES (?, ?, ?)
        """

        try:
            self.execute_raw_query(query, [species_id, area_id, priority_id])
            logger.info(f"Created SAP link: S{species_id}-A{area_id}-P{priority_id}")
            return True
        except duckdb.Error as e:
            logger.error(
                f"Failed to create SAP link S{species_id}-A{area_id}-P{priority_id}: {e}",
                exc_info=True,
            )
            raise

    def delete_species_area_priority_link(
        self, species_id: int, area_id: int, priority_id: int
    ) -> bool:
        """Delete a species-area-priority link.

        Args:
            species_id: ID of the species
            area_id: ID of the area
            priority_id: ID of the priority

        Returns:
            bool: True if link was deleted successfully
        """
        query = """
            DELETE FROM species_area_priority
            WHERE species_id = ? AND area_id = ? AND priority_id = ?
        """

        try:
            self.execute_raw_query(query, [species_id, area_id, priority_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete SAP link: {e}", exc_info=True)
            raise

    # ============================================================================
    # HABITAT-AREA RELATIONSHIPS
    # ============================================================================

    def get_all_habitat_creation_areas(self) -> pl.DataFrame:
        """Get all habitat-creation-area relationships.

        Returns:
            pl.DataFrame: All habitat creation links
        """
        query = """
            SELECT
                hca.habitat_id,
                h.habitat,
                hca.area_id,
                a.area_name
            FROM habitat_creation_area hca
            JOIN habitat h ON hca.habitat_id = h.habitat_id
            JOIN area a ON hca.area_id = a.area_id
            ORDER BY h.habitat, a.area_name
        """

        result = self.execute_raw_query(query)
        return result.pl()

    def get_all_habitat_management_areas(self) -> pl.DataFrame:
        """Get all habitat-management-area relationships.

        Returns:
            pl.DataFrame: All habitat management links
        """
        query = """
            SELECT
                hma.habitat_id,
                h.habitat,
                hma.area_id,
                a.area_name
            FROM habitat_management_area hma
            JOIN habitat h ON hma.habitat_id = h.habitat_id
            JOIN area a ON hma.area_id = a.area_id
            ORDER BY h.habitat, a.area_name
        """

        result = self.execute_raw_query(query)
        return result.pl()

    def create_habitat_creation_link(self, habitat_id: int, area_id: int) -> bool:
        """Link a habitat to an area for creation.

        Args:
            habitat_id: ID of the habitat
            area_id: ID of the area

        Returns:
            bool: True if link was created successfully

        Raises:
            Exception: If link already exists or creation fails
        """
        # Check if link already exists
        query_check = """
            SELECT COUNT(*) as count
            FROM habitat_creation_area
            WHERE habitat_id = ? AND area_id = ?
        """
        result = self.execute_raw_query(query_check, [habitat_id, area_id])
        if result.fetchone()[0] > 0:
            raise ValueError(
                f"Habitat creation link already exists: "
                f"habitat_id={habitat_id}, area_id={area_id}"
            )

        # Create the link
        query = """
            INSERT INTO habitat_creation_area (habitat_id, area_id)
            VALUES (?, ?)
        """

        try:
            self.execute_raw_query(query, [habitat_id, area_id])
            return True
        except Exception as e:
            logger.error(f"Failed to create habitat creation link: {e}", exc_info=True)
            raise

    def create_habitat_management_link(self, habitat_id: int, area_id: int) -> bool:
        """Link a habitat to an area for management.

        Args:
            habitat_id: ID of the habitat
            area_id: ID of the area

        Returns:
            bool: True if link was created successfully

        Raises:
            Exception: If link already exists or creation fails
        """
        # Check if link already exists
        query_check = """
            SELECT COUNT(*) as count
            FROM habitat_management_area
            WHERE habitat_id = ? AND area_id = ?
        """
        result = self.execute_raw_query(query_check, [habitat_id, area_id])
        if result.fetchone()[0] > 0:
            raise ValueError(
                f"Habitat management link already exists: "
                f"habitat_id={habitat_id}, area_id={area_id}"
            )

        # Create the link
        query = """
            INSERT INTO habitat_management_area (habitat_id, area_id)
            VALUES (?, ?)
        """

        try:
            self.execute_raw_query(query, [habitat_id, area_id])
            return True
        except Exception as e:
            logger.error(f"Failed to create habitat management link: {e}", exc_info=True)
            raise

    def delete_habitat_creation_link(self, habitat_id: int, area_id: int) -> bool:
        """Delete a habitat-creation-area link.

        Args:
            habitat_id: ID of the habitat
            area_id: ID of the area

        Returns:
            bool: True if link was deleted successfully
        """
        query = """
            DELETE FROM habitat_creation_area
            WHERE habitat_id = ? AND area_id = ?
        """

        try:
            self.execute_raw_query(query, [habitat_id, area_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete habitat creation link: {e}", exc_info=True)
            raise

    def delete_habitat_management_link(self, habitat_id: int, area_id: int) -> bool:
        """Delete a habitat-management-area link.

        Args:
            habitat_id: ID of the habitat
            area_id: ID of the area

        Returns:
            bool: True if link was deleted successfully
        """
        query = """
            DELETE FROM habitat_management_area
            WHERE habitat_id = ? AND area_id = ?
        """

        try:
            self.execute_raw_query(query, [habitat_id, area_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete habitat management link: {e}", exc_info=True)
            raise

    # ============================================================================
    # BULK OPERATIONS
    # ============================================================================

    def bulk_create_measure_area_priority_links(
        self, measure_ids: list[int], area_ids: list[int], priority_ids: list[int]
    ) -> tuple[int, list[str]]:
        """Create multiple measure-area-priority links atomically (Cartesian product).

        All links are created in a single transaction - either all succeed or all fail.
        Links that already exist are skipped.

        Args:
            measure_ids: List of measure IDs
            area_ids: List of area IDs
            priority_ids: List of priority IDs

        Returns:
            tuple: (number of links created, list of skipped/error messages)

        Raises:
            duckdb.Error: If transaction fails (all changes rolled back)
        """
        queries = []
        skipped = []

        # Generate all combinations (Cartesian product)
        for measure_id in measure_ids:
            for area_id in area_ids:
                for priority_id in priority_ids:
                    # Check if link already exists
                    if self.link_exists_measure_area_priority(
                        measure_id, area_id, priority_id
                    ):
                        skipped.append(
                            f"Link already exists: M{measure_id}-A{area_id}-P{priority_id}"
                        )
                    else:
                        queries.append(
                            (
                                "INSERT INTO measure_area_priority (measure_id, area_id, priority_id) VALUES (?, ?, ?)",
                                [measure_id, area_id, priority_id],
                            )
                        )

        if not queries:
            logger.info("No new MAP links to create (all already exist)")
            return 0, skipped

        try:
            db.execute_transaction(queries)
            logger.info(
                f"Successfully created {len(queries)} MAP links in bulk "
                f"({len(skipped)} skipped as duplicates)"
            )
            return len(queries), skipped
        except duckdb.Error as e:
            logger.error(
                f"Failed to bulk create MAP links: {e}. Transaction rolled back.",
                exc_info=True,
            )
            raise

    # ============================================================================
    # VIEW EXPORTS
    # ============================================================================

    def get_apmg_slim_view(self) -> pl.DataFrame:
        """Get all data from apmg_slim_vw (Area-Priority-Measure-Grant slim view).

        This view contains the core relationships between areas, priorities, measures,
        and grants in a denormalized format suitable for export and reporting.

        Returns:
            pl.DataFrame: All data from the apmg_slim_vw view
        """
        query = """
            SELECT
                core_supplementary,
                measure_type,
                stakeholder,
                area_name,
                area_id,
                grant_id,
                priority_id,
                biodiversity_priority,
                measure,
                concise_measure,
                measure_id,
                link_to_further_guidance,
                grant_name,
                url
            FROM apmg_slim_vw
            ORDER BY area_name, biodiversity_priority, measure_id
        """

        result = self.execute_raw_query(query)
        return result.pl()


# %%
if __name__ == "__main__":
    """Test the Relationship model."""
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    print("Testing Relationship Model\n")

    model = RelationshipModel()

    # Test measure-area-priority
    print("1. Testing measure-area-priority links:")
    map_links = model.get_all_measure_area_priority()
    print(f"   Total measure-area-priority links: {len(map_links)}")
    if len(map_links) > 0:
        print("   First 3 links:")
        print(map_links.select([
            "measure_id", "concise_measure", "area_name",
            "simplified_biodiversity_priority", "theme"
        ]).head(3))

    # Test unfunded links
    print("\n2. Testing unfunded measure-area-priority links:")
    unfunded = model.get_unfunded_measure_area_priority_links()
    print(f"   Total unfunded links: {len(unfunded)}")

    # Test grant-funded links
    print("\n3. Testing grant-funded measure-area-priority links:")
    grant_links = model.get_all_measure_area_priority_grants()
    print(f"   Total grant-funded links: {len(grant_links)}")

    # Test species-area-priority
    print("\n4. Testing species-area-priority links:")
    species_links = model.get_all_species_area_priority()
    print(f"   Total species-area-priority links: {len(species_links)}")

    # Test habitat links
    print("\n5. Testing habitat-creation-area links:")
    habitat_creation = model.get_all_habitat_creation_areas()
    print(f"   Total habitat creation links: {len(habitat_creation)}")

    print("\n6. Testing habitat-management-area links:")
    habitat_management = model.get_all_habitat_management_areas()
    print(f"   Total habitat management links: {len(habitat_management)}")

    print("\n✓ All Relationship model tests completed!")
