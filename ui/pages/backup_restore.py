"""Backup & Restore page - View and restore database snapshots.

This page is only functional in local development mode.
On Streamlit Cloud, backups are disabled due to ephemeral filesystem.
"""

import logging
import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.backup import BackupManager  # noqa: E402

logger = logging.getLogger(__name__)

# Page configuration
st.title("💾 Database Backup & Restore")

# Initialize backup manager
backup_mgr = BackupManager()

# Check if backups are enabled
if not backup_mgr.enabled:
    st.warning(
        "⚠️ **Backup functionality is disabled**\n\n"
        "You are running on Streamlit Cloud, which has an ephemeral filesystem. "
        "Any backups created would be lost when the app restarts or redeploys.\n\n"
        "**For production deployment:**\n"
        "- MotherDuck provides cloud infrastructure reliability\n"
        "- Database changes are persisted in the cloud\n"
        "- No local backups are necessary\n\n"
        "**For local development:**\n"
        "- Run the app locally with `DATABASE_MODE=local`\n"
        "- Full backup/restore functionality will be available"
    )
    st.info(
        "💡 **Tip:** Use MotherDuck's time-travel features for point-in-time recovery "
        "in production environments."
    )
    st.stop()  # Don't render the rest of the page

# Initialize session state for modals
if "preview_snapshot_id" not in st.session_state:
    st.session_state.preview_snapshot_id = None
if "restore_snapshot_id" not in st.session_state:
    st.session_state.restore_snapshot_id = None
if "restore_confirm_text" not in st.session_state:
    st.session_state.restore_confirm_text = ""

# Create tabs (only shown if backups are enabled)
tab1, tab2, tab3 = st.tabs(["📋 Snapshots", "➕ Create Backup", "⚙️ Settings"])

