import sqlite3
import datetime

# Подключение к базе данных
conn = sqlite3.connect('store.db')
cursor = conn.cursor()

# Создание таблиц
cursor.executescript('''
    CREATE TABLE IF NOT EXISTS categories (
        id_category INTEGER PRIMARY KEY,
        name_category TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS products (
        id_product INTEGER PRIMARY KEY,
        name_of_product TEXT NOT NULL,
        price REAL NOT NULL,
        id_category INTEGER NOT NULL,
        quantity_at_storage REAL NOT NULL,
        FOREIGN KEY(id_category) REFERENCES categories(id_category)
    );

    CREATE TABLE IF NOT EXISTS employees (
        id_employee INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        surname TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS receipts (
        id_check INTEGER PRIMARY KEY,
        created_at TEXT NOT NULL,
        id_employee INTEGER NOT NULL,
        FOREIGN KEY(id_employee) REFERENCES employees(id_employee)
    );

    CREATE TABLE IF NOT EXISTS sale_items (
        id_sale INTEGER PRIMARY KEY,
        id_check INTEGER NOT NULL,
        id_product INTEGER NOT NULL,
        quantity REAL NOT NULL,
        price_at_sale REAL NOT NULL,
        FOREIGN KEY(id_check) REFERENCES receipts(id_check),
        FOREIGN KEY(id_product) REFERENCES products(id_product)
    );
''')
conn.commit()

# Добавляем тестовые данные
cursor.execute("SELECT COUNT(*) FROM categories")
if cursor.fetchone()[0] == 0:
    print("Добавляем тестовые данные...")
    cursor.execute("INSERT INTO categories (name_category) VALUES ('Напитки'), ('Снеки'), ('Молочные')")
    cursor.execute(
        "INSERT INTO products (name_of_product, price, id_category, quantity_at_storage) VALUES ('Кола', 50, 1, 100), ('Чипсы', 40, 2, 50), ('Молоко', 60, 3, 30)")
    cursor.execute("INSERT INTO employees (name, surname) VALUES ('Иван', 'Иванов'), ('Мария', 'Петрова')")
    conn.commit()


def print_line():
    print("-" * 50)


def show_products():
    """Показать все товары"""
    cursor.execute("SELECT id_product, name_of_product, price, quantity_at_storage FROM products")
    products = cursor.fetchall()

    print("\nТовары на складе:")
    print_line()
    for p in products:
        print(f"{p[0]}. {p[1]} - {p[2]} руб. (в наличии: {p[3]})")
    print_line()


def buy_products():
    """Оформить покупку"""
    # Выбираем сотрудника
    cursor.execute("SELECT id_employee, name, surname FROM employees")
    employees = cursor.fetchall()

    print("\nСотрудники:")
    for e in employees:
        print(f"{e[0]}. {e[1]} {e[2]}")

    emp_id = int(input("Выберите ID сотрудника: "))

    # Создаем чек
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO receipts (created_at, id_employee) VALUES (?, ?)", (now, emp_id))
    check_id = cursor.lastrowid

    print(f"\nЧек №{check_id} создан!")
    print("Добавляйте товары (0 - закончить)\n")

    total = 0
    items = []

    while True:
        show_products()
        prod_id = int(input("Введите ID товара (0 - закончить): "))

        if prod_id == 0:
            break

        # Получаем информацию о товаре
        cursor.execute("SELECT name_of_product, price, quantity_at_storage FROM products WHERE id_product = ?",
                       (prod_id,))
        product = cursor.fetchone()

        if not product:
            print("Товар не найден!\n")
            continue

        name, price, stock = product
        print(f"{name} - {price} руб. Доступно: {stock}")

        quantity = int(input("Сколько купить? "))

        if quantity > stock:
            print(f"Недостаточно! Есть только {stock}\n")
            continue

        # Добавляем в чек
        cursor.execute("INSERT INTO sale_items (id_check, id_product, quantity, price_at_sale) VALUES (?, ?, ?, ?)",
                       (check_id, prod_id, quantity, price))

        # Уменьшаем остаток
        cursor.execute("UPDATE products SET quantity_at_storage = quantity_at_storage - ? WHERE id_product = ?",
                       (quantity, prod_id))

        conn.commit()

        item_total = price * quantity
        total += item_total
        items.append([name, quantity, price, item_total])
        print(f"Добавлено! Сумма: {item_total} руб.\n")

    # Показываем чек
    if items:
        print_line()
        print(f"ЧЕК №{check_id}")
        print_line()
        for item in items:
            print(f"{item[0]} x{item[1]} = {item[3]} руб.")
        print_line()
        print(f"ИТОГО: {total} руб.")
        print(f"Дата: {now}")
        print_line()
    else:
        cursor.execute("DELETE FROM receipts WHERE id_check = ?", (check_id,))
        conn.commit()
        print("Чек отменён (нет товаров)")


