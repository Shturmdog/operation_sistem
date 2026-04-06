import sqlite3 as sql
import pandas as pd

conn = sql.connect('students.db')
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

try:
    # ВАШ SQL КОД (полностью неизменен)
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS направление (
        id_направления INTEGER PRIMARY KEY AUTOINCREMENT,
        название VARCHAR(255) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS предметы (
        id_предмета INTEGER PRIMARY KEY AUTOINCREMENT,
        название_предмета VARCHAR(255) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS студенты (
        id_студента INTEGER PRIMARY KEY AUTOINCREMENT,
        id_направления INTEGER NOT NULL,
        id_предмета INTEGER NOT NULL,
        фамилия VARCHAR(255) NOT NULL,
        имя VARCHAR(255) NOT NULL,
        age INTEGER,
        email TEXT UNIQUE,
        оценка INTEGER CHECK (оценка >= 2 AND оценка <= 5),
        FOREIGN KEY (id_направления) REFERENCES направление(id_направления),
        FOREIGN KEY (id_предмета) REFERENCES предметы(id_предмета)
    );
    """)

    levels = [("Прикладная информатика",), ("Педагогика",), ("Аналитическая химия",), ("Филология",)]
    cursor.executemany("INSERT OR IGNORE INTO направление (название) VALUES (?)", levels)

    pred = [("Математика",), ("Русский язык",), ("Информатика",), ("История России",), ("ОРГ",), ("Химия",),
            ("Программирование",)]
    cursor.executemany("INSERT OR IGNORE INTO предметы (название_предмета) VALUES (?)", pred)

    students = [
        (1, 1, "Иванов", "Иван", 20, "ivan@mail.ru", 5),
        (1, 3, "Петрова", "Мария", 19, "petrova@mail.ru", 4),
        (2, 2, "Сидоров", "Алексей", 21, "sidorov@mail.ru", 3),
        (2, 4, "Козлова", "Елена", 20, "kozlova@mail.ru", 4),
        (3, 6, "Морозов", "Дмитрий", 22, "morozov@mail.ru", 5),
        (3, 1, "Волкова", "Анна", 19, "volkova@mail.ru", 4),
        (4, 2, "Соколов", "Павел", 21, "sokolov@mail.ru", 4),
        (1, 7, "Новикова", "Татьяна", 20, "novikova@mail.ru", 5),
        (2, 5, "Федоров", "Артем", 22, "fedorov@mail.ru", 3),
        (4, 4, "Егорова", "Ольга", 19, "egorova@mail.ru", 4),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO студенты 
        (id_направления, id_предмета, фамилия, имя, age, email, оценка)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, students)

    conn.commit()

    # СОХРАНЯЕМ В CSV ЧЕРЕЗ PANDAS
    # Читаем таблицы из SQL и сохраняем в CSV
    for table in ['направление', 'предметы', 'студенты']:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        df.to_csv(f'{table}.csv', index=False, encoding='utf-8-sig')
        print(f"✅ Сохранено: {table}.csv ({len(df)} записей)")

    # Сохраняем объединенную таблицу
    df_all = pd.read_sql_query("""
        SELECT 
            с.фамилия,
            с.имя,
            с.age,
            н.название as направление,
            п.название_предмета as предмет,
            с.оценка,
            с.email
        FROM студенты с
        JOIN направление н ON с.id_направления = н.id_направления
        JOIN предметы п ON с.id_предмета = п.id_предмета
    """, conn)

    df_all.to_csv('все_студенты.csv', index=False, encoding='utf-8-sig')
    print(f"Сохранено: все_студенты.csv ({len(df_all)} записей)")

except sql.Error as e:
    print(f"Ошибка: {e}")

finally:
    conn.close()