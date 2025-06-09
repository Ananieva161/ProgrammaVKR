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
    enterprises = [(row[0], row[1], parse_point1(row[2], row[3])) for row in cursor.fetchall()]
    # cursor.execute("SELECT ID_enterprise, EnterpriseName, EnterpriseLocation FROM Enterprises")
    # enterprises = [(row[0], row[1], parse_point1(row[2])) for row in cursor.fetchall()]

    cursor.execute("SELECT ID_timber_enterprise, Timber_enterpriseName, TimberLocation[0], TimberLocation[1] FROM Timber_Enterprises")
    timber_enterprises = [(row[0], row[1], parse_point1(row[2], row[3])) for row in cursor.fetchall()]
    # cursor.execute("SELECT ID_timber_enterprise, Timber_enterpriseName, TimberLocation FROM Timber_Enterprises")
    # timber_enterprises = [(row[0], row[1], parse_point1(row[2])) for row in cursor.fetchall()]

    cursor.execute("SELECT ID_consumer, ConsumerName, ConsumerLocation[0], ConsumerLocation[1] FROM Product_Consumers")
    consumers = [(row[0], row[1], parse_point1(row[2], row[3])) for row in cursor.fetchall()]
    # cursor.execute("SELECT ID_consumer, ConsumerName, ConsumerLocation FROM Product_Consumers")
    # consumers = [(row[0], row[1], parse_point1(row[2])) for row in cursor.fetchall()]

    cursor.execute("SELECT ID_logging, AreaName, AreaLocation[0], AreaLocation[1], ID_timber_enterprise FROM Logging_Areas")
    logging_areas = [(row[0], row[1], parse_point1(row[2], row[3]), row[4]) for row in cursor.fetchall()]
    # cursor.execute("SELECT ID_logging, AreaName, AreaLocation, ID_timber_enterprise FROM Logging_Areas")
    # logging_areas = [(row[0], row[1], parse_point1(row[2])) for row in cursor.fetchall()]
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
# Обновление координат в БД
# @app.route('/update_location', methods=['POST'])
# def update_location():
#     data = request.json
#     entity_id = data['id']
#     entity_type = data['type']  # "enterprise", "timber", "consumer", "logging"
#     lat, lon = data['lat'], data['lon']
#
#     table_mapping = {
#         "enterprise": "Enterprises",
#         "timber": "Timber_Enterprises",
#         "consumer": "Product_Consumers",
#         "logging": "Logging_Areas"
#     }
#
#     table_name = table_mapping.get(entity_type)
#     if not table_name:
#         return jsonify({'error': 'Неверный тип объекта'}), 400
#
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute(
#         f"UPDATE {table_name} SET {table_name[:-1]}Location = 'POINT({lon} {lat})' WHERE ID_{entity_type} = %s",
#         (entity_id,)
#     )
#     conn.commit()
#     cursor.close()
#     conn.close()
#
#     return jsonify({'message': 'Координаты обновлены'}), 200

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
        "Raw_Material_Needs": ["Предприятие", "Продукция", "С Sortiment", "Объем сырья"],
        "Productions": ["Предприятие", "Продукция", "Объем производства", "Средняя цена"],
        "Raw_Material_Supply": ["Предприятие-получатель", "С Sortiment", "Лесной участок", "Продукция", "Поставщик", "Маршрут", "Перевозчик", "Объем", "Стоимость"],
        "Product_Delivery": ["Предприятие", "Продукция", "Потребитель", "Маршрут", "Перевозчик", "Объем", "Стоимость"],
        "Transportation_Routes": ["Длина маршрута", "Время в пути"],
        "Employee_Enterprise": ["Предприятие", "Должность", "Количество", "Заработная плата"],
        "Enterprise_Equipment": ["Предприятие", "Оборудование", "Количество", "Амортизация", "Электричество", "Другие ресурсы", "Стоимость оборудования"],
        "Route_Roads": ["Маршрут", "Дорога", "Порядок"],
        "Carriers": ["Название перевозчика"],
        "Tariffs": ["Перевозчик", "Расстояние", "Единица измерения", "Стоимость"]
    }

    table_data = {}

    # Получаем имя таблицы из параметра URL
    table_name = request.args.get('table_name')  # Получаем параметр из URL

    if table_name and table_name in tables:
        # Получаем столбцы таблицы, исключая 'id'
        cur.execute(f"PRAGMA table_info({table_name})")
        columns_in_table = cur.fetchall()

        # Отладочный вывод для столбцов
        print(f"Столбцы в таблице {table_name}: {columns_in_table}")

        column_names = [column[1] for column in columns_in_table if column[1] != 'id']  # Исключаем 'id'

        # Отладочный вывод для столбцов, которые будут запрашиваться
        print(f"Запрашиваемые столбцы: {column_names}")

        select_query = f"SELECT {', '.join(column_names)} FROM {table_name}"

        # Отладочный вывод для SQL-запроса
        print(f"SQL-запрос: {select_query}")

        cur.execute(select_query)
        rows = cur.fetchall()

        # Отладочный вывод для данных
        print(f"Данные из базы: {rows}")

        table_data[table_name] = rows

    cur.close()
    conn.close()

    return render_template('dictionaries1.html', tables=tables, columns=columns, table_data=table_data)


