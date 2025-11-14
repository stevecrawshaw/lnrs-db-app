"""Schema diagram generation utilities.

This module provides functions to parse the database schema XML file
and generate Mermaid ER diagrams for visualization in Streamlit.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple


class Table:
    """Represents a database table."""

    def __init__(self, name: str):
        self.name = name
        self.columns: List[Tuple[str, str, str]] = []  # (name, type, nullable)
        self.primary_keys: Set[str] = set()
        self.foreign_keys: Dict[str, str] = {}  # {column_name: referenced_table}

    def add_column(self, name: str, col_type: str, nullable: str):
        """Add a column to the table."""
        self.columns.append((name, col_type, nullable))

    def infer_primary_key(self):
        """Infer primary key from column names."""
        # Common PK patterns: <table>_id, id
        for col_name, _, _ in self.columns:
            if col_name == f"{self.name}_id" or (
                col_name == "id" and self.name != "source_table"
            ):
                self.primary_keys.add(col_name)

    def infer_foreign_keys(self, all_tables: Dict[str, "Table"]):
        """Infer foreign keys from column names."""
        for col_name, _, _ in self.columns:
            # Skip if it's this table's PK
            if col_name in self.primary_keys:
                continue

            # Look for _id suffix pattern
            if col_name.endswith("_id"):
                # Extract potential table name
                potential_table = col_name[:-3]  # Remove '_id'

                # Check if this table exists
                if potential_table in all_tables:
                    self.foreign_keys[col_name] = potential_table

    def is_bridge_table(self) -> bool:
        """Check if this is a bridge/junction table for many-to-many relationships."""
        bridge_indicators = [
            "_has_",
            "_area_priority",
            "habitat_creation_area",
            "habitat_management_area",
            "species_area_priority",
            "area_funding_schemes",
        ]
        return any(indicator in self.name for indicator in bridge_indicators)


class SchemaParser:
    """Parses XML schema and generates Mermaid diagrams."""

    def __init__(self, schema_path: str | Path):
        self.schema_path = Path(schema_path)
        self.tables: Dict[str, Table] = {}
        self._parse_schema()

    def _parse_schema(self):
        """Parse the XML schema file."""
        tree = ET.parse(self.schema_path)
        root = tree.getroot()

        # Parse all tables
        for table_elem in root.findall("table"):
            table_name = table_elem.get("name")
            table = Table(table_name)

            # Parse columns
            for col_elem in table_elem.findall("column"):
                col_name = col_elem.get("name")
                col_type = col_elem.get("type")
                nullable = col_elem.get("nullable")
                table.add_column(col_name, col_type, nullable)

            self.tables[table_name] = table

        # Infer primary and foreign keys
        for table in self.tables.values():
            table.infer_primary_key()

        for table in self.tables.values():
            table.infer_foreign_keys(self.tables)

    def get_core_tables(self) -> Set[str]:
        """Get the core entity tables (non-bridge, non-view)."""
        core = set()
        for name, table in self.tables.items():
            # Skip views
            if name.endswith("_vw"):
                continue
            # Skip bridge tables
            if table.is_bridge_table():
                continue
            # Skip source_table (legacy)
            if name == "source_table":
                continue
            core.add(name)
        return core

    def get_bridge_tables(self) -> Set[str]:
        """Get bridge/junction tables for many-to-many relationships."""
        return {name for name, table in self.tables.items() if table.is_bridge_table()}

    def _generate_table_mermaid(self, table: Table, include_all_columns: bool = False) -> str:
        """Generate Mermaid syntax for a single table."""
        lines = [f"    {table.name.upper()} {{"]

        # Determine which columns to include
        columns_to_show = []
        if include_all_columns:
            columns_to_show = table.columns
        else:
            # Show only key columns (PKs and FKs)
            for col_name, col_type, _ in table.columns:
                if col_name in table.primary_keys or col_name in table.foreign_keys:
                    columns_to_show.append((col_name, col_type, ""))

        # Add columns
        for col_name, col_type, _ in columns_to_show:
            # Determine key type
            key_type = ""
            if col_name in table.primary_keys:
                key_type = " PK"
            elif col_name in table.foreign_keys:
                key_type = " FK"

            lines.append(f"        {col_type} {col_name}{key_type}")

        lines.append("    }")
        return "\n".join(lines)

    def _generate_relationships_mermaid(
        self, tables_to_include: Set[str]
    ) -> List[str]:
        """Generate Mermaid relationship syntax."""
        relationships = []
        added_relationships = set()

        for table_name in tables_to_include:
            table = self.tables.get(table_name)
            if not table:
                continue

            for fk_col, ref_table in table.foreign_keys.items():
                # Only include if both tables are in the diagram
                if ref_table not in tables_to_include:
                    continue

                # Avoid duplicate relationships
                rel_key = f"{ref_table}-{table_name}"
                if rel_key in added_relationships:
                    continue
                added_relationships.add(rel_key)

                # Determine relationship cardinality
                # If this is a bridge table, it's many-to-many
                if table.is_bridge_table():
                    # Bridge table has many-to-one relationship with each parent
                    relationships.append(
                        f"    {ref_table.upper()} ||--o{{ {table_name.upper()} : \"has\""
                    )
                else:
                    # Regular one-to-many
                    relationships.append(
                        f"    {ref_table.upper()} ||--o{{ {table_name.upper()} : \"has\""
                    )

        return relationships

    def generate_full_diagram(self, include_all_columns: bool = False) -> str:
        """Generate a complete ER diagram with all tables."""
        # Exclude views and source_table
        tables_to_include = {
            name
            for name in self.tables.keys()
            if not name.endswith("_vw") and name != "source_table"
        }

        return self._generate_diagram(tables_to_include, include_all_columns)

    def generate_core_diagram(self, include_all_columns: bool = False) -> str:
        """Generate ER diagram with core tables and their immediate relationships."""
        core_tables = self.get_core_tables()

        # Add bridge tables that connect core tables
        bridge_tables = set()
        for bridge_name, bridge_table in self.tables.items():
            if not bridge_table.is_bridge_table():
                continue

            # Check if this bridge connects core tables
            connects_core = all(
                ref_table in core_tables
                for ref_table in bridge_table.foreign_keys.values()
            )
            if connects_core:
                bridge_tables.add(bridge_name)

        tables_to_include = core_tables | bridge_tables
        return self._generate_diagram(tables_to_include, include_all_columns)

    def generate_domain_diagram(
        self, domain: str, include_all_columns: bool = False
    ) -> str:
        """Generate ER diagram for a specific domain.

        Args:
            domain: One of 'species', 'habitat', 'grant', 'measure-area-priority'
            include_all_columns: Whether to show all columns or just keys
        """
        domain_tables = {
            "species": {
                "species",
                "measure_has_species",
                "species_area_priority",
                "measure",
                "area",
                "priority",
            },
            "habitat": {
                "habitat",
                "habitat_creation_area",
                "habitat_management_area",
                "area",
            },
            "grant": {
                "grant_table",
                "measure_area_priority_grant",
                "measure",
                "area",
                "priority",
            },
            "measure-area-priority": {
                "measure",
                "area",
                "priority",
                "measure_area_priority",
                "measure_area_priority_grant",
                "grant_table",
            },
        }

        tables_to_include = domain_tables.get(domain, set())
        if not tables_to_include:
            raise ValueError(f"Unknown domain: {domain}")

        return self._generate_diagram(tables_to_include, include_all_columns)

    def _generate_diagram(
        self, tables_to_include: Set[str], include_all_columns: bool = False
    ) -> str:
        """Generate Mermaid ER diagram syntax."""
        lines = ["erDiagram"]

        # Add table definitions
        for table_name in sorted(tables_to_include):
            table = self.tables.get(table_name)
            if table:
                lines.append(self._generate_table_mermaid(table, include_all_columns))

        # Add relationships
        lines.append("")
        lines.extend(self._generate_relationships_mermaid(tables_to_include))

        return "\n".join(lines)


def generate_mermaid_html(mermaid_code: str, height: int = 600) -> str:
    """Generate HTML with embedded Mermaid diagram with interactive zoom/pan.

    Args:
        mermaid_code: Mermaid diagram syntax
        height: Height of the diagram container in pixels

    Returns:
        HTML string with embedded Mermaid diagram and zoom controls
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                er: {{
                    fontSize: 18,
                    useMaxWidth: false,
                    layoutDirection: 'TB'
                }}
            }});
        </script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                padding: 0;
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                overflow: hidden;
            }}
            #container {{
                position: relative;
                width: 100vw;
                height: 100vh;
                overflow: hidden;
                background-color: white;
            }}
            #diagram-container {{
                width: 100%;
                height: calc(100% - 60px);
                overflow: hidden;
                position: relative;
                cursor: grab;
            }}
            #diagram-container:active {{
                cursor: grabbing;
            }}
            .mermaid {{
                min-width: 100%;
                min-height: 100%;
                display: flex;
                justify-content: center;
                align-items: flex-start;
                padding: 20px;
            }}
            .mermaid svg {{
                max-width: none !important;
                height: auto !important;
            }}
            #controls {{
                position: absolute;
                top: 10px;
                right: 10px;
                display: flex;
                gap: 8px;
                z-index: 1000;
                background: white;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .control-btn {{
                background: #0066cc;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            .control-btn:hover {{
                background: #0052a3;
                transform: translateY(-1px);
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            .control-btn:active {{
                transform: translateY(0);
            }}
            #info {{
                position: absolute;
                bottom: 10px;
                left: 10px;
                background: rgba(255, 255, 255, 0.95);
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 13px;
                color: #666;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                z-index: 1000;
            }}
        </style>
    </head>
    <body>
        <div id="container">
            <div id="controls">
                <button class="control-btn" onclick="zoomIn()">
                    <span>🔍</span> Zoom In
                </button>
                <button class="control-btn" onclick="zoomOut()">
                    <span>🔍</span> Zoom Out
                </button>
                <button class="control-btn" onclick="resetZoom()">
                    <span>↺</span> Reset
                </button>
                <button class="control-btn" onclick="fitToScreen()">
                    <span>⛶</span> Fit Screen
                </button>
            </div>
            <div id="info">
                💡 Use mouse wheel to zoom • Click and drag to pan • Use controls to navigate
            </div>
            <div id="diagram-container">
                <div class="mermaid">
{mermaid_code}
                </div>
            </div>
        </div>
        <script>
            let panZoomInstance = null;
            let currentScale = 1;

            // Wait for Mermaid to render
            setTimeout(() => {{
                const svg = document.querySelector('.mermaid svg');
                if (svg) {{
                    // Initialize svg-pan-zoom
                    panZoomInstance = svgPanZoom(svg, {{
                        zoomEnabled: true,
                        controlIconsEnabled: false,
                        fit: true,
                        center: true,
                        minZoom: 0.1,
                        maxZoom: 10,
                        zoomScaleSensitivity: 0.3,
                        dblClickZoomEnabled: true,
                        mouseWheelZoomEnabled: true,
                        preventMouseEventsDefault: true,
                        contain: false
                    }});

                    // Initial zoom to fit
                    setTimeout(() => {{
                        panZoomInstance.fit();
                        panZoomInstance.center();
                        // Zoom out slightly for better initial view
                        panZoomInstance.zoom(0.9);
                    }}, 100);
                }}
            }}, 500);

            function zoomIn() {{
                if (panZoomInstance) {{
                    panZoomInstance.zoomIn();
                }}
            }}

            function zoomOut() {{
                if (panZoomInstance) {{
                    panZoomInstance.zoomOut();
                }}
            }}

            function resetZoom() {{
                if (panZoomInstance) {{
                    panZoomInstance.resetZoom();
                    panZoomInstance.center();
                }}
            }}

            function fitToScreen() {{
                if (panZoomInstance) {{
                    panZoomInstance.fit();
                    panZoomInstance.center();
                    panZoomInstance.zoom(0.9);
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html


def get_schema_path() -> Path:
    """Get the path to the schema XML file."""
    # Assume we're running from project root
    return Path(__file__).parent.parent / "lnrs_3nf_o1_schema.xml"
