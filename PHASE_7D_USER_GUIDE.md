# Phase 7D User Guide: Bulk Operations & Data Export

**Created**: 2025-11-03
**App URL**: http://localhost:8502

---

## 🚀 Quick Start

The Streamlit app is now running! Access it at: **http://localhost:8502**

All Phase 7D features are located in the **Relationships** section of the app.

---

## 📍 How to Access Phase 7D Features

### Step 1: Launch the Application

```bash
cd /home/steve/projects/lnrs-db-app
uv run streamlit run app.py
```

The app will open in your browser at `http://localhost:8502`

### Step 2: Navigate to the Features

The navigation sidebar has **4 sections**:
1. **Main** - Dashboard
2. **Entities** - All entity CRUD pages
3. **Relationships** - Bridge table management
4. **Export** - Data export (NEW!)

**For Bulk Create**: Click **"🔗 Relationships"** in sidebar
**For Data Export**: Click **"📊 Data Export"** in sidebar

---

## ✨ Feature 1: Bulk Create Links

**Location**: Relationships → Measure-Area-Priority tab (first tab)

### What You'll See:

At the top of the Measure-Area-Priority tab, you'll see **two buttons side by side**:
- **Left button**: `➕ Create New Link` (creates single links)
- **Right button**: `➕➕ Bulk Create Links` (NEW - this is the Phase 7D feature!)

### How to Use Bulk Create:

1. Click the **`➕➕ Bulk Create Links`** button
2. A form will appear with three multi-select dropdowns:
   - **Select Measures**: Choose one or more measures (e.g., "1 - On areas that are currently...")
   - **Select Areas**: Choose one or more areas (e.g., "1 - ASNW buffers & corridors")
   - **Select Priorities**: Choose one or more priorities (e.g., "1 - [Biodiversity] The extent...")

3. As you select items, you'll see a warning message showing:
   ```
   ⚠️ This will attempt to create X links
   (M measures × A areas × P priorities)
   ```

4. Click **`Create X Links`** button (disabled if no selections made)

5. The system will:
   - Create all possible combinations (Cartesian product)
   - Skip links that already exist
   - Report how many were created
   - Show any errors in an expandable section

### Example:
- Select 2 measures, 3 areas, 1 priority
- System will attempt to create 2 × 3 × 1 = **6 links**
- If 2 already exist, it will create 4 and report "2 already exist"

---

## 📊 Feature 2: Data Export Page

**Location**: Sidebar → Export section → 📊 Data Export

### What You'll See:

The Data Export page (standalone navigation entry) has **two main sections**:

#### Section 1: APMG Slim View Export (Top Section)

This is the **main export feature** - exports the complete denormalized view.

**What's Displayed:**
- Description of what APMG Slim View contains
- List of all columns included
- **Total Records** metric (shows ~6,528 records)
- **`📥 Download APMG CSV`** button (large, primary button)
- Filename preview with timestamp

**How to Export:**
1. Click the **`📥 Download APMG CSV`** button
2. Your browser will download a file named: `apmg_slim_export_2025-11-03_HHMMSS.csv`
3. The file contains all 6,528 records with 14 columns

**What's in the Export:**
- All Area-Priority-Measure-Grant relationships
- Fully denormalized (no need to join tables)
- Includes: measures, areas, priorities, grants, stakeholders, types
- Ready for Excel, Tableau, or other analysis tools

#### Section 2: Bridge Table Exports (Bottom Section)

Six smaller export buttons arranged in a 3×2 grid:

**Row 1:**
1. **Measure-Area-Priority** (2,936 records)
2. **Grant Funding** (3,271 records)
3. **Species-Area-Priority** (2,505 records)

**Row 2:**
4. **Habitat Creation** (681 records)
5. **Habitat Management** (817 records)
6. **Unfunded Links** (1,589 records)

**How to Export Individual Tables:**
1. Look at the record count for the table you want
2. Click the **`📥 Download CSV`** button under that table
3. File downloads with a timestamp (e.g., `measure_area_priority_2025-11-03_HHMMSS.csv`)

---

## 🎯 Common Use Cases

### Use Case 1: Bulk Linking a New Measure to Multiple Areas

**Scenario**: You've created a new measure and need to link it to 20 areas and 5 priorities (100 combinations).

**Steps:**
1. Go to: Relationships → Measure-Area-Priority tab
2. Click: `➕➕ Bulk Create Links`
3. Select: 1 measure, 20 areas, 5 priorities
4. Preview: "This will create 100 links"
5. Click: `Create 100 Links`
6. Done! All 100 links created in seconds

### Use Case 2: Exporting All Relationships for Analysis

**Scenario**: You need to analyze all biodiversity measures across areas in Excel.

**Steps:**
1. Go to: Relationships → 📊 Data Export tab
2. See: "Total Records: 6,528"
3. Click: `📥 Download APMG CSV`
4. Open file in Excel or your preferred tool
5. All relationships are in one denormalized table, ready to analyze

