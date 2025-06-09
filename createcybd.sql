-- Создание таблицы Logging_Areas
CREATE TABLE Logging_Areas (
    ID_logging SERIAL PRIMARY KEY,                           -- Уникальный идентификатор участка
    AreaLocation POINT NOT NULL,                              -- Координаты участка (x - долгота, y - широта)
    AreaName VARCHAR(255),                                    -- Наименование участка
    ID_timber_enterprise INT NOT NULL,                        -- ID лесозаготовителя
    FOREIGN KEY (ID_timber_enterprise) REFERENCES Timber_Enterprises(ID_timber_enterprise)
);

-- Создание таблицы Timber_Species
CREATE TABLE Timber_Species (
    ID_timber SERIAL PRIMARY KEY,                            -- Уникальный идентификатор лесоматериалов
    TimberName VARCHAR(255) NOT NULL,                         -- Название сортимента
    SpeciesName VARCHAR(255) NOT NULL,                        -- Название породы
    Length DECIMAL,                                          -- Длина сортимента
    Diameter DECIMAL,                                        -- Диаметр сортимента
    Quality INT                                              -- Бонитет
);

-- Создание таблицы Timber_Enterprises
CREATE TABLE Timber_Enterprises (
    ID_timber_enterprise SERIAL PRIMARY KEY,                  -- Уникальный идентификатор лесозаготовителя
    TimberLocation POINT,                                     -- Координаты лесозаготовителя
    Timber_enterpriseName VARCHAR(255) NOT NULL               -- Наименование лесозаготовителя
);

-- Создание таблицы Products
CREATE TABLE Products (
    ID_product SERIAL PRIMARY KEY,                           -- Уникальный идентификатор продукции
    ProductName VARCHAR(255) NOT NULL,                        -- Наименование продукции
    Unit VARCHAR(50)                                          -- Единица измерения продукции
);

-- Создание таблицы Equipments
CREATE TABLE Equipments (
    ID_equipment SERIAL PRIMARY KEY,                         -- Уникальный идентификатор оборудования
    EquipmentName VARCHAR(255) NOT NULL,                      -- Наименование оборудования
    EquipmentCost DECIMAL                                     -- Стоимость оборудования
);

-- Создание таблицы Employees
CREATE TABLE Employees (
    ID_Employee SERIAL PRIMARY KEY,                          -- Уникальный идентификатор специалиста
    EmployeeName VARCHAR(255) NOT NULL,                       -- Наименование должности/специальности
    Tariff_Rate DECIMAL                                       -- Начисленная месячная з/п
);

-- Создание таблицы Roads
CREATE TABLE Roads (
    ID_road SERIAL PRIMARY KEY,                              -- Уникальный идентификатор отрезка дороги
    RoadStart POINT NOT NULL,                                -- Начальная точка дороги (x - долгота, y - широта)
    RoadEnd POINT NOT NULL,                                  -- Конечная точка дороги (x - долгота, y - широта)
    RoadLength DECIMAL,                                      -- Длина дороги
    RoadCapacity DECIMAL,                                    -- Пропускная способность
    Max_Speed DECIMAL                                        -- Максимальная скорость
);

-- Создание таблицы Product_Consumers
CREATE TABLE Product_Consumers (
    ID_consumer SERIAL PRIMARY KEY,                          -- Уникальный идентификатор потребителя
    ConsumerName VARCHAR(255) NOT NULL,                       -- Наименование потребителя
    ConsumerLocation POINT NOT NULL                          -- Координаты потребителя (x - долгота, y - широта)
);

-- Создание таблицы Regulations
CREATE TABLE Regulations (
    ID_regulation SERIAL PRIMARY KEY,                        -- Уникальный идентификатор
    TaxName VARCHAR(255) NOT NULL,                            -- Наименование налога
    Rate DECIMAL                                             -- Ставка налога
);

-- Создание таблицы Enterprises
CREATE TABLE Enterprises (
    ID_enterprise SERIAL PRIMARY KEY,                        -- Уникальный идентификатор предприятия
    EnterpriseName VARCHAR(255) NOT NULL,                     -- Наименование предприятия
    EnterpriseLocation POINT NOT NULL,                        -- Координаты предприятия (x - долгота, y - широта)
    Other_Expenses DECIMAL                                    -- Прочие расходы
);

-- Создание таблицы Raw_Material_Needs
CREATE TABLE Raw_Material_Needs (
    ID_need SERIAL PRIMARY KEY,                              -- Уникальный идентификатор потребности
    ID_enterprise INT NOT NULL,                              -- Предприятие
    ID_product INT,                                          -- Продукция
    ID_timber INT,                                           -- Сортимент
    Raw_Material_Volume DECIMAL,                             -- Объем необходимого сырья
    FOREIGN KEY (ID_enterprise) REFERENCES Enterprises(ID_enterprise),
    FOREIGN KEY (ID_product) REFERENCES Products(ID_product),
    FOREIGN KEY (ID_timber) REFERENCES Timber_Species(ID_timber)
);

-- Создание таблицы Productions
CREATE TABLE Productions (
    ID_production SERIAL PRIMARY KEY,                        -- Уникальный идентификатор производства
    ID_enterprise INT NOT NULL,                              -- Предприятие
    ID_product INT NOT NULL,                                 -- Продукция
    Production_Volume DECIMAL,                               -- Объем производства
    ProductCost DECIMAL,                                     -- Стоимость продукции
    FOREIGN KEY (ID_enterprise) REFERENCES Enterprises(ID_enterprise),
    FOREIGN KEY (ID_product) REFERENCES Products(ID_product)
);

