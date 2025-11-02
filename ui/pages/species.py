"""Species page - View and manage species data."""

import sys
from pathlib import Path

import polars as pl
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.species import SpeciesModel
from ui.components.tables import display_data_table

# Initialize model
species_model = SpeciesModel()

# Initialize session state
if "species_view" not in st.session_state:
    st.session_state.species_view = "list"
if "selected_species_id" not in st.session_state:
    st.session_state.selected_species_id = None
if "show_create_form" not in st.session_state:
    st.session_state.show_create_form = False
if "show_edit_form" not in st.session_state:
    st.session_state.show_edit_form = False
if "show_delete_confirm" not in st.session_state:
    st.session_state.show_delete_confirm = False


def show_create_form():
    """Display form to create a new species."""
    st.subheader("➕ Create New Species")

    with st.form("create_species_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            common_name = st.text_input(
                "Common Name*",
                help="Common name of the species (required)",
            )

            scientific_name = st.text_input(
                "Scientific Name*",
                help="Scientific name of the species (required)",
            )

            assemblage = st.selectbox(
                "Assemblage*",
                options=[
                    "Birds",
                    "Butterflies",
                    "Fish",
                    "Mammals",
                    "Moths",
                    "Plants",
                    "Reptiles and amphibians",
                ],
                help="Assemblage group (required)"
            )

            taxa = st.selectbox(
                "Taxa*",
                options=["Bird", "Butterfly", "Fish", "Mammal", "Moth", "Plant", "Reptile/Amphibian"],
                help="Taxa classification (required)"
            )

        with col2:
            st.markdown("**Taxonomy (Optional)**")
            kingdom = st.text_input("Kingdom", help="e.g., Animalia, Plantae")
            phylum = st.text_input("Phylum", help="e.g., Chordata")
            class_name = st.text_input("Class", help="e.g., Aves, Mammalia")
            order = st.text_input("Order", help="e.g., Passeriformes")
            family = st.text_input("Family", help="e.g., Turdidae")
            genus = st.text_input("Genus", help="e.g., Turdus")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Create Species", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_create_form = False
            st.rerun()

        if submitted:
            # Validate required fields
            if not common_name or not common_name.strip():
                st.error("❌ Common Name is required")
                return

            if not scientific_name or not scientific_name.strip():
                st.error("❌ Scientific Name is required")
                return

            # Get next species_id
            max_id = species_model.execute_raw_query("SELECT MAX(species_id) FROM species").fetchone()[0]
            next_id = (max_id or 0) + 1

            # Create species
            try:
                species_model.create({
                    "species_id": next_id,
                    "common_name": common_name.strip(),
                    "scientific_name": scientific_name.strip(),
                    "linnaean_name": scientific_name.strip(),  # Use same as scientific_name
                    "assemblage": assemblage,
                    "taxa": taxa,
                    "kingdom": kingdom.strip() if kingdom and kingdom.strip() else None,
                    "phylum": phylum.strip() if phylum and phylum.strip() else None,
                    "class": class_name.strip() if class_name and class_name.strip() else None,
                    "order": order.strip() if order and order.strip() else None,
                    "family": family.strip() if family and family.strip() else None,
                    "genus": genus.strip() if genus and genus.strip() else None,
                })
                st.success(f"✅ Successfully created species ID {next_id}!")
                st.session_state.show_create_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error creating species: {str(e)}")


def show_edit_form(species_id: int):
    """Display form to edit an existing species."""
    species_data = species_model.get_by_id(species_id)

    if not species_data:
        st.error("Species not found")
        return

    st.subheader(f"✏️ Edit Species {species_id}")

    with st.form("edit_species_form"):
        col1, col2 = st.columns(2)

        with col1:
            common_name = st.text_input(
                "Common Name*",
                value=species_data['common_name']
            )

            scientific_name = st.text_input(
                "Scientific Name*",
                value=species_data['scientific_name']
            )

            assemblage_options = [
                "Birds",
                "Butterflies",
                "Fish",
                "Mammals",
                "Moths",
                "Plants",
                "Reptiles and amphibians",
            ]
            assemblage = st.selectbox(
                "Assemblage*",
                options=assemblage_options,
                index=assemblage_options.index(species_data['assemblage']) if species_data['assemblage'] in assemblage_options else 0
            )

            taxa_options = ["Bird", "Butterfly", "Fish", "Mammal", "Moth", "Plant", "Reptile/Amphibian"]
            taxa = st.selectbox(
                "Taxa*",
                options=taxa_options,
                index=taxa_options.index(species_data['taxa']) if species_data['taxa'] in taxa_options else 0
            )

        with col2:
            st.markdown("**Taxonomy (Optional)**")
            kingdom = st.text_input("Kingdom", value=species_data.get('kingdom', '') or '')
            phylum = st.text_input("Phylum", value=species_data.get('phylum', '') or '')
            class_name = st.text_input("Class", value=species_data.get('class', '') or '')
            order = st.text_input("Order", value=species_data.get('order', '') or '')
            family = st.text_input("Family", value=species_data.get('family', '') or '')
            genus = st.text_input("Genus", value=species_data.get('genus', '') or '')

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Update Species", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_edit_form = False
            st.rerun()

        if submitted:
            # Validate required fields
            if not common_name or not common_name.strip():
                st.error("❌ Common Name is required")
                return

            if not scientific_name or not scientific_name.strip():
                st.error("❌ Scientific Name is required")
                return

            # Update species
            try:
                species_model.update(species_id, {
                    "common_name": common_name.strip(),
                    "scientific_name": scientific_name.strip(),
                    "linnaean_name": scientific_name.strip(),
                    "assemblage": assemblage,
                    "taxa": taxa,
                    "kingdom": kingdom.strip() if kingdom and kingdom.strip() else None,
                    "phylum": phylum.strip() if phylum and phylum.strip() else None,
                    "class": class_name.strip() if class_name and class_name.strip() else None,
                    "order": order.strip() if order and order.strip() else None,
                    "family": family.strip() if family and family.strip() else None,
                    "genus": genus.strip() if genus and genus.strip() else None,
                })
                st.success(f"✅ Successfully updated species ID {species_id}!")
                st.session_state.show_edit_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating species: {str(e)}")


