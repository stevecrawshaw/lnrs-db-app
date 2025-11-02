"""Home page / Dashboard for LNRS Database Manager."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db

st.title("🌿 LNRS Database Manager")
st.markdown("### Local Nature Recovery Strategy Database")

# Database health check
st.subheader("Database Status")
col1, col2 = st.columns([1, 3])

with col1:
    if db.test_connection():
        st.success("✓ Connected")
    else:
        st.error("✗ Not Connected")

with col2:
    db_path = Path(project_root) / "data" / "lnrs_3nf_o1.duckdb"
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        st.info(f"Database: `{db_path.name}` ({size_mb:.2f} MB)")

# Quick stats
st.subheader("Database Summary")

# Create metrics in columns
col1, col2, col3, col4, col5 = st.columns(5)

try:
    with col1:
        measure_count = db.get_table_count("measure")
        st.metric("Measures", f"{measure_count:,}")

    with col2:
        area_count = db.get_table_count("area")
        st.metric("Areas", f"{area_count:,}")

    with col3:
        priority_count = db.get_table_count("priority")
        st.metric("Priorities", f"{priority_count:,}")

    with col4:
        species_count = db.get_table_count("species")
        st.metric("Species", f"{species_count:,}")

    with col5:
        grant_count = db.get_table_count("grant_table")
        st.metric("Grants", f"{grant_count:,}")

except Exception as e:
    st.error(f"Error loading database statistics: {e}")

# Relationship stats
st.subheader("Relationship Statistics")

col1, col2, col3 = st.columns(3)

try:
    with col1:
        map_count = db.get_table_count("measure_area_priority")
        st.metric("Measure-Area-Priority Links", f"{map_count:,}")

    with col2:
        grant_links = db.get_table_count("measure_area_priority_grant")
        st.metric("Grant Funding Links", f"{grant_links:,}")

    with col3:
        species_links = db.get_table_count("species_area_priority")
        st.metric("Species-Area-Priority Links", f"{species_links:,}")

except Exception as e:
    st.error(f"Error loading relationship statistics: {e}")

# Recent activity / Quick actions
st.subheader("Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### View Data")
    st.markdown("- Browse Measures")
    st.markdown("- Explore Areas")
    st.markdown("- View Priorities")

with col2:
    st.markdown("#### Add New")
    st.markdown("- Create Measure")
    st.markdown("- Add Area")
    st.markdown("- Define Priority")

with col3:
    st.markdown("#### Reports")
    st.markdown("- Export Data")
    st.markdown("- View Statistics")
    st.markdown("- Generate Reports")

# Info section
st.markdown("---")
st.info(
    """
    **About this application:**

    This CRUD application manages the LNRS (Local Nature Recovery Strategy) database,
    which contains biodiversity measures, priority areas, species data, and grant information.

    Use the navigation menu on the left to access different sections of the application.
    """
)
