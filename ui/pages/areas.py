"""Areas page - CRUD operations for priority areas."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db

st.title("🗺️ Areas Management")

st.info(
    """
    **Priority Areas** define geographic regions important for biodiversity.

    Currently, there are **{:,}** priority areas in the database.
    """.format(
        db.get_table_count("area")
    )
)

st.markdown("### Features Coming Soon")
st.markdown("- View all priority areas")
st.markdown("- Search and filter areas")
st.markdown("- Add new areas")
st.markdown("- Edit existing areas")
st.markdown("- Delete areas (with cascade handling)")
st.markdown("- View area geometries on a map")
st.markdown("- Manage area funding schemes")

st.markdown("---")
st.caption("Phase 2: Read Operations - Coming in the next phase")
