"""Reusable table display components for entity data.

This module provides components for displaying data tables with search,
filter, and action capabilities.
"""

import sys
from pathlib import Path
from typing import Any, Callable

import polars as pl
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def display_data_table(
    data: pl.DataFrame,
    title: str,
    entity_name: str,
    id_column: str,
    searchable_columns: list[str] | None = None,
    column_config: dict[str, Any] | None = None,
    show_actions: bool = True,
    on_view_details: Callable[[Any], None] | None = None,
) -> None:
    """Display a data table with search and actions.

    Args:
        data: Polars DataFrame to display
        title: Title to display above the table
        entity_name: Name of the entity (for session state keys)
        id_column: Name of the ID column
        searchable_columns: Columns to search across (None = all text columns)
        column_config: Streamlit column configuration dict
        show_actions: Whether to show action buttons
        on_view_details: Callback function for view details action
    """
    st.subheader(title)

    # Display count
    total_count = len(data)
    st.caption(f"Total records: {total_count:,}")

    if total_count == 0:
        st.info("No records found.")
        return

    # Convert to pandas for st.dataframe
    df_pandas = data.to_pandas()

    # Search functionality
    search_key = f"{entity_name}_search"
    if searchable_columns:
        search_term = st.text_input(
            "🔍 Search",
            key=search_key,
            placeholder=f"Search in {', '.join(searchable_columns)}...",
        )

        if search_term:
            # Filter dataframe based on search term
            mask = pl.lit(False)
            for col in searchable_columns:
                if col in data.columns:
                    mask = mask | data[col].cast(str).str.contains(f"(?i){search_term}")

            data_filtered = data.filter(mask)
            df_pandas = data_filtered.to_pandas()
            st.caption(f"Showing {len(df_pandas)} of {total_count} records")

    # Display table
    if column_config is None:
        column_config = {}

    # Add ID column config if not specified
    if id_column not in column_config:
        column_config[id_column] = st.column_config.NumberColumn(
            "ID", width="small", help=f"{entity_name} ID"
        )

    st.dataframe(
        df_pandas,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )

    # Action buttons (if enabled and callback provided)
    if show_actions and on_view_details:
        st.markdown("---")
        st.markdown("##### Actions")
        st.caption("Select a record ID to view details:")

        # ID selection
        id_select_key = f"{entity_name}_id_select"
        selected_id = st.number_input(
            f"Enter {entity_name} ID",
            min_value=int(df_pandas[id_column].min()),
            max_value=int(df_pandas[id_column].max()),
            key=id_select_key,
            help=f"Enter the ID of the {entity_name} to view details",
        )

        if st.button(f"View Details", key=f"{entity_name}_view_btn"):
            on_view_details(selected_id)


def display_grouped_table(
    data: pl.DataFrame,
    title: str,
    group_column: str,
    display_columns: list[str] | None = None,
) -> None:
    """Display data grouped by a column.

    Args:
        data: Polars DataFrame to display
        title: Title to display above the tables
        group_column: Column to group by
        display_columns: Columns to display (None = all)
    """
    st.subheader(title)

    # Get unique groups
    groups = data[group_column].unique().sort()

    for group in groups:
        with st.expander(f"**{group}** ({len(data.filter(pl.col(group_column) == group))} records)", expanded=True):
            group_data = data.filter(pl.col(group_column) == group)

            if display_columns:
                group_data = group_data.select(display_columns)

            st.dataframe(
                group_data.to_pandas(),
                use_container_width=True,
                hide_index=True,
            )


def display_detail_view(
    entity_name: str,
    entity_data: dict[str, Any],
    relationships: dict[str, pl.DataFrame] | None = None,
    back_callback: Callable[[], None] | None = None,
) -> None:
    """Display detailed view of a single entity.

    Args:
        entity_name: Name of the entity
        entity_data: Dictionary of entity field names and values
        relationships: Dictionary of related entity name -> DataFrame
        back_callback: Callback to return to list view
    """
    st.title(f"{entity_name} Details")

    # Back button
    if back_callback:
        if st.button("← Back to List"):
            back_callback()
            st.rerun()

    # Display entity data
    st.subheader("Basic Information")

    # Display as key-value pairs in columns
    col1, col2 = st.columns(2)

    items = list(entity_data.items())
    mid = len(items) // 2

    with col1:
        for key, value in items[:mid]:
            if value is not None:
                # Format key: convert snake_case to Title Case
                formatted_key = key.replace("_", " ").title()
                # Handle URLs
                if isinstance(value, str) and value.startswith("http"):
                    st.markdown(f"**{formatted_key}:** [{value}]({value})")
                else:
                    st.markdown(f"**{formatted_key}:** {value}")

    with col2:
        for key, value in items[mid:]:
            if value is not None:
                formatted_key = key.replace("_", " ").title()
                if isinstance(value, str) and value.startswith("http"):
                    st.markdown(f"**{formatted_key}:** [{value}]({value})")
                else:
                    st.markdown(f"**{formatted_key}:** {value}")

    # Display relationships
    if relationships:
        st.markdown("---")
        st.subheader("Related Data")

        # Create tabs for each relationship
        tabs = st.tabs(list(relationships.keys()))

        for tab, (rel_name, rel_data) in zip(tabs, relationships.items()):
            with tab:
                if len(rel_data) > 0:
                    st.dataframe(
                        rel_data.to_pandas(),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.caption(f"Total: {len(rel_data):,} records")
                else:
                    st.info(f"No {rel_name.lower()} linked to this {entity_name.lower()}.")


def create_filter_widgets(
    filter_configs: dict[str, dict[str, Any]],
    entity_name: str,
) -> dict[str, Any]:
    """Create filter widgets and return selected values.

    Args:
        filter_configs: Dict of column -> {type, options, label}
            Example: {
                "core_supplementary": {
                    "type": "selectbox",
                    "options": ["All", "Core", "Supplementary"],
                    "label": "Core/Supplementary"
                }
            }
        entity_name: Name of entity (for session state keys)

    Returns:
        Dict of column -> selected value
    """
    filters = {}

    st.markdown("##### Filters")

    cols = st.columns(len(filter_configs))

    for col, (col_name, config) in zip(cols, filter_configs.items()):
        with col:
            filter_type = config.get("type", "selectbox")
            options = config.get("options", [])
            label = config.get("label", col_name.replace("_", " ").title())
            key = f"{entity_name}_{col_name}_filter"

            if filter_type == "selectbox":
                selected = st.selectbox(label, options, key=key)
                filters[col_name] = selected
            elif filter_type == "multiselect":
                selected = st.multiselect(label, options, key=key)
                filters[col_name] = selected

    return filters


# %%
if __name__ == "__main__":
    """Test the table component."""
    import polars as pl

    # Create sample data
    sample_data = pl.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "value": [100, 200, 150, 300, 250],
    })

    print("Table component module loaded successfully")
    print(f"Sample data shape: {sample_data.shape}")
