"""Relationships page - Manage many-to-many relationships (bridge tables)."""

import sys
from pathlib import Path

import polars as pl
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.area import AreaModel
from models.grant import GrantModel
from models.habitat import HabitatModel
from models.measure import MeasureModel
from models.priority import PriorityModel
from models.relationship import RelationshipModel
from models.species import SpeciesModel
from ui.components.tables import display_data_table

# Initialize models
relationship_model = RelationshipModel()
measure_model = MeasureModel()
area_model = AreaModel()
priority_model = PriorityModel()
grant_model = GrantModel()
species_model = SpeciesModel()
habitat_model = HabitatModel()

# Initialize session state for each relationship type
if "show_create_map_form" not in st.session_state:
    st.session_state.show_create_map_form = False
if "show_bulk_create_map_form" not in st.session_state:
    st.session_state.show_bulk_create_map_form = False
if "show_create_grant_form" not in st.session_state:
    st.session_state.show_create_grant_form = False
if "show_create_species_form" not in st.session_state:
    st.session_state.show_create_species_form = False
if "show_create_habitat_creation_form" not in st.session_state:
    st.session_state.show_create_habitat_creation_form = False
if "show_create_habitat_management_form" not in st.session_state:
    st.session_state.show_create_habitat_management_form = False


# ==============================================================================
# TAB 1: MEASURE-AREA-PRIORITY RELATIONSHIPS
# ==============================================================================


def show_measure_area_priority_interface():
    """Display interface for managing measure-area-priority relationships."""
    st.header("Measure-Area-Priority Links")
    st.info(
        "The core relationship in the database - links measures to specific "
        "area-priority combinations."
    )

    # Create buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Create New Link", type="primary", key="create_map_btn"):
            st.session_state.show_create_map_form = True
    with col2:
        if st.button("➕➕ Bulk Create Links", key="bulk_create_map_btn"):
            st.session_state.show_bulk_create_map_form = True

    # Show create form if requested
    if st.session_state.show_create_map_form:
        show_create_map_form()
        st.markdown("---")

    # Show bulk create form if requested
    if st.session_state.show_bulk_create_map_form:
        show_bulk_create_map_form()
        st.markdown("---")

    # Get all links
    all_links = relationship_model.get_all_measure_area_priority()

    st.metric("Total Links", f"{len(all_links):,}")

    # Display links table with filters
    st.subheader("All Measure-Area-Priority Links")

    # Add filters
    col1, col2, col3 = st.columns(3)

    with col1:
        # Filter by theme (filter out None values)
        themes = sorted([t for t in all_links["theme"].unique().to_list() if t is not None])
        selected_theme = st.selectbox(
            "Filter by Theme", ["All"] + themes, key="map_theme_filter"
        )

    with col2:
        # Filter by area (filter out None values)
        areas = sorted([a for a in all_links["area_name"].unique().to_list() if a is not None])
        selected_area = st.selectbox(
            "Filter by Area", ["All"] + areas, key="map_area_filter"
        )

    with col3:
        # Search by measure
        search_term = st.text_input(
            "Search Measure", placeholder="Type to search...", key="map_search"
        )

    # Apply filters
    filtered_links = all_links.clone()

    if selected_theme != "All":
        filtered_links = filtered_links.filter(pl.col("theme") == selected_theme)

    if selected_area != "All":
        filtered_links = filtered_links.filter(pl.col("area_name") == selected_area)

    if search_term:
        filtered_links = filtered_links.filter(
            pl.col("concise_measure").str.to_lowercase().str.contains(search_term.lower())
            | pl.col("measure").str.to_lowercase().str.contains(search_term.lower())
        )

    st.info(f"Showing {len(filtered_links):,} of {len(all_links):,} links")

    # Display table with actions
    if len(filtered_links) > 0:
        display_df = filtered_links.select([
            "measure_id",
            "concise_measure",
            "area_name",
            "simplified_biodiversity_priority",
            "theme",
        ])

        # Add delete functionality
        st.dataframe(
            display_df.to_pandas(),
            use_container_width=True,
            hide_index=True,
            column_config={
                "measure_id": st.column_config.NumberColumn("Measure ID", width="small"),
                "concise_measure": st.column_config.TextColumn("Measure", width="large"),
                "area_name": st.column_config.TextColumn("Area", width="medium"),
                "simplified_biodiversity_priority": st.column_config.TextColumn(
                    "Priority", width="medium"
                ),
                "theme": st.column_config.TextColumn("Theme", width="medium"),
            },
        )

        # Delete section
        with st.expander("🗑️ Delete Link"):
            st.warning("⚠️ Delete a measure-area-priority link")

            delete_col1, delete_col2, delete_col3 = st.columns(3)

            with delete_col1:
                delete_measure_id = st.number_input(
                    "Measure ID", min_value=1, value=1, key="delete_map_measure"
                )

            with delete_col2:
                delete_area_id = st.number_input(
                    "Area ID", min_value=1, value=1, key="delete_map_area"
                )

            with delete_col3:
                delete_priority_id = st.number_input(
                    "Priority ID", min_value=1, value=1, key="delete_map_priority"
                )

            if st.button("🗑️ Delete Link", type="primary", key="delete_map_link_btn"):
                try:
                    # Check if link exists
                    if relationship_model.link_exists_measure_area_priority(
                        delete_measure_id, delete_area_id, delete_priority_id
                    ):
                        relationship_model.delete_measure_area_priority_link(
                            delete_measure_id, delete_area_id, delete_priority_id
                        )
                        st.success(
                            f"✅ Successfully deleted link: Measure {delete_measure_id} - "
                            f"Area {delete_area_id} - Priority {delete_priority_id}"
                        )
                        st.rerun()
                    else:
                        st.error("❌ Link does not exist")
                except Exception as e:
                    st.error(f"❌ Error deleting link: {str(e)}")
    else:
        st.info("No links match your filters.")


