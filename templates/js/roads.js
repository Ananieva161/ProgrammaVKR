// Получение данных о дорогах
function getRoads() {
  // Здесь можно реализовать логику получения данных из локального хранилища или API
  const roads = [
    { section: 'Участок 1', capacity: 1000, maxSpeed: 80 },
    { section: 'Участок 2', capacity: 800, maxSpeed: 60 },
    { section: 'Участок 3', capacity: 1200, maxSpeed: 90 },
  ];
  return roads;
}

// Отображение данных на странице
function renderRoads() {
  const roadsTable = document.getElementById('roads-table');
  const roads = getRoads();

  roads.forEach(road => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${road.section}</td>
      <td>${road.capacity} авт/ч</td>
      <td>${road.maxSpeed} км/ч</td>
    `;
    roadsTable.querySelector('tbody').appendChild(row);
  });
}

renderRoads();
