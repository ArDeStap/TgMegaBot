import sqlite3

# Создание или подключение к базе данных
conn = sqlite3.connect('database.db')

# Создание курсора
c = conn.cursor()

# Создание таблицы Groups
c.execute('''CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL);''')

# Создание таблицы прав пользователей
c.execute('''CREATE TABLE IF NOT EXISTS user_rights (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          description TEXT);''')

# Создание таблицы Users
c.execute('''CREATE TABLE IF NOT EXISTS users (
             id INTEGER DEFAULT 1 PRIMARY KEY AUTOINCREMENT NOT NULL,
             username TEXT NOT NULL,
             password TEXT NOT NULL,
             third_Name TEXT,
             second_Name TEXT NOT NULL,
             first_Name TEXT NOT NULL,
             rights_id INTEGER,
             group_id INTEGER,
             tg_data TEXT DEFAULT 'NONE',
             FOREIGN KEY (rights_id) REFERENCES user_rights (id) ON DELETE SET NULL,
             FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE SET NULL);''')

conn.close()

conn = sqlite3.connect('TelegramUsersDB.db')

c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS user_data(
             id INTEGER DEFAULT 1 PRIMARY KEY AUTOINCREMENT NOT NULL,
             users_id INTEGER NOT NULL,
             tg_data_json TEXT NOT NULL,
             rights_id INTEGER,
             group_id INTEGER);''')

conn.close()