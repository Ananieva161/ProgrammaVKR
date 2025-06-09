// Инициализация карты
var map = L.map('map').setView([62.5, 34.5], 8);

// Добавление слоя OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Группа для маркеров
var markers = L.featureGroup().addTo(map);

// Переменная для хранения объекта маршрута
var routingControl;

// Обработчик клика на карте для установки маркеров
map.on('click', function (e) {
    var marker = L.marker(e.latlng).addTo(markers);
    marker.bindPopup('Координаты: ' + e.latlng.lat.toFixed(5) + ', ' + e.latlng.lng.toFixed(5));

    updateRoute();
});

// Функция для обновления маршрута
function updateRoute() {
    // Получение массива координат маркеров
    var markerCoords = markers.getLayers().map(function (marker) {
        return marker.getLatLng();
    });

    // Очистка предыдущего маршрута
    if (routingControl) {
        map.removeControl(routingControl);
    }

    // Построение нового маршрута с помощью Leaflet Routing Machine
    routingControl = L.Routing.control({
        waypoints: markerCoords,
        routeWhileDragging: true,
        showAlternatives: true,
        altLineOptions: {
            styles: [
                { color: 'blue', weight: 4 },
                { color: 'green', weight: 4 },
                { color: 'orange', weight: 4 }
            ]
        },
        createMarker: function (i, wp, n) {
            return L.marker(wp.latLng, {
                draggable: true,
                icon: L.divIcon({ className: 'leaflet-marker-icon' })
            });
        },
        routeWhileDragging: true,
        show: false,
        collapsible: true,
        autoRoute: true,
        itineraryControl: {
            showSubHeading: true,
            show: true
        }
    }).addTo(map);

    routingControl.on('routesfound', function (e) {
        var routes = e.routes;
        var summary = routes[0].summary;
        var distance = (summary.totalDistance / 1000).toFixed(2); // Расстояние в километрах
        var condition = 'Хорошее'; // Состояние дороги (можно добавить логику для определения состояния)

        var popup = L.popup()
            .setLatLng(markerCoords[0])
            .setContent(`
                <p>Расстояние: ${distance} км</p>
                <p>Состояние дороги: ${condition}</p>
            `);
        markers.getLayers()[0].bindPopup(popup).openPopup();
    });
}

// Функция для удаления маркера
markers.on('click', function (e) {
    if (e.layer) {
        markers.removeLayer(e.layer);
        updateRoute();
    }
});