### Use Case 3: Finding Unfunded Opportunities

**Scenario**: Identify which measure-area-priority combinations lack grant funding.

**Steps:**
1. Go to: Relationships → 📊 Data Export tab
2. Scroll to: Bridge Table Exports section
3. Click: `📥 Download CSV` under "Unfunded Links"
4. You get: 1,589 unfunded combinations
5. Use this to prioritize grant applications

---

## ✅ Verification Checklist

Use this checklist to confirm Phase 7D is working:

- [ ] **App Running**: Visit http://localhost:8502 - you see the dashboard
- [ ] **Four Sections**: Sidebar shows Main, Entities, Relationships, and Export sections
- [ ] **Relationships Page**: Click "🔗 Relationships" - you see 5 tabs
- [ ] **Bulk Button**: On first tab, you see "➕➕ Bulk Create Links" button
- [ ] **Bulk Form**: Click bulk button - form appears with 3 multi-selects
- [ ] **Export Page**: Click "📊 Data Export" in sidebar - dedicated export page opens
- [ ] **APMG Export**: You see "Total Records: 6,528" metric
- [ ] **Download Button**: "📥 Download APMG CSV" button is present and clickable
- [ ] **Bridge Exports**: You see 6 download buttons in a grid layout

---

## 🐛 Troubleshooting

### Problem: Can't see "Relationships" in sidebar
**Solution**:
- Refresh the page (Ctrl+R or Cmd+R)
- Check the sidebar is expanded (click hamburger menu top-left)
- Look for the third section labeled "Relationships"

### Problem: Don't see "📊 Data Export" in sidebar
**Solution**:
- You should see a separate "Export" section in the sidebar (4th section)
- If you don't see it, refresh the page (Ctrl+R or Cmd+R)
- Check that `app.py` includes the data_export_page definition
- Verify `ui/pages/data_export.py` file exists

### Problem: Bulk Create button not showing
**Solution**:
- Make sure you're on the first tab "Measure-Area-Priority"
- Look for two buttons at the top: single create (left) and bulk create (right)
- If missing, check lines 60-67 in `ui/pages/relationships.py`

### Problem: Download button doesn't work
**Solution**:
- Check browser console for errors (F12)
- Ensure you have write permissions in your downloads folder
- Try a different browser

### Problem: "Loading data..." spinner never stops
**Solution**:
- Check database connection: `test_phase_7d.py` should run without errors
- Ensure database file exists at: `data/lnrs_3nf_o1.duckdb`
- Restart the Streamlit app

---

## 📁 File Locations

If you need to modify the code:

| Feature | File | Lines |
|---------|------|-------|
| Bulk Create Method | `models/relationship.py` | 636-674 |
| APMG Export Method | `models/relationship.py` | 680-710 |
| Bulk Create UI | `ui/pages/relationships.py` | 60-67, 279-388 |
| Data Export Page | `ui/pages/data_export.py` | 1-220 (entire file) |
| Tab Registration | `ui/pages/relationships.py` | 933-954 |
| App Navigation | `app.py` | 16-42 |

---

## 🔢 Data Volumes

Current database statistics (as of 2025-11-03):

| Dataset | Record Count | Export Size |
|---------|-------------|-------------|
| **APMG Slim View** | **6,528** | **4.95 MB** |
| Measure-Area-Priority | 2,936 | 1.9 MB |
| Grant Funding | 3,271 | 1.7 MB |
| Species-Area-Priority | 2,505 | 893 KB |
| Habitat Creation | 681 | 51 KB |
| Habitat Management | 817 | 61 KB |
| Unfunded Links | 1,589 | 464 KB |

---

## 🎓 Tips & Best Practices

### For Bulk Create:
1. **Start small**: Test with 1-2 items in each dropdown first
2. **Check preview**: Always review the "will create X links" message
3. **Review errors**: If many links already exist, that's normal
4. **Use for new measures**: Most useful when adding new measures to existing areas

### For Exports:
1. **APMG for analysis**: Use the main APMG export for comprehensive analysis
2. **Bridge tables for focused**: Use individual exports for specific relationships
3. **Unfunded links for planning**: Export unfunded links to identify grant opportunities
4. **Timestamps are automatic**: Files include timestamps, no need to rename

### For Performance:
1. **Large exports**: APMG export is 4.95 MB - may take 2-3 seconds
2. **Browser downloads**: Ensure you have adequate disk space
3. **Multiple exports**: You can download multiple files - each has a unique timestamp

---

## 📞 Support

If you encounter issues:

1. **Run tests**: `uv run python test_phase_7d.py`
2. **Check logs**: Look at the terminal where Streamlit is running
3. **Database check**: Verify `data/lnrs_3nf_o1.duckdb` exists and is ~22 MB
4. **Review documentation**: See `PHASE_7_IMPLEMENTATION.md` for technical details

---

**Phase 7D Status**: ✅ Complete and Production Ready
**Last Updated**: 2025-11-03
**Version**: 1.0
