## areas_tbl
This defines the priority areas for biodiversity. There are 50 areas in total. This table will be joined to the (LNRS Priority Areas for Biodiversity — WECA-open-data (opendatasoft.com). The dataset currently has 111 records because multiple polygons have a common ID. The area_id field joins to id on the published dataset.
## species_tbl
We have defined 39 species of importance in the context of the LNRS, listed in the species_tbl, which also contains data about the species derived from the GBIF. Species are related to areas and priorities. So multiple species are important for a given area and (potentially different) species are important for different priorities. Species are related to areas and priorities through the relevant lookup tables.
## priorities_tbl
There are 33 priorities for biodiversity in the region, grouped into themes. Each priority can apply to multiple areas, and each area can have multiple priorities.
## measures_tbl
Measures can be thought of as actions, or recommendations for actions which will deliver biodiversity priorities in appropriate areas. Measures have been split into two tables, because there are some area – specific measures (which also deliver on a priority), and many priority – specific measures which could apply in multiple areas.
## area_measures_tbl
These are measures which relate specifically to an area, but also deliver a priority. The relationship with the priority is defined by the priorities_areas_measures_lookup_tbl.
## priority_measures_tbl
These are measures which could deliver priorities across any area in the region. They are linked to the priorities_tbl through the priorities_measures_lookup_tbl.
## grants_tbl
A range of financial incentives or grants are available to landowners. These can be related to areas or priorities, and they fund specific measures. Lookup tables connect grants to area_measures_tbl and priority_measures_tbl.