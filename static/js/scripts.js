const MQTTStatus = {
  DISCONNECTED: 'disconnected',
  PROCESSING: 'processing',
  CONNECTED: 'connected'
};

const DiscoveryStatus = {
  UNDISCOVERED: 'undiscovered',
  PROCESSING: 'processing',
  DISCOVERED: 'discovered'
};

function mqttToggle() {
  return document.getElementById('mqtt-toggle');
}

function mqttStatus() {
  return document.getElementById('mqtt-status');
}

function mqttDescription() {
  return document.getElementById('mqtt-description');
}

function discoveryToggle() {
  return document.getElementById('discovery-toggle');
}

function discoveryStatus() {
  return document.getElementById('discovery-status');
}

function discoveryDescription() {
  return document.getElementById('discovery-description');
}

function errorMsg() {
  return document.getElementById('error-msg');
}

function isMQTTConnected() {
  return mqttToggle().classList.contains(MQTTStatus.CONNECTED);
}

function isDiscoveryDiscovered() {
  return discoveryToggle().classList.contains(DiscoveryStatus.DISCOVERED);
}

function isMQTTProcessing() {
  return mqttToggle().classList.contains(MQTTStatus.PROCESSING);
}

function isDiscoveryProcessing() {
  return discoveryToggle().classList.contains(DiscoveryStatus.PROCESSING);
}

function isMQTTDisconnected() {
  return mqttToggle().classList.contains(MQTTStatus.DISCONNECTED);
}

function isDiscoveryUndiscovered() {
  return discoveryToggle().classList.contains(DiscoeryStatus.UNDISCOVERED);
}

function getState(error) {
  return {
      Connected: isMQTTConnected(),
      Discovered: isDiscoveryDiscovered(),
      Error: error
    };
}

function getStatus(toggle) {
  const cList = toggle.classList;
  const isMqtt = toggle == mqttToggle();
  const toggleName = isMqtt ? 'mqttToggle' : 'discoveryToggle';
  const stat = isMqtt ? MQTTStatus : DiscoveryStatus;
  const defaultStatus = isMqtt ? MQTTStatus.DISCONNECTED : DiscoveryStatus.UNDISCOVERED;
  let list = [];
  for(let key in stat) {
    if (cList.contains(stat[key])) {
      list.push(stat[key]);
    }
  }
  if (list.length > 1) {
    throw new Error("Invalid status for toggle");
  }
  if (list.length == 0) {
    list.push(defaultStatus);
  }
  return list[0];
}

function setMQTTState(state) {
  for(let key in MQTTStatus) {
    mqttToggle().classList.remove(MQTTStatus[key]);
  }
  mqttToggle().classList.add(state);
}

function setDiscoveryState(state) {
  for(let key in DiscoveryStatus) {
    discoveryToggle().classList.remove(DiscoveryStatus[key]);
  }
  discoveryToggle().classList.add(state);
}

function setDisabled(toggle) {
  toggle.classList.add('disabled');
}

function setEnabled(toggle) {
  toggle.classList.remove('disabled');
}

function setDisconnected() {
  mqttStatus().textContent = 'Not Connected';
  mqttDescription().textContent = 'Click to Connect';
  discoveryStatus().textContent = 'Not discovered';
  discoveryDescription().textContent = 'You must Connect before Discovery';
  setMQTTState(MQTTStatus.DISCONNECTED);
  setEnabled(mqttToggle());
  setDisabled(discoveryToggle());
}

