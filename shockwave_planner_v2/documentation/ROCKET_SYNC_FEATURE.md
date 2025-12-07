# 🚀 NEW FEATURE: Sync Rocket Details from Space Devs!

## What's New

Two ways to populate rocket details (family, variant, manufacturer, country):

1. **Automatic** - During launch sync (new!)
2. **Manual** - Separate rocket details sync (new menu item!)

---

## 🎯 Feature 1: Automatic During Launch Sync

When you sync launches, rockets are now automatically created/updated with full details!

**Before:**
- Rocket: Falcon 9 Block 5
- Family: (empty)
- Variant: (empty)
- Country: (empty)

**After:**
- Rocket: Falcon 9 Block 5
- Family: Falcon
- Variant: Block 5
- Manufacturer: SpaceX
- Country: USA

---

## 🎯 Feature 2: Separate Rocket Details Sync

**New Menu Item:** Data → Sync Rocket Details (Space Devs)

Updates ALL existing rockets in your database with details from Space Devs!

**How To Use:**
1. Data → Sync Rocket Details (Space Devs)
2. Confirm the dialog
3. Watch progress
4. Check 🚀 Rockets tab!

**Example Output:**
```
🚀 Updating rocket details from Space Devs...
   Fetching details for: Falcon 9 Block 5... ✓
   Fetching details for: Long March 2D... ✓
   Fetching details for: Electron... ✓
   Skipping phil (no external_id)

✅ Updated 44 rockets
```

---

## 📊 Results

**Before:**
| Name | Family | Variant | Country |
|------|--------|---------|---------|
| Falcon 9 Block 5 | | | |
| Long March 2D | | | |

**After:**
| Name | Family | Variant | Manufacturer | Country |
|------|--------|---------|--------------|---------|
| Falcon 9 Block 5 | Falcon | Block 5 | SpaceX | USA |
| Long March 2D | Long March | CZ-2D | CASC | CHN |

---

## 🚀 Try It Now!

1. Extract updated ZIP
2. Launch SHOCKWAVE
3. Data → Sync Rocket Details
4. Wait ~30 seconds
5. Check 🚀 Rockets tab - full details! 🎉

**Your rockets now have complete data from Space Devs!**
