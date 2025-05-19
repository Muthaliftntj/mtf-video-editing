# alter_db.py
import sqlite3

conn = sqlite3.connect('instance/site.db')
cursor = conn.cursor()
cursor.execute("ALTER TABLE reporter ADD COLUMN is_approved BOOLEAN DEFAULT 0")
conn.commit()
conn.close()

print("is_approved column added to reporter table.")