def show_delete_confirmation(species_id: int):
    """Show confirmation dialog before deleting."""
    species_data = species_model.get_by_id(species_id)
    counts = species_model.get_relationship_counts(species_id)

    st.warning(f"⚠️ Are you sure you want to delete this species?")

    st.markdown(f"**Common Name:** {species_data['common_name']}")
    st.markdown(f"**Scientific Name:** {species_data['scientific_name']}")
    st.markdown(f"**Assemblage:** {species_data['assemblage']}")

    # Show impact
    total_relationships = sum(counts.values())
    if total_relationships > 0:
        st.error("**This will also delete the following relationships:**")
        for relationship, count in counts.items():
            if count > 0:
                relationship_display = relationship.replace('_', ' ').title()
                st.write(f"- {count} {relationship_display}")
        st.write(f"\n**Total relationships to be removed: {total_relationships}**")
    else:
        st.info("This species has no relationships and can be safely deleted.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_delete_confirm = False
            st.rerun()
    with col2:
        if st.button("🗑️ Delete Species", type="primary", use_container_width=True):
            try:
                species_model.delete_with_cascade(species_id)
                st.success(f"✅ Successfully deleted species ID {species_id}!")
                st.session_state.show_delete_confirm = False
                st.session_state.species_view = "list"
                st.session_state.selected_species_id = None
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error deleting species: {str(e)}")


def show_list_view():
    """Display list of all species with taxonomy."""
    st.title("🦋 Species")

    # Create button
    if st.button("➕ Create New Species", type="primary"):
        st.session_state.show_create_form = True

    # Show create form if requested
    if st.session_state.show_create_form:
        show_create_form()
        st.markdown("---")

    total_count = species_model.count()
    st.info(f"**{total_count}** species with GBIF taxonomy data")

    # Get all species
    all_species = species_model.get_all(order_by="common_name")

    def on_view_details(species_id):
        st.session_state.selected_species_id = species_id
        st.session_state.species_view = "detail"

    display_data_table(
        data=all_species,
        title="All Species",
        entity_name="species",
        id_column="species_id",
        searchable_columns=["common_name", "scientific_name", "assemblage", "taxa"],
        column_config={
            "species_id": st.column_config.NumberColumn("ID", width="small"),
            "common_name": st.column_config.TextColumn("Common Name", width="medium"),
            "linnaean_name": st.column_config.TextColumn("Linnaean Name", width="medium"),
            "scientific_name": st.column_config.TextColumn("Scientific Name", width="medium"),
            "assemblage": st.column_config.TextColumn("Assemblage", width="medium"),
            "taxa": st.column_config.TextColumn("Taxa", width="small"),
            "kingdom": st.column_config.TextColumn("Kingdom", width="small"),
            "phylum": st.column_config.TextColumn("Phylum", width="small"),
            "class": st.column_config.TextColumn("Class", width="small"),
            "order": st.column_config.TextColumn("Order", width="small"),
            "family": st.column_config.TextColumn("Family", width="small"),
            "genus": st.column_config.TextColumn("Genus", width="small"),
            "species_link": st.column_config.LinkColumn("Info Link", width="small"),
            "gbif_species_url": st.column_config.LinkColumn("GBIF", width="small"),
        },
        show_actions=True,
        on_view_details=on_view_details,
    )


def show_detail_view():
    """Display details of a single species."""
    species_id = st.session_state.selected_species_id

    if species_id is None:
        st.error("No species selected")
        if st.button("← Back to List"):
            st.session_state.species_view = "list"
            st.rerun()
        return

    # Get species data
    species_data = species_model.get_by_id(species_id)

    if not species_data:
        st.error(f"Species ID {species_id} not found")
        if st.button("← Back to List"):
            st.session_state.species_view = "list"
            st.rerun()
        return

    # Get related data
    related_measures = species_model.get_related_measures(species_id)
    related_areas = species_model.get_related_areas(species_id)
    related_priorities = species_model.get_related_priorities(species_id)

    # Get counts
    counts = species_model.get_relationship_counts(species_id)

    # Display detail view
    def back_to_list():
        st.session_state.species_view = "list"
        st.session_state.selected_species_id = None
        st.session_state.show_edit_form = False
        st.session_state.show_delete_confirm = False

    st.title(f"🦋 Species Details")

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("← Back to List"):
            back_to_list()
            st.rerun()
    with col2:
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.show_edit_form = True
            st.session_state.show_delete_confirm = False
    with col3:
        if st.button("🗑️ Delete", use_container_width=True):
            st.session_state.show_delete_confirm = True
            st.session_state.show_edit_form = False

    # Show edit form if requested
    if st.session_state.show_edit_form:
        st.markdown("---")
        show_edit_form(species_id)
        st.markdown("---")

    # Show delete confirmation if requested
    if st.session_state.show_delete_confirm:
        st.markdown("---")
        show_delete_confirmation(species_id)
        st.markdown("---")

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Species ID:** {species_data['species_id']}")
        st.markdown(f"**Common Name:** {species_data['common_name']}")
        st.markdown(f"**Scientific Name:** {species_data['scientific_name']}")
        st.markdown(f"**Assemblage:** {species_data['assemblage']}")
        st.markdown(f"**Taxa:** {species_data['taxa']}")

        # Links if available
        if species_data.get('species_link'):
            st.markdown(f"**Info Link:** [{species_data['species_link']}]({species_data['species_link']})")
        if species_data.get('gbif_species_url'):
            st.markdown(f"**GBIF:** [{species_data['gbif_species_url']}]({species_data['gbif_species_url']})")

    with col2:
        st.markdown("**Relationship Counts:**")
        st.metric("Measures", counts['measures'])
        st.metric("Areas", counts['areas'])
        st.metric("Priorities", counts['priorities'])

    # Taxonomy section
    st.markdown("---")
    st.subheader("Taxonomy")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Kingdom:** {species_data.get('kingdom') or '_Not provided_'}")
        st.markdown(f"**Phylum:** {species_data.get('phylum') or '_Not provided_'}")
    with col2:
        st.markdown(f"**Class:** {species_data.get('class') or '_Not provided_'}")
        st.markdown(f"**Order:** {species_data.get('order') or '_Not provided_'}")
    with col3:
        st.markdown(f"**Family:** {species_data.get('family') or '_Not provided_'}")
        st.markdown(f"**Genus:** {species_data.get('genus') or '_Not provided_'}")

    # Display related data in tabs
    st.markdown("---")
    st.subheader("Related Data")

    tab1, tab2, tab3 = st.tabs(["Measures", "Areas", "Priorities"])

    with tab1:
        if len(related_measures) > 0:
            st.dataframe(
                related_measures.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "measure_id": st.column_config.NumberColumn("ID", width="small"),
                    "measure": st.column_config.TextColumn("Measure", width="large"),
                    "concise_measure": st.column_config.TextColumn("Concise", width="medium"),
                    "core_supplementary": st.column_config.TextColumn("Type", width="small"),
                },
            )
            st.caption(f"Total: {len(related_measures):,} measures")
        else:
            st.info("No measures linked to this species.")

    with tab2:
        if len(related_areas) > 0:
            st.dataframe(
                related_areas.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "area_id": st.column_config.NumberColumn("ID", width="small"),
                    "area_name": st.column_config.TextColumn("Area Name", width="medium"),
                    "area_description": st.column_config.TextColumn("Description", width="large"),
                },
            )
            st.caption(f"Total: {len(related_areas):,} areas")
        else:
            st.info("No areas linked to this species.")

    with tab3:
        if len(related_priorities) > 0:
            st.dataframe(
                related_priorities.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "priority_id": st.column_config.NumberColumn("ID", width="small"),
                    "biodiversity_priority": st.column_config.TextColumn(
                        "Biodiversity Priority", width="large"
                    ),
                    "simplified_biodiversity_priority": st.column_config.TextColumn(
                        "Simplified", width="medium"
                    ),
                    "theme": st.column_config.TextColumn("Theme", width="medium"),
                },
            )
            st.caption(f"Total: {len(related_priorities):,} priorities")
        else:
            st.info("No priorities linked to this species.")


# Main page logic
if st.session_state.species_view == "list":
    show_list_view()
elif st.session_state.species_view == "detail":
    show_detail_view()
