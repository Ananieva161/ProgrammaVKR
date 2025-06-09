// Получение данных о продукции
function getProducts() {
  return [
    { name: 'Пиломатериалы', price: 5500, coordinates: [62.0917, 32.3489] },
    { name: 'Фанера', price: 16000, coordinates: [62.0917, 32.3489] },
    { name: 'Щепа', price: 1200, coordinates: [62.0917, 32.3489] },
  ];
}

// Отображение данных на странице
function renderProducts() {
  const productsTable = document.getElementById('products-table');
  const productsMap = document.getElementById('products-map');
  const products = getProducts();

  // Очистить таблицу
  productsTable.querySelector('tbody').innerHTML = '';

  // Отобразить данные в таблице
  products.forEach(product => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${product.name}</td>
      <td>${product.price} руб.</td>
    `;
    productsTable.querySelector('tbody').appendChild(row);
  });

  // Отобразить данные на карте
  const map = new google.maps.Map(productsMap, {
    zoom: 8,
    center: { lat: 62.0, lng: 34.0 },
    mapTypeId: 'terrain',
  });

  // Отобразить маршруты перевозок
  const directionsService = new google.maps.DirectionsService();
  const directionsRenderer = new google.maps.DirectionsRenderer();
  directionsRenderer.setMap(map);

  const waypoints = [
    { location: 'Петрозаводск', stopover: true },
    { location: 'Суоярви', stopover: true },
    { location: 'Кондопога', stopover: true },
  ];

  directionsService.route({
    origin: 'Петрозаводск',
    destination: 'Кондопога',
    waypoints: waypoints,
    optimizeWaypoints: true,
    travelMode: google.maps.TravelMode.DRIVING,
  }, (response, status) => {
    if (status === 'OK') {
      directionsRenderer.setDirections(response);
    } else {
      console.error('Directions request failed due to ' + status);
    }
  });
}