# TAB 1: View Snapshots
with tab1:
    st.header("Available Snapshots")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_operation = st.selectbox(
            "Filter by Operation",
            ["All", "delete", "update", "bulk_delete", "pre_restore", "manual"],
        )
    with col2:
        filter_entity = st.selectbox(
            "Filter by Entity",
            ["All", "measure", "area", "priority", "species", "habitat", "grant"],
        )
    with col3:
        limit = st.number_input(
            "Show last N snapshots", min_value=10, max_value=200, value=50
        )

    # Get snapshots
    operation_filter = None if filter_operation == "All" else filter_operation
    entity_filter = None if filter_entity == "All" else filter_entity

    snapshots = backup_mgr.list_snapshots(
        operation_type=operation_filter, entity_type=entity_filter, limit=limit
    )

    if not snapshots:
        st.info("No snapshots found matching filters")
    else:
        st.success(f"Found {len(snapshots)} snapshots")

        # Display snapshots
        for idx, snapshot in enumerate(snapshots):
            with st.expander(
                f"📸 {snapshot['datetime']} - {snapshot['description']} ({snapshot['size_mb']} MB)",
                expanded=False,
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write("**Snapshot Details:**")
                    st.write(f"- **ID:** `{snapshot['snapshot_id']}`")
                    st.write(f"- **Description:** {snapshot['description']}")
                    st.write(f"- **Date:** {snapshot['datetime']}")
                    st.write(
                        f"- **Operation:** {snapshot.get('operation_type', 'N/A') or 'N/A'}"
                    )
                    st.write(
                        f"- **Entity Type:** {snapshot.get('entity_type', 'N/A') or 'N/A'}"
                    )
                    st.write(
                        f"- **Entity ID:** {snapshot.get('entity_id', 'N/A') or 'N/A'}"
                    )
                    st.write(f"- **Size:** {snapshot['size_mb']} MB")
                    st.write(f"- **File:** `{snapshot['file_path']}`")

                with col2:
                    st.write("**Actions:**")

                    # Preview button
                    if st.button("🔍 Preview", key=f"preview_{idx}"):
                        st.session_state.preview_snapshot_id = snapshot["snapshot_id"]
                        st.rerun()

                    # Restore button
                    if st.button(
                        "⚠️ Restore", key=f"restore_{idx}", type="primary"
                    ):
                        st.session_state.restore_snapshot_id = snapshot["snapshot_id"]
                        st.session_state.restore_confirm_text = ""
                        st.rerun()

# TAB 2: Create Manual Backup
with tab2:
    st.header("Create Manual Backup")

    st.info(
        "💡 **Tip:** Automatic snapshots are created before all delete operations. "
        "Use manual backups before making major changes or for periodic archival."
    )

    with st.form("create_backup_form"):
        description = st.text_input(
            "Backup Description*",
            placeholder="e.g., Before bulk update of measures",
        )

        submit = st.form_submit_button("Create Backup", type="primary")

        if submit:
            if not description:
                st.error("❌ Please provide a description")
            else:
                try:
                    with st.spinner("Creating backup..."):
                        snapshot_id = backup_mgr.create_snapshot(
                            description=description, operation_type="manual"
                        )

                    st.success("✅ Backup created successfully!")
                    st.code(f"Snapshot ID: {snapshot_id}")
                    logger.info(f"Manual backup created: {snapshot_id}")

                except Exception as e:
                    st.error(f"❌ Failed to create backup: {str(e)}")
                    logger.exception("Manual backup failed")

# TAB 3: Settings
with tab3:
    st.header("Backup Settings")

    # Storage info
    st.subheader("💾 Storage Information")
    snapshots = backup_mgr.list_snapshots()
    total_size = sum(s["size_mb"] for s in snapshots)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Snapshots", len(snapshots))
    with col2:
        st.metric("Total Storage", f"{total_size:.2f} MB")

    # Cleanup
    st.subheader("🗑️ Cleanup Old Snapshots")

    with st.form("cleanup_form"):
        keep_count = st.number_input(
            "Number of snapshots to keep",
            min_value=5,
            max_value=200,
            value=50,
            help="Older snapshots will be deleted",
        )

        cleanup = st.form_submit_button("Clean Up", type="secondary")

        if cleanup:
            try:
                deleted = backup_mgr.cleanup_old_snapshots(keep_count=keep_count)
                if deleted > 0:
                    st.success(f"✅ Deleted {deleted} old snapshots")
                    logger.info(f"Cleaned up {deleted} snapshots, kept {keep_count}")
                    st.rerun()
                else:
                    st.info("No snapshots to delete")
            except Exception as e:
                st.error(f"❌ Cleanup failed: {str(e)}")
                logger.exception("Cleanup failed")


# PREVIEW MODAL
if st.session_state.preview_snapshot_id:
    snapshot_id = st.session_state.preview_snapshot_id

    st.divider()
    st.subheader(f"🔍 Preview Snapshot: {snapshot_id}")

    try:
        # Open snapshot in read-only mode
        snapshot_path = f"data/backups/{snapshot_id}.duckdb"
        preview_conn = duckdb.connect(snapshot_path, read_only=True)

        # Show summary stats
        col1, col2, col3 = st.columns(3)

        with col1:
            measure_count = preview_conn.execute(
                "SELECT COUNT(*) FROM measure"
            ).fetchone()[0]
            st.metric("Measures", measure_count)

        with col2:
            area_count = preview_conn.execute(
                "SELECT COUNT(*) FROM area"
            ).fetchone()[0]
            st.metric("Areas", area_count)

        with col3:
            priority_count = preview_conn.execute(
                "SELECT COUNT(*) FROM priority"
            ).fetchone()[0]
            st.metric("Priorities", priority_count)

        # Show recent measures
        st.write("**Recent Measures:**")
        measures_df = preview_conn.execute(
            "SELECT measure_id, measure_name FROM measure ORDER BY measure_id DESC LIMIT 10"
        ).df()
        st.dataframe(measures_df, use_container_width=True)

        preview_conn.close()

        if st.button("Close Preview"):
            st.session_state.preview_snapshot_id = None
            st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to preview snapshot: {str(e)}")
        logger.exception(f"Preview failed for {snapshot_id}")


# RESTORE CONFIRMATION MODAL
if st.session_state.restore_snapshot_id:
    snapshot_id = st.session_state.restore_snapshot_id

    st.divider()
    st.warning("⚠️ **RESTORE DATABASE**")
    st.write(f"You are about to restore the database from snapshot: `{snapshot_id}`")

    st.error(
        """
    **WARNING:** This action will:
    - Replace the current database with the snapshot
    - Create a safety backup of the current state first
    - Disconnect all active sessions
    - **ALL changes since the snapshot will be LOST**
    """
    )

    # Confirmation input
    confirm_text = st.text_input(
        "Type RESTORE to confirm",
        key="restore_confirmation_input",
        value=st.session_state.restore_confirm_text,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Cancel", key="restore_cancel"):
            st.session_state.restore_snapshot_id = None
            st.session_state.restore_confirm_text = ""
            st.rerun()

    with col2:
        if st.button("⚠️ RESTORE NOW", key="restore_execute", type="primary"):
            if confirm_text != "RESTORE":
                st.error("❌ Please type RESTORE to confirm")
            else:
                try:
                    with st.spinner(
                        "Restoring database... This may take a moment."
                    ):
                        backup_mgr.restore_snapshot(snapshot_id)

                    st.success("✅ Database restored successfully!")
                    st.info("Please refresh the page to see the restored data.")
                    logger.info(f"Database restored from snapshot: {snapshot_id}")

                    # Clear session state
                    st.session_state.restore_snapshot_id = None
                    st.session_state.restore_confirm_text = ""

                    # Clear all caches
                    st.cache_data.clear()

                except Exception as e:
                    st.error(f"❌ Restore failed: {str(e)}")
                    logger.exception(f"Restore failed for {snapshot_id}")
