// Данные о лесных ресурсах
const forestResourcesData = {
  Суоярви: [
    { location: 'Склад 1', volume: 12000, type: 'Сосна' },
    { location: 'Склад 2', volume: 18000, type: 'Ель' },
    { location: 'Склад 3', volume: 9000, type: 'Береза' },
  ],
  Петрозаводск: [
    { location: 'Склад 1', volume: 15000, type: 'Сосна' },
    { location: 'Склад 2', volume: 20000, type: 'Ель' },
    { location: 'Склад 3', volume: 12000, type: 'Береза' },
  ],
};

// Функция для получения данных о лесных ресурсах
export function getForestResources(location) {
  return forestResourcesData[location] || [];
}

// Функция для отображения данных о лесных ресурсах в таблице
export function renderForestResourcesTable(location) {
  const forestResourcesTable = document.getElementById('forest-resources-table');
  const forestResources = getForestResources(location);

  // Очистка таблицы
  forestResourcesTable.querySelector('tbody').innerHTML = '';

  // Заполнение таблицы
  forestResources.forEach(resource => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${resource.location}</td>
      <td>${resource.volume}</td>
      <td>${resource.type}</td>
    `;
    forestResourcesTable.querySelector('tbody').appendChild(row);
  });
}

// Функция для отображения данных о лесных ресурсах на карте
export function renderForestResourcesMap(location) {
  const forestResources = getForestResources(location);
  let lat, lng, zoom;

  if (location === 'Суоярви') {
    lat = 61.75;
    lng = 30.15;
    zoom = 10;
  } else if (location === 'Петрозаводск') {
    lat = 61.78;
    lng = 34.35;
    zoom = 10;
  } else {
    return;
  }

  const map = L.map('map').setView([lat, lng], zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  forestResources.forEach(resource => {
    L.marker([lat, lng]).addTo(map)
      .bindPopup(`Местоположение: ${resource.location}<br>Запас: ${resource.volume} м³<br>Порода: ${resource.type}`);
  });
}
