"""Home page / Dashboard for LNRS Database Manager."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db


# Cached functions for dashboard metrics (5 minute TTL)
@st.cache_data(ttl=300, show_spinner="Loading dashboard data...")
def get_database_counts():
    """Get all database table counts in a single cached call.

    Returns:
        dict: Dictionary with all table counts
    """
    return {
        "measure": db.get_table_count("measure"),
        "area": db.get_table_count("area"),
        "priority": db.get_table_count("priority"),
        "species": db.get_table_count("species"),
        "grant_table": db.get_table_count("grant_table"),
        "measure_area_priority": db.get_table_count("measure_area_priority"),
        "measure_area_priority_grant": db.get_table_count(
            "measure_area_priority_grant"
        ),
        "species_area_priority": db.get_table_count("species_area_priority"),
    }


@st.cache_data(ttl=300)
def get_connection_status():
    """Check database connection status (cached).

    Returns:
        bool: True if connected
    """
    return db.test_connection()


@st.cache_data(ttl=300)
def get_connection_info():
    """Get database connection information (cached).

    Returns:
        dict: Connection info including mode and database name
    """
    return db.get_connection_info()


st.title("🌿 LNRS Database Manager")
st.markdown("### Local Nature Recovery Strategy Database")

# Database health check
st.subheader("Database Status")
col1, col2 = st.columns([1, 3])

with col1:
    if get_connection_status():
        st.success("✓ Connected")
    else:
        st.error("✗ Not Connected")

with col2:
    # Show connection info (mode and database)
    conn_info = get_connection_info()
    mode = conn_info.get("mode", "unknown").upper()
    database = conn_info.get("database", "unknown")

    if mode == "LOCAL":
        # For local mode, show file size
        db_path = Path(project_root) / "data" / "lnrs_3nf_o1.duckdb"
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            st.info(f"MODE: {mode} | Database: `{db_path.name}` ({size_mb:.2f} MB)")
        else:
            st.info(f"MODE: {mode}")
    else:
        # For MotherDuck mode, show database name
        st.info(f"MODE: {mode} | Database: `{database}`")

# Quick stats - Load all counts at once using cached function
st.subheader("Database Summary")

# Create metrics in columns
col1, col2, col3, col4, col5 = st.columns(5)

try:
    # Single cached call for all counts
    counts = get_database_counts()

    with col1:
        st.metric("Measures", f"{counts['measure']:,}")

    with col2:
        st.metric("Areas", f"{counts['area']:,}")

    with col3:
        st.metric("Priorities", f"{counts['priority']:,}")

    with col4:
        st.metric("Species", f"{counts['species']:,}")

    with col5:
        st.metric("Grants", f"{counts['grant_table']:,}")

except Exception as e:
    st.error(f"Error loading database statistics: {e}")

# Relationship stats
st.subheader("Relationship Statistics")

col1, col2, col3 = st.columns(3)

try:
    # Reuse cached counts from above
    counts = get_database_counts()

    with col1:
        st.metric("Measure-Area-Priority Links", f"{counts['measure_area_priority']:,}")

    with col2:
        st.metric("Grant Funding Links", f"{counts['measure_area_priority_grant']:,}")

    with col3:
        st.metric("Species-Area-Priority Links", f"{counts['species_area_priority']:,}")

except Exception as e:
    st.error(f"Error loading relationship statistics: {e}")

# Info section
st.markdown("---")
st.info(
    """
    **About this application:**

    This CRUD application manages the LNRS (Local Nature Recovery Strategy) database,
    which contains biodiversity priorities, areas, species data, and grant information.

    Use the navigation menu on the left to access different sections of the application.
    """
)