-- Создание таблицы Raw_Material_Supply
CREATE TABLE Raw_Material_Supply (
    ID_supply SERIAL PRIMARY KEY,                            -- Уникальный идентификатор поставки
    ID_enterprise INT NOT NULL,                              -- Предприятие получатель
    ID_timber INT,                                           -- Сортимент
    ID_logging INT,                                          -- Лесной участок
    ID_product INT,                                          -- Продукция
    ID_enterprise_resource INT,                              -- Поставщик
    ID_route INT NOT NULL,                                   -- Маршрут поставки
    ID_carrier INT,                                          -- Транспортная компания
    Material_Volume DECIMAL,                                 -- Объем поставки
    Material_Cost DECIMAL,                                   -- Стоимость сырья
    FOREIGN KEY (ID_enterprise) REFERENCES Enterprises(ID_enterprise),
    FOREIGN KEY (ID_timber) REFERENCES Timber_Species(ID_timber),
    FOREIGN KEY (ID_logging) REFERENCES Logging_Areas(ID_logging),
    FOREIGN KEY (ID_product) REFERENCES Products(ID_product),
    FOREIGN KEY (ID_enterprise_resource) REFERENCES Enterprises(ID_enterprise),
    FOREIGN KEY (ID_route) REFERENCES Transportation_Routes(ID_route),
    FOREIGN KEY (ID_carrier) REFERENCES Carriers(ID_carrier)
);

-- Создание таблицы Product_Delivery
CREATE TABLE Product_Delivery (
    ID_delivery SERIAL PRIMARY KEY,                          -- Уникальный идентификатор поставки продукции
    ID_enterprise INT NOT NULL,                              -- Предприятие производитель
    ID_product INT NOT NULL,                                 -- Продукция
    ID_consumer INT NOT NULL,                                -- Потребитель
    ID_route INT NOT NULL,                                   -- Маршрут
    ID_carrier INT NOT NULL,                                 -- Транспортная компания
    Delivery_Volume DECIMAL,                                 -- Объем поставки
    Delivery_Cost DECIMAL,                                   -- Стоимость поставки
    FOREIGN KEY (ID_enterprise) REFERENCES Enterprises(ID_enterprise),
    FOREIGN KEY (ID_product) REFERENCES Products(ID_product),
    FOREIGN KEY (ID_consumer) REFERENCES Product_Consumers(ID_consumer),
    FOREIGN KEY (ID_route) REFERENCES Transportation_Routes(ID_route),
    FOREIGN KEY (ID_carrier) REFERENCES Carriers(ID_carrier)
);

-- Создание таблицы Transportation_Routes
CREATE TABLE Transportation_Routes (
    ID_route SERIAL PRIMARY KEY,                            -- Уникальный идентификатор маршрута
    Distance DECIMAL,                                       -- Дистанция
    Travel_Time DECIMAL                                     -- Время в пути
);

-- Создание таблицы Employee_Enterprise
CREATE TABLE Employee_Enterprise (
    ID_Employee_Enterprise SERIAL PRIMARY KEY,               -- Уникальный идентификатор
    ID_enterprise INT NOT NULL,                              -- Предприятие
    ID_employee INT NOT NULL,                                -- Должность
    NCount INT NOT NULL,                                     -- Количество сотрудников
    Salary DECIMAL                                           -- Заработная плата
);

-- Создание таблицы Enterprise_Equipment
CREATE TABLE Enterprise_Equipment (
    ID_Equipment_Enterprise SERIAL PRIMARY KEY,              -- Уникальный идентификатор
    ID_enterprise INT NOT NULL,                              -- Предприятие
    ID_equipment INT NOT NULL,                               -- Оборудование
    NCount INT NOT NULL,                                     -- Количество оборудования
    Depreciation DECIMAL,                                    -- Амортизация
    Energy DECIMAL,                                          -- Затраты на электроэнергию
    Other_Resource_Sum DECIMAL,                              -- Прочие расходы на ресурсы
    EquipmentCost DECIMAL,                                   -- Стоимость оборудования
    FOREIGN KEY (ID_enterprise) REFERENCES Enterprises(ID_enterprise),
    FOREIGN KEY (ID_equipment) REFERENCES Equipments(ID_equipment)
);

-- Создание таблицы Route_Roads
CREATE TABLE Route_Roads (
    ID_route_road SERIAL PRIMARY KEY,                        -- Уникальный идентификатор
    ID_route INT NOT NULL,                                   -- Маршрут
    ID_road INT NOT NULL,                                    -- Дорога
    Road_Order INT NOT NULL,                                 -- Порядок дороги в маршруте
    FOREIGN KEY (ID_route) REFERENCES Transportation_Routes(ID_route),
    FOREIGN KEY (ID_road) REFERENCES Roads(ID_road)
);

-- Создание таблицы Carriers
CREATE TABLE Carriers (
    ID_carrier SERIAL PRIMARY KEY,                           -- Уникальный идентификатор перевозчика
    CarrierName VARCHAR(255)                                  -- Наименование перевозчика
);

-- Создание таблицы Tariffs
CREATE TABLE Tariffs (
    ID_tariff SERIAL PRIMARY KEY,                            -- Уникальный идентификатор тарифа
    ID_carrier INT NOT NULL,                                  -- Перевозчик
    Distance DECIMAL,                                         -- Дистанция
    Unit VARCHAR(50),                                         -- Единица измерения
    TariffCost DECIMAL                                        -- Стоимость тарифа
);
