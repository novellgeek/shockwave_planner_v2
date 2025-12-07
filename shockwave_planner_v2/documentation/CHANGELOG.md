# SHOCKWAVE PLANNER - Changelog

All notable changes to this project will be documented in this file.

---

## [2.0.0] - December 2025

### 🎉 Major Release - Architecture Restoration & API Integration

This release represents a complete restoration of the codebase architecture with significant new features and improvements.

### ✨ Added

**Space Devs API Integration:**
- New `data/space_devs.py` module for API communication
- Automated fetch of upcoming launches (up to 100)
- Automated fetch of previous launches (up to 50)
- Date range queries for specific periods
- Intelligent duplicate detection and merging
- Sync operation logging and tracking
- Background sync with progress indicators

**Re-entry Tracking:**
- New `reentry_sites` database table
- New `reentries` database table
- Re-entry timeline view (`gui/timeline_view_reentry.py`)
- Dedicated re-entry operations visualization
- Drop zone tracking
- Vehicle component tracking
- Recovery period visualization

**Enhanced Database Schema:**
- `launches.notam_reference` - NOTAM tracking
- `launches.data_source` - Track manual vs. API entries
- `launches.external_id` - Space Devs launch ID
- `launches.last_synced` - Sync timestamp
- `sync_log` table - Complete sync operation history
- Proper foreign key constraints throughout
- Database indexes for performance

**User Interface Enhancements:**
- Splash screen on startup (3-second display)
- Sync status in Statistics tab
- Background sync with Qt threading
- Progress feedback during operations
- Enhanced menu system with sync options
- Emoji icons for better visual navigation

**Documentation:**
- Comprehensive README.md
- Detailed MIGRATION_GUIDE.md
- CHANGELOG.md (this file)
- Inline code documentation
- Architecture diagrams

### 🔧 Fixed

**Critical Fixes:**
- `main.py` - Fixed missing imports (os, QPixmap, QSplashScreen, QTimer)
- `main.py` - Removed duplicate `sys.exit(app.exec())` call
- `main.py` - Proper splash screen implementation
- `timeline_view_reentry.py` - Fixed references to non-existent fields
- Database schema inconsistencies

**Architecture Fixes:**
- Restored proper module structure
- Separated concerns (GUI, Data, Business Logic)
- Fixed import paths
- Cleaned up circular dependencies

### 🚀 Improved

**Performance:**
- Database query optimization
- Indexed foreign key columns
- Efficient sync operations
- Async UI updates during sync

**Code Quality:**
- Modular architecture
- Clear separation of concerns
- Comprehensive error handling
- Type hints where appropriate
- Detailed comments

**User Experience:**
- Intuitive sync workflow
- Clear status messages
- Progress indicators
- Error reporting
- Professional startup experience

### 📦 Dependencies

**Added:**
- `requests` - HTTP library for API calls

**Existing:**
- `PyQt6` - GUI framework
- `sqlite3` - Database (Python standard library)

### 🗃️ Database Schema Changes

**New Tables:**
```sql
reentry_sites (
    reentry_site_id, location, drop_zone,
    latitude, longitude, country, zone_type, external_id
)

reentries (
    reentry_id, launch_id, reentry_date, reentry_time,
    reentry_site_id, vehicle_component, reentry_type,
    status_id, remarks, data_source, external_id
)

sync_log (
    sync_id, sync_time, data_source,
    records_added, records_updated, status, error_message
)
```

**Modified Tables:**
```sql
launches (
    ... existing fields ...
    + notam_reference TEXT
    + data_source TEXT DEFAULT 'MANUAL'
    + external_id TEXT
    + last_synced DATETIME
)

launch_sites (
    ... existing fields ...
    + site_type TEXT DEFAULT 'LAUNCH'
    + external_id TEXT
)

rockets (
    ... existing fields ...
    + external_id TEXT
)
```

### 🔄 Migration Path

**From v1.x:**
- Fully backward compatible
- Automatic schema migration
- Preserves all existing data
- See MIGRATION_GUIDE.md for details

### 📝 API Integration Details

**Space Devs Endpoints Used:**
- `/launch/upcoming/` - Fetch upcoming launches
- `/launch/previous/` - Fetch historical launches
- `/launch/` - Query by date range

**Rate Limiting:**
- Default public API limits apply
- Sync operations track and respect limits
- Failed requests logged for retry

**Data Mapping:**
- Space Devs launch ID → `external_id`
- Automatic site/rocket matching
- Status normalization
- Time zone handling (UTC)

### 🐛 Known Issues

**Minor:**
- Re-entry editor dialog not yet implemented (view-only)
- Sync history viewer shows basic message (full UI coming)
- Custom manual edits may be overwritten by sync if external_id matches

**Workarounds:**
- Re-entries can be edited via database directly
- Sync logs available in database
- Keep manual entries without external_id to prevent overwrites

### 🎯 Roadmap

**v2.1 (Planned):**
- Re-entry editor dialog
- Sync history viewer UI
- Advanced filtering options
- Export to Excel/CSV

**v2.2 (Future):**
- TLE integration
- Orbital parameter tracking
- Conjunction screening link
- Multiple API sources

**v2.3 (Future):**
- Multi-user support
- Change tracking
- Comments/annotations
- Email notifications

---

## [1.1.0] - November 2025

### Added
- Timeline view for launches
- Enhanced list view with date filters
- NOTAM reference field
- Quick date range filters (7 days, 30 days, etc.)
- Custom date range picker
- Splash screen image
- Re-entry timeline view (preliminary)

### Fixed
- Performance improvements
- UI responsiveness

---

## [1.0.0] - November 2025

### Initial Release

**Features:**
- Calendar view of launches
- List view with search
- Manual launch entry
- Site and rocket management
- Launch status tracking
- Statistics dashboard
- SQLite database backend
- PyQt6 GUI

**Included:**
- Pre-populated Chinese launch sites
- Pre-populated rocket data
- Sample launches for testing
- Basic documentation

---

## Version History Summary

| Version | Date | Key Features |
|---------|------|--------------|
| 2.0.0 | Dec 2025 | Space Devs API, Re-entry tracking, Architecture restoration |
| 1.1.0 | Nov 2025 | Timeline views, Date filters, NOTAM |
| 1.0.0 | Nov 2025 | Initial release with core features |

---

## Breaking Changes

### v2.0.0
- **File Structure**: Code reorganized into proper modules (backward compatible)
- **Database**: New tables and columns (backward compatible with migration)
- **Dependencies**: Added `requests` library requirement

**Migration Required:** Yes (automatic schema migration supported)  
**Data Loss Risk:** None (all v1.x data preserved)  
**Backward Compatibility:** Database compatible, code structure changed

---

## Upgrade Instructions

### v1.x → v2.0

1. Backup your database
2. Install new dependencies: `pip install requests --break-system-packages`
3. Extract v2.0 files
4. Copy database (automatic migration on first run)
5. Sync from Space Devs for current data

See MIGRATION_GUIDE.md for detailed instructions.

---

## Contributors

- **Remix Astronautics** - v2.0 Development
- **Phil @ NZDF 62SQN** - Requirements & Testing

---

## License

Created for NZDF 62SQN Space Operations Centre  
Unauthorized distribution prohibited

---

*For detailed release notes and migration guides, see the /docs directory.*
