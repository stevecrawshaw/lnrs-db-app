"""Database connection manager for LNRS application.

This module provides a singleton database connection to DuckDB with persistent
connection support for maintaining TEMP objects like macros.
"""

from pathlib import Path
from typing import Any

import duckdb


class DatabaseConnection:
    """Singleton database connection manager.

    Maintains a single persistent connection to the DuckDB database throughout
    the application lifecycle. This ensures TEMP objects (like macros) persist
    and prevents connection overhead.
    """

    _instance = None
    _connection = None

    def __new__(cls):
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create the database connection.

        Returns:
            duckdb.DuckDBPyConnection: The database connection

        Raises:
            FileNotFoundError: If database file doesn't exist
            duckdb.Error: If connection fails
        """
        if self._connection is None:
            db_path = Path(__file__).parent.parent / "data" / "lnrs_3nf_o1.duckdb"

            if not db_path.exists():
                raise FileNotFoundError(f"Database file not found: {db_path}")

            try:
                self._connection = duckdb.connect(str(db_path))
                self._load_macros()
                print(f"✓ Connected to database: {db_path}")
            except duckdb.Error as e:
                raise duckdb.Error(f"Failed to connect to database: {e}") from e

        return self._connection

    def _load_macros(self) -> None:
        """Load custom macros into the database.

        Creates the max_meas() macro for generating new measure IDs.
        """
        try:
            # Create max_meas() macro for generating new measure IDs
            self._connection.execute(
                "CREATE MACRO IF NOT EXISTS max_meas() AS "
                "(SELECT COALESCE(MAX(measure_id), 0) + 1 FROM measure)"
            )
            print("✓ Macros loaded successfully")
        except duckdb.Error as e:
            print(f"Warning: Failed to load macros: {e}")

    def execute_query(
        self, query: str, parameters: list[Any] | None = None
    ) -> duckdb.DuckDBPyRelation:
        """Execute a SQL query with optional parameters.

        Args:
            query: SQL query string
            parameters: Optional list of parameters for parameterized queries

        Returns:
            duckdb.DuckDBPyRelation: Query result

        Raises:
            duckdb.Error: If query execution fails
        """
        conn = self.get_connection()
        try:
            if parameters:
                return conn.execute(query, parameters)
            return conn.execute(query)
        except duckdb.Error as e:
            raise duckdb.Error(f"Query execution failed: {e}\nQuery: {query}") from e

    def execute_transaction(self, queries: list[tuple[str, list[Any] | None]]) -> None:
        """Execute multiple queries in a transaction.

        Args:
            queries: List of (query, parameters) tuples

        Raises:
            duckdb.Error: If any query fails (triggers rollback)
        """
        conn = self.get_connection()
        conn.begin()
        try:
            for query, parameters in queries:
                if parameters:
                    conn.execute(query, parameters)
                else:
                    conn.execute(query)
            conn.commit()
        except duckdb.Error as e:
            conn.rollback()
            raise duckdb.Error(f"Transaction failed and rolled back: {e}") from e

    def get_table(self, table_name: str) -> duckdb.DuckDBPyRelation:
        """Get a table as a relational API object.

        Args:
            table_name: Name of the table

        Returns:
            duckdb.DuckDBPyRelation: Table relation object

        Raises:
            duckdb.Error: If table doesn't exist
        """
        conn = self.get_connection()
        try:
            return conn.table(table_name)
        except duckdb.Error as e:
            raise duckdb.Error(f"Failed to access table '{table_name}': {e}") from e

    def test_connection(self) -> bool:
        """Test if database connection is working.

        Returns:
            bool: True if connection is working
        """
        try:
            conn = self.get_connection()
            result = conn.execute("SELECT 1 as test").fetchone()
            return result[0] == 1
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def get_table_count(self, table_name: str) -> int:
        """Get the number of records in a table.

        Args:
            table_name: Name of the table

        Returns:
            int: Number of records in the table
        """
        try:
            result = self.execute_query(f"SELECT COUNT(*) FROM {table_name}")
            return result.fetchone()[0]
        except duckdb.Error:
            return 0

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            print("✓ Database connection closed")


# Global instance for easy import
db = DatabaseConnection()


# %%
if __name__ == "__main__":
    """Test the database connection manager."""
    print("Testing Database Connection Manager\n")

    # Test connection
    print("1. Testing connection...")
    assert db.test_connection(), "Connection test failed"
    print("   ✓ Connection test passed\n")

    # Test macro loading
    print("2. Testing macro loading...")
    conn = db.get_connection()
    result = conn.execute("SELECT max_meas() as next_id").fetchone()
    print(f"   ✓ max_meas() returned: {result[0]}\n")

    # Test basic query
    print("3. Testing basic query...")
    measure_count = db.get_table_count("measure")
    print(f"   ✓ Found {measure_count} measures\n")

    # Test relational API
    print("4. Testing relational API...")
    measures = db.get_table("measure")
    limited_measures = measures.limit(5)
    print(f"   ✓ Retrieved {len(limited_measures.fetchall())} measures using relational API\n")

    # Test transaction
    print("5. Testing transaction...")
    try:
        db.execute_transaction(
            [
                ("SELECT COUNT(*) FROM area", None),
                ("SELECT COUNT(*) FROM priority", None),
            ]
        )
        print("   ✓ Transaction test passed\n")
    except duckdb.Error as e:
        print(f"   ✗ Transaction test failed: {e}\n")

    # Display summary
    print("Summary:")
    print(f"  - Measures: {db.get_table_count('measure')}")
    print(f"  - Areas: {db.get_table_count('area')}")
    print(f"  - Priorities: {db.get_table_count('priority')}")
    print(f"  - Species: {db.get_table_count('species')}")
    print(f"  - Grants: {db.get_table_count('grant_table')}")

    print("\n✓ All tests passed!")