def show_create_map_form():
    """Display form to create a new measure-area-priority link."""
    st.subheader("➕ Create New Measure-Area-Priority Link")

    # Get options for dropdowns
    all_measures = measure_model.get_all()
    all_areas = area_model.get_all()
    all_priorities = priority_model.get_all()

    with st.form("create_map_form", clear_on_submit=True):
        # Measure selection
        measure_options = all_measures.select(["measure_id", "concise_measure"])
        measure_display = [
            f"{row['measure_id']} - {row['concise_measure'][:80]}"
            for row in measure_options.iter_rows(named=True)
        ]
        selected_measure = st.selectbox(
            "Select Measure*",
            options=measure_display,
            help="Select the measure to link",
        )

        # Area selection
        area_options = all_areas.select(["area_id", "area_name"])
        area_display = [
            f"{row['area_id']} - {row['area_name']}"
            for row in area_options.iter_rows(named=True)
        ]
        selected_area = st.selectbox(
            "Select Area*",
            options=area_display,
            help="Select the priority area",
        )

        # Priority selection
        priority_options = all_priorities.select(
            ["priority_id", "simplified_biodiversity_priority", "theme"]
        )
        priority_display = [
            f"{row['priority_id']} - [{row['theme']}] {row['simplified_biodiversity_priority']}"
            for row in priority_options.iter_rows(named=True)
        ]
        selected_priority = st.selectbox(
            "Select Priority*",
            options=priority_display,
            help="Select the biodiversity priority",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Create Link", type="primary", use_container_width=True
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_create_map_form = False
            st.rerun()

        if submitted:
            # Parse IDs from selections
            measure_id = int(selected_measure.split(" - ")[0])
            area_id = int(selected_area.split(" - ")[0])
            priority_id = int(selected_priority.split(" - ")[0])

            # Create link
            try:
                relationship_model.create_measure_area_priority_link(
                    measure_id, area_id, priority_id
                )
                st.success(
                    f"✅ Successfully created link: Measure {measure_id} - "
                    f"Area {area_id} - Priority {priority_id}"
                )
                st.session_state.show_create_map_form = False
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Error creating link: {str(e)}")


def show_bulk_create_map_form():
    """Display form to bulk create measure-area-priority links."""
    st.subheader("➕➕ Bulk Create Measure-Area-Priority Links")
    st.info(
        "Select multiple measures, areas, and priorities to create all possible "
        "combinations (Cartesian product)."
    )

    # Get options for multi-select
    all_measures = measure_model.get_all()
    all_areas = area_model.get_all()
    all_priorities = priority_model.get_all()

    with st.form("bulk_create_map_form", clear_on_submit=True):
        # Measure multi-select
        measure_options = all_measures.select(["measure_id", "concise_measure"])
        measure_display = {
            f"{row['measure_id']} - {row['concise_measure'][:80]}": row["measure_id"]
            for row in measure_options.iter_rows(named=True)
        }
        selected_measures = st.multiselect(
            "Select Measures*",
            options=list(measure_display.keys()),
            help="Select one or more measures to link",
        )

        # Area multi-select
        area_options = all_areas.select(["area_id", "area_name"])
        area_display = {
            f"{row['area_id']} - {row['area_name']}": row["area_id"]
            for row in area_options.iter_rows(named=True)
        }
        selected_areas = st.multiselect(
            "Select Areas*",
            options=list(area_display.keys()),
            help="Select one or more priority areas",
        )

        # Priority multi-select
        priority_options = all_priorities.select(
            ["priority_id", "simplified_biodiversity_priority", "theme"]
        )
        priority_display = {
            f"{row['priority_id']} - [{row['theme']}] {row['simplified_biodiversity_priority']}": row[
                "priority_id"
            ]
            for row in priority_options.iter_rows(named=True)
        }
        selected_priorities = st.multiselect(
            "Select Priorities*",
            options=list(priority_display.keys()),
            help="Select one or more biodiversity priorities",
        )

        # Calculate total links that will be created
        total_links = (
            len(selected_measures) * len(selected_areas) * len(selected_priorities)
        )
        if total_links > 0:
            st.warning(
                f"⚠️ This will attempt to create **{total_links}** links "
                f"({len(selected_measures)} measures × {len(selected_areas)} areas × "
                f"{len(selected_priorities)} priorities)"
            )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                f"Create {total_links} Links",
                type="primary",
                use_container_width=True,
                disabled=(total_links == 0),
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_bulk_create_map_form = False
            st.rerun()

        if submitted and total_links > 0:
            # Parse IDs from selections
            measure_ids = [measure_display[m] for m in selected_measures]
            area_ids = [area_display[a] for a in selected_areas]
            priority_ids = [priority_display[p] for p in selected_priorities]

            # Create links
            with st.spinner(f"Creating {total_links} links..."):
                try:
                    created_count, errors = (
                        relationship_model.bulk_create_measure_area_priority_links(
                            measure_ids, area_ids, priority_ids
                        )
                    )

                    if created_count > 0:
                        st.success(f"✅ Successfully created {created_count} links!")

                    if errors:
                        st.warning(f"⚠️ Encountered {len(errors)} issues:")
                        with st.expander("Show errors"):
                            for error in errors[:20]:  # Show first 20 errors
                                st.text(error)
                            if len(errors) > 20:
                                st.text(f"... and {len(errors) - 20} more errors")

                    st.session_state.show_bulk_create_map_form = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error during bulk create: {str(e)}")


# ==============================================================================
# TAB 2: GRANT FUNDING RELATIONSHIPS
# ==============================================================================


def show_grant_funding_interface():
    """Display interface for managing grant funding (measure_area_priority_grant)."""
    st.header("Grant Funding")
    st.info(
        "Links grants to measure-area-priority combinations, showing which "
        "biodiversity actions have funding available."
    )

    # Create button
    if st.button("➕ Add Grant to Link", type="primary", key="create_grant_btn"):
        st.session_state.show_create_grant_form = True

    # Show create form if requested
    if st.session_state.show_create_grant_form:
        show_create_grant_form()
        st.markdown("---")

    # Get all grant-funded links
    grant_links = relationship_model.get_all_measure_area_priority_grants()
    unfunded_links = relationship_model.get_unfunded_measure_area_priority_links()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Grant-Funded Links", f"{len(grant_links):,}")
    with col2:
        st.metric("Unfunded Links", f"{len(unfunded_links):,}")

    # Display grant-funded links
    st.subheader("Grant-Funded Measure-Area-Priority Links")

    if len(grant_links) > 0:
        # Filter by grant scheme (filter out None values)
        schemes = sorted([s for s in grant_links["grant_scheme"].unique().to_list() if s is not None])
        selected_scheme = st.selectbox(
            "Filter by Grant Scheme", ["All"] + schemes, key="grant_scheme_filter"
        )

        filtered_grants = grant_links.clone()
        if selected_scheme != "All":
            filtered_grants = filtered_grants.filter(
                pl.col("grant_scheme") == selected_scheme
            )

        st.info(f"Showing {len(filtered_grants):,} of {len(grant_links):,} grant links")

        display_df = filtered_grants.select([
            "measure_id",
            "concise_measure",
            "area_name",
            "simplified_biodiversity_priority",
            "grant_name",
            "grant_scheme",
            "url",
        ])

        st.dataframe(
            display_df.to_pandas(),
            use_container_width=True,
            hide_index=True,
            column_config={
                "measure_id": st.column_config.NumberColumn("Measure ID", width="small"),
                "concise_measure": st.column_config.TextColumn("Measure", width="medium"),
                "area_name": st.column_config.TextColumn("Area", width="small"),
                "simplified_biodiversity_priority": st.column_config.TextColumn(
                    "Priority", width="medium"
                ),
                "grant_name": st.column_config.TextColumn("Grant", width="medium"),
                "grant_scheme": st.column_config.TextColumn("Scheme", width="small"),
                "url": st.column_config.LinkColumn("URL", width="small"),
            },
        )
    else:
        st.info("No grant-funded links found.")


def show_create_grant_form():
    """Display form to add grant funding to an existing measure-area-priority link."""
    st.subheader("➕ Add Grant Funding to Link")

    # Get options
    unfunded_links = relationship_model.get_unfunded_measure_area_priority_links()
    all_grants = grant_model.get_all()

    with st.form("create_grant_form", clear_on_submit=True):
        st.write("**Step 1: Select Unfunded Link**")

        if len(unfunded_links) > 0:
            link_display = [
                f"M{row['measure_id']} A{row['area_id']} P{row['priority_id']} - "
                f"{row['concise_measure'][:40]} in {row['area_name']}"
                for row in unfunded_links.iter_rows(named=True)
            ]
            selected_link = st.selectbox(
                "Select Link",
                options=link_display,
                help="Select an unfunded measure-area-priority link",
            )
        else:
            st.warning("No unfunded links available. All links have grants.")
            st.form_submit_button("Close", use_container_width=True)
            return

        st.write("**Step 2: Select Grant**")

        grant_options = all_grants.select(["grant_id", "grant_name", "grant_scheme"])
        grant_display = [
            f"{row['grant_id']} - [{row['grant_scheme']}] {row['grant_name']}"
            for row in grant_options.iter_rows(named=True)
        ]
        selected_grant = st.selectbox(
            "Select Grant",
            options=grant_display,
            help="Select the grant to link",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Add Grant", type="primary", use_container_width=True
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_create_grant_form = False
            st.rerun()

        if submitted:
            # Parse IDs
            link_parts = selected_link.split(" - ")[0]
            measure_id = int(link_parts.split("M")[1].split(" A")[0])
            area_id = int(link_parts.split(" A")[1].split(" P")[0])
            priority_id = int(link_parts.split(" P")[1])

            grant_id = int(selected_grant.split(" - ")[0])

            # Add grant
            try:
                relationship_model.add_grant_to_link(
                    measure_id, area_id, priority_id, grant_id
                )
                st.success(
                    f"✅ Successfully added grant {grant_id} to link "
                    f"M{measure_id}-A{area_id}-P{priority_id}"
                )
                st.session_state.show_create_grant_form = False
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Error adding grant: {str(e)}")


# ==============================================================================
# TAB 3: SPECIES-AREA-PRIORITY RELATIONSHIPS
# ==============================================================================


def show_species_area_priority_interface():
    """Display interface for managing species-area-priority relationships."""
    st.header("Species-Area-Priority Links")
    st.info(
        "Links species to areas and priorities, showing which species are "
        "important in which areas."
    )

    # Create button
    if st.button("➕ Create New Link", type="primary", key="create_species_btn"):
        st.session_state.show_create_species_form = True

    # Show create form if requested
    if st.session_state.show_create_species_form:
        show_create_species_form()
        st.markdown("---")

    # Get all links
    species_links = relationship_model.get_all_species_area_priority()

    st.metric("Total Links", f"{len(species_links):,}")

    # Display links
    st.subheader("All Species-Area-Priority Links")

    if len(species_links) > 0:
        # Filter by assemblage
        assemblages = sorted(
            [a for a in species_links["assemblage"].unique().to_list() if a]
        )
        selected_assemblage = st.selectbox(
            "Filter by Assemblage", ["All"] + assemblages, key="species_assemblage_filter"
        )

        filtered_links = species_links.clone()
        if selected_assemblage != "All":
            filtered_links = filtered_links.filter(
                pl.col("assemblage") == selected_assemblage
            )

        st.info(f"Showing {len(filtered_links):,} of {len(species_links):,} links")

        display_df = filtered_links.select([
            "species_id",
            "common_name",
            "linnaean_name",
            "assemblage",
            "area_name",
            "simplified_biodiversity_priority",
            "theme",
        ])

        st.dataframe(
            display_df.to_pandas(),
            use_container_width=True,
            hide_index=True,
            column_config={
                "species_id": st.column_config.NumberColumn("ID", width="small"),
                "common_name": st.column_config.TextColumn("Common Name", width="medium"),
                "linnaean_name": st.column_config.TextColumn("Scientific", width="medium"),
                "assemblage": st.column_config.TextColumn("Assemblage", width="small"),
                "area_name": st.column_config.TextColumn("Area", width="medium"),
                "simplified_biodiversity_priority": st.column_config.TextColumn(
                    "Priority", width="medium"
                ),
                "theme": st.column_config.TextColumn("Theme", width="medium"),
            },
        )
    else:
        st.info("No species-area-priority links found.")


def show_create_species_form():
    """Display form to create a new species-area-priority link."""
    st.subheader("➕ Create New Species-Area-Priority Link")

    # Get options
    all_species = species_model.get_all()
    all_areas = area_model.get_all()
    all_priorities = priority_model.get_all()

    with st.form("create_species_form", clear_on_submit=True):
        # Species selection
        species_options = all_species.select(["species_id", "common_name", "linnaean_name"])
        species_display = [
            f"{row['species_id']} - {row['common_name']} ({row['linnaean_name']})"
            for row in species_options.iter_rows(named=True)
        ]
        selected_species = st.selectbox(
            "Select Species*",
            options=species_display,
            help="Select the species",
        )

        # Area selection
        area_options = all_areas.select(["area_id", "area_name"])
        area_display = [
            f"{row['area_id']} - {row['area_name']}"
            for row in area_options.iter_rows(named=True)
        ]
        selected_area = st.selectbox(
            "Select Area*",
            options=area_display,
            help="Select the priority area",
        )

        # Priority selection
        priority_options = all_priorities.select([
            "priority_id",
            "simplified_biodiversity_priority",
            "theme"
        ])
        priority_display = [
            f"{row['priority_id']} - [{row['theme']}] {row['simplified_biodiversity_priority']}"
            for row in priority_options.iter_rows(named=True)
        ]
        selected_priority = st.selectbox(
            "Select Priority*",
            options=priority_display,
            help="Select the biodiversity priority",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Create Link", type="primary", use_container_width=True
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_create_species_form = False
            st.rerun()

        if submitted:
            # Parse IDs
            species_id = int(selected_species.split(" - ")[0])
            area_id = int(selected_area.split(" - ")[0])
            priority_id = int(selected_priority.split(" - ")[0])

            # Create link
            try:
                relationship_model.create_species_area_priority_link(
                    species_id, area_id, priority_id
                )
                st.success(
                    f"✅ Successfully created link: Species {species_id} - "
                    f"Area {area_id} - Priority {priority_id}"
                )
                st.session_state.show_create_species_form = False
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Error creating link: {str(e)}")


# ==============================================================================
# TAB 4 & 5: HABITAT-AREA RELATIONSHIPS
# ==============================================================================


def show_habitat_creation_interface():
    """Display interface for managing habitat creation in areas."""
    st.header("Habitat Creation")
    st.info(
        "Links habitats to areas for creation - showing which habitats should be "
        "created in which areas."
    )

    # Create button
    if st.button("➕ Create New Link", type="primary", key="create_hc_btn"):
        st.session_state.show_create_habitat_creation_form = True

    # Show create form if requested
    if st.session_state.show_create_habitat_creation_form:
        show_create_habitat_creation_form()
        st.markdown("---")

    # Get all links
    habitat_links = relationship_model.get_all_habitat_creation_areas()

    st.metric("Total Links", f"{len(habitat_links):,}")

    # Display links
    if len(habitat_links) > 0:
        st.dataframe(
            habitat_links.to_pandas(),
            use_container_width=True,
            hide_index=True,
            column_config={
                "habitat_id": st.column_config.NumberColumn("Habitat ID", width="small"),
                "habitat": st.column_config.TextColumn("Habitat Type", width="large"),
                "area_id": st.column_config.NumberColumn("Area ID", width="small"),
                "area_name": st.column_config.TextColumn("Area", width="medium"),
            },
        )
    else:
        st.info("No habitat creation links found.")


def show_create_habitat_creation_form():
    """Display form to create a new habitat-creation-area link."""
    st.subheader("➕ Create New Habitat Creation Link")

    all_habitats = habitat_model.get_all()
    all_areas = area_model.get_all()

    with st.form("create_habitat_creation_form", clear_on_submit=True):
        # Habitat selection
        habitat_options = all_habitats.select(["habitat_id", "habitat"])
        habitat_display = [
            f"{row['habitat_id']} - {row['habitat']}"
            for row in habitat_options.iter_rows(named=True)
        ]
        selected_habitat = st.selectbox(
            "Select Habitat Type*",
            options=habitat_display,
            help="Select the habitat type",
        )

        # Area selection
        area_options = all_areas.select(["area_id", "area_name"])
        area_display = [
            f"{row['area_id']} - {row['area_name']}"
            for row in area_options.iter_rows(named=True)
        ]
        selected_area = st.selectbox(
            "Select Area*",
            options=area_display,
            help="Select the priority area",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Create Link", type="primary", use_container_width=True
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_create_habitat_creation_form = False
            st.rerun()

        if submitted:
            # Parse IDs
            habitat_id = int(selected_habitat.split(" - ")[0])
            area_id = int(selected_area.split(" - ")[0])

            # Create link
            try:
                relationship_model.create_habitat_creation_link(habitat_id, area_id)
                st.success(
                    f"✅ Successfully created habitat creation link: "
                    f"Habitat {habitat_id} - Area {area_id}"
                )
                st.session_state.show_create_habitat_creation_form = False
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Error creating link: {str(e)}")


def show_habitat_management_interface():
    """Display interface for managing habitat management in areas."""
    st.header("Habitat Management")
    st.info(
        "Links habitats to areas for management - showing which existing habitats "
        "require management in which areas."
    )

    # Create button
    if st.button("➕ Create New Link", type="primary", key="create_hm_btn"):
        st.session_state.show_create_habitat_management_form = True

    # Show create form if requested
    if st.session_state.show_create_habitat_management_form:
        show_create_habitat_management_form()
        st.markdown("---")

    # Get all links
    habitat_links = relationship_model.get_all_habitat_management_areas()

    st.metric("Total Links", f"{len(habitat_links):,}")

    # Display links
    if len(habitat_links) > 0:
        st.dataframe(
            habitat_links.to_pandas(),
            use_container_width=True,
            hide_index=True,
            column_config={
                "habitat_id": st.column_config.NumberColumn("Habitat ID", width="small"),
                "habitat": st.column_config.TextColumn("Habitat Type", width="large"),
                "area_id": st.column_config.NumberColumn("Area ID", width="small"),
                "area_name": st.column_config.TextColumn("Area", width="medium"),
            },
        )
    else:
        st.info("No habitat management links found.")


def show_create_habitat_management_form():
    """Display form to create a new habitat-management-area link."""
    st.subheader("➕ Create New Habitat Management Link")

    all_habitats = habitat_model.get_all()
    all_areas = area_model.get_all()

    with st.form("create_habitat_management_form", clear_on_submit=True):
        # Habitat selection
        habitat_options = all_habitats.select(["habitat_id", "habitat"])
        habitat_display = [
            f"{row['habitat_id']} - {row['habitat']}"
            for row in habitat_options.iter_rows(named=True)
        ]
        selected_habitat = st.selectbox(
            "Select Habitat Type*",
            options=habitat_display,
            help="Select the habitat type",
        )

        # Area selection
        area_options = all_areas.select(["area_id", "area_name"])
        area_display = [
            f"{row['area_id']} - {row['area_name']}"
            for row in area_options.iter_rows(named=True)
        ]
        selected_area = st.selectbox(
            "Select Area*",
            options=area_display,
            help="Select the priority area",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Create Link", type="primary", use_container_width=True
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_create_habitat_management_form = False
            st.rerun()

        if submitted:
            # Parse IDs
            habitat_id = int(selected_habitat.split(" - ")[0])
            area_id = int(selected_area.split(" - ")[0])

            # Create link
            try:
                relationship_model.create_habitat_management_link(habitat_id, area_id)
                st.success(
                    f"✅ Successfully created habitat management link: "
                    f"Habitat {habitat_id} - Area {area_id}"
                )
                st.session_state.show_create_habitat_management_form = False
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Error creating link: {str(e)}")


# ==============================================================================
# MAIN PAGE LAYOUT
# ==============================================================================

st.title("🔗 Relationships")
st.markdown(
    "Manage many-to-many relationships between entities. These bridge tables "
    "link measures, areas, priorities, species, habitats, and grants."
)

# Create tabs for different relationship types
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Measure-Area-Priority",
    "Grant Funding",
    "Species-Area-Priority",
    "Habitat Creation",
    "Habitat Management",
])

with tab1:
    show_measure_area_priority_interface()

with tab2:
    show_grant_funding_interface()

with tab3:
    show_species_area_priority_interface()

with tab4:
    show_habitat_creation_interface()

with tab5:
    show_habitat_management_interface()
