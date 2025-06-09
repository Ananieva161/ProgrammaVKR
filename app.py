import math
from flask import Flask, render_template, jsonify, request, redirect, url_for
import os
import psycopg2
from decimal import Decimal
from folium import folium
from geopy.distance import geodesic

app = Flask(__name__)


# Функция подключения к базе данных
def get_db_connection():
    conn = psycopg2.connect(
        # dbname="forest_management",
        dbname="ForestManagement",
        user="postgres",
        password="Ljcz2015",
        host="localhost"
    )
    return conn


@app.route('/')
def index():
    return render_template('index.html')
# # Функция парсинга координат
def parse_point1(x, y):
    return [y, x]  # Меняем порядок на [lat, lon]

# Получение данных из таблиц
def get_location_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ID_enterprise, EnterpriseName, EnterpriseLocation[0], EnterpriseLocation[1] FROM Enterprises")
    enterprises = [(row[0], row[1], parse_point1(row[3], row[2])) for row in cursor.fetchall()]
    cursor.execute("SELECT ID_timber_enterprise, Timber_enterpriseName, TimberLocation[0], TimberLocation[1] FROM Timber_Enterprises")
    timber_enterprises = [(row[0], row[1], parse_point1(row[2], row[3])) for row in cursor.fetchall()]
    cursor.execute("SELECT ID_consumer, ConsumerName, ConsumerLocation[0], ConsumerLocation[1] FROM Product_Consumers")
    consumers = [(row[0], row[1], parse_point1(row[3], row[2])) for row in cursor.fetchall()]
    cursor.execute("SELECT ID_logging, AreaName, AreaLocation[0], AreaLocation[1], ID_timber_enterprise FROM Logging_Areas")
    logging_areas = [(row[0], row[1], parse_point1(row[2], row[3]), row[4]) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return enterprises, timber_enterprises, consumers, logging_areas

@app.route('/map')
def map_view():
    enterprises, timber_enterprises, consumers, logging_areas = get_location_data()
    return render_template(
        'map.html',
        enterprises=enterprises,
        timber_enterprises=timber_enterprises,
        consumers=consumers,
        logging_areas=logging_areas
    )
def calculate_distance(p1, p2):
    # p1 и p2 — кортежи (lon, lat)
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.json
    entity_id = data['id']
    entity_type = data['type']
    lat, lon = data['lat'], data['lon']

    table_mapping = {
        "enterprise": "Enterprises",
        "timber": "Timber_Enterprises",
        "consumer": "Product_Consumers",
        "logging": "Logging_Areas"
    }

    location_column = f"{table_mapping[entity_type][:-1]}Location"
    id_column = f"ID_{entity_type}"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE {table_mapping[entity_type]} SET {location_column} = POINT(%s, %s) WHERE {id_column} = %s",
        (lon, lat, entity_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Координаты обновлены'})

@app.route('/save_roads', methods=['POST'])
def save_roads():
    data = request.json  # list of roads [{start: [lon, lat], end: [lon, lat]}]
    conn = get_db_connection()
    cur = conn.cursor()

    road_ids = []

    for road in data['roads']:
        start = road['start']
        end = road['end']
        length = calculate_distance(start, end)
        cur.execute("""
            INSERT INTO Roads (RoadStart, RoadEnd, RoadLength)
            VALUES (POINT(%s, %s), POINT(%s, %s), %s)
            RETURNING ID_road
        """, (start[0], start[1], end[0], end[1], length))
        road_id = cur.fetchone()[0]
        road_ids.append(road_id)

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'road_ids': road_ids})

@app.route('/save_route', methods=['POST'])
def save_route():
    data = request.json  # { roads: [id_road], type: 'supply' | 'delivery', ... }
    conn = get_db_connection()
    cur = conn.cursor()

    # Получить суммарную длину маршрута
    cur.execute("SELECT SUM(RoadLength) FROM Roads WHERE ID_road = ANY(%s)", (data['roads'],))
    distance = cur.fetchone()[0]
    travel_time = distance / 50  # допущение: средняя скорость 50

    # Сохранить маршрут
    cur.execute("INSERT INTO Transportation_Routes (Distance, Travel_Time) VALUES (%s, %s) RETURNING ID_route",
                (distance, travel_time))
    route_id = cur.fetchone()[0]

    # Добавить дороги маршрута
    for order, road_id in enumerate(data['roads']):
        cur.execute("INSERT INTO Route_Roads (ID_route, ID_road, Road_Order) VALUES (%s, %s, %s)",
                    (route_id, road_id, order))

    # Тариф: находим тариф перевозчика по дистанции
    carrier_id = data['carrier_id']
    cur.execute("""
        SELECT TariffCost FROM Tariffs 
        WHERE ID_carrier = %s AND Distance <= %s
        ORDER BY Distance DESC LIMIT 1
    """, (carrier_id, distance))
    cost = cur.fetchone()[0] if cur.rowcount else 0

    if data['type'] == 'supply':
        cur.execute("""
            INSERT INTO Raw_Material_Supply (ID_enterprise, ID_logging, ID_carrier, ID_route, Material_Volume, Material_Cost)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['enterprise_id'], data['logging_id'], carrier_id,
            route_id, data['volume'], cost
        ))
    elif data['type'] == 'delivery':
        cur.execute("""
            INSERT INTO Product_Delivery (ID_enterprise, ID_consumer, ID_carrier, ID_route, Delivery_Volume, Delivery_Cost)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['enterprise_id'], data['consumer_id'], carrier_id,
            route_id, data['volume'], cost
        ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'route_id': route_id, 'distance': distance, 'cost': cost})


import requests


def get_route_distance(lat1, lon1, lat2, lon2):
    """Функция для получения расстояния между двумя точками через API (например, OSRM)"""
    url = f'https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['routes'][0]['legs'][0]['distance'] / 1000  # Возвращаем расстояние в километрах
    return 0

