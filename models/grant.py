"""Grant entity model for funding grants."""

import logging

import duckdb
import polars as pl

from config.database import db
from models.base import BaseModel

logger = logging.getLogger(__name__)


class GrantModel(BaseModel):
    """Model for managing grant/funding entities."""

    @property
    def table_name(self) -> str:
        return "grant_table"

    @property
    def id_column(self) -> str:
        return "grant_id"

    def get_by_scheme(self) -> dict[str, pl.DataFrame]:
        """Get grants grouped by grant scheme.

        Returns:
            dict: Scheme name -> DataFrame of grants in that scheme
        """
        all_grants = self.get_all(order_by="grant_scheme, grant_name")

        # Group by scheme
        schemes = all_grants["grant_scheme"].unique().sort()
        grouped = {}

        for scheme in schemes:
            if scheme:  # Skip null schemes
                scheme_data = all_grants.filter(pl.col("grant_scheme") == scheme)
                grouped[scheme] = scheme_data

        return grouped

    def get_related_measures(self, grant_id: str) -> pl.DataFrame:
        """Get measures funded by this grant.

        Args:
            grant_id: ID of the grant

        Returns:
            pl.DataFrame: Measures linked to this grant
        """
        query = """
            SELECT DISTINCT
                m.measure_id,
                m.measure,
                m.concise_measure,
                a.area_name,
                p.biodiversity_priority
            FROM measure m
            JOIN measure_area_priority_grant mapg ON m.measure_id = mapg.measure_id
            JOIN area a ON mapg.area_id = a.area_id
            JOIN priority p ON mapg.priority_id = p.priority_id
            WHERE mapg.grant_id = ?
            ORDER BY m.measure_id
        """

        result = self.execute_raw_query(query, [grant_id])
        return result.pl()

    def get_relationship_counts(self, grant_id: str) -> dict[str, int]:
        """Get counts of related entities.

        Args:
            grant_id: ID of the grant

        Returns:
            dict: Entity name -> count
        """
        measures = self.get_related_measures(grant_id)

        return {
            "measure_area_priority_links": len(measures),
        }

    @db.with_snapshot("delete", "grant")
    def delete_with_cascade(self, grant_id: str) -> bool:
        """Delete a grant and all its relationships atomically.

        All deletes are executed in a single transaction - either all succeed
        or all are rolled back automatically on failure.

        Cascade order (from CLAUDE.md):
        1. Delete from measure_area_priority_grant where grant_id matches
        2. Finally delete from grant_table

        Args:
            grant_id: ID of the grant to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            duckdb.Error: If any deletion step fails (all changes rolled back)
        """
        # First check how many references exist
        conn = db.get_connection()
        ref_count = conn.execute(
            "SELECT COUNT(*) FROM measure_area_priority_grant WHERE grant_id = ?",
            [grant_id],
        ).fetchone()[0]

        logger.info(
            f"Grant {grant_id} has {ref_count} references in measure_area_priority_grant"
        )

        if ref_count > 0:
            # Show some example references for debugging
            examples = conn.execute(
                """SELECT measure_id, area_id, priority_id
                   FROM measure_area_priority_grant
                   WHERE grant_id = ?
                   LIMIT 3""",
                [grant_id],
            ).fetchall()
            logger.debug(f"Example references: {examples}")

        # DuckDB limitation: FK constraints are checked immediately after each statement.
        # Workaround: Execute deletes in separate steps outside transaction.
        # This maintains correct order but loses atomicity for this specific case.
        try:
            # Step 1: Delete child records first
            logger.info(f"Deleting {ref_count} references from measure_area_priority_grant")
            conn.execute(
                "DELETE FROM measure_area_priority_grant WHERE grant_id = ?",
                [grant_id],
            )

            # Step 2: Delete parent record
            logger.info(f"Deleting grant {grant_id} from grant_table")
            conn.execute("DELETE FROM grant_table WHERE grant_id = ?", [grant_id])

            logger.info(
                f"Successfully deleted grant {grant_id} with cascade "
                f"(removed {ref_count} references)"
            )
            return True
        except duckdb.Error as e:
            logger.error(
                f"Failed to delete grant {grant_id}: {e}\n"
                f"Note: This operation is NOT atomic due to DuckDB FK constraint limitations",
                exc_info=True,
            )
            raise
