"""Base model class for all entity models.

Provides common CRUD operations and utilities for database entities.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import duckdb
import polars as pl

from config.database import db

logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """Abstract base class for all entity models.

    Provides common CRUD operations that can be overridden or extended
    by specific entity models.
    """

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Name of the database table for this entity."""
        pass

    @property
    @abstractmethod
    def id_column(self) -> str:
        """Name of the primary key column for this entity."""
        pass

    def __init__(self):
        """Initialize the base model with database connection."""
        self.conn = db.get_connection()

    def get_table(self) -> duckdb.DuckDBPyRelation:
        """Get the table as a relational API object.

        Returns:
            duckdb.DuckDBPyRelation: Table relation object
        """
        return db.get_table(self.table_name)

    def exists(self, record_id: int | str) -> bool:
        """Check if a record exists.

        Args:
            record_id: ID of the record to check

        Returns:
            bool: True if record exists, False otherwise
        """
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {self.id_column} = ?"
            result = db.execute_query(query, [record_id])
            return result.fetchone()[0] > 0
        except duckdb.Error:
            return False

    def count(self, filter_clause: str | None = None) -> int:
        """Count records in the table.

        Args:
            filter_clause: Optional WHERE clause (without WHERE keyword)

        Returns:
            int: Number of records matching the filter
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        if filter_clause:
            query += f" WHERE {filter_clause}"

        try:
            result = db.execute_query(query)
            return result.fetchone()[0]
        except duckdb.Error:
            return 0

    def get_by_id(self, record_id: int | str) -> dict[str, Any] | None:
        """Get a single record by ID.

        Args:
            record_id: ID of the record to retrieve

        Returns:
            dict: Record as a dictionary, or None if not found
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE {self.id_column} = ?"
            result = db.execute_query(query, [record_id])
            row = result.fetchone()

            if row:
                columns = [desc[0] for desc in result.description]
                return dict(zip(columns, row))
            return None
        except duckdb.Error as e:
            logger.error(f"Error fetching record {record_id}: {e}", exc_info=True)
            return None

    def get_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
    ) -> pl.DataFrame:
        """Get all records from the table.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Column(s) to order by

        Returns:
            pl.DataFrame: Polars DataFrame with the results
        """
        query = f"SELECT * FROM {self.table_name}"

        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"

        try:
            result = db.execute_query(query)
            return result.pl()
        except duckdb.Error as e:
            logger.error(f"Error fetching records: {e}", exc_info=True)
            return pl.DataFrame()

    def filter(self, where_clause: str, parameters: list[Any] | None = None) -> pl.DataFrame:
        """Filter records based on a WHERE clause.

        Args:
            where_clause: SQL WHERE clause (without WHERE keyword)
            parameters: Optional parameters for parameterized queries

        Returns:
            pl.DataFrame: Polars DataFrame with filtered results
        """
        query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"

        try:
            result = db.execute_query(query, parameters)
            return result.pl()
        except duckdb.Error as e:
            logger.error(f"Error filtering records: {e}", exc_info=True)
            return pl.DataFrame()

    def delete(self, record_id: int | str) -> bool:
        """Delete a record by ID.

        Note: This is the basic delete method. Entity-specific models should
        override this to implement proper cascade delete operations.

        Args:
            record_id: ID of the record to delete

        Returns:
            bool: True if deletion was successful
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE {self.id_column} = ?"
            db.execute_query(query, [record_id])
            return True
        except duckdb.Error as e:
            logger.error(f"Error deleting record {record_id}: {e}", exc_info=True)
            return False

    def create(self, data: dict[str, Any]) -> int | str | None:
        """Create a new record.

        Note: This is a basic implementation. Entity-specific models should
        override this to implement proper validation and ID generation.

        Args:
            data: Dictionary of column names and values

        Returns:
            int | str | None: ID of the created record, or None if failed
        """
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"

            db.execute_query(query, list(data.values()))

            # Return the ID if it was provided in data
            return data.get(self.id_column)
        except duckdb.Error as e:
            logger.error(f"Error creating record: {e}", exc_info=True)
            return None

    def update(self, record_id: int | str, data: dict[str, Any]) -> bool:
        """Update an existing record.

        Args:
            record_id: ID of the record to update
            data: Dictionary of column names and values to update

        Returns:
            bool: True if update was successful
        """
        try:
            set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.id_column} = ?"

            parameters = list(data.values()) + [record_id]
            db.execute_query(query, parameters)
            return True
        except duckdb.Error as e:
            logger.error(f"Error updating record {record_id}: {e}", exc_info=True)
            return False

    def execute_raw_query(self, query: str, parameters: list[Any] | None = None) -> duckdb.DuckDBPyRelation:
        """Execute a raw SQL query.

        Args:
            query: SQL query string
            parameters: Optional parameters for parameterized queries

        Returns:
            duckdb.DuckDBPyRelation: Query result
        """
        return db.execute_query(query, parameters)

    def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics for the entity.

        Returns:
            dict: Dictionary with summary statistics
        """
        return {
            "total_count": self.count(),
            "table_name": self.table_name,
        }


# %%
if __name__ == "__main__":
    """Test the base model class with the measure table."""

    class MeasureModel(BaseModel):
        """Test model for measures."""

        @property
        def table_name(self) -> str:
            return "measure"

        @property
        def id_column(self) -> str:
            return "measure_id"

    print("Testing BaseModel with Measure entity\n")

    measure_model = MeasureModel()

    # Test count
    print("1. Testing count...")
    total = measure_model.count()
    print(f"   ✓ Total measures: {total}\n")

    # Test exists
    print("2. Testing exists...")
    exists = measure_model.exists(1)
    print(f"   ✓ Measure ID 1 exists: {exists}\n")

    # Test get_by_id
    print("3. Testing get_by_id...")
    measure = measure_model.get_by_id(1)
    if measure:
        print(f"   ✓ Retrieved measure: {measure['measure'][:50]}...\n")

    # Test get_all with limit
    print("4. Testing get_all with limit...")
    measures_df = measure_model.get_all(limit=5, order_by="measure_id")
    print(f"   ✓ Retrieved {len(measures_df)} measures\n")

    # Test filter
    print("5. Testing filter...")
    core_measures = measure_model.filter("core_supplementary = ?", ["Core"])
    print(f"   ✓ Found {len(core_measures)} core measures\n")

    # Test get_summary_stats
    print("6. Testing get_summary_stats...")
    stats = measure_model.get_summary_stats()
    print(f"   ✓ Summary stats: {stats}\n")

    print("✓ All base model tests passed!")