@app.route('/Spravka')
def spravka():
    conn = get_db_connection()
    cur = conn.cursor()

    # Названия таблиц и их описания
    tables = {
        "Logging_Areas": "Участки лесозаготовки",
        "Timber_Species": "Лесоматериалы",
        "Timber_Enterprises": "Лесозаготовители",
        "Products": "Продукция",
        "Equipments": "Оборудование",
        "Employees": "Сотрудники",
        "Roads": "Дороги",
        "Product_Consumers": "Потребители продукции",
        "Regulations": "Регламент",
        "Enterprises": "Предприятия",
        "Raw_Material_Needs": "Потребность в сырье",
        "Productions": "Производство",
        "Raw_Material_Supply": "Поставка сырья",
        "Product_Delivery": "Доставка продукции",
        "Transportation_Routes": "Маршруты",
        "Employee_Enterprise": "Сотрудники предприятий",
        "Enterprise_Equipment": "Оборудование предприятий",
        "Route_Roads": "Дороги маршрутов",
        "Carriers": "Перевозчики",
        "Tariffs": "Тарифы"
    }

    # Столбцы для каждой таблицы
    columns = {
        "Logging_Areas": ["Название участка", "Географическое положение", "Предприятие-арендатор"],
        "Timber_Species": ["Название сортимента", "Название породы", "Длина", "Диаметр", "Бонитет"],
        "Timber_Enterprises": ["Название предприятия", "Географическое положение"],
        "Products": ["Название продукции", "Единица измерения"],
        "Equipments": ["Название оборудования", "Стоимость"],
        "Employees": ["Должность", "Тарифная ставка"],
        "Roads": ["Начальная точка", "Конечная точка", "Длина", "Пропускная способность", "Максимальная скорость"],
        "Product_Consumers": ["Название", "Географическое положение"],
        "Regulations": ["Наименование параметра", "Значение"],
        "Enterprises": ["Название", "Географическое положение", "Прочие расходы"],
        "Raw_Material_Needs": ["Предприятие", "Продукция", "Сортимент", "Объем сырья"],
        "Productions": ["Предприятие", "Продукция", "Объем производства", "Средняя цена"],
        "Raw_Material_Supply": ["Предприятие-получатель", "Сортимент", "Лесной участок", "Продукция", "Поставщик", "Маршрут", "Перевозчик", "Объем", "Стоимость"],
        "Product_Delivery": ["Предприятие", "Продукция", "Потребитель", "Маршрут", "Перевозчик", "Объем", "Стоимость"],
        "Transportation_Routes": ["Длина маршрута", "Время в пути"],
        "Employee_Enterprise": ["Предприятие", "Должность", "Количество", "Заработная плата"],
        "Enterprise_Equipment": ["Предприятие", "Оборудование", "Количество", "Амортизация", "Электричество", "Другие ресурсы", "Стоимость оборудования"],
        "Route_Roads": ["Маршрут", "Дорога", "Порядок"],
        "Carriers": ["Название перевозчика"],
        "Tariffs": ["Перевозчик", "Расстояние", "Единица измерения", "Стоимость"]
    }
    # Загружаем данные по каждой таблице
    table_data = {}
    for table in tables.keys():
        cur.execute(f'SELECT * FROM {table}')
        rows = cur.fetchall()

        # Убираем столбцы с id (предположим, что столбец id - это первый столбец)
        columns_for_table = columns.get(table, [])
        rows_without_id = []
        for row in rows:
            rows_without_id.append(row[1:])  # исключаем первый столбец (ID)

        table_data[table] = {
            'columns': columns_for_table,
            'data': rows_without_id
        }

    cur.close()
    conn.close()

    return render_template('dictionaries.html', tables=tables, columns=columns, table_data=table_data)
@app.route('/Spravka1', methods=['GET'])
def spravka1():
    conn = get_db_connection()
    cur = conn.cursor()

    # Названия таблиц и их описания
    tables = {
        "Logging_Areas": "Участки лесозаготовки",
        "Timber_Species": "Лесоматериалы",
        "Timber_Enterprises": "Лесозаготовители",
        "Products": "Продукция",
        "Equipments": "Оборудование",
        "Employees": "Сотрудники",
        "Roads": "Дороги",
        "Product_Consumers": "Потребители продукции",
        "Regulations": "Регламент",
        "Enterprises": "Предприятия",
        "Raw_Material_Needs": "Потребность в сырье",
        "Productions": "Производство",
        "Raw_Material_Supply": "Поставка сырья",
        "Product_Delivery": "Доставка продукции",
        "Transportation_Routes": "Маршруты",
        "Employee_Enterprise": "Сотрудники предприятий",
        "Enterprise_Equipment": "Оборудование предприятий",
        "Route_Roads": "Дороги маршрутов",
        "Carriers": "Перевозчики",
        "Tariffs": "Тарифы"
    }

    return render_template('dictionaries1.html', tables=tables)


