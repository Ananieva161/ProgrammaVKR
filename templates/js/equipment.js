// Получение данных об оборудовании
function getEquipment() {

  // Здесь можно реализовать логику получения данных из локального хранилища или API
  const equipment = [
    { name: 'Лесопильный станок', productivity: 1000, resourceIntensity: 0.5 },
    { name: 'Сушильная камера', productivity: 500, resourceIntensity: 0.3 },
    { name: 'Фрезерный станок', productivity: 800, resourceIntensity: 0.4 },
  ];
  return equipment;
}

// Отображение данных на странице
function renderEquipment() {
  const equipmentTable = document.getElementById('equipment-table');
  const equipment = getEquipment();

  equipment.forEach(item => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${item.name}</td>
      <td>${item.productivity} шт/ч</td>
      <td>${item.resourceIntensity}</td>
    `;
    equipmentTable.querySelector('tbody').appendChild(row);
  });
}

renderEquipment();
