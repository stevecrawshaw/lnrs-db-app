"""LNRS Database CRUD Application.

Main entry point for the Streamlit application.
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="LNRS Database Manager",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Define pages
home_page = st.Page("ui/pages/home.py", title="Dashboard", icon="🏠")
measures_page = st.Page("ui/pages/measures.py", title="Measures", icon="📋")
areas_page = st.Page("ui/pages/areas.py", title="Areas", icon="🗺️")
priorities_page = st.Page("ui/pages/priorities.py", title="Priorities", icon="🎯")
species_page = st.Page("ui/pages/species.py", title="Species", icon="🦋")
grants_page = st.Page("ui/pages/grants.py", title="Grants", icon="💰")
habitats_page = st.Page("ui/pages/habitats.py", title="Habitats", icon="🌳")
relationships_page = st.Page("ui/pages/relationships.py", title="Relationships", icon="🔗")

# Create navigation
pg = st.navigation(
    {
        "Main": [home_page],
        "Entities": [
            measures_page,
            areas_page,
            priorities_page,
            species_page,
            grants_page,
            habitats_page,
        ],
        "Relationships": [relationships_page],
    }
)

# Run the selected page
pg.run()
