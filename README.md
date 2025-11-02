# CRUD App for LNRS Database

This is a simple CRUD (Create, Read, Update, Delete) application for managing a database of LNRS (Local Nature Recovery Strategy) entries. The application allows users to add, view, update, and delete records in tables.

## Features

- Create new records in the LNRS database.
- Read and display existing records.
- Update existing records.
- Delete records from the database, respecting CASCADING deletes.

The database is stored in a DuckDB database file named `data/lnrs_3nf_o1.duckdb`.
The schema is in `data/lnrs_3nf_o1.sql`.

## Requirements

- An app to enable all CRUD operations on the LNRS database.
- Use DuckDB as the database engine.
- Use streamlit for the web interface.
- Use duckDB's relational python API for data manipulation wherever possible.
- Use SQL queries for complex operations if needed.
- Ensure all operations respect CASCADING deletes.
- Include documentation on how to set up and run the application.
- Ensure the app is responsive and works on different screen sizes.
- Ensure the app is user-friendly and intuitive.
- Ensure the app is easy to maintain and host.
- Include error handling for database operations.



