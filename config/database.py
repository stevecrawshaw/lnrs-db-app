"""Database connection manager for LNRS application.

This module provides a singleton database connection to DuckDB with support for
both local and MotherDuck (cloud) databases. It maintains persistent connections
for TEMP objects like macros.
"""

import os
from pathlib import Path
from typing import Any

import duckdb
from dotenv import load_dotenv

# Try to import streamlit for secrets (only available when running in Streamlit)
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


class DatabaseConnection:
    """Singleton database connection manager.

    Maintains a single persistent connection to either a local DuckDB file
    or MotherDuck cloud database throughout the application lifecycle.
    This ensures TEMP objects (like macros) persist and prevents connection overhead.
    """

    _instance = None
    _connection = None
    _mode = None

    def __new__(cls):
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_database_mode(self) -> str:
        """Determine which database mode to use.

        Priority order:
        1. Environment variable DATABASE_MODE (.env file)
        2. Streamlit secrets (for deployed apps)
        3. Auto-detect based on STREAMLIT_SHARING_MODE
        4. Default to "local"

        Returns:
            str: "local" or "motherduck"
        """
        # Load .env file first
        load_dotenv()

        # Priority 1: Environment variable (includes .env file)
        mode = os.getenv("DATABASE_MODE", "").lower()
        if mode:
            return mode

        # Priority 2: Streamlit secrets
        if HAS_STREAMLIT:
            try:
                secrets_mode = st.secrets.get("DATABASE_MODE", "").lower()
                if secrets_mode:
                    return secrets_mode
            except (KeyError, FileNotFoundError, AttributeError):
                pass

        # Priority 3: Auto-detect Streamlit Cloud
        if os.getenv("STREAMLIT_SHARING_MODE"):
            return "motherduck"

        # Priority 4: Default to local
        return "local"

    def _get_config(self, key: str, default: str = "") -> str:
        """Get configuration value from environment.

        Priority order:
        1. Streamlit secrets
        2. Environment variables
        3. .env file (loaded via python-dotenv)

        Args:
            key: Configuration key name
            default: Default value if key not found

        Returns:
            str: Configuration value
        """
        # Priority 1: Streamlit secrets
        if HAS_STREAMLIT:
            try:
                return st.secrets.get(key, default)
            except (KeyError, FileNotFoundError, AttributeError):
                pass

        # Priority 2 & 3: Environment variables (including .env)
        load_dotenv()  # Load .env file if it exists
        return os.getenv(key, default)

    def _create_local_connection(self) -> duckdb.DuckDBPyConnection:
        """Create connection to local DuckDB file.

        Returns:
            duckdb.DuckDBPyConnection: Local database connection

        Raises:
            FileNotFoundError: If database file doesn't exist
            duckdb.Error: If connection fails
        """
        db_path = Path(__file__).parent.parent / "data" / "lnrs_3nf_o1.duckdb"

        if not db_path.exists():
            raise FileNotFoundError(
                f"Local database file not found: {db_path}\n"
                f"Please ensure the database file exists or switch to MotherDuck mode."
            )

        try:
            connection = duckdb.connect(str(db_path))
            print(f"[OK] Connected to LOCAL database: {db_path}")
            return connection
        except duckdb.Error as e:
            raise duckdb.Error(f"Failed to connect to local database: {e}") from e

    def _create_motherduck_connection(self) -> duckdb.DuckDBPyConnection:
        """Create connection to MotherDuck cloud database.

        Returns:
            duckdb.DuckDBPyConnection: MotherDuck database connection

        Raises:
            ValueError: If token or database name not configured
            duckdb.Error: If connection fails
        """
        token = self._get_config("motherduck_token")
        database_name = self._get_config("database_name", "lnrs_weca")

        if not token:
            raise ValueError(
                "MotherDuck token not configured!\n"
                "Please set 'motherduck_token' in:\n"
                "  - .env file (local development), or\n"
                "  - Streamlit secrets (cloud deployment)"
            )

        try:
            # MotherDuck connection string format: md:database_name?motherduck_token=TOKEN
            connection_string = f"md:{database_name}?motherduck_token={token}"
            connection = duckdb.connect(connection_string)
            print(f"[OK] Connected to MOTHERDUCK database: {database_name}")
            return connection
        except duckdb.Error as e:
            raise duckdb.Error(
                f"Failed to connect to MotherDuck: {e}\n"
                f"Database: {database_name}\n"
                f"Please check your token and database name."
            ) from e

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create the database connection.

        Returns:
            duckdb.DuckDBPyConnection: The database connection

        Raises:
            FileNotFoundError: If local database file doesn't exist
            ValueError: If MotherDuck not properly configured
            duckdb.Error: If connection fails
        """
        if self._connection is None:
            # Determine database mode
            self._mode = self._get_database_mode()

            # Create appropriate connection
            if self._mode == "motherduck":
                self._connection = self._create_motherduck_connection()
            else:
                self._connection = self._create_local_connection()

            # Load macros into the connection
            self._load_macros()

        return self._connection

    def _load_macros(self) -> None:
        """Load custom macros into the database.

        Creates the max_meas() macro for generating new measure IDs.
        Macros are recreated each time to ensure they exist in both
        local and MotherDuck environments.
        """
        if self._connection is None:
            return

        try:
            # Drop if exists to ensure clean state
            self._connection.execute("DROP MACRO IF EXISTS max_meas")

            # Create max_meas() macro for generating new measure IDs
            self._connection.execute(
                "CREATE MACRO max_meas() AS "
                "(SELECT COALESCE(MAX(measure_id), 0) + 1 FROM measure)"
            )
            print("[OK] Macros loaded successfully")
        except duckdb.Error as e:
            print(f"Warning: Failed to load macros: {e}")

    def get_connection_info(self) -> dict[str, Any]:
        """Get information about the current database connection.

        Returns:
            dict: Connection information including mode, status, and database name
        """
        mode = self._mode if self._mode else self._get_database_mode()

        info = {
            "mode": mode,
            "connected": self._connection is not None,
        }

        if mode == "motherduck":
            info["database"] = self._get_config("database_name", "lnrs_weca")
        else:
            db_path = Path(__file__).parent.parent / "data" / "lnrs_3nf_o1.duckdb"
            info["database"] = str(db_path)

        return info

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
            self._mode = None
            print("[OK] Database connection closed")


# Global instance for easy import
db = DatabaseConnection()


# %%
if __name__ == "__main__":
    """Test the database connection manager."""
    print("Testing Database Connection Manager\n")
    print("=" * 60)

    # Show connection info
    print("\n1. Connection Information:")
    info = db.get_connection_info()
    print(f"   Mode: {info['mode'].upper()}")
    print(f"   Database: {info['database']}")
    print(f"   Connected: {info['connected']}")

    # Test connection
    print("\n2. Testing connection...")
    assert db.test_connection(), "Connection test failed"
    print("   ✓ Connection test passed")

    # Test macro loading
    print("\n3. Testing macro loading...")
    conn = db.get_connection()
    result = conn.execute("SELECT max_meas() as next_id").fetchone()
    print(f"   ✓ max_meas() returned: {result[0]}")

    # Test basic query
    print("\n4. Testing basic query...")
    measure_count = db.get_table_count("measure")
    print(f"   ✓ Found {measure_count} measures")

    # Test relational API
    print("\n5. Testing relational API...")
    measures = db.get_table("measure")
    limited_measures = measures.limit(5)
    print(f"   ✓ Retrieved {len(limited_measures.fetchall())} measures using relational API")

    # Test transaction
    print("\n6. Testing transaction...")
    try:
        db.execute_transaction(
            [
                ("SELECT COUNT(*) FROM area", None),
                ("SELECT COUNT(*) FROM priority", None),
            ]
        )
        print("   ✓ Transaction test passed")
    except duckdb.Error as e:
        print(f"   ✗ Transaction test failed: {e}")

    # Display summary
    print("\n7. Database Summary:")
    print(f"   - Measures: {db.get_table_count('measure')}")
    print(f"   - Areas: {db.get_table_count('area')}")
    print(f"   - Priorities: {db.get_table_count('priority')}")
    print(f"   - Species: {db.get_table_count('species')}")
    print(f"   - Grants: {db.get_table_count('grant_table')}")

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
