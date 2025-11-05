"""Database mode selector component for Streamlit.

This component allows users to switch between local and MotherDuck databases
when running the application locally. It is automatically hidden in production.
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db


def render_database_selector():
    """Render the database mode selector in the sidebar.

    Only shown when mode switching is allowed (local development).
    Provides a radio button selector and switch confirmation.
    """
    # Check if switching is allowed
    switch_info = db.can_switch_mode()

    if not switch_info["allowed"]:
        return  # Don't show selector in production or when unavailable

    st.sidebar.markdown("### 🎚️ Database Connection")

    # Initialize session state
    if "database_mode" not in st.session_state:
        current_info = db.get_connection_info()
        st.session_state.database_mode = current_info["mode"]

    # Current mode display
    current_mode = st.session_state.database_mode
    mode_label = "📁 LOCAL" if current_mode == "local" else "☁️ MOTHERDUCK"
    st.sidebar.info(f"**Current:** {mode_label}")

    # Mode selector options
    mode_options = {"local": "📁 Local Database", "motherduck": "☁️ MotherDuck Cloud"}

    selected_mode = st.sidebar.radio(
        "Select Database:",
        options=switch_info["available_modes"],
        format_func=lambda x: mode_options[x],
        index=switch_info["available_modes"].index(current_mode),
        key="db_mode_selector",
    )

    # Show switch button if mode changed
    if selected_mode != current_mode:
        st.sidebar.warning(f"⚠️ Switch to {selected_mode.upper()}?")

        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("✓ Switch", type="primary", use_container_width=True):
                switch_database(selected_mode)

        with col2:
            if st.button("✗ Cancel", use_container_width=True):
                # Reset the radio selection
                st.session_state.database_mode = current_mode
                st.rerun()

    st.sidebar.markdown("---")


def switch_database(new_mode: str):
    """Handle database mode switching with feedback.

    Args:
        new_mode: Target database mode ("local" or "motherduck")
    """
    with st.spinner(f"Switching to {new_mode.upper()} database..."):
        # Attempt the switch
        result = db.set_mode(new_mode)

        if result["success"]:
            # Update session state
            st.session_state.database_mode = new_mode

            # Clear all caches to prevent stale data
            st.cache_data.clear()

            # Show success message
            st.sidebar.success(f"✓ {result['message']}")

            # Force page reload to refresh all data
            st.rerun()
        else:
            # Show error message
            st.sidebar.error(f"✗ {result['message']}")

            # Revert selection to actual current mode
            actual_mode = db.get_connection_info()["mode"]
            st.session_state.database_mode = actual_mode
