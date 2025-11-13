"""Database backup and restore functionality.

This module provides database snapshot capabilities for local development.

IMPORTANT: Backup functionality is only available in local development.
On Streamlit Cloud (ephemeral filesystem), backups are gracefully disabled.
For production deployment, MotherDuck provides cloud infrastructure reliability.
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.monitoring import monitor_performance

logger = logging.getLogger(__name__)


class BackupManager:
    """Manage database backups and snapshots.

    NOTE: Backup functionality is only available in local development.
    On Streamlit Cloud (ephemeral filesystem), backups are gracefully disabled.

    Attributes:
        enabled: Whether backup functionality is available
        is_cloud: Whether running on Streamlit Cloud
        backup_dir: Directory for storing backups (local only)
        metadata_file: JSON file tracking snapshots (local only)
        db_path: Path to database file (local only)
    """

    def __init__(self):
        """Initialize backup manager with environment detection."""
        # Detect cloud environment
        self.is_cloud = self._detect_cloud_environment()

        if self.is_cloud:
            logger.warning(
                "Backup functionality disabled: Running on Streamlit Cloud "
                "(ephemeral filesystem). Backups would be lost on restart."
            )
            self.enabled = False
            self.backup_dir = None
            self.metadata_file = None
            self.db_path = None
        else:
            self.enabled = True
            self.backup_dir = Path("data/backups")
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.metadata_file = self.backup_dir / "snapshot_metadata.json"
            self.db_path = Path("data/lnrs_3nf_o1.duckdb")
            logger.info("Backup functionality enabled (local development mode)")

    def _detect_cloud_environment(self) -> bool:
        """Detect if running on Streamlit Cloud.

        Checks multiple indicators:
        - STREAMLIT_SHARING_MODE environment variable
        - STREAMLIT_SERVER_HEADLESS environment variable
        - Typical cloud deployment path patterns

        Returns:
            True if running on Streamlit Cloud, False otherwise
        """
        # Streamlit Cloud sets these environment variables
        cloud_indicators = [
            os.getenv("STREAMLIT_SHARING_MODE"),
            os.getenv("STREAMLIT_SERVER_HEADLESS") == "true",
        ]

        # Also check if we're in a typical cloud deployment path
        is_cloud = any(cloud_indicators) or "/mount/src/" in str(Path.cwd())

        return is_cloud

    @monitor_performance("snapshot_create")
    def create_snapshot(
        self,
        description: str,
        operation_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
    ) -> Optional[str]:
        """Create a database snapshot.

        Args:
            description: Human-readable description
            operation_type: Type of operation (delete, update, manual, etc.)
            entity_type: Entity type (measure, area, priority, etc.)
            entity_id: ID of entity being modified

        Returns:
            snapshot_id: Unique identifier for the snapshot, or None if disabled

        Raises:
            Exception: If snapshot creation fails (when enabled)
        """
        if not self.enabled:
            logger.debug(f"Snapshot creation skipped (disabled): {description}")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Build filename
        parts = [timestamp]
        if operation_type:
            parts.append(operation_type)
        if entity_type:
            parts.append(entity_type)
        if entity_id:
            parts.append(str(entity_id))

        snapshot_id = "_".join(parts)
        snapshot_path = self.backup_dir / f"{snapshot_id}.duckdb"

        try:
            # Create snapshot (file copy)
            logger.info(f"Creating snapshot: {snapshot_id}")
            shutil.copy2(self.db_path, snapshot_path)

            # Calculate size
            size_mb = snapshot_path.stat().st_size / (1024**2)

            # Save metadata
            metadata = {
                "snapshot_id": snapshot_id,
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(),
                "description": description,
                "operation_type": operation_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "file_path": str(snapshot_path),
                "size_mb": round(size_mb, 2),
            }

            self._save_metadata(metadata)

            logger.info(f"Created snapshot {snapshot_id} ({size_mb:.2f} MB)")
            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}", exc_info=True)
            raise

    def list_snapshots(
        self,
        operation_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """List all available snapshots with filtering.

        Args:
            operation_type: Filter by operation type
            entity_type: Filter by entity type
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot metadata dicts, newest first
        """
        if not self.enabled:
            logger.debug("Snapshot listing skipped (disabled)")
            return []

        if not self.metadata_file.exists():
            return []

        try:
            with open(self.metadata_file, "r") as f:
                all_snapshots = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to read snapshot metadata: {e}")
            return []

        # Filter
        snapshots = all_snapshots
        if operation_type:
            snapshots = [
                s for s in snapshots if s.get("operation_type") == operation_type
            ]
        if entity_type:
            snapshots = [s for s in snapshots if s.get("entity_type") == entity_type]

        # Sort by timestamp descending (newest first)
        snapshots.sort(key=lambda x: x["timestamp"], reverse=True)

        # Limit
        if limit:
            snapshots = snapshots[:limit]

        return snapshots

    @monitor_performance("snapshot_restore")
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore database from a snapshot.

        Creates a safety backup before restoring, closes database connections,
        replaces the database file, and verifies integrity.

        Args:
            snapshot_id: ID of snapshot to restore

        Returns:
            True if successful

        Raises:
            ValueError: If snapshot not found
            FileNotFoundError: If snapshot file missing
            Exception: If restore fails
        """
        if not self.enabled:
            logger.error("Restore attempted but backups are disabled")
            raise RuntimeError(
                "Backup functionality is disabled (running on Streamlit Cloud)"
            )

        # Import here to avoid circular dependency
        from config.database import DatabaseConnection

        # Find snapshot
        snapshots = self.list_snapshots()
        snapshot = next(
            (s for s in snapshots if s["snapshot_id"] == snapshot_id), None
        )

        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        snapshot_path = Path(snapshot["file_path"])

        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {snapshot_path}")

        try:
            # Create safety backup before restore
            logger.info(f"Creating safety backup before restore of {snapshot_id}")
            safety_snapshot_id = self.create_snapshot(
                description=f"Pre-restore safety backup (restoring {snapshot_id})",
                operation_type="pre_restore",
            )
            logger.info(f"Safety backup created: {safety_snapshot_id}")

            # Close all database connections
            logger.info("Closing database connections")
            db = DatabaseConnection()
            db.close()

            # Replace database file
            logger.info(f"Restoring from {snapshot_path}")
            shutil.copy2(snapshot_path, self.db_path)

            # Reconnect
            logger.info("Re-establishing database connection")
            db.reset_connection()
            db.get_connection()

            # Verify integrity
            self._verify_database_integrity()

            logger.info(f"Successfully restored snapshot {snapshot_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to restore snapshot {snapshot_id}: {e}", exc_info=True
            )
            raise

    def cleanup_old_snapshots(self, keep_count: int = 10) -> int:
        """Delete old snapshots, keeping only the most recent.

        Args:
            keep_count: Number of snapshots to keep (default: 10)

        Returns:
            Number of snapshots deleted
        """
        if not self.enabled:
            logger.debug("Snapshot cleanup skipped (disabled)")
            return 0

        snapshots = self.list_snapshots()

        if len(snapshots) <= keep_count:
            logger.debug(
                f"Cleanup not needed: {len(snapshots)} snapshots <= {keep_count} limit"
            )
            return 0

        to_delete = snapshots[keep_count:]
        deleted_count = 0

        for snapshot in to_delete:
            try:
                snapshot_path = Path(snapshot["file_path"])
                if snapshot_path.exists():
                    snapshot_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old snapshot {snapshot['snapshot_id']}")
                else:
                    logger.warning(
                        f"Snapshot file not found: {snapshot['snapshot_id']}"
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to delete snapshot {snapshot['snapshot_id']}: {e}"
                )

        # Update metadata
        kept_snapshots = snapshots[:keep_count]
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(kept_snapshots, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update metadata after cleanup: {e}")

        logger.info(
            f"Cleaned up {deleted_count} old snapshots (keeping {keep_count})"
        )
        return deleted_count

    def _save_metadata(self, new_snapshot: dict):
        """Append new snapshot metadata to file.

        Args:
            new_snapshot: Metadata dictionary for new snapshot
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    metadata = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Corrupted metadata file, starting fresh")
                metadata = []
        else:
            metadata = []

        metadata.append(new_snapshot)

        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def _verify_database_integrity(self):
        """Verify database can be opened and basic queries work.

        Raises:
            Exception: If database integrity check fails
        """
        from config.database import DatabaseConnection

        db = DatabaseConnection()
        conn = db.get_connection()

        try:
            # Test basic query
            result = conn.execute("SELECT COUNT(*) FROM measure").fetchone()
            measure_count = result[0]
            logger.info(
                f"Database integrity check passed: {measure_count} measures found"
            )
        except Exception as e:
            logger.error(f"Database integrity check failed: {e}", exc_info=True)
            raise
