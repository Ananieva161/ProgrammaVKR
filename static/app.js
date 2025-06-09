//$('#submit-btn').click(function() {
//    var enterpriseName = $('#enterprise_name').val();
//
//    $.ajax({
//        url: '/add_enterprise',
//        type: 'POST',
//        data: JSON.stringify({ 'enterprise_name': enterpriseName }),
//        contentType: 'application/json; charset=utf-8',
//        dataType: 'json',
//        success: function(response) {
//            alert('Предприятие успешно добавлено!');
//        },
//        error: function(xhr, status, error) {
//            alert('Ошибка при добавлении предприятия: ' + error);
//        }
//    });
//});
/// Функция для открытия модального окна редактирования
function openEditModal(table, id) {
    // Отправляем запрос на сервер, чтобы получить данные по указанному ID и таблице
    $.ajax({
        type: 'GET',
        url: '/get_data/' + table + '/' + id,
        success: function(data) {
            // Заполняем заголовок модального окна
            $('#edit-modal-title').text('Редактирование ' + table);
            // Сохраняем название таблицы и ID записи в форме редактирования
            $('#edit-modal-form').attr('data-table', table);
            $('#edit-modal-form').attr('data-id', id);

            // Заполняем поля формы редактирования данными, полученными с сервера
            switch (table) {
                case 'Product_Consumers_Enterprise':
                    $('#purchased-volume').val(data.purchased_volume);
                    $('#purchased-price').val(data.purchased_price);
                    break;
                case 'Enterprise':
                    $('#enterprise-name').val(data.name);
                    $('#enterprise-location').val(data.location);
                    break;
                case 'Products':
                    $('#product-name').val(data.name);
                    break;
                case 'Equipment':
                    $('#equipment-name').val(data.name);
                    $('#equipment-productivity').val(data.productivity);
                    $('#equipment-fuel-consumption').val(data.fuel_consumption);
                    $('#equipment-electricity-consumption').val(data.electricity_consumption);
                    $('#equipment-depreciation').val(data.depreciation);
                    $('#equipment-cost').val(data.cost);
                    break;
                case 'Labor_Resources':
                    $('#labor-specialty').val(data.specialty);
                    $('#labor-tariff-rate').val(data.tariff_rate);
                    break;
                case 'Supplier_Enterprises':
                    $('#supplier-name').val(data.name);
                    break;
                case 'Wood_Species':
                    $('#species-name').val(data.name);
                    break;
                case 'Energy_Resources':
                    $('#energy-type').val(data.type);
                    break;
                case 'Product_Consumers':
                    $('#consumer-name').val(data.name);
                    break;
            }

            // Показываем модальное окно
            $('#edit-modal').modal('show');
        }
    });
}

// Функция для сохранения отредактированных данных
function saveEditedData() {
    const table = $('#edit-modal-form').attr('data-table');
    const id = $('#edit-modal-form').attr('data-id');

    // Собираем обновленные данные из формы редактирования
    let updatedData;
    switch (table) {
        case 'Product_Consumers_Enterprise':
            updatedData = $('#purchased-volume').val() + ',' + $('#purchased-price').val();
            break;
        case 'Enterprise':
            updatedData = $('#enterprise-name').val() + ',' + $('#enterprise-location').val();
            break;
        case 'Products':
            updatedData = $('#product-name').val();
            break;
        case 'Equipment':
            updatedData = $('#equipment-name').val() + ',' + $('#equipment-productivity').val() + ',' + $('#equipment-fuel-consumption').val() + ',' + $('#equipment-electricity-consumption').val() + ',' + $('#equipment-depreciation').val() + ',' + $('#equipment-cost').val();
            break;

        case 'Labor_Resources':
            updatedData = $('#labor-specialty').val() + ',' + $('#labor-tariff-rate').val();
            break;
        case 'Supplier_Enterprises':
            updatedData = $('#supplier-name').val();
            break;
        case 'Wood_Species':
            updatedData = $('#species-name').val();
            break;
        case 'Energy_Resources':
            updatedData = $('#energy-type').val();
            break;
        case 'Product_Consumers':
            updatedData = $('#consumer-name').val();
            break;
    }

    // Отправляем запрос на сервер для обновления данных
    $.ajax({
        type: 'POST',
        url: '/update_data',
        data: {
            table_name: table,
            row_id: id,
            updated_data: updatedData
        },
        success: function(response) {
            if (response.success) {
                // Обновляем соответствующую строку в таблице
                updateTableRow(table, id, updatedData);
                // Скрываем модальное окно
                $('#edit-modal').modal('hide');
            } else {
                alert('Ошибка при обновлении данных.');
            }
        }
    });
}

