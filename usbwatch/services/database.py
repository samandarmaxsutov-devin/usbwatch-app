"""SQLite repository: the single place that reads/writes the events database.

Called only from the UI thread (the tick loop), so it uses one connection.
"""
import sqlite3

from .. import config


class Repository:
    def __init__(self, path=None):
        self.db = sqlite3.connect(path or config.DB)
        self._init_schema()

    def _init_schema(self):
        c = self.db
        c.execute("CREATE TABLE IF NOT EXISTS events(ts TEXT, drive TEXT, action TEXT, "
                  "path TEXT, dest TEXT, size TEXT)")
        try:
            c.execute("ALTER TABLE events ADD COLUMN serial TEXT")
        except sqlite3.OperationalError:
            pass
        c.execute("CREATE TABLE IF NOT EXISTS capacity(serial TEXT PRIMARY KEY, label TEXT, "
                  "fs TEXT, total INTEGER, free INTEGER, ts TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS snapshot(serial TEXT, rel TEXT, size INTEGER, "
                  "PRIMARY KEY(serial, rel))")
        c.execute("CREATE TABLE IF NOT EXISTS policy(serial TEXT PRIMARY KEY, kind TEXT, "
                  "name TEXT, ts TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS blocked_devices(serial TEXT PRIMARY KEY, "
                  "pnp TEXT, ts TEXT)")
        c.commit()

    def commit(self):
        self.db.commit()

    # ---- events ----
    def insert_events(self, rows):
        if not rows:
            return
        self.db.executemany(
            "INSERT INTO events(ts,drive,action,path,dest,size,serial) VALUES(?,?,?,?,?,?,?)", rows)
        self.db.commit()

    def count_events(self):
        return self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def events_for_serial(self, serial, limit=5000):
        return list(self.db.execute(
            "SELECT ts,drive,action,path,dest,size FROM events WHERE upper(serial)=? "
            "ORDER BY rowid DESC LIMIT ?", (serial.upper(), limit)))

    def query_activity(self, like, action=None, limit=5000):
        sql = "SELECT ts,drive,action,path,dest,size FROM events WHERE (path LIKE ? OR dest LIKE ?)"
        args = [like, like]
        if action:
            sql += " AND action=?"
            args.append(action)
        sql += " ORDER BY rowid DESC LIMIT ?"
        args.append(limit)
        return list(self.db.execute(sql, args))

    def deleted_files(self, limit=5000):
        q = ("SELECT rowid,ts,serial,drive,path,size,action FROM events "
             "WHERE action IN ('Deleted','Deleted (offline)') ORDER BY rowid DESC LIMIT ?")
        return list(self.db.execute(q, (limit,)))

    # ---- snapshot ----
    def snapshot(self, serial):
        return dict(self.db.execute("SELECT rel,size FROM snapshot WHERE serial=?", (serial,)).fetchall())

    def replace_snapshot(self, serial, files):
        self.db.execute("DELETE FROM snapshot WHERE serial=?", (serial,))
        self.db.executemany("INSERT INTO snapshot VALUES(?,?,?)",
                            [(serial, rel, sz) for rel, sz in files.items()])
        self.db.commit()

    def snapshot_set(self, serial, rel, size):
        self.db.execute("INSERT OR REPLACE INTO snapshot VALUES(?,?,?)", (serial, rel, size))

    def snapshot_del(self, serial, rel):
        self.db.execute("DELETE FROM snapshot WHERE serial=? AND rel=?", (serial, rel))

    # ---- policy / blocked ----
    def policy_all(self):
        return self.db.execute("SELECT serial,kind,name FROM policy").fetchall()

    def policy_set(self, serial, kind, name, ts):
        self.db.execute("INSERT OR REPLACE INTO policy VALUES(?,?,?,?)", (serial.upper(), kind, name, ts))

    def policy_del(self, serial):
        self.db.execute("DELETE FROM policy WHERE serial=?", (serial,))

    def blocked_all(self):
        return self.db.execute("SELECT serial,pnp FROM blocked_devices").fetchall()

    def blocked_serials(self):
        return {r[0].upper() for r in self.db.execute("SELECT serial FROM blocked_devices")}

    def blocked_set(self, serial, pnp, ts):
        self.db.execute("INSERT OR REPLACE INTO blocked_devices VALUES(?,?,?)", (serial, pnp, ts))

    def blocked_del(self, serial):
        self.db.execute("DELETE FROM blocked_devices WHERE serial=?", (serial,))

    # ---- capacity ----
    def capacity_map(self):
        return {r[0]: (r[1], r[2]) for r in self.db.execute("SELECT serial,total,free FROM capacity")}

    def capacity_for(self, serial):
        return self.db.execute("SELECT total,free FROM capacity WHERE serial=?", (serial.upper(),)).fetchone()

    def capacity_set(self, serial, label, fs, total, free, ts):
        self.db.execute("INSERT OR REPLACE INTO capacity VALUES(?,?,?,?,?,?)",
                        (serial.upper(), label, fs, total, free, ts))
