# SHOCKWAVE PLANNER - Migration Guide
## Upgrading from v1.x to v2.0

**Important**: This guide will help you safely migrate your data from SHOCKWAVE PLANNER v1.x to v2.0.

---

## 🚨 Before You Start

### Backup Your Data

**CRITICAL**: Always backup your database before migration!

```bash
# Backup v1.x database
cp shockwave_planner.db shockwave_v1_backup_$(date +%Y%m%d).db
```

### What's Changed

**Database Schema:**
- ✅ All v1.x tables preserved
- ✅ New tables added (reentry_sites, reentries, sync_log)
- ✅ New columns added to launches table
- ✅ Fully backward compatible

**Code Structure:**
- 📁 Reorganized into proper modules (gui/, data/)
- 📄 New files: space_devs.py, timeline_view_reentry.py
- 🔧 Fixed: main.py imports and structure
- 🎨 Enhanced: main_window.py with sync support

---

## 📋 Migration Steps

### Option 1: Fresh Install (Recommended)

**Best for**: Starting fresh with Space Devs data

1. **Backup old database** (see above)
2. **Extract v2.0 files** to new directory:
   ```bash
   mkdir shockwave_v2
   cd shockwave_v2
   # Extract all v2.0 files here
   ```
3. **Install dependencies**:
   ```bash
   pip install PyQt6 requests --break-system-packages
   ```
4. **Copy resources**:
   ```bash
   cp ../shockwave_v1/resources/splash_intro.png resources/
   ```
5. **Run application**:
   ```bash
   python3 main.py
   ```
6. **Sync from Space Devs**:
   - Data → Sync Upcoming Launches
   - Wait for completion
   - Review results

**Result**: Clean v2.0 installation with current launch data

---

### Option 2: Database Migration

**Best for**: Preserving existing manual entries

1. **Backup old database** (see above)

2. **Copy database to v2.0**:
   ```bash
   cp ../shockwave_v1/shockwave_planner.db shockwave_planner.db
   ```

3. **Update database schema**:
   ```bash
   python3 -c "
   from data.database import LaunchDatabase
   db = LaunchDatabase()
   print('Database schema updated successfully!')
   db.close()
   "
   ```
   
   This will:
   - Add new tables (reentry_sites, reentries, sync_log)
   - Add new columns to existing tables
   - Preserve all existing data

4. **Verify migration**:
   ```bash
   python3 -c "
   import sqlite3
   conn = sqlite3.connect('shockwave_planner.db')
   cursor = conn.cursor()
   cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
   print('Tables:', [row[0] for row in cursor.fetchall()])
   conn.close()
   "
   ```
   
   Should show: launch_sites, rockets, launch_vehicles, launch_status, launches, launch_tles, launch_predictions, reentry_sites, reentries, sync_log

5. **Run application**:
   ```bash
   python3 main.py
   ```

6. **Verify data**:
   - Check Launch List View for your existing launches
   - Verify sites and rockets in dropdowns
   - Check Statistics tab

**Result**: All v1.x data preserved with v2.0 enhancements

---

### Option 3: Selective Migration

**Best for**: Migrating specific data categories

1. **Start fresh v2.0** (Option 1)

2. **Export v1.x data**:
   ```bash
   # In v1.x directory
   python3 -c "
   import sqlite3
   import json
   
   conn = sqlite3.connect('shockwave_planner.db')
   conn.row_factory = sqlite3.Row
   cursor = conn.cursor()
   
   # Export launches
   cursor.execute('SELECT * FROM launches')
   launches = [dict(row) for row in cursor.fetchall()]
   
   with open('v1_launches_export.json', 'w') as f:
       json.dump(launches, f, indent=2)
   
   print(f'Exported {len(launches)} launches')
   conn.close()
   "
   ```

3. **Import into v2.0**:
   ```python
   # Create import_v1_data.py in v2.0 directory
   import json
   from data.database import LaunchDatabase
   
   db = LaunchDatabase()
   
   # Load exported data
   with open('v1_launches_export.json', 'r') as f:
       launches = json.load(f)
   
   # Import launches
   for launch in launches:
       # Skip if already exists
       if launch.get('external_id'):
           continue
       
       # Add manual entry
       launch['data_source'] = 'MANUAL'
       db.add_launch(launch)
   
   print(f'Imported {len(launches)} launches')
   db.close()
   ```

---

## 🔍 Verification Checklist

After migration, verify:

### Data Integrity
- [ ] All launches visible in List View
- [ ] Launch dates correct
- [ ] Site and rocket data preserved
- [ ] Status colors showing correctly
- [ ] Timeline views working

### Functionality
- [ ] Can add new launch
- [ ] Can edit existing launch
- [ ] Search function works
- [ ] Date filters work
- [ ] Statistics calculating correctly

### New Features
- [ ] Space Devs sync functional
- [ ] Re-entry timeline loads
- [ ] NOTAM field accessible
- [ ] Sync log recording operations

### Performance
- [ ] Application starts quickly
- [ ] Timeline renders smoothly
- [ ] List view scrolls well
- [ ] Database queries fast

---

## 🛠️ Troubleshooting Migration

### "Table already exists" errors

**Cause**: Trying to create tables that already exist  
**Solution**: SQLite's `CREATE TABLE IF NOT EXISTS` handles this automatically

### Missing columns

**Cause**: Old database schema missing new columns  
**Solution**: 
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('shockwave_planner.db')
cursor = conn.cursor()