@app.route('/get_table_data', methods=['POST'])
def get_table_data():
    data = request.get_json()  # Получаем данные как JSON
    table = data.get('table')

    if not table:
        return jsonify({'error': 'Table not specified'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    columns = {
        "Logging_Areas": ["Название участка", "Географическое положение", "Предприятие-арендатор"],
        "Timber_Species": ["Название сортимента", "Название породы", "Длина", "Диаметр", "Бонитет"],
        "Timber_Enterprises": ["Название предприятия", "Географическое положение"],
        "Products": ["Название продукции", "Единица измерения"],
        "Equipments": ["Название оборудования", "Стоимость"],
        "Employees": ["Должность", "Тарифная ставка"],
        "Roads": ["Начальная точка", "Конечная точка", "Длина", "Пропускная способность", "Максимальная скорость"],
        "Product_Consumers": ["Название", "Географическое положение"],
        "Regulations": ["Наименование параметра", "Значение"],
        "Enterprises": ["Название", "Географическое положение", "Прочие расходы"],
        "Raw_Material_Needs": ["Предприятие", "Продукция", "С Sortiment", "Объем сырья"],
        "Productions": ["Предприятие", "Продукция", "Объем производства", "Средняя цена"],
        "Raw_Material_Supply": ["Предприятие-получатель", "С Sortiment", "Лесной участок", "Продукция", "Поставщик",
                                "Маршрут", "Перевозчик", "Объем", "Стоимость"],
        "Product_Delivery": ["Предприятие", "Продукция", "Потребитель", "Маршрут", "Перевозчик", "Объем", "Стоимость"],
        "Transportation_Routes": ["Длина маршрута", "Время в пути"],
        "Employee_Enterprise": ["Предприятие", "Должность", "Количество", "Заработная плата"],
        "Enterprise_Equipment": ["Предприятие", "Оборудование", "Количество", "Амортизация", "Электричество",
                                 "Другие ресурсы", "Стоимость оборудования"],
        "Route_Roads": ["Маршрут", "Дорога", "Порядок"],
        "Carriers": ["Название перевозчика"],
        "Tariffs": ["Перевозчик", "Расстояние", "Единица измерения", "Стоимость"]
    }

    if table not in columns:
        return jsonify({'error': 'Invalid table selected'}), 400

    # Получаем все данные из таблицы, кроме 'id'
    cur.execute(f'SELECT * FROM {table}')
    rows = cur.fetchall()

    # Возвращаем данные
    return jsonify({
        'columns': columns[table],  # Возвращаем русские заголовки
        'rows': rows
    })


@app.route('/add_new_record', methods=['POST'])
def add_new_record():
    data = request.get_json()  # Получаем данные как JSON
    table = data['table']
    record_data = data['data']

    conn = get_db_connection()
    cur = conn.cursor()

    # Подготовим запрос для добавления новой записи
    columns = record_data.keys()
    placeholders = ', '.join([f"%({col})s" for col in columns])
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    cur.execute(sql, record_data)
    conn.commit()

    return jsonify({'success': True})


@app.route('/delete_record1', methods=['POST'])
def delete_record1():
    data = request.get_json()  # Получаем данные как JSON
    table = data['table']
    record_id = data['id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = %s", (record_id,))
    conn.commit()

    return jsonify({'success': True})


@app.route('/get_record', methods=['POST'])
def get_record():
    data = request.get_json()  # Получаем данные как JSON
    table = data['table']
    record_id = data['id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE id = %s", (record_id,))
    row = cur.fetchone()

    return jsonify({
        'row': row,
        'columns': [col[0] for col in cur.description]
    })

@app.route('/add_record', methods=['POST'])
def add_record():
    data = request.json
    table = data['table']
    values = data['values']

    conn = get_db_connection()
    cur = conn.cursor()

    # Убираем ID из значений
    if 'id' in values:
        del values['id']

    column_names = ', '.join(values.keys())
    column_values = tuple(values.values())
    placeholders = ', '.join(['%s'] * len(values))

    sql = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
    cur.execute(sql, column_values)
    conn.commit()

    cur.close()
    conn.close()
    return jsonify({"status": "success"})


@app.route('/update_record', methods=['POST'])
def update_record():
    data = request.json
    table = data['table']
    record_id = data['id']
    values = data['values']

    conn = get_db_connection()
    cur = conn.cursor()

    # Убираем ID из значений
    if 'id' in values:
        del values['id']

    set_clause = ', '.join([f"{col} = %s" for col in values.keys()])
    sql = f"UPDATE {table} SET {set_clause} WHERE id = %s"

    cur.execute(sql, (*values.values(), record_id))
    conn.commit()

    cur.close()
    conn.close()
    return jsonify({"status": "success"})


@app.route('/delete_record', methods=['POST'])
def delete_record():
    data = request.json
    table = data['table']
    record_id = data['id']

    conn = get_db_connection()
    cur = conn.cursor()

    sql = f"DELETE FROM {table} WHERE id = %s"
    cur.execute(sql, (record_id,))
    conn.commit()

    cur.close()
    conn.close()
    return jsonify({"status": "success"})

# Главная страница со списком предприятий
@app.route('/index22')
def index22():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ID_enterprise, EnterpriseName, EnterpriseLocation 
        FROM Enterprises
    """)

    enterprises = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index22.html', enterprises=enterprises)


# Детальная страница предприятия с возможностью редактирования
@app.route('/enterprise1/<int:enterprise_id>', methods=['GET', 'POST'])
def enterprise1(enterprise_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Получение новых координат и расчёт маршрута с карты
        data = request.json
        new_location = data.get('location')
        route_distances = data.get('route_distances')  # Получаем список дистанций маршрутов для перерасчёта

        # Обновляем местоположение предприятия в базе данных
        cursor.execute("""
                UPDATE Enterprises
                SET EnterpriseLocation = %s
                WHERE ID_enterprise = %s;
            """, (str(new_location), enterprise_id))
        conn.commit()
        supplier_tariff = float(data.get('supplier_tariff', 0))
        consumer_tariff = float(data.get('consumer_tariff', 0))
        # Обновляем маршруты с новыми дистанциями
        for route in route_distances:
            route_id = route['route_id']
            distance = Decimal(route['distance'])
            cursor.execute("""
                    UPDATE Transportation_Routes
                    SET Distance = %s
                    WHERE ID_route = %s;
                """, (distance, route_id))
            conn.commit()

        # Перерасчёт рентабельности после обновлений
        # Обновление данных, аналогично предыдущей логике
        recalculate_profitability(cursor, enterprise_id)

        cursor.close()
        conn.close()

        return jsonify({"message": "Местоположение и маршруты обновлены, рентабельность перерасчитана!"}), 200

    # 1. Информация о предприятии
    cursor.execute("""
        SELECT ID_enterprise, EnterpriseName, EnterpriseLocation, Other_Expenses
        FROM Enterprises WHERE ID_enterprise = %s;
    """, (enterprise_id,))
    enterprise = cursor.fetchone()
    if not enterprise:
        return jsonify({"error": "Предприятие не найдено."}), 404

    enterprise_location = enterprise[2] if enterprise[2] else (0, 0)
    other_expenses = Decimal(enterprise[3]) if enterprise[3] else Decimal(0)

    # 2. Поставщики сырья
    cursor.execute("""
        SELECT te.ID_timber_enterprise, te.Timber_enterpriseName, te.TimberLocation
        FROM Timber_Enterprises te
        JOIN Raw_Material_Supply rs ON te.ID_timber_enterprise = rs.ID_enterprise_resource 
        WHERE rs.ID_enterprise = %s;
    """, (enterprise_id,))
    suppliers = cursor.fetchall()  # Получаем данные о поставщиках

    # 3. Потребители продукции
    cursor.execute("""
        SELECT c.ID_consumer, c.ConsumerName, c.ConsumerLocation 
        FROM Product_Consumers c
        JOIN Product_Delivery pd ON c.ID_consumer = pd.ID_consumer
        WHERE pd.ID_enterprise = %s;
    """, (enterprise_id,))
    consumers = cursor.fetchall()  # Получаем данные о потребителях

    # 4. Оборудование предприятия
    cursor.execute("""
        SELECT eq.EquipmentName, ee.NCount, ee.EquipmentCost, ee.Depreciation, ee.Energy, ee.Other_Resource_Sum
        FROM Enterprise_Equipment ee
        JOIN Equipments eq ON ee.ID_equipment = eq.ID_equipment
        WHERE ee.ID_enterprise = %s;
    """, (enterprise_id,))
    equipment = cursor.fetchall()  # Получаем данные о оборудовании

    # 5. Трудовые ресурсы
    cursor.execute("""
        SELECT lr.EmployeeName, SUM(ee.Salary) AS Total_Salary, COUNT(ee.ID_employee) AS Employee_Count
        FROM Employee_Enterprise ee
        JOIN Employees lr ON ee.ID_employee = lr.ID_Employee
        WHERE ee.ID_enterprise = %s
        GROUP BY lr.EmployeeName;
    """, (enterprise_id,))
    labor_resources = cursor.fetchall()  # Получаем данные о трудовых ресурсах

    # 6. Поставки сырья (только через "Перевозчик 1")
    cursor.execute("""
        SELECT ts.TimberName, ts.SpeciesName, rs.Material_Volume, rs.Material_Cost, tr.Distance, tr.Travel_Time, c.CarrierName
        FROM Raw_Material_Supply rs
        JOIN Timber_Species ts ON rs.ID_timber = ts.ID_timber
        JOIN Transportation_Routes tr ON rs.ID_route = tr.ID_route
        JOIN Carriers c ON rs.ID_carrier = c.ID_carrier
        WHERE rs.ID_enterprise = %s AND c.CarrierName = '1';
    """, (enterprise_id,))
    raw_materials = cursor.fetchall()  # Получаем данные о поставках сырья
    cursor.execute("""
            SELECT p.ProductName, pr.Production_Volume, pr.ProductCost, tr.Distance, tr.Travel_Time, c.CarrierName
            FROM Productions pr
            JOIN Products p ON pr.ID_product = p.ID_product
            LEFT JOIN Product_Delivery pd ON pr.ID_product = pd.ID_product AND pr.ID_enterprise = pd.ID_enterprise
            LEFT JOIN Transportation_Routes tr ON pd.ID_route = tr.ID_route
            LEFT JOIN Carriers c ON pd.ID_carrier = c.ID_carrier
            WHERE pr.ID_enterprise = %s AND c.CarrierName = '2';
        """, (enterprise_id,))
    products = cursor.fetchall()  # Получаем данные о продукции
    cursor.execute("""
        SELECT p.ProductName, 
               pr.Production_Volume, 
               pr.ProductCost
        FROM Productions pr
        JOIN Products p ON pr.ID_product = p.ID_product
        WHERE pr.ID_enterprise = %s;
    """, (enterprise_id,))

    production_data = cursor.fetchall()  # Получаем данные о продукции
    cursor.execute("""
        SELECT SUM(Delivery_Volume * Delivery_Cost) AS Total_Revenue
        FROM Product_Delivery
        WHERE ID_enterprise = %s;
    """, (enterprise_id,))

    # Получение результата
    result = cursor.fetchone()
    revenue = result[0] if result[0] is not None else Decimal(0)  # Если выручка равна NULL, устанавливаем 0
    # print(revenue)
    # 8. Налоговые ставки
    cursor.execute("SELECT TaxName, Rate FROM Regulations")
    tax_rates = cursor.fetchall()
    taxes = {tax[0]: Decimal(tax[1]) for tax in tax_rates}  # Получение налоговых ставок

    # Получаем налоговые ставки с корректной проверкой
    cursor.execute("SELECT Rate FROM Regulations WHERE TaxName = 'Налоговая ставка на прибыль'")
    result = cursor.fetchone()
    profit_tax_rate = Decimal(result[0]) if result is not None else Decimal(0)
    # print(f"Налоговая ставка на прибыль: {profit_tax_rate}")

    cursor.execute("SELECT Rate FROM Regulations WHERE TaxName = 'Налоговая ставка на имущество'")
    result = cursor.fetchone()
    property_tax_rate = Decimal(result[0]) if result is not None else Decimal(0)
    # print(f"Налоговая ставка на имущество: {property_tax_rate}")

    cursor.execute("SELECT Rate FROM Regulations WHERE TaxName = 'Единый социальный налог'")
    result = cursor.fetchone()
    social_tax_rate = Decimal(result[0]) if result is not None else Decimal(0)
    # print(f"Единый социальный налог: {social_tax_rate}")

    # Рассчитываем показатели
    # 1. Выручка
    # revenue = sum([Decimal(p[1]) * Decimal(p[2]) for p in products])  # p[1]: Delivery_Volume, p[2]: Delivery_Cost
    print(f"Выручка (revenue) = {' + '.join([f'({p[1]} * {p[2]})' for p in products])} = {revenue}")

    # 2. Расходы на оплату труда
    labor_costs = sum([Decimal(lr[1]) * Decimal(lr[2]) * 12 for lr in labor_resources])  # lr[1]: Count, lr[2]: Salary
    print(
        f"Расходы на оплату труда (labor_costs) = {' + '.join([f'({lr[1]} * {lr[2]} * 12)' for lr in labor_resources])} = {labor_costs}")

    # 3. Стоимость основных фондов
    total_fixed_assets = sum(
        [Decimal(eq[2]) * Decimal(eq[1]) for eq in equipment])  # eq[1]: NCount, eq[2]: EquipmentCost
    print(
        f"Стоимость основных фондов (total_fixed_assets) = {' + '.join([f'({eq[2]} * {eq[1]})' for eq in equipment])} = {total_fixed_assets}")

    # 4. Амортизация оборудования
    total_depreciation = sum(
        [Decimal(eq[3]) * Decimal(eq[1]) for eq in equipment])  # eq[1]: NCount, eq[3]: Depreciation
    print(
        f"Амортизация оборудования (total_depreciation) = {' + '.join([f'({eq[1]} * {eq[3]})' for eq in equipment])} = {total_depreciation}")

    # Функция расчета транспортных расходов
    def get_transport_cost(route_id, carrier_id):
        cursor.execute("SELECT Distance FROM Transportation_Routes WHERE ID_route = %s", (route_id,))
        distance = cursor.fetchone()

        if not distance:
            return Decimal(0)

        distance = Decimal(distance[0])
        cursor.execute("SELECT Distance, TariffCost FROM Tariffs WHERE ID_carrier = %s ORDER BY Distance ASC",
                       (carrier_id,))
        tariffs = cursor.fetchall()

        for tariff_distance, tariff_cost in tariffs:
            if distance <= Decimal(tariff_distance):
                return Decimal(tariff_cost)

        return Decimal(tariffs[-1][1]) if tariffs else Decimal(0)

    # 5. Материальные расходы
    material_expenses = sum([
        Decimal(rm[2]) * Decimal(rm[3]) + get_transport_cost(rm[4], rm[5]) * Decimal(rm[2])
        # rm[2]: Material_Volume, rm[3]: Material_Cost, rm[4]: ID_route, rm[5]: ID_carrier
        for rm in raw_materials
    ])

    # Дополним выводом
    material_expenses_details = []
    for rm in raw_materials:
        transport_cost = get_transport_cost(rm[4], rm[5])  # Получаем стоимость транспортировки
        material_expenses_highlight = (Decimal(rm[2]) * Decimal(rm[3])) + (
                    transport_cost * Decimal(rm[2]))  # Показать детали
        material_expenses_details.append(
            f'({rm[2]} * {rm[3]}) + ({transport_cost} * {rm[2]}) = {material_expenses_highlight}')

    print(f"Материальные расходы (material_expenses) = {' + '.join(material_expenses_details)} = {material_expenses}")

    # Расходы на энергетические и другие ресурсы оборудования
    material_expenses_eff = sum([
        Decimal(eq[1]) * (Decimal(eq[4]) + Decimal(eq[5]))  # eq[1]: NCount, eq[4]: Energy, eq[5]: Other_Resource_Sum
        for eq in equipment
    ])

    print(
        f"Материальные расходы на эксплуатацию оборудования = {' + '.join([f'({eq[1]} * ({eq[4]} + {eq[5]}))' for eq in equipment])} = {material_expenses_eff}")

    # Транспортировка продукции
    material_expenses += sum([
        Decimal(p[1]) * get_transport_cost(p[3], p[4])  # p[1]: Delivery_Volume, p[3]: ID_route, p[4]: ID_carrier
        for p in products
    ])

    print(
        f"Транспортные расходы (продукции) = {' + '.join([f'({p[1]} * {get_transport_cost(p[3], p[4])})' for p in products])} = {material_expenses}")

    # 6. Себестоимость продукции
    production_cost = material_expenses + labor_costs + total_depreciation + other_expenses
    print(
        f"Себестоимость продукции (production_cost) = {material_expenses} + {labor_costs} + {total_depreciation} + {other_expenses} = {production_cost}")

    # 7. Оборотные средства (в данном случае просто равны себестоимости)
    working_capital = production_cost
    print(f"Оборотные средства (working_capital) = {working_capital}")

    # 8. Прибыль
    realized_profit = revenue - production_cost
    print(f"Прибыль (realized_profit) = {revenue} - {production_cost} = {realized_profit}")

    # 9. Налогооблагаемая прибыль
    taxable_profit = realized_profit - total_fixed_assets * property_tax_rate
    print(
        f"Налогооблагаемая прибыль (taxable_profit) = {realized_profit} - ({total_fixed_assets} * {property_tax_rate}) = {taxable_profit}")

    # 10. Расчет налогов
    property_tax = total_fixed_assets * property_tax_rate
    profit_tax = taxable_profit * profit_tax_rate if taxable_profit > 0 else Decimal(0)
    social_tax = labor_costs * social_tax_rate
    total_taxes = property_tax + profit_tax + social_tax

    print(
        f"Налоги: \n  - Налог на имущество = {total_fixed_assets} * {property_tax_rate} = {property_tax} \n  - Налог на прибыль = {taxable_profit} * {profit_tax_rate} = {profit_tax} \n  - Социальный налог = {labor_costs} * {social_tax_rate} = {social_tax}")
    print(f"Общие налоги (total_taxes) = {property_tax} + {profit_tax} + {social_tax} = {total_taxes}")

    # 11. Рентабельность
    profitability = (taxable_profit / (total_fixed_assets + working_capital)) * Decimal(100) if \
        (total_fixed_assets + working_capital) > 0 else Decimal(0)

    print(
        f"Рентабельность (profitability) = ({taxable_profit} / ({total_fixed_assets} + {working_capital})) * 100 = {profitability}")


    # Получение баланса сырья и продукции
    raw_material_balance = get_raw_material_balance(enterprise_id)
    product_balance = get_product_balance(enterprise_id)

    cursor.close()
    conn.close()

    return render_template(
        'enterprise13.html',
        enterprise=enterprise,
        suppliers=suppliers,
        consumers=consumers,
        equipment=equipment,
        labor_resources=labor_resources,
        raw_materials=raw_materials,
        products=products,
        total_fixed_assets=total_fixed_assets,
        total_depreciation=total_depreciation,
        material_expenses=material_expenses,
        production_cost=production_cost,
        working_capital=working_capital,
        realized_profit=realized_profit,
        taxable_profit=taxable_profit,
        property_tax=property_tax,
        profit_tax=profit_tax,
        social_tax=social_tax,
        total_taxes=total_taxes,
        profitability=profitability,
        production_data = production_data,
        enterprise_location=enterprise_location,
        raw_material_balance=raw_material_balance,
        product_balance=product_balance
    )

def calculate_tariff(distance_km, carrier_id, conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT Distance, TariffCost FROM Tariffs
        WHERE ID_carrier = %s
        ORDER BY Distance
    """, (carrier_id,))
    tariffs = cur.fetchall()
    for dist, cost in tariffs:
        if distance_km < dist:
            return float(cost)
    return float(tariffs[-1][1]) if tariffs else 0

@app.route('/recalculate-profitability', methods=['POST'])
def recalculate_profitability():
    data = request.get_json()
    enterprise_id = data['enterprise_id']
    tariff = Decimal(data['tariff'])

    profitability = calculate_profitability(enterprise_id, tariff)
    return jsonify({'profitability': float(profitability)})
def calculate_profitability(enterprise_id, tariff):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Информация о предприятии
    cursor.execute("""
        SELECT ID_enterprise, EnterpriseName, EnterpriseLocation, Other_Expenses
        FROM Enterprises WHERE ID_enterprise = %s;
    """, (enterprise_id,))
    enterprise = cursor.fetchone()
    if not enterprise:
        return jsonify({"error": "Предприятие не найдено."}), 404

    enterprise_location = enterprise[2] if enterprise[2] else (0, 0)
    other_expenses = Decimal(enterprise[3]) if enterprise[3] else Decimal(0)

    # 2. Поставщики сырья
    cursor.execute("""
        SELECT te.ID_timber_enterprise, te.Timber_enterpriseName, te.TimberLocation
        FROM Timber_Enterprises te
        JOIN Raw_Material_Supply rs ON te.ID_timber_enterprise = rs.ID_enterprise_resource 
        WHERE rs.ID_enterprise = %s;
    """, (enterprise_id,))
    suppliers = cursor.fetchall()  # Получаем данные о поставщиках

    # 3. Потребители продукции
    cursor.execute("""
        SELECT c.ID_consumer, c.ConsumerName, c.ConsumerLocation 
        FROM Product_Consumers c
        JOIN Product_Delivery pd ON c.ID_consumer = pd.ID_consumer
        WHERE pd.ID_enterprise = %s;
    """, (enterprise_id,))
    consumers = cursor.fetchall()  # Получаем данные о потребителях

    # 4. Оборудование предприятия
    cursor.execute("""
        SELECT eq.EquipmentName, ee.NCount, ee.EquipmentCost, ee.Depreciation, ee.Energy, ee.Other_Resource_Sum
        FROM Enterprise_Equipment ee
        JOIN Equipments eq ON ee.ID_equipment = eq.ID_equipment
        WHERE ee.ID_enterprise = %s;
    """, (enterprise_id,))
    equipment = cursor.fetchall()  # Получаем данные о оборудовании

    # 5. Трудовые ресурсы
    cursor.execute("""
        SELECT lr.EmployeeName, SUM(ee.Salary) AS Total_Salary, COUNT(ee.ID_employee) AS Employee_Count
        FROM Employee_Enterprise ee
        JOIN Employees lr ON ee.ID_employee = lr.ID_Employee
        WHERE ee.ID_enterprise = %s
        GROUP BY lr.EmployeeName;
    """, (enterprise_id,))
    labor_resources = cursor.fetchall()  # Получаем данные о трудовых ресурсах
    # 6. Поставки сырья (только через "Перевозчик 1")
    cursor.execute("""
        SELECT ts.TimberName, ts.SpeciesName, rs.Material_Volume, rs.Material_Cost, tr.Distance, tr.Travel_Time, c.CarrierName
        FROM Raw_Material_Supply rs
        JOIN Timber_Species ts ON rs.ID_timber = ts.ID_timber
        JOIN Transportation_Routes tr ON rs.ID_route = tr.ID_route
        JOIN Carriers c ON rs.ID_carrier = c.ID_carrier
        WHERE rs.ID_enterprise = %s AND c.CarrierName = '1';
    """, (enterprise_id,))
    raw_materials = cursor.fetchall()  # Получаем данные о поставках сырья
    cursor.execute("""
            SELECT p.ProductName, pr.Production_Volume, pr.ProductCost, tr.Distance, tr.Travel_Time, c.CarrierName
            FROM Productions pr
            JOIN Products p ON pr.ID_product = p.ID_product
            LEFT JOIN Product_Delivery pd ON pr.ID_product = pd.ID_product AND pr.ID_enterprise = pd.ID_enterprise
            LEFT JOIN Transportation_Routes tr ON pd.ID_route = tr.ID_route
            LEFT JOIN Carriers c ON pd.ID_carrier = c.ID_carrier
            WHERE pr.ID_enterprise = %s AND c.CarrierName = '2';
        """, (enterprise_id,))
    products = cursor.fetchall()  # Получаем данные о продукции
    # 6. Поставки сырья (только через "Перевозчик 1")
    cursor.execute("""
        SELECT ts.TimberName, ts.SpeciesName, rs.Material_Volume, rs.Material_Cost, tr.Distance, tr.Travel_Time, c.CarrierName
        FROM Raw_Material_Supply rs
        JOIN Timber_Species ts ON rs.ID_timber = ts.ID_timber
        JOIN Transportation_Routes tr ON rs.ID_route = tr.ID_route
        JOIN Carriers c ON rs.ID_carrier = c.ID_carrier
        WHERE rs.ID_enterprise = %s AND c.CarrierName = '1';
    """, (enterprise_id,))
    raw_materials = cursor.fetchall()  # Получаем данные о поставках сырья
    cursor.execute("""
            SELECT p.ProductName, pr.Production_Volume, pr.ProductCost, tr.Distance, tr.Travel_Time, c.CarrierName
            FROM Productions pr
            JOIN Products p ON pr.ID_product = p.ID_product
            LEFT JOIN Product_Delivery pd ON pr.ID_product = pd.ID_product AND pr.ID_enterprise = pd.ID_enterprise
            LEFT JOIN Transportation_Routes tr ON pd.ID_route = tr.ID_route
            LEFT JOIN Carriers c ON pd.ID_carrier = c.ID_carrier
            WHERE pr.ID_enterprise = %s AND c.CarrierName = '2';
        """, (enterprise_id,))
    products = cursor.fetchall()  # Получаем данные о продукции
    # Выполнение запроса для получения выручки
    cursor.execute("""
        SELECT SUM(Delivery_Volume * Delivery_Cost) AS Total_Revenue
        FROM Product_Delivery
        WHERE ID_enterprise = %s;
    """, (enterprise_id,))

    # Получение результата
    result = cursor.fetchone()
    revenue = result[0] if result[0] is not None else Decimal(0)  # Если выручка равна NULL, устанавливаем 0
    print(revenue)

    print(f"Выручка (revenue) = {revenue}")
    # 8. Налоговые ставки
    cursor.execute("SELECT TaxName, Rate FROM Regulations")
    tax_rates = cursor.fetchall()
    taxes = {tax[0]: Decimal(tax[1]) for tax in tax_rates}  # Получение налоговых ставок

    # Получаем налоговые ставки с корректной проверкой
    cursor.execute("SELECT Rate FROM Regulations WHERE TaxName = 'Налоговая ставка на прибыль'")
    result = cursor.fetchone()
    profit_tax_rate = Decimal(result[0]) if result is not None else Decimal(0)
    print(f"Налоговая ставка на прибыль: {profit_tax_rate}")

    cursor.execute("SELECT Rate FROM Regulations WHERE TaxName = 'Налоговая ставка на имущество'")
    result = cursor.fetchone()
    property_tax_rate = Decimal(result[0]) if result is not None else Decimal(0)
    print(f"Налоговая ставка на имущество: {property_tax_rate}")

    cursor.execute("SELECT Rate FROM Regulations WHERE TaxName = 'Единый социальный налог'")
    result = cursor.fetchone()
    social_tax_rate = Decimal(result[0]) if result is not None else Decimal(0)
    print(f"Единый социальный налог: {social_tax_rate}")

    # Рассчитываем показатели
    # 1. Выручка
    # revenue = sum([Decimal(p[1]) * Decimal(p[2]) for p in products])  # p[1]: Delivery_Volume, p[2]: Delivery_Cost
    print(f"Выручка (revenue) = {' + '.join([f'({p[1]} * {p[2]})' for p in products])} = {revenue}")

    # 2. Расходы на оплату труда
    labor_costs = sum([Decimal(lr[1]) * Decimal(lr[2]) * 12 for lr in labor_resources])  # lr[1]: Count, lr[2]: Salary
    print(
        f"Расходы на оплату труда (labor_costs) = {' + '.join([f'({lr[1]} * {lr[2]} * 12)' for lr in labor_resources])} = {labor_costs}")

    # 3. Стоимость основных фондов
    total_fixed_assets = sum(
        [Decimal(eq[2]) * Decimal(eq[1]) for eq in equipment])  # eq[1]: NCount, eq[2]: EquipmentCost
    print(
        f"Стоимость основных фондов (total_fixed_assets) = {' + '.join([f'({eq[2]} * {eq[1]})' for eq in equipment])} = {total_fixed_assets}")

    # 4. Амортизация оборудования
    total_depreciation = sum(
        [Decimal(eq[3]) * Decimal(eq[1]) for eq in equipment])  # eq[1]: NCount, eq[3]: Depreciation
    print(
        f"Амортизация оборудования (total_depreciation) = {' + '.join([f'({eq[1]} * {eq[3]})' for eq in equipment])} = {total_depreciation}")

    # Функция расчета транспортных расходов
    def get_transport_cost(route_id, carrier_id):
        cursor.execute("SELECT Distance FROM Transportation_Routes WHERE ID_route = %s", (route_id,))
        distance = cursor.fetchone()

        if not distance:
            return Decimal(0)

        distance = Decimal(distance[0])
        cursor.execute("SELECT Distance, TariffCost FROM Tariffs WHERE ID_carrier = %s ORDER BY Distance ASC",
                       (carrier_id,))
        tariffs = cursor.fetchall()

        for tariff_distance, tariff_cost in tariffs:
            if distance <= Decimal(tariff_distance):
                return Decimal(tariff_cost)

        return Decimal(tariffs[-1][1]) if tariffs else Decimal(0)

    # 5. Материальные расходы
    material_expenses = sum([
        Decimal(rm[2]) * Decimal(rm[3]) + get_transport_cost(rm[4], rm[5]) * Decimal(rm[2])
        # rm[2]: Material_Volume, rm[3]: Material_Cost, rm[4]: ID_route, rm[5]: ID_carrier
        for rm in raw_materials
    ])

    # Дополним выводом
    material_expenses_details = []
    for rm in raw_materials:
        transport_cost = get_transport_cost(rm[4], rm[5])  # Получаем стоимость транспортировки
        material_expenses_highlight = (Decimal(rm[2]) * Decimal(rm[3])) + (
                    transport_cost * Decimal(rm[2]))  # Показать детали
        material_expenses_details.append(
            f'({rm[2]} * {rm[3]}) + ({transport_cost} * {rm[2]}) = {material_expenses_highlight}')

    print(f"Материальные расходы (material_expenses) = {' + '.join(material_expenses_details)} = {material_expenses}")

    # Расходы на энергетические и другие ресурсы оборудования
    material_expenses_eff = sum([
        Decimal(eq[1]) * (Decimal(eq[4]) + Decimal(eq[5]))  # eq[1]: NCount, eq[4]: Energy, eq[5]: Other_Resource_Sum
        for eq in equipment
    ])

    print(
        f"Материальные расходы на эксплуатацию оборудования = {' + '.join([f'({eq[1]} * ({eq[4]} + {eq[5]}))' for eq in equipment])} = {material_expenses_eff}")

    # Транспортировка продукции
    material_expenses_eff += sum([
        Decimal(p[1]) * get_transport_cost(p[3], p[4])  # p[1]: Delivery_Volume, p[3]: ID_route, p[4]: ID_carrier
        for p in products
    ])
    # Добавляем к материальным расходам эксплуатацию оборудования
    material_expenses += material_expenses_eff

    # Добавляем к материальным расходам переданный тариф
    material_expenses += tariff
    print(
        f"Транспортные расходы (продукции) = {' + '.join([f'({p[1]} * {get_transport_cost(p[3], p[4])})' for p in products])} = {material_expenses}")

    # 6. Себестоимость продукции
    production_cost = material_expenses + labor_costs + total_depreciation + other_expenses
    print(
        f"Себестоимость продукции (production_cost) = {material_expenses} + {labor_costs} + {total_depreciation} + {other_expenses} = {production_cost}")

    # 7. Оборотные средства (в данном случае просто равны себестоимости)
    working_capital = production_cost
    print(f"Оборотные средства (working_capital) = {working_capital}")

    # 8. Прибыль
    realized_profit = revenue - production_cost
    print(f"Прибыль (realized_profit) = {revenue} - {production_cost} = {realized_profit}")

    # 9. Налогооблагаемая прибыль
    taxable_profit = realized_profit - total_fixed_assets * property_tax_rate
    print(
        f"Налогооблагаемая прибыль (taxable_profit) = {realized_profit} - ({total_fixed_assets} * {property_tax_rate}) = {taxable_profit}")

    # 10. Расчет налогов
    property_tax = total_fixed_assets * property_tax_rate
    profit_tax = taxable_profit * profit_tax_rate if taxable_profit > 0 else Decimal(0)
    social_tax = labor_costs * social_tax_rate
    total_taxes = property_tax + profit_tax + social_tax

    print(
        f"Налоги: \n  - Налог на имущество = {total_fixed_assets} * {property_tax_rate} = {property_tax} \n  - Налог на прибыль = {taxable_profit} * {profit_tax_rate} = {profit_tax} \n  - Социальный налог = {labor_costs} * {social_tax_rate} = {social_tax}")
    print(f"Общие налоги (total_taxes) = {property_tax} + {profit_tax} + {social_tax} = {total_taxes}")

    # 11. Рентабельность
    profitability = (taxable_profit / (total_fixed_assets + working_capital)) * Decimal(100) if \
        (total_fixed_assets + working_capital) > 0 else Decimal(0)

    print(
        f"Рентабельность (profitability) = ({taxable_profit} / ({total_fixed_assets} + {working_capital})) * 100 = {profitability}")

    cursor.close()
    conn.close()
    return profitability


@app.route('/update-enterprise-location', methods=['POST'])
def update_enterprise_location(enterprise_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    data = request.get_json()
    lat = data['lat']
    lng = data['lng']
    dmsCoords = data['dmsCoords']

    # Обновление местоположения предприятия в базе данных
    cursor.execute(
        "UPDATE Enterprises SET EnterpriseLocation = POINT(%s, %s), EnterpriseLocationDMS = %s WHERE ID_enterprise = %s",
        (lng, lat, dmsCoords, enterprise_id))  # Здесь 1 - это ID предприятия
    conn.commit()

    return jsonify({"status": "success", "message": "Местоположение обновлено!"})
import re

import folium
from folium import Marker, PolyLine

@app.route('/rout')
def rout():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Получение данных о предприятиях и маршрутах из базы данных
    cursor.execute("SELECT * FROM Enterprises")
    enterprises = cursor.fetchall()

    enterprise_data = []
    for enterprise in enterprises:
        id_enterprise, enterprisename, enterpriselocation, other_expenses = enterprise

        # Получение маршрутов для данного предприятия
        cursor.execute("SELECT  tr.Distance, tr.Travel_Time "
                      "FROM Transportation_Route tr "
                      "JOIN Enterprise_Transportation_Route etr ON tr.ID_route = etr.ID_route "
                      "WHERE etr.ID_enterprise = %s", (id_enterprise,))
        routes = cursor.fetchall()

        route_data = []
        for route in routes:
            # Извлечение координат из строковых значений
            start_point_coords = [float(x) for x in re.findall(r"-?\d+\.?\d*", route[0])]
            end_point_coords = [float(x) for x in re.findall(r"-?\d+\.?\d*", route[1])]

            route_data.append({
                "start_point": start_point_coords,
                "end_point": end_point_coords,
                "distance": route[2],
                "travel_time": route[3],
                "capacity": route[4]
            })

        # Извлечение координат из строкового значения для предприятия
        enterprise_location_coords = [float(x) for x in re.findall(r"-?\d+\.?\d*", enterpriselocation)]

        enterprise_data.append({
            "id": id_enterprise,
            "name": enterprisename,
            "location": enterprise_location_coords,
            "other_expenses": other_expenses,
            "routes": route_data
        })
    conn.close()

    # Создание карты Карелии
    map = folium.Map(location=[62.5833, 30.1667], zoom_start=8)

    # Отображение предприятий на карте
    for enterprise in enterprise_data:
        Marker(
            location=enterprise["location"],
            popup=f"<b>{enterprise['name']}</b><br>"
                  f"Производственный объем: {enterprise['production_volume']}<br>"
                  f"Количество работников: {enterprise['num_workers']}"
                  # f"Производственный объем: {enterprise['production_volume']}<br>"\
                  # f"Количество работников: {enterprise['num_workers']}<br>" \
                  # f"Цена продукции: {enterprise['product_price']} руб.<br>" \
                  # f"Затраты на топливо: {enterprise['fuel_cost']} руб.<br>" \
                  # f"Прочие расходы: {enterprise['other_expenses']} руб.<br>" \
                  # f"Количество рабочих дней в году: {enterprise['calendar_days']}<br>"
                  # f"Норма складских запасов: {enterprise['stock_norm']} дней"
        ).add_to(map)

    # Отображение дорог на карте
    feature_group = folium.FeatureGroup(name="Маршруты")
    for enterprise in enterprise_data:
        for route in enterprise["routes"]:
            PolyLine(
                locations=[route["start_point"], route["end_point"]],
                color="green",
                weight=10,
                popup=f"Расстояние: {route['distance']} км<br>"
                      f"Время в пути: {route['travel_time']} ч<br>"
                      f"Вместимость: {route['capacity']} т"
            ).add_to(feature_group)
    feature_group.add_to(map)

    # Добавление легенды
    folium.LayerControl().add_to(map)

    # Сохранение карты в HTML-файл
    map.save('templates/transrout1.html')

    return render_template('transrout.html', enterprises=enterprise_data, routes=enterprise_data)


def get_enterprises():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ID_enterprise, EnterpriseName FROM Enterprises")
    enterprises = cur.fetchall()
    enterprise_logo = os.path.join('static', 'enterprise_logo.png')
    conn.close()
    return enterprises

# Получение баланса сырья для выбранного предприятия
def get_raw_material_balance(enterprise_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''
        WITH combined AS (
            SELECT 
                COALESCE(r.ID_timber, s.ID_timber) AS ID_timber,
                COALESCE(r.ID_enterprise, s.ID_enterprise) AS ID_enterprise,
                COALESCE(r.ID_product, s.ID_product) AS ID_product,
                COALESCE(r.Raw_Material_Volume, 0) AS required_volume,
                COALESCE(s.Material_Volume, 0) AS supplied_volume
            FROM Raw_Material_Needs r
            FULL OUTER JOIN Raw_Material_Supply s ON 
                r.ID_timber = s.ID_timber AND 
                r.ID_enterprise = s.ID_enterprise AND 
                r.ID_product = s.ID_product
            WHERE COALESCE(r.ID_enterprise, s.ID_enterprise) = %s
        )
        SELECT 
            CONCAT(ts.TimberName, ' ', ts.SpeciesName) AS name,
            SUM(combined.required_volume) AS planned_volume,
            SUM(combined.supplied_volume) AS total_supplied_volume
        FROM combined
        LEFT JOIN Timber_Species ts ON combined.ID_timber = ts.ID_timber
        GROUP BY name
        ORDER BY name;
    ''', (enterprise_id, ))

    data = cur.fetchall()
    conn.close()

    result = []
    for name, planned_volume, supplied_volume in data:
        planned_volume = planned_volume or 0
        supplied_volume = supplied_volume or 0
        diff = planned_volume - supplied_volume
        if diff == 0:
            status = "✓"
        elif diff < 0:
            status = "+" + str(abs(diff))
        else:
            status = "-" + str(diff)

        result.append((name, planned_volume, supplied_volume, status))

    return result


def get_product_balance(enterprise_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.ProductName, COALESCE(pr.Production_Volume, 0), COALESCE(SUM(d.Delivery_Volume), 0)
        FROM Productions pr
        LEFT JOIN Product_Delivery d ON pr.ID_product = d.ID_product AND pr.ID_enterprise = d.ID_enterprise
        JOIN Products p ON pr.ID_product = p.ID_product
        WHERE pr.ID_enterprise = %s
        GROUP BY p.ProductName, pr.Production_Volume;
    ''', (enterprise_id,))

    data = cur.fetchall()
    conn.close()

    # print("Данные по продукции:")
    # for row in data:
    #     print(row)  # Для отладки выводим каждую строку

    result = []
    for name, produced, delivered in data:
        produced = produced or 0  # Заменяем None на 0
        delivered = delivered or 0  # Заменяем None на 0
        diff = produced - delivered
        status = "✓" if diff == 0 else ("+" + str(abs(diff)) if diff < 0 else "-" + str(diff))
        result.append((name, produced, delivered, status))

    return result


@app.route('/balans')
def balans():
    enterprises = get_enterprises()
    return render_template('balance.html', enterprises=enterprises)


@app.route('/get_balance', methods=['POST'])
def get_balance():
    data = request.get_json()  # Получаем JSON-данные
    enterprise_id = data.get('enterprise_id') if data else None
    # enterprise_id = request.form.get('enterprise_id')
    raw_material_balance = get_raw_material_balance(enterprise_id)
    product_balance = get_product_balance(enterprise_id)
    return jsonify({'raw_material': raw_material_balance, 'product': product_balance})



def parse_point(point_str):
    """Парсит строку формата (lat, lng) и возвращает словарь {lat, lng}"""
    point_str = point_str.strip("()")  # Убираем скобки
    lat, lng = map(float, point_str.split(","))  # Разделяем по запятой
    return {'lat': lat, 'lng': lng}


def parse_polygon(polygon_str):
    """Парсит строку формата ((lat1 lng1, lat2 lng2, ...)) и возвращает список координат"""
    polygon_str = polygon_str.replace("(", "").replace(")", "").strip()  # Убираем скобки
    if not polygon_str:
        return []  # Если строка пустая, возвращаем пустой список

    # Разделяем строку по запятой, но проверяем, чтобы пробелы вокруг запятой не мешали
    points = polygon_str.split(",")
    coordinates = []

    for point in points:
        try:
            # Удаляем лишние пробелы вокруг координат
            lat, lng = map(float, point.strip().split())  # Разделяем по пробелу
            coordinates.append([lat, lng])
        except ValueError:
            print(f"Ошибка обработки точки: {point}")  # Выводим проблемную строку
            continue  # Пропускаем ошибочные точки

    return coordinates
def get_suppliers():
    """
    Получает список поставщиков из базы данных.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ID_timber_enterprise, Timber_enterpriseName, TimberLocation FROM Timber_Enterprises")
    suppliers = cur.fetchall()
    cur.close()
    conn.close()

    return [{'id': s[0], 'name': s[1], 'location': parse_point(s[2])} for s in suppliers]


def get_logging_areas():
    """
    Получает список всех участков лесозаготовки и их границы.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ID_logging, AreaName, AreaLocation, ID_timber_enterprise FROM Logging_Areas")
    areas = cur.fetchall()
    cur.close()
    conn.close()

    return [{'id': a[0], 'name': a[1], 'polygon': parse_point(a[2]), 'enterprise_id': a[3]} for a in areas]


def get_all_timber_species():
    """
    Получает все данные о древесине для всех участков.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM Timber_Species;

    """)
    species_data = cur.fetchall()
    cur.close()
    conn.close()
    # Для отладки: выводим результат
    print("Тимбер Списки:", species_data)
    return [{
        'name': s[0],
        'species': s[1],
        'length': s[2],
        'diameter': s[3],
        'quality': s[4],
        'area_name': s[5]
    } for s in species_data]


@app.route('/supmap')
def sup():
    """
    Главная страница, отображающая карту с поставщиками и участками.
    """
    suppliers = get_suppliers()  # Получаем данные о поставщиках
    logging_areas = get_logging_areas()  # Получаем данные об участках
    timber_species = get_all_timber_species()  # Получаем данные о древесине для всех участков

    return render_template('supmap.html', suppliers=suppliers, logging_areas=logging_areas, timber_species=timber_species)

if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=5000, debug=True)
    app.run(debug=True)