// Функция для открытия модального окна удаления
function openDeleteModal(table, id) {
    // Заполняем заголовок модального окна
    $('#delete-modal-title').text('Удаление ' + table);
    // Сохраняем название таблицы и ID записи в форме удаления
    $('#delete-modal-form').attr('data-table', table);
    $('#delete-modal-form').attr('data-id', id);
    // Показываем модальное окно
    $('#delete-modal').modal('show');
}

// Функция для удаления данных
function deleteData() {
    const table = $('#delete-modal-form').attr('data-table');
    const id = $('#delete-modal-form').attr('data-id');

    // Отправляем запрос на сервер для удаления данных
    $.ajax({
        type: 'POST',
        url: '/delete_data',
        data: {
            table_name: table,
            row_id: id
        },
        success: function(response) {
            if (response.success) {
                // Удаляем соответствующую строку из таблицы
                $('tr[data-table="' + table + '"][data-id="' + id + '"]').remove();
                // Скрываем модальное окно
                $('#delete-modal').modal('hide');
            } else {
                alert('Ошибка при удалении данных.');
            }
        }
    });
}

// Функция для обновления строки в таблице
function updateTableRow(table, id, updatedData) {
    // Находим соответствующую строку в таблице
    const row = $('tr[data-table="' + table + '"][data-id="' + id + '"]');

    // Обновляем значения ячеек строки в соответствии с новыми данными
    switch (table) {
        case 'Product_Consumers_Enterprise':
            const [newPurchasedVolume, newPurchasedPrice] = updatedData.split(',');
            row.find('td:eq(1)').text(newPurchasedVolume);
            row.find('td:eq(2)').text(newPurchasedPrice);
            break;
        case 'Enterprise':
            const [newEnterpriseName, newEnterpriseLocation] = updatedData.split(',');
            row.find('td:eq(0)').text(newEnterpriseName);
            row.find('td:eq(1)').text(newEnterpriseLocation);
            break;
        case 'Products':
            row.find('td:eq(0)').text(updatedData);
            break;
        case 'Equipment':
            const [newEquipmentName, newEquipmentProductivity, newEquipmentFuelConsumption, newEquipmentElectricityConsumption, newEquipmentDepreciation, newEquipmentCost] = updatedData.split(',');
            row.find('td:eq(0)').text(newEquipmentName);
            row.find('td:eq(1)').text(newEquipmentProductivity);

            row.find('td:eq(2)').text(newEquipmentFuelConsumption);
            row.find('td:eq(3)').text(newEquipmentElectricityConsumption);
            row.find('td:eq(4)').text(newEquipmentDepreciation);
            row.find('td:eq(5)').text(newEquipmentCost);
            break;
        case 'Labor_Resources':
            const [newLaborSpecialty, newLaborTariffRate] = updatedData.split(',');
            row.find('td:eq(0)').text(newLaborSpecialty);
            row.find('td:eq(1)').text(newLaborTariffRate);
            break;
        case 'Supplier_Enterprises':
            row.find('td:eq(0)').text(updatedData);
            break;
        case 'Wood_Species':
            row.find('td:eq(0)').text(updatedData);
            break;
        case 'Energy_Resources':
            row.find('td:eq(0)').text(updatedData);
            break;
        case 'Product_Consumers':
            row.find('td:eq(0)').text(updatedData);
            break;
    }
}
