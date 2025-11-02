"""Species page - CRUD operations for species data."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db

st.title("🦋 Species Management")

st.info(
    """
    **Species** tracks important flora and fauna with GBIF taxonomy data.

    Currently, there are **{:,}** species in the database.
    """.format(
        db.get_table_count("species")
    )
)

st.markdown("### Features Coming Soon")
st.markdown("- View all species with images")
st.markdown("- Search and filter by assemblage or taxa")
st.markdown("- Add new species with GBIF lookup")
st.markdown("- Edit existing species")
st.markdown("- Delete species (with cascade handling)")
st.markdown("- View species-area-priority relationships")
st.markdown("- Display taxonomy and images")

st.markdown("---")
st.caption("Phase 2: Read Operations - Coming in the next phase")
