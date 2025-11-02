"""Grant entity model for funding grants."""

import polars as pl

from models.base import BaseModel


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

    def delete_with_cascade(self, grant_id: str) -> bool:
        """Delete a grant and all its relationships following cascade order.

        Cascade order (from CLAUDE.md):
        1. Delete from measure_area_priority_grant where grant_id matches
        2. Finally delete from grant_table

        Args:
            grant_id: ID of the grant to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            Exception: If any deletion step fails
        """
        try:
            # Step 1: Delete from measure_area_priority_grant
            query1 = "DELETE FROM measure_area_priority_grant WHERE grant_id = ?"
            self.execute_raw_query(query1, [grant_id])

            # Step 2: Delete from grant_table
            query2 = "DELETE FROM grant_table WHERE grant_id = ?"
            self.execute_raw_query(query2, [grant_id])

            return True
        except Exception as e:
            print(f"Error deleting grant {grant_id} with cascade: {e}")
            raise