def report_by_date():
    """Отчёт по дате"""
    date = input("Введите дату (ГГГГ-ММ-ДД): ")

    # Получаем выручку
    cursor.execute('''
        SELECT SUM(si.quantity * si.price_at_sale)
        FROM receipts r
        JOIN sale_items si ON r.id_check = si.id_check
        WHERE DATE(r.created_at) = ?
    ''', (date,))

    revenue = cursor.fetchone()[0]
    if revenue is None:
        revenue = 0

    print_line()
    print(f"ОТЧЁТ ЗА {date}")
    print_line()
    print(f"Выручка: {revenue} руб.")

    # Получаем проданные товары
    cursor.execute('''
        SELECT p.name_of_product, SUM(si.quantity) as total_qty, SUM(si.quantity * si.price_at_sale) as total_sum
        FROM sale_items si
        JOIN products p ON si.id_product = p.id_product
        JOIN receipts r ON si.id_check = r.id_check
        WHERE DATE(r.created_at) = ?
        GROUP BY p.id_product
    ''', (date,))

    products = cursor.fetchall()

    if products:
        print("\nПроданные товары:")
        for p in products:
            print(f"{p[0]} - {p[1]} шт. на сумму {p[2]} руб.")
    else:
        print("\nПродаж нет")
    print_line()


def show_receipt():
    """Показать чек"""
    check_id = int(input("Введите ID чека: "))

    cursor.execute('''
        SELECT r.id_check, r.created_at, e.name, e.surname
        FROM receipts r
        JOIN employees e ON r.id_employee = e.id_employee
        WHERE r.id_check = ?
    ''', (check_id,))

    receipt = cursor.fetchone()
    if not receipt:
        print("Чек не найден!")
        return

    check_id, created_at, name, surname = receipt

    cursor.execute('''
        SELECT p.name_of_product, si.quantity, si.price_at_sale
        FROM sale_items si
        JOIN products p ON si.id_product = p.id_product
        WHERE si.id_check = ?
    ''', (check_id,))

    items = cursor.fetchall()

    print_line()
    print(f"ЧЕК №{check_id}")
    print(f"Кассир: {name} {surname}")
    print(f"Дата: {created_at}")
    print_line()

    total = 0
    for item in items:
        sum_item = item[1] * item[2]
        print(f"{item[0]} x{item[1]} = {sum_item} руб.")
        total += sum_item

    print_line()
    print(f"ИТОГО: {total} руб.")
    print_line()


def check_stock():
    """Проверить остатки"""
    prod_id = int(input("Введите ID товара: "))

    cursor.execute("SELECT name_of_product, quantity_at_storage FROM products WHERE id_product = ?", (prod_id,))
    product = cursor.fetchone()

    if product:
        print(f"{product[0]} - в наличии: {product[1]} шт.")
    else:
        print("Товар не найден!")


def add_product():
    """Добавить товар"""
    name = input("Название товара: ")
    price = float(input("Цена: "))
    quantity = float(input("Количество: "))

    cursor.execute("SELECT id_category, name_category FROM categories")
    categories = cursor.fetchall()

    print("\nКатегории:")
    for cat in categories:
        print(f"{cat[0]}. {cat[1]}")

    cat_id = int(input("Выберите ID категории: "))

    cursor.execute(
        "INSERT INTO products (name_of_product, price, id_category, quantity_at_storage) VALUES (?, ?, ?, ?)",
        (name, price, cat_id, quantity))
    conn.commit()
    print(f"Товар {name} добавлен!")


def add_category():
    """Добавить категорию"""
    name = input("Название категории: ")
    cursor.execute("INSERT INTO categories (name_category) VALUES (?)", (name,))
    conn.commit()
    print(f"Категория {name} добавлена!")


def add_employee():
    """Добавить сотрудника"""
    name = input("Имя: ")
    surname = input("Фамилия: ")
    cursor.execute("INSERT INTO employees (name, surname) VALUES (?, ?)", (name, surname))
    conn.commit()
    print(f"Сотрудник {name} {surname} добавлен!")


# Главное меню
while True:
    print("\n" + "=" * 40)
    print("МАГАЗИН")
    print("=" * 40)
    print("1. Показать товары")
    print("2. Купить")
    print("3. Отчёт по дате")
    print("4. Посмотреть чек")
    print("5. Проверить остатки")
    print("6. Добавить товар")
    print("7. Добавить категорию")
    print("8. Добавить сотрудника")
    print("0. Выход")
    print("=" * 40)

    choice = input("Выберите действие: ")

    if choice == "1":
        show_products()
    elif choice == "2":
        buy_products()
    elif choice == "3":
        report_by_date()
    elif choice == "4":
        show_receipt()
    elif choice == "5":
        check_stock()
    elif choice == "6":
        add_product()
    elif choice == "7":
        add_category()
    elif choice == "8":
        add_employee()
    elif choice == "0":
        print("До свидания!")
        conn.close()
        break
    else:
        print("Неверный выбор!")