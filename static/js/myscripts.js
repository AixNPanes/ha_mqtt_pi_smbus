document.addEventListener('DOMContentLoaded', function () {
  const mqttToggle = document.getElementById('mqtt-toggle');
  const mqttStatus = document.getElementById('mqtt-status');
  const mqttDescription = document.getElementById('mqtt-description');
  const discoveryToggle = document.getElementById('discovery-toggle');

  discoveryToggle.addEventListener('change', function () {
    fetch('/discovery-toggle', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ discovery_state: this.checked, mqtt_state: mqttToggle.checked})
    })
    .then(response => response.json())
    .catch(error => {
      console.error("Error toggling MQTT:", error);
    });
  });

  mqttToggle.addEventListener('change', function () {
    // Immediately show "Connecting..." when toggled ON
    mqttStatus.textContent = !this.checked
		  ? 'Disconnecting...'
		  : 'Connecting...' ;
    mqttDescription.textContent = !this.checked
		  ? 'Disconnecting...'
		  : 'Connecting...' ;

    fetch('/mqtt-toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ discovery_state: discoveryToggle.checked, mqtt_state: this.checked })
    })
    .then(response => { return response.json(); })
    .then(data => {
      mqttStatus.textContent = data.Connected ? 'Connected' : 'Disconnected';
      discoveryToggle.disabled = !data.Connected;
    })
    .catch(error => { console.error("Error toggling MQTT:", error); });
  });
});      
