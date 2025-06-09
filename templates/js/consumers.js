// Получение данных о потребителях
function getConsumers() {
  // Здесь можно реализовать логику получения данных из локального хранилища или API
  const consumers = [
    { name: 'Компания A', volume: 5000, price: 10000 },
    { name: 'Компания B', volume: 7000, price: 12000 },
    { name: 'Компания C', volume: 3000, price: 8000 },
  ];
  return consumers;
}

// Отображение данных на странице
function renderConsumers() {
  const consumersTable = document.getElementById('consumers-table');
  const consumers = getConsumers();

  consumers.forEach(consumer => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${consumer.name}</td>
      <td>${consumer.volume} м³</td>
      <td>${consumer.price} руб.</td>
    `;
    consumersTable.querySelector('tbody').appendChild(row);
  });
}

renderConsumers();
