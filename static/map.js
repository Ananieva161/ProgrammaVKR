// map.js

let map;
let marker;

function initMap(elementId, center = [61.78, 34.35], zoom = 8) {
    map = L.map(elementId).setView(center, zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    map.on('click', function(e) {
        setMarker(e.latlng);
    });
}

function setMarker(latlng) {
    if (marker) {
        map.removeLayer(marker);
    }
    marker = L.marker(latlng).addTo(map);
    document.querySelector('[name="location"]').value = `${latlng.lat}, ${latlng.lng}`;
}

function updateMarker(lat, lng) {
    const latlng = L.latLng(lat, lng);
    setMarker(latlng);
    map.setView(latlng, 10);
}

export { initMap, setMarker, updateMarker };
