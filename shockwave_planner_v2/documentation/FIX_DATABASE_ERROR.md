# QUICK FIX - Database Error Solution

## 🔧 The Problem

You're getting errors like:
```
sqlite3.OperationalError: no such column: st.status_color
sqlite3.OperationalError: no such column: country
```

**Cause**: Your database is from an older version and is missing columns needed for v2.0.

---

## ✅ Two Solutions - Pick One

### OPTION 1: Fresh Start (Recommended - 30 seconds)
**Best if**: You don't have important data OR want to sync from Space Devs

### OPTION 2: Repair Database (2 minutes)  
**Best if**: You have important manual data to preserve

---

## 🚀 OPTION 1: Fresh Start (Easiest!)

### Step 1: Run the Fresh Start Script

**Open Command Prompt** in your shockwave folder and run:

```cmd
python start_fresh.py
```

When prompted "Delete current database and start fresh?", type: **yes**

### Step 2: Run the Application

```cmd
python main.py
```

A brand new v2.0 database will be created automatically!

### Step 3: Get Launch Data

In the application:
1. Click **Data** menu
2. Click **Sync Upcoming Launches (Space Devs)**
3. Wait ~30 seconds
4. Done! You now have current global launch data

**✅ That's it!** Everything works now.

---

## 🔧 OPTION 2: Repair Database

### Step 1: Run the Repair Script

**Open Command Prompt** in your shockwave folder and run:

```cmd
python repair_database.py
```

This will:
- ✅ Backup your current database
- ✅ Add all missing columns
- ✅ Create new tables
- ✅ Preserve your existing data

### Step 2: Run the Application

```cmd
python main.py
```

**✅ Done!** Your data is preserved and updated to v2.0.

---

## 📋 Comparison

| Feature | Fresh Start | Repair |
|---------|-------------|--------|
| **Speed** | 30 seconds | 2 minutes |
| **Keeps old data** | ❌ No | ✅ Yes |
| **Gets latest data** | ✅ Yes (via sync) | Manual sync needed |
| **Complexity** | ⭐ Simple | ⭐⭐ Medium |
| **Recommended for** | New users | Existing users |

---

## 🎯 Step-by-Step: Fresh Start

### Windows Command Prompt Method:

1. **Navigate to folder**:
   ```
   C:\Users\Standalone1\Desktop\shockwave_planner_v2
   ```

2. **Run fresh start**:
   ```cmd
   python start_fresh.py
   ```

3. **Type 'yes'** when prompted

4. **Run app**:
   ```cmd
   python main.py
   ```

5. **Sync data**:
   - In app: Data → Sync Upcoming Launches
   - Wait for completion
   - Done!

---

## 🎯 Step-by-Step: Repair Database

### Windows Command Prompt Method:

1. **Navigate to folder**:
   ```
   C:\Users\Standalone1\Desktop\shockwave_planner_v2
   ```

2. **Run repair**:
   ```cmd
   python repair_database.py
   ```

3. **Wait for completion** (shows what was fixed)

4. **Run app**:
   ```cmd
   python main.py
   ```

5. **Verify** everything works!

---

## 💾 Your Data is Safe

### Fresh Start
- Old database backed up as: `shockwave_planner.db.OLD`
- Can always restore if needed

### Repair
- Backup created as: `shockwave_planner.db.backup`
- Original data preserved in updated database

**Both methods create backups before making changes!**

---

## 🆘 If Scripts Don't Work

### Manual Fresh Start:

1. **Rename old database**:
   ```cmd
   ren shockwave_planner.db shockwave_planner.db.old
   ```

2. **Run application**:
   ```cmd
   python main.py
   ```
   
   A new database is created automatically!

3. **Sync from Space Devs**:
   - Data → Sync Upcoming Launches

---

## ✅ Verify It's Fixed

After using either method:

```cmd
python verify_installation.py
```

Should show all tests passing!

---

## 🎊 After It's Fixed

You can now:
- ✅ Use all v2.0 features
- ✅ Sync from Space Devs API
- ✅ Track launches and re-entries
- ✅ Use NOTAM tracking
- ✅ Everything works perfectly!

---

## 💡 Recommendation

**For most users**: Use **Fresh Start** (Option 1)
- Faster
- Simpler
- Gets you the latest launch data via Space Devs
- Less error-prone

**Use Repair** only if you have important manual entries to preserve.

---

## 🔄 What Happened?

Your database structure was from an older version. The v2.0 code expects:
- `status_color` column in `launch_status` table
- `country`, `latitude`, `longitude` columns in `launch_sites` table
- Plus many other new v2.0 features

The scripts fix this automatically!

---

**Run one of these and you'll be up and running in under a minute!**

✨ **Recommended**: `python start_fresh.py` then sync from Space Devs!
