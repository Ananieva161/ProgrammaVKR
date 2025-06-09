$(document).ready(function() {
    const $dictionarySelect = $('#dictionary-select');
    const $dictionaryTable = $('#dictionary-table');
    const $modalForm = $('#modal-form');
    const $modal = $('#modal');
    let map, markers = [];

    // Загрузка списка справочников с сервера
    $.ajax({
        url: '/get_dictionary_tables',
        method: 'GET',
        success: function(data) {
            data.forEach(function(table) {
                $dictionarySelect.append(`<option value="${table.name}">${table.comment}</option>`);
            });
        },
        error: function(xhr, status, error) {
            console.error('Error fetching dictionary tables:', error);
        }
    });

    // Обработка выбора справочника
    $dictionarySelect.on('change', function() {
        const selectedTable = $(this).val();
        if (selectedTable) {
            loadDictionaryData(selectedTable);
        } else {
            clearDictionaryTable();
            clearMap();
        }
    });

    // Функция для загрузки данных из выбранного справочника
    function loadDictionaryData(tableName) {
        $.ajax({
            url: '/get_dictionary_data',
            method: 'POST',
            data: JSON.stringify({ table_name: tableName }),
            contentType: 'application/json',
            success: function(data) {
                populateDictionaryTable(data);
                initializeMap(data, tableName);
            },
            error: function(xhr, status, error) {
                console.error('Error fetching dictionary data:', error);
            }
        });
    }

    // Функция для заполнения таблицы данными из справочника
    function populateDictionaryTable(data) {
        $dictionaryTable.find('thead tr').empty();
        $dictionaryTable.find('tbody').empty();

        // Создание заголовка таблицы
        const columnNames = Object.keys(data[0] || {});
        columnNames.forEach(function(name) {
            $dictionaryTable.find('thead tr').append(`<th>${name}</th>`);
        });

        // Заполнение таблицы данными
        data.forEach(function(row) {
            const $tr = $('<tr>');
            columnNames.forEach(function(name) {
                $tr.append(`<td>${row[name] || ''}</td>`);
            });
            $dictionaryTable.find('tbody').append($tr);
        });
    }

    // Обработка кнопок "Добавить", "Изменить" и "Удалить"
    $('#add-button').on('click', function() {
        showModal('Добавить запись', {});
    });

    $('#edit-button').on('click', function() {
        const selectedRow = getSelectedRow();
        if (selectedRow) {
            showModal('Изменить запись', selectedRow);
        } else {
            alert('Выберите запись для изменения.');
        }
    });

    $('#delete-button').on('click', function() {
        const selectedRow = getSelectedRow();
        if (selectedRow) {
            if (confirm('Вы действительно хотите удалить эту запись?')) {
                deleteRecord(selectedRow.id, $dictionarySelect.val());
            }
        } else {
            alert('Выберите запись для удаления.');
        }
    });

    // Функция для получения выбранной строки в таблице
    function getSelectedRow() {
        const $selectedRow = $dictionaryTable.find('tbody tr.table-active');
        if ($selectedRow.length) {
            const rowData = {};
            $selectedRow.find('td').each(function(index) {
                rowData[$dictionaryTable.find('thead th').eq(index).text()] = $(this).text();
            });

            return rowData;
        }
        return null;
    }

    // Функция для отображения модального окна
    function showModal(title, data) {
        $modal.find('#modal-title').text(title);
        $modalForm[0].reset();
        $('#modal-fields').empty();

        // Заполнение полей формы данными
        Object.keys(data).forEach(function(key) {
            $modalForm.append(`<div class="form-group">
                <label for="${key}">${key}:</label>
                <input type="text" class="form-control" id="${key}" name="${key}" value="${data[key] || ''}">
            </div>`);
        });

        $modal.modal('show');
    }

    // Функция для удаления записи
    function deleteRecord(id, tableName) {
        $.ajax({
            url: '/delete_dictionary_data',
            method: 'POST',
            data: JSON.stringify({ table_name: tableName, id: id }),
            contentType: 'application/json',
            success: function(data) {
                console.log(data.message);
                loadDictionaryData(tableName);
            },
            error: function(xhr, status, error) {
                console.error('Error deleting record:', error);
            }
        });
    }

    // Функция для инициализации карты
    function initializeMap(data, tableName) {
        clearMap();

        map = L.map('map').setView([62.2, 30.45], 8); // Центр карты в Карелии
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
        }).addTo(map);

        switch (tableName) {
            case 'Forest_Resources':
                data.forEach(function(row) {
                    addMarker([row.latitude, row.longitude], `Запас древесины: ${row.wood_reserve}`);
                });
                break;
            case 'Enterprises':
                data.forEach(function(row) {
                    addMarker([row.latitude, row.longitude], `Предприятие: ${row.name}\nПродукция: ${row.products}\nСтоимость: ${row.cost}`);
                });
                break;
            case 'Products':
                data.forEach(function(row) {
                    addMarker([row.latitude, row.longitude], `Наименование: ${row.name}\nЦена: ${row.price}`);
                });
                break;
            case 'Transportation_Vehicles':
                data.forEach(function(row) {
                    addMarker([row.latitude, row.longitude], `Тип ТС: ${row.type}\nМарка: ${row.brand}\nГрузоподъемность: ${row.capacity}\nМакс. скорость: ${row.max_speed}\nСтоимость транспортировки: ${row.transportation_cost}\nНорма расхода ГСМ: ${row.fuel_consumption}\nАмортизационные отчисления: ${row.depreciation}\nСтоимость ТС: ${row.cost}`);
                });
                break;
            case 'Equipment':
                data.forEach(function(row) {
                    addMarker([row.latitude, row.longitude], `Наименование: ${row.name}\nПроизводительность: ${row.productivity}\nНорма расхода ГСМ: ${row.fuel_consumption}\nАмортизационные отчисления: ${row.depreciation}\nСтоимость оборудования: ${row.cost}\nМощность: ${row.power}\nНорма расхода электроэнергии: ${row.electricity_consumption}`);
                });
                break;
            case 'Labor_Resources':
                data.forEach(function(row) {
                    addMarker([row.latitude, row.longitude], `Специальность: ${row.profession}\nТарифная ставка: ${row.rate}`);
                });
                break;
            case 'Roads':
                data.forEach(function(row) {

                    addMarker([row.latitude, row.longitude], `Пропускная способность: ${row.capacity}\nСредняя скорость: ${row.avg_speed}\nИнтенсивность движения: ${row.traffic_intensity}`);
                });
                break;
            case 'Consumers':
                data.forEach(function(row) {
                    addMarker([row.latitude, row.longitude], `Наименование: ${row.name}\nОбъем и цена по видам: ${row.products}`);
                });
                break;
            case 'Regulations':
                data.forEach(function(row) {
                    addMarker([row.latitude, row.longitude], `Ставка налога на прибыль: ${row.profit_tax}\nСтавка налога на имущество: ${row.property_tax}\nЕдиный социальный налог: ${row.social_tax}`);
                });
                break;
            case 'Energy_Resources':
                data.forEach(function(row) {
                    addMarker([row.latitude, row.longitude], `Вид: ${row.type}\nСтоимость: ${row.cost}\nЕдиницы потребления: ${row.units}`);
                });
                break;
            case 'Financial_Resources':
                data.forEach(function(row) {
                    addMarker([row.latitude, row.longitude], `Наименование: ${row.name}\nОбъем: ${row.volume}`);
                });
                break;
        }
    }

    function addMarker(latLng, content) {
        const marker = L.marker(latLng).addTo(map);
        marker.bindPopup(content);
        markers.push(marker);
    }

    function clearMap() {
        if (map) {
            markers.forEach(function(marker) {
                map.removeLayer(marker);
            });
            markers = [];
        }
    }
});

