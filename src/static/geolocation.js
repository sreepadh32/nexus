const getLocationButton = document.getElementById('get-location');

getLocationButton.addEventListener('click', () => {
  navigator.geolocation.getCurrentPosition(position => {
    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;

    fetch('/location', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ latitude, longitude })
    })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error(error));
  });
});