# Add missing columns
cursor.execute('ALTER TABLE launches ADD COLUMN notam_reference TEXT')
cursor.execute('ALTER TABLE launches ADD COLUMN data_source TEXT DEFAULT \"MANUAL\"')
cursor.execute('ALTER TABLE launches ADD COLUMN external_id TEXT')
cursor.execute('ALTER TABLE launches ADD COLUMN last_synced DATETIME')

conn.commit()
conn.close()
print('Columns added successfully')
"
```

### Duplicate data after sync

**Cause**: Syncing when manual entries already exist  
**Solution**: 
- V2.0 uses `external_id` to prevent duplicates
- Manual entries (no `external_id`) won't be overwritten
- Space Devs entries (with `external_id`) will be updated, not duplicated

### Performance degradation

**Cause**: Large database without indexes  
**Solution**:
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('shockwave_planner.db')
cursor = conn.cursor()

# Create indexes
cursor.execute('CREATE INDEX IF NOT EXISTS idx_launches_date ON launches(launch_date)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_launches_external ON launches(external_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_launches_site ON launches(site_id)')

conn.commit()
conn.close()
print('Indexes created')
"
```

---

## 📊 Comparing v1.x and v2.0

### File Structure

**v1.x:**
```
shockwave_planner/
├── main.py
├── gui/
│   └── main_window.py (monolithic)
├── data/
│   └── database.py
└── shockwave_planner.db
```

**v2.0:**
```
shockwave_v2/
├── main.py (fixed)
├── gui/
│   ├── main_window.py (enhanced)
│   ├── timeline_view.py
│   ├── timeline_view_reentry.py (new)
│   └── enhanced_list_view.py
├── data/
│   ├── database.py (enhanced)
│   └── space_devs.py (new)
├── resources/
│   └── splash_intro.png
└── shockwave_planner.db
```

### Database Schema

**New in v2.0:**
- `reentry_sites` table
- `reentries` table
- `sync_log` table
- `launches.notam_reference` column
- `launches.data_source` column
- `launches.external_id` column
- `launches.last_synced` column

### Features

**v1.x:**
- ✅ Manual launch entry
- ✅ Calendar view
- ✅ List view
- ✅ Basic statistics
- ❌ No API integration
- ❌ No re-entry tracking
- ❌ Limited documentation

**v2.0:**
- ✅ All v1.x features
- ✅ **Space Devs API integration**
- ✅ **Automated data sync**
- ✅ **Re-entry timeline view**
- ✅ **Enhanced date filters**
- ✅ **NOTAM tracking**
- ✅ **Sync logging**
- ✅ **Comprehensive documentation**
- ✅ **Fixed splash screen**
- ✅ **Proper architecture**

---

## 🎯 Recommended Migration Path

### For Production Use

1. **Test Environment First**:
   - Set up v2.0 in separate directory
   - Copy database and test migration
   - Verify all functionality
   - Test Space Devs sync

2. **Parallel Operation**:
   - Run v1.x and v2.0 simultaneously
   - Compare data between versions
   - Ensure v2.0 meets requirements

3. **Cutover**:
   - Schedule cutover during quiet period
   - Final backup of v1.x
   - Switch to v2.0
   - Archive v1.x for reference

### For Development/Testing

1. **Direct Migration**:
   - Backup v1.x
   - Extract v2.0
   - Copy database
   - Test and iterate

---

## 📝 Post-Migration Tasks

### Immediate (Day 1)
- [ ] Verify all existing data
- [ ] Test adding new launches
- [ ] Perform first Space Devs sync
- [ ] Review sync results
- [ ] Update any documentation

### Short-term (Week 1)
- [ ] Set up regular sync schedule
- [ ] Train team on new features
- [ ] Establish backup routine
- [ ] Monitor performance
- [ ] Collect user feedback

### Long-term (Month 1)
- [ ] Evaluate data quality
- [ ] Assess API usage
- [ ] Plan enhancements
- [ ] Document lessons learned
- [ ] Archive v1.x

---

## 🆘 Rollback Procedure

If you need to revert to v1.x:

1. **Stop v2.0**:
   ```bash
   # Kill all instances
   killall python3
   ```

2. **Restore v1.x database**:
   ```bash
   cp shockwave_v1_backup_YYYYMMDD.db ../shockwave_v1/shockwave_planner.db
   ```

3. **Restart v1.x**:
   ```bash
   cd ../shockwave_v1
   python3 main.py
   ```

4. **Document issues** for later resolution

---

## ✅ Migration Success Criteria

Migration is successful when:

- ✅ All v1.x data visible and accessible
- ✅ All v1.x features working
- ✅ All v2.0 new features operational
- ✅ Space Devs sync functional
- ✅ Performance acceptable
- ✅ No data loss
- ✅ Team trained on new features
- ✅ Backup procedures established

---

## 🎓 Training Resources

After migration, review:

1. **README.md** - Feature overview
2. **USER_GUIDE.md** - Detailed operations manual
3. **API_INTEGRATION.md** - Space Devs sync guide
4. **ARCHITECTURE.md** - Technical details

---

## 📞 Support

For migration issues:

1. Check this guide
2. Review error messages
3. Examine database with SQLite browser
4. Test with backup copy first
5. Document and report issues

---

**Good luck with your migration!** 🚀

Remember: Always backup before migration, test in non-production environment first, and take your time to verify everything works correctly.

---

*SHOCKWAVE PLANNER v2.0 - Migration Guide*  
*Remix Astronautics - December 2025*
