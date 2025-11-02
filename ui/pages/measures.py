"""Measures page - CRUD operations for biodiversity measures."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db

st.title("📋 Measures Management")

st.info(
    """
    **Measures** are actions or recommendations for delivering biodiversity priorities in specific areas.

    Currently, there are **{:,}** measures in the database.
    """.format(
        db.get_table_count("measure")
    )
)

st.markdown("### Features Coming Soon")
st.markdown("- View all measures")
st.markdown("- Search and filter measures")
st.markdown("- Add new measures")
st.markdown("- Edit existing measures")
st.markdown("- Delete measures (with cascade handling)")
st.markdown("- Link measures to areas, priorities, and grants")

st.markdown("---")
st.caption("Phase 2: Read Operations - Coming in the next phase")