# Получаем данные столбцов для формы добавления записи
@app.route('/get_columns', methods=['POST'])
def get_columns():
    table = request.json['table']
    columns = {
        # Возвращаем столбцы для таблиц
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
    return jsonify({"columns": columns.get(table, [])})

@app.route('/add_logging_area', methods=['POST'])
def add_logging_area():
    data = request.json
    name = data['AreaName']
    lat = data['Latitude']
    lng = data['Longitude']
    enterprise_name = data['Enterprise']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT ID_timber_enterprise FROM Timber_Enterprises WHERE Timber_enterpriseName = %s', (enterprise_name,))
    enterprise_id = cur.fetchone()[0]

    cur.execute(
        'INSERT INTO Logging_Areas (AreaName, AreaLocation, ID_timber_enterprise) VALUES (%s, point(%s, %s), %s)',
        (name, lng, lat, enterprise_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/update_logging_area', methods=['POST'])
def update_logging_area():
    data = request.json
    old_name = data['OldName']
    new_name = data['AreaName']
    lat = data['Latitude']
    lng = data['Longitude']
    enterprise_name = data['Enterprise']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT ID_timber_enterprise FROM Timber_Enterprises WHERE Timber_enterpriseName = %s', (enterprise_name,))
    enterprise_id = cur.fetchone()[0]

    cur.execute(
        'UPDATE Logging_Areas SET AreaName = %s, AreaLocation = point(%s, %s), ID_timber_enterprise = %s WHERE AreaName = %s',
        (new_name, lng, lat, enterprise_id, old_name)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/delete_logging_area', methods=['POST'])
def delete_logging_area():
    name = request.json['AreaName']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM Logging_Areas WHERE AreaName = %s', (name,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True})
# Timber_Species – получение всех данных
@app.route('/get_timber_species')
def get_timber_species():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT TimberName, SpeciesName, Length, Diameter, Quality FROM Timber_Species')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

# Добавление Timber_Species
@app.route('/add_timber_species', methods=['POST'])
def add_timber_species():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO Timber_Species (TimberName, SpeciesName, Length, Diameter, Quality)
        VALUES (%s, %s, %s, %s, %s)
    ''', (data['TimberName'], data['SpeciesName'], data['Length'], data['Diameter'], data['Quality']))
    conn.commit()
    cur.close()
    conn.close()
    return '', 204

# Timber_Enterprises – получение данных
@app.route('/get_timber_enterprises')
def get_timber_enterprises():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT Timber_enterpriseName, TimberLocation[0], TimberLocation[1] FROM Timber_Enterprises')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

# Добавление Timber_Enterprises
@app.route('/add_timber_enterprise', methods=['POST'])
def add_timber_enterprise():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO Timber_Enterprises (Timber_enterpriseName, TimberLocation)
        VALUES (%s, point(%s, %s))
    ''', (data['Timber_enterpriseName'], data['lon'], data['lat']))
    conn.commit()
    cur.close()
    conn.close()
    return '', 204

# Редактирование Timber_Enterprises
@app.route('/edit_timber_enterprise', methods=['POST'])
def edit_timber_enterprise():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE Timber_Enterprises
        SET Timber_enterpriseName = %s, TimberLocation = point(%s, %s)
        WHERE Timber_enterpriseName = %s
    ''', (data['Timber_enterpriseName'], data['lon'], data['lat'], data['old_name']))
    conn.commit()
    cur.close()
    conn.close()
    return '', 204


# Детальная страница предприятия с возможностью редактирования
@app.route('/enterprise1/<int:enterprise_id>', methods=['GET', 'POST'])
def enterprise1(enterprise_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_location = request.json.get('location')
        cursor.execute("""
            UPDATE Enterprises
            SET EnterpriseLocation = %s
            WHERE ID_enterprise = %s;
        """, (str(new_location), enterprise_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Местоположение обновлено!"}), 200
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
    print("Запрос выполнен. Получено записей:", len(products))
    for product in products:
        print(product)
    # 8. Налоговые ставки
    cursor.execute("SELECT TaxName, Rate FROM Regulations")
    tax_rates = cursor.fetchall()
    taxes = {tax[0]: Decimal(tax[1]) for tax in tax_rates}  # Получение налоговых ставок

    # 7. Продукция предприятия (доставка только через "Перевозчик 2")
    # # Информация о предприятии
    # cursor.execute("""
    #     SELECT ID_enterprise, EnterpriseName, EnterpriseLocation, Other_Expenses
    #     FROM Enterprises WHERE ID_enterprise = %s;
    # """, (enterprise_id,))
    #
    # enterprise = cursor.fetchone()
    # enterprise_location = enterprise[2] if enterprise[2] else (0, 0)
    # other_expenses = Decimal(enterprise[3]) if enterprise[3] else Decimal(0)
    #
    # # Поставщики сырья
    # cursor.execute("""
    #     SELECT te.ID_timber_enterprise, te.Timber_enterpriseName, te.TimberLocation
    #     FROM Timber_Enterprises te
    #     JOIN Raw_Material_Supply rs ON te.ID_timber_enterprise = rs.ID_enterprise_resource
    #     WHERE rs.ID_enterprise = %s;
    # """, (enterprise_id,))
    # suppliers = [(s[0], s[1], eval(s[2])) for s in cursor.fetchall()]
    #
    # # Потребители продукции
    # cursor.execute("""
    #     SELECT c.ID_consumer, c.ConsumerName, c.ConsumerLocation
    #     FROM Product_Consumers c
    #     JOIN Productions p ON c.ID_consumer = p.ID_enterprise
    #     WHERE p.ID_enterprise = %s;
    # """, (enterprise_id,))
    # consumers = [(c[0], c[1], eval(c[2])) for c in cursor.fetchall()]
    #
    # # Оборудование предприятия
    # cursor.execute("""
    #     SELECT eq.EquipmentName, ee.NCount, ee.EquipmentCost, ee.Depreciation, ee.Energy, ee.Other_Resource_Sum
    #     FROM Enterprise_Equipment ee
    #     JOIN Equipments eq ON ee.ID_equipment = eq.ID_equipment
    #     WHERE ee.ID_enterprise = %s;
    # """, (enterprise_id,))
    # equipment = cursor.fetchall()
    #
    # # Трудовые ресурсы
    # cursor.execute("""
    #     SELECT lr.EmployeeName, SUM(ee.Salary), ee.Count
    #     FROM Employee_Enterprise ee
    #     JOIN Employees lr ON ee.ID_employee = lr.ID_Employee
    #     WHERE ee.ID_enterprise = %s
    #     GROUP BY lr.EmployeeName;
    # """, (enterprise_id,))
    # labor_resources = cursor.fetchall()
    #
    # # Поставки сырья (только через "Перевозчик 1")
    # cursor.execute("""
    #     SELECT ts.TimberName, ts.SpeciesName, rs.Material_Volume, rs.Material_Cost, tr.Distance, tr.Travel_Time, c.CarrierName
    #     FROM Raw_Material_Supply rs
    #     JOIN Timber_Species ts ON rs.ID_timber = ts.ID_timber
    #     JOIN Transportation_Routes tr ON rs.ID_route = tr.ID_route
    #     JOIN Carriers c ON rs.ID_carrier = c.ID_carrier
    #     WHERE rs.ID_enterprise = %s AND c.CarrierName = '1';
    # """, (enterprise_id,))
    # raw_materials = cursor.fetchall()
    #
    # # Продукция предприятия (доставка только через "Перевозчик 2")
    # cursor.execute("""
    #     SELECT p.ProductName, pr.Production_Volume, pr.ProductCost, tr.Distance, tr.Travel_Time, c.CarrierName
    #     FROM Productions pr
    #     JOIN Products p ON pr.ID_product = p.ID_product
    #     LEFT JOIN Product_Delivery pd ON pr.ID_product = pd.ID_product AND pr.ID_enterprise = pd.ID_enterprise
    #     LEFT JOIN Transportation_Routes tr ON pd.ID_route = tr.ID_route
    #     LEFT JOIN Carriers c ON pd.ID_carrier = c.ID_carrier
    #     WHERE pr.ID_enterprise = %s AND c.CarrierName = '2';
    # """, (enterprise_id,))
    # products = cursor.fetchall()

    # Получаем налоговые ставки
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
    revenue = sum([Decimal(p[1]) * Decimal(p[2]) for p in products])  # p[1]: Delivery_Volume, p[2]: Delivery_Cost
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

    # # Налоговые ставки
    # cursor.execute("SELECT Rate FROM Regulations WHERE TaxName = 'Налоговая ставка на прибыль'")
    # profit_tax_rate = Decimal(cursor.fetchone()[0])
    #
    # cursor.execute("SELECT Rate FROM Regulations WHERE TaxName = 'Налоговая ставка на имущество'")
    # property_tax_rate = Decimal(cursor.fetchone()[0])
    #
    # cursor.execute("SELECT Rate FROM Regulations WHERE TaxName = 'Единый социальный налог'")
    # social_tax_rate = Decimal(cursor.fetchone()[0])
    # # Рассчитываем показатели
    # revenue = sum([Decimal(p[1]) * Decimal(p[2]) for p in products])
    # labor_costs = sum([Decimal(lr[1]) * Decimal(lr[2]) * 12 for lr in labor_resources])
    # total_fixed_assets = sum([Decimal(eq[2]) * Decimal(eq[1]) for eq in equipment])
    # total_depreciation = sum([Decimal(eq[3]) * Decimal(eq[1]) for eq in equipment])
    #
    # def get_transport_cost(route_id, carrier_id):
    #         cursor.execute("SELECT Distance FROM Transportation_Routes WHERE ID_route = %s", (route_id,))
    #         distance = cursor.fetchone()
    #         if not distance:
    #             return Decimal(0)
    #         distance = Decimal(distance[0])
    #
    #         cursor.execute("SELECT Distance, TariffCost FROM Tariffs WHERE ID_carrier = %s ORDER BY Distance ASC",
    #                        (carrier_id,))
    #         tariffs = cursor.fetchall()
    #
    #         for tariff_distance, tariff_cost in tariffs:
    #             if distance <= Decimal(tariff_distance):
    #                 return Decimal(tariff_cost)
    #         return Decimal(tariffs[-1][1]) if tariffs else Decimal(0)
    #
    # material_expenses = sum([
    #         Decimal(rm[2]) * Decimal(rm[3]) + get_transport_cost(rm[4], rm[5]) * Decimal(rm[2])
    #         for rm in raw_materials
    #     ])
    # material_expenses += sum([
    #         Decimal(eq[1]) * (Decimal(eq[4]) + Decimal(eq[5]))
    #         for eq in equipment
    #     ])
    # material_expenses += sum([
    #         Decimal(p[1]) * get_transport_cost(p[3], p[4])
    #         for p in products
    #     ])
    #
    # production_cost = material_expenses + labor_costs + total_depreciation + other_expenses
    # working_capital = production_cost
    # realized_profit = revenue - production_cost
    # taxable_profit = realized_profit - total_fixed_assets * property_tax_rate
    #
    # property_tax = total_fixed_assets * property_tax_rate
    # profit_tax = taxable_profit * profit_tax_rate
    # social_tax = labor_costs * social_tax_rate
    # total_taxes = property_tax + profit_tax + social_tax
    #
    # profitability = (taxable_profit / (total_fixed_assets + working_capital)) * Decimal(100) if \
    #     (total_fixed_assets + working_capital) > 0 else Decimal(0)

    # Получение баланса сырья и продукции
    raw_material_balance = get_raw_material_balance(enterprise_id)
    product_balance = get_product_balance(enterprise_id)

    cursor.close()
    conn.close()

    return render_template(
        'enterprise11.html',
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
        enterprise_location=enterprise_location,
        raw_material_balance=raw_material_balance,
        product_balance=product_balance
    )


if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=5000, debug=True)
    app.run(debug=True)