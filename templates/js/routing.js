// Получение данных о маршрутах
function getRoutes() {
  const routes = [
    {
      name: 'Маршрут Петрозаводск - Суоярви',
      roads: ['Участок 1', 'Участок 2'],
      travelTime: '4.5 ч',
      cost: 2000,
      startCoords: [61.7851, 34.3397],
      endCoords: [62.0914, 32.3528],
    },
    {
      name: 'Маршрут Петрозаводск - Кондопога',
      roads: ['Участок 3', 'Участок 4'],
      travelTime: '1 ч',
      cost: 1500,
      startCoords: [61.7851, 34.3397],
      endCoords: [62.2061, 34.2689],
    },
    {
      name: 'Маршрут Суоярви - Кондопога',
      roads: ['Участок 2', 'Участок 4'],
      travelTime: '3.2 ч',
      cost: 1800,
      startCoords: [62.0914, 32.3528],
      endCoords: [62.2061, 34.2689],
    },
  ];
  return routes;
}
// Получение названий городов
function getCityNames(coords) {
  const cities = {
    [JSON.stringify([61.7851, 34.3397])]: 'Петрозаводск',
    [JSON.stringify([62.0914, 32.3528])]: 'Суоярви',
    [JSON.stringify([62.2061, 34.2689])]: 'Кондопога',
  };
  return cities[JSON.stringify(coords)] || 'Новый город';
}

// Отображение данных на странице
function renderRoutes() {
  const routingTable = document.getElementById('routing-table');
  const routes = getRoutes();

  // Сортируем маршруты по стоимости
  routes.sort((a, b) => a.cost - b.cost);

  routes.forEach(route => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${route.name}</td>
      <td>${route.roads.join(', ')}</td>
      <td>${route.travelTime}</td>
      <td>${route.cost} руб.</td>
    `;
    routingTable.querySelector('tbody').appendChild(row);
  });

  // Инициализация карты и отображение маршрутов
  initMap(routes);
}

function initMap(routes) {
  const map = L.map('map').setView([61.7851, 34.3397], 8);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  let markers = [];
  let polylines = [];
  let newRoutes = [];

  // Отображаем маршруты в порядке возрастания стоимости
  routes.forEach(route => {
    const polyline = L.polyline([route.startCoords, route.endCoords], { color: 'red' }).addTo(map);
    polyline.bindPopup(`Маршрут: ${route.name}<br>Время в пути: ${route.travelTime}<br>Стоимость: ${route.cost} руб.`);
    polylines.push(polyline);

    const startMarker = L.marker(route.startCoords, { title: getCityNames(route.startCoords) }).addTo(map);
    startMarker.on('click', () => {
      map.removeLayer(startMarker);
      markers = markers.filter(m => m !== startMarker);
      polylines = polylines.filter(p => p !== polyline);
      map.removeLayer(polyline);
      updateRoutingTable([...routes, ...newRoutes]);
    });

    const endMarker = L.marker(route.endCoords, { title: getCityNames(route.endCoords) }).addTo(map);
    endMarker.on('click', () => {
      map.removeLayer(endMarker);
      markers = markers.filter(m => m !== endMarker);
      polylines = polylines.filter(p => p !== polyline);
      map.removeLayer(polyline);
      updateRoutingTable([...routes, ...newRoutes]);
    });

    markers.push(startMarker);
    markers.push(endMarker);
  });

  map.on('click', (event) => {
    const marker = L.marker(event.latlng, { title: getCityNames(event.latlng) }).addTo(map);
    marker.on('click', () => {
      map.removeLayer(marker);
      markers = markers.filter(m => m !== marker);
      
      const polyline = polylines.find(p => p.getLatLngs()[1].equals(marker.getLatLng()));
      if (polyline) {
        map.removeLayer(polyline);
        polylines = polylines.filter(p => p !== polyline);
      }
      updateRoutingTable([...routes, ...newRoutes]);
    });
    markers.push(marker);

    const polyline = L.polyline([markers[0].getLatLng(), marker.getLatLng()], { color: 'blue' }).addTo(map);
    polylines.push(polyline);

    const newRoute = {
      name: `Маршрут ${getCityNames(markers[0].getLatLng())} - ${getCityNames(marker.getLatLng())}`,
      roads: ['Новый участок'],
      travelTime: ((map.distance(markers[0].getLatLng(), marker.getLatLng()) / 60).toFixed(1) + ' ч'),
      cost: ((map.distance(markers[0].getLatLng(), marker.getLatLng()) / 1000 * 50).toFixed(0) + ' руб.'),
      startCoords: markers[0].getLatLng(),
      endCoords: marker.getLatLng(),
    };
    newRoutes.push(newRoute);
    updateRoutingTable([...routes, ...newRoutes]);
  });
}

function updateRoutingTable(routes) {
  const routingTable = document.getElementById('routing-table');
  routingTable.querySelector('tbody').innerHTML = '';

  // Сортируем маршруты по стоимости
  routes.sort((a, b) => a.cost - b.cost);

  routes.forEach(route => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${route.name}</td>
      <td>${route.roads.join(', ')}</td>
      <td>${route.travelTime}</td>
      <td>${route.cost} руб.</td>
    `;
    routingTable.querySelector('tbody').appendChild(row);
  });
}

renderRoutes();
