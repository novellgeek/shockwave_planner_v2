# 🚨 IMMEDIATE FIX - Do This Now!

## You Have Database Errors - Here's The Quick Fix

Your database is from an old version. **Choose ONE option below:**

---

## ⚡ OPTION 1: Fresh Start (30 seconds) ⭐ RECOMMENDED

**This is the easiest and fastest!**

### Do This:

1. **Open Command Prompt** in your shockwave folder
2. **Run this command**:
   ```cmd
   python start_fresh.py
   ```
3. **Type**: `yes` (when asked)
4. **Run the app**:
   ```cmd
   python main.py
   ```
5. **Sync data**: Data → Sync Upcoming Launches

**✅ DONE!** You now have a working v2.0 system with current launch data!

---

## 🔧 OPTION 2: Keep Old Data (2 minutes)

**Only use this if you have important data to preserve**

### Do This:

1. **Open Command Prompt** in your shockwave folder
2. **Run this command**:
   ```cmd
   python repair_database.py
   ```
3. **Wait** for it to finish (shows what was fixed)
4. **Run the app**:
   ```cmd
   python main.py
   ```

**✅ DONE!** Your old data is preserved and updated to v2.0!

---

## 🪟 How to Open Command Prompt

**Quick Method:**
1. Open the folder: `C:\Users\Standalone1\Desktop\shockwave_planner_v2`
2. Click in the **address bar** (where it shows the path)
3. Type: `cmd`
4. Press **Enter**

**You're now in Command Prompt in the right folder!**

---

## 💡 Which Option Should You Choose?

### Choose **Fresh Start** if:
- ✅ You just want it to work
- ✅ You don't have important manual entries
- ✅ You want the latest launch data
- ✅ You want the fastest solution

### Choose **Repair** if:
- ✅ You have manual launch entries to keep
- ✅ You have custom data you need

**Most people should use Fresh Start!**

---

## 🎯 Copy-Paste Commands

### Fresh Start:
```cmd
cd C:\Users\Standalone1\Desktop\shockwave_planner_v2
python start_fresh.py
```
Type `yes` when asked, then:
```cmd
python main.py
```

### Repair:
```cmd
cd C:\Users\Standalone1\Desktop\shockwave_planner_v2
python repair_database.py
python main.py
```

---

## ✅ What Happens Next

**After Fresh Start:**
1. Old database backed up (in case you need it)
2. New v2.0 database created
3. App runs perfectly
4. Sync gets you current launch data
5. Everything works!

**After Repair:**
1. Old database backed up
2. Missing columns added
3. Your data preserved
4. App runs perfectly
5. Everything works!

**Both methods are safe and create backups!**

---

## 🆘 Still Having Problems?

If the scripts don't work, do this manually:

```cmd
cd C:\Users\Standalone1\Desktop\shockwave_planner_v2
ren shockwave_planner.db shockwave_planner.db.old
python main.py
```

This renames your old database and lets the app create a fresh one.

---

## 📞 Need More Help?

See these guides in your folder:
- **FIX_DATABASE_ERROR.md** - Detailed instructions
- **WINDOWS_QUICK_START.md** - Windows setup guide
- **README.md** - Complete manual

---

**Just run one of those commands above and you'll be fixed in under a minute!**

**Recommended**: `python start_fresh.py` 🚀
