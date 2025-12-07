# SHOCKWAVE PLANNER v2.0 - Quick Reference

**One-page guide for daily operations**

---

## 🚀 Starting Up

```bash
cd shockwave_v2
python3 main.py
```

**First time?** The splash screen shows for 3 seconds while loading.

---

## ⚡ Common Tasks

### Add a Launch
1. Click **âž• New Launch** (or Ctrl+N)
2. Fill form → **Save**

### Edit a Launch
1. Double-click launch in any view
2. Modify → **Save**

### Sync Latest Data
1. **Data** menu → **Sync Upcoming Launches**
2. Wait ~30 seconds
3. Review results

### Search Launches
1. Go to **Launch List View** tab
2. Type in search box (searches everything)

### Filter by Date
1. **Launch List View** tab
2. Select date range dropdown:
   - Previous 7/30 days
   - Current (today)
   - Next 30 days
   - Custom range

---

## 📅 Timeline Views

### Navigate Months
- **◀ Previous Month** / **Next Month ▶**

### Expand/Collapse Groups
- Click country/region headers (e.g., "▶ China")

### View Launch Details
- Click on numbered date cells

### Adjust Turnaround
- Use spinner: "Pad turnaround (days)"
- Shows pad unavailability after launch

---

## 🔍 Finding Information

| What | Where | How |
|------|-------|-----|
| Today's launches | List View → "Current" filter | |
| Upcoming week | List View → "Next 30 days" | |
| Specific mission | List View → Search box | Type mission name |
| Launch statistics | Statistics tab | |
| Last sync status | Statistics tab → "Last Space Devs Sync" | |
| NOTAM launches | List View → Search "A" | Yellow highlighted |

---

## 🎯 Views Quick Guide

### ðŸš€ Master Activity Schedule - Launch
- **Best for**: Visual timeline, pad planning
- **Shows**: Launches grouped by country/site
- **Features**: Turnaround visualization, expand/collapse

### ðŸ›¬ Master Activity Schedule - Re-entry
- **Best for**: Recovery operations planning
- **Shows**: Re-entries grouped by region
- **Features**: Drop zone tracking, recovery periods

### 📋 Launch List View
- **Best for**: Searching, detailed review
- **Shows**: Tabular list with all details
- **Features**: Real-time search, date filters, NOTAM highlighting

### 📊 Statistics
- **Best for**: Overview, success rates
- **Shows**: Totals, top rockets, by site
- **Features**: Sync status, trends

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New launch |
| Ctrl+Q | Exit |
| F5 | Refresh all views |

---

## 🔄 Space Devs Sync

### When to Sync
- **Daily**: Start of operations
- **Weekly**: Comprehensive update
- **As needed**: Before important planning

### Types of Sync

**Upcoming Launches** (most common):
- Menu: Data → Sync Upcoming Launches
- Gets: Next 100 launches
- Use: Daily operational planning

**Previous Launches** (historical):
- Menu: Data → Sync Previous Launches
- Gets: Last 50 launches
- Use: Backfilling history, analysis

### What Happens During Sync
1. Fetches data from Space Devs API
2. Matches existing launches (by external ID)
3. Updates changed launches
4. Adds new launches
5. Shows results dialog
6. Updates Statistics tab

---

## 🗄️ Database Quick Facts

**Location**: `shockwave_planner.db`

**Backup**:
```bash
cp shockwave_planner.db backup_$(date +%Y%m%d).db
```

**Manual Entries**: Have no `external_id` → won't be overwritten by sync

**API Entries**: Have `external_id` → will be updated by sync

---

## 🎨 Status Colors

| Color | Status | Meaning |
|-------|--------|---------|
| 🟡 Yellow | Scheduled | Launch planned |
| 🟢 Green | Go for Launch | Cleared to launch |
| 🟢 Dark Green | Success | Successful launch |
| 🔴 Red | Failure | Launch failed |
| 🟠 Orange | Partial Failure | Some objectives met |
| ⚫ Gray | Scrubbed | Launch cancelled |
| 🟡 Amber | Hold | Launch on hold |
| 🔵 Blue | In Flight | Vehicle flying |

---

## 📍 NOTAM Tracking

### Adding NOTAM
1. Edit launch
2. Fill "NOTAM Reference" field (e.g., "A1234/25")
3. Save

### Finding NOTAM Launches
- List View → Search for NOTAM number
- Launches with NOTAMs have yellow highlight

---

## 🐛 Quick Troubleshooting

### Application won't start
```bash
pip install PyQt6 requests --break-system-packages
python3 main.py
```

### Sync fails
- Check internet: `ping ll.thespacedevs.com`
- View error in Statistics tab
- Try again (transient network issues)

### Data missing
- Check date filters (may be filtering out)
- Enable "Show all" in timeline views
- Sync from Space Devs

### Slow performance
```bash
# Create database indexes
python3 -c "
from data.database import LaunchDatabase
db = LaunchDatabase()
db.conn.execute('CREATE INDEX IF NOT EXISTS idx_launches_date ON launches(launch_date)')
db.conn.commit()
db.close()
"
```

---

## 📱 Daily Workflow Example

### Morning Start
1. Launch SHOCKWAVE PLANNER
2. **Data** → **Sync Upcoming Launches**
3. Review Statistics tab for today's count
4. Switch to **Master Activity Schedule - Launch**
5. Check current month timeline

### Planning
1. Use **Next 30 days** filter in List View
2. Identify launches of interest
3. Check NOTAM status
4. Add any manual entries

### Analysis
1. Statistics tab for success rates
2. Export database for detailed reports (external tools)

### End of Day
1. Update any launch statuses
2. Add new information/NOTAMs
3. **File** → **Exit** (or Ctrl+Q)

---

## 🔧 Advanced: Command Line Sync

For automation/scripting:

```bash
# Sync upcoming (100 launches)
python3 data/space_devs.py upcoming 100

# Sync previous (50 launches)  
python3 data/space_devs.py previous 50

# Sync date range
python3 data/space_devs.py range 2025-01-01 2025-12-31
```

Add to cron for automatic daily sync:
```bash
# Daily at 6 AM
0 6 * * * cd /path/to/shockwave_v2 && python3 data/space_devs.py upcoming 100
```

---

## 📚 More Information

- **Full Manual**: README.md
- **Migration**: MIGRATION_GUIDE.md
- **Changes**: CHANGELOG.md
- **Architecture**: ARCHITECTURE.md (in uploads)

---

## 🆘 Emergency Contacts

**System**: NZDF 62SQN Space Operations Centre  
**Developer**: Remix Astronautics  
**For**: TAWHIRI Space Domain Awareness Platform

---

## ✅ Pre-Operations Checklist

Before major operations:
- [ ] Backup database
- [ ] Sync latest data
- [ ] Verify critical launches present
- [ ] Check NOTAM references
- [ ] Review timeline for conflicts
- [ ] Update team on changes

---

**SHOCKWAVE PLANNER v2.0** - Ready for Operations! 🚀

*Keep this reference handy for daily use*

---

*Last Updated: December 2025 | Version 2.0.0*
