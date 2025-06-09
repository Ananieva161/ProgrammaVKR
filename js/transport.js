// Получение данных о транспортных средствах
function getTransport() {
  // Здесь можно реализовать логику получения данных из локального хранилища или API
  const transport = [
    { type: 'Грузовик', brand: 'Volvo', capacity: 20000, maxSpeed: 80, cost: 50, volume: 50 },
    { type: 'Фура', brand: 'Scania', capacity: 40000, maxSpeed: 90, cost: 80, volume: 100 },
    { type: 'Манипулятор', brand: 'Камаз', capacity: 10000, maxSpeed: 60, cost: 30, volume: 30 },
  ];
  return transport;
}

// Отображение данных на странице
function renderTransport() {
  const transportTable = document.getElementById('transport-table');
  const transport = getTransport();

  transport.forEach(item => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${item.type}</td>
      <td>${item.brand}</td>
      <td>${item.capacity} кг</td>
      <td>${item.maxSpeed} км/ч</td>
      <td>${item.cost} руб./км</td>
      <td>${item.volume} м³</td>
    `;
    transportTable.querySelector('tbody').appendChild(row);
  });
}

renderTransport();