function setMQTTConnectProcessing() {
  mqttStatus().textContent = 'Connection in process';
  mqttDescription().textContent = 'Wait for completion';
  discoveryStatus().textContent = 'Not discovered';
  discoveryDescription().textContent = 'You must Connect before Discovery';
  setMQTTState(MQTTStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

function setConnected() {
  mqttStatus().textContent = 'Connected';
  mqttDescription().textContent = 'Start Discovery or Click To Disconnect';
  discoveryStatus().textContent = 'Not discovered';
  discoveryDescription().textContent = 'Click to start Discovery';
  setMQTTState(MQTTStatus.CONNECTED);
  setEnabled(mqttToggle());
  setEnabled(discoveryToggle());
}

function setMQTTDisconnectProcessing() {
  mqttStatus().textContent = 'Disconnection in process';
  mqttDescription().textContent = 'Wait for completion';
  discoveryStatus().textContent = 'Not discovered';
  discoveryDescription().textContent = 'You must Connect before Discovery';
  setMQTTState(MQTTStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

function setDiscovered() {
  mqttStatus().textContent = 'Connected';
  mqttDescription().textContent = 'You must Undiscover before Connect';
  discoveryStatus().textContent = 'Discovered';
  discoveryDescription().textContent = 'Click to Undiscover';
  setDiscoveryState(DiscoveryStatus.DISCOVERED);
  setDisabled(mqttToggle());
  setEnabled(discoveryToggle());
}

function setUndiscovered() {
  mqttStatus().textContent = 'Connected';
  mqttDescription().textContent = 'Start Discovery or Click To Disconnect';
  discoveryStatus().textContent = 'Not discovered';
  discoveryDescription().textContent = 'Click to Discover';
  setDiscoveryState(DiscoveryStatus.UNDISCOVERED);
  setEnabled(mqttToggle());
  setEnabled(discoveryToggle());
}

function setDiscoveryProcessing() {
  mqttStatus().textContent = 'Connected';
  mqttDescription().textContent = 'You must Undiscover before Connect';
  discoveryStatus().textContent = 'Discovery in process';
  discoveryDescription().textContent = 'Wait for completion';
  setDiscoveryState(DiscoveryStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

function setUndiscoveryProcessing() {
  mqttStatus().textContent = 'Connected';
  mqttDescription().textContent = 'You must Undiscover before Connect';
  discoveryStatus().textContent = 'Un-Discovery in process';
  discoveryDescription().textContent = 'Wait for completion';
  setDiscoveryState(DiscoveryStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

function formatError(msg, error) {
  return "Error toggling MQTT: " + error + "\n"
    "\tname: " + error.name; + "\n"
    "\tlineNumber: " + error.lineNumber + "\n"
    "\tcolumnNumber: " + error.columnNumber + "\n"
    "\tmessage: " + error.message | "\n"
    "\tcause: " + error.causex;
}

async function updateButtonsFromStatus() {
  const response = await fetch('/status');
  const state = await response.json();

  if (state.Error || (state.Discovered && !state.Connected)) {
    setDisabled(mqttToggle().disabled);
  }
  if (!state.Connected || state.Error) {
    setDisabled(discoveryToggle());
  }

  // Optionally show error
  if (state.Error) {
    errorMsg().textContent = state.Error;
  }
  if (state.Error) {
    errorMsg().textContent = state.Error;
    errorMsg().style.display = 'block';
  } else {
    errorMsg().textContent = '';
    errorMsg().style.display = 'none';
  }

}

document.addEventListener('DOMContentLoaded', updateButtonsFromStatus);

document.addEventListener('DOMContentLoaded', function () {

  mqttToggle().addEventListener('click', function () {
    const mqttState = getStatus(mqttToggle());
    const discoveryState = getStatus(discoveryToggle());
    if (isMQTTProcessing()) {
      mqttDescription().textContent = 'Wait until Discovery turned off';
      return;
    }
    state = getState("");
    if (isMQTTConnected()) {
      setMQTTDisconnectProcessing();
    } else {
      setMQTTConnectProcessing();
    }

    fetch('/mqtt-toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state)
    })
    .then(response => response.json())
    .then(data => {
      if (data.Error != '') {
        console.error('Error: '+data.Error);
      }
      if (data.Connected) {
        setConnected();
      } else {
        setDisconnected();
      }
    })
    .catch(error => {
      console.error(formatError("Error Toggling MQTT", error));
    });
  });

  discoveryToggle().addEventListener('click', function () {
    const mqttState = getStatus(mqttToggle());
    const discoveryState = getStatus(discoveryToggle());
    const isDiscovered = isDiscoveryDiscovered();
    if (!isMQTTConnected()) {
      discoveryDescription().textContent = 'MQTT must be connected first';
      return;
    }
    state = getState("")
    if (isDiscovered) {
      setUndiscoveryProcessing();
    } else {
      setDiscoveryProcessing();
    }
    fetch('/discovery-toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state)
    })
    .then(response => response.json())
    .then(data => {
      if (data.Error != '') {
        console.error('Error: '+data.Error);
      }
      if (isDiscovered) {
        setUndiscovered();
      } else {
        setDiscovered();
      }
    })
    .catch(error => {
      console.error(formatError("Error toggling Discovery:", error));
    });
  });
});
