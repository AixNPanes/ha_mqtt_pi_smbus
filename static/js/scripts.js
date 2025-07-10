export const MQTTStatus = {
  DISCONNECTED: 'disconnected',
  PROCESSING: 'processing',
  CONNECTED: 'connected'
};

export const DiscoveryStatus = {
  UNDISCOVERED: 'undiscovered',
  PROCESSING: 'processing',
  DISCOVERED: 'discovered'
};

export function mqttToggle() {
  return document.getElementById('mqtt-toggle');
}

export function mqttStatus() {
  return document.getElementById('mqtt-status');
}

export function mqttDescription() {
  return document.getElementById('mqtt-description');
}

export function discoveryToggle() {
  return document.getElementById('discovery-toggle');
}

export function discoveryStatus() {
  return document.getElementById('discovery-status');
}

export function discoveryDescription() {
  return document.getElementById('discovery-description');
}

export function errorMsg() {
  return document.getElementById('error-msg');
}

export function isMQTTConnected() {
  return mqttToggle().classList.contains(MQTTStatus.CONNECTED);
}

export function isDiscoveryDiscovered() {
  return discoveryToggle().classList.contains(DiscoveryStatus.DISCOVERED);
}

export function isMQTTProcessing() {
  return mqttToggle().classList.contains(MQTTStatus.PROCESSING);
}

export function isDiscoveryProcessing() {
  return discoveryToggle().classList.contains(DiscoveryStatus.PROCESSING);
}

export function isMQTTDisconnected() {
  return mqttToggle().classList.contains(MQTTStatus.DISCONNECTED);
}

export function isDiscoveryUndiscovered() {
  return discoveryToggle().classList.contains(DiscoeryStatus.UNDISCOVERED);
}

export function getState(error) {
  return {
      Connected: isMQTTConnected(),
      Discovered: isDiscoveryDiscovered(),
      Error: error
    };
}

export function getStatus(toggle) {
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
    console.error("Invalid status for toggle: "+list);
    throw new Error("Invalid status for toggle: "+list);
  }
  if (list.length == 0) {
    list.push(defaultStatus);
  }
  return list[0];
}

export function setMQTTState(state) {
  for(let key in MQTTStatus) {
    mqttToggle().classList.remove(MQTTStatus[key]);
  }
  mqttToggle().classList.add(state);
}

export function setDiscoveryState(state) {
  for(let key in DiscoveryStatus) {
    discoveryToggle().classList.remove(DiscoveryStatus[key]);
  }
  discoveryToggle().classList.add(state);
}

export function setDisabled(toggle) {
  toggle.classList.add('disabled');
}

export function setEnabled(toggle) {
  toggle.classList.remove('disabled');
}

export function setDisconnected() {
  mqttStatus().textContent = 'Not Connected';
  mqttDescription().textContent = 'Click to Connect';
  discoveryStatus().textContent = 'Not discovered';
  discoveryDescription().textContent = 'You must Connect before Discovery';
  setMQTTState(MQTTStatus.DISCONNECTED);
  setEnabled(mqttToggle());
  setDisabled(discoveryToggle());
}

export function setMQTTConnectProcessing() {
  mqttStatus().textContent = 'Connection in process';
  mqttDescription().textContent = 'Wait for completion';
  discoveryStatus().textContent = 'Not discovered';
  discoveryDescription().textContent = 'You must Connect before Discovery';
  setMQTTState(MQTTStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

export function setConnected() {
  mqttStatus().textContent = 'Connected';
  mqttDescription().textContent = 'Start Discovery or Click To Disconnect';
  discoveryStatus().textContent = 'Not discovered';
  discoveryDescription().textContent = 'Click to start Discovery';
  setMQTTState(MQTTStatus.CONNECTED);
  setEnabled(mqttToggle());
  setEnabled(discoveryToggle());
}

export function setMQTTDisconnectProcessing() {
  mqttStatus().textContent = 'Disconnection in process';
  mqttDescription().textContent = 'Wait for completion';
  discoveryStatus().textContent = 'Not discovered';
  discoveryDescription().textContent = 'You must Connect before Discovery';
  setMQTTState(MQTTStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

export function setDiscovered() {
  mqttStatus().textContent = 'Connected';
  mqttDescription().textContent = 'You must Undiscover before Connect';
  discoveryStatus().textContent = 'Discovered';
  discoveryDescription().textContent = 'Click to Undiscover';
  setDiscoveryState(DiscoveryStatus.DISCOVERED);
  setDisabled(mqttToggle());
  setEnabled(discoveryToggle());
}

export function setUndiscovered() {
  mqttStatus().textContent = 'Connected';
  mqttDescription().textContent = 'Start Discovery or Click To Disconnect';
  discoveryStatus().textContent = 'Not discovered';
  discoveryDescription().textContent = 'Click to Discover';
  setDiscoveryState(DiscoveryStatus.UNDISCOVERED);
  setEnabled(mqttToggle());
  setEnabled(discoveryToggle());
}

export function setDiscoveryProcessing() {
  mqttStatus().textContent = 'Connected';
  mqttDescription().textContent = 'You must Undiscover before Connect';
  discoveryStatus().textContent = 'Discovery in process';
  discoveryDescription().textContent = 'Wait for completion';
  setDiscoveryState(DiscoveryStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

export function setUndiscoveryProcessing() {
  mqttStatus().textContent = 'Connected';
  mqttDescription().textContent = 'You must Undiscover before Connect';
  discoveryStatus().textContent = 'Un-Discovery in process';
  discoveryDescription().textContent = 'Wait for completion';
  setDiscoveryState(DiscoveryStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

export function setErrorMessage(msg) {
  if (msg === null) {
    errorMsg().textContent = '\u00a0';
  } else {
    errorMsg().textContent = msg.join("<br>");
    console.error("Error->: "+msg);
  }
}

export function resyncState(state) {
  console.log(state);
  if (state.Discovered) {
    console.log('setDiscovered()');
    setDiscovered();
  } else if (state.Connected) {
    console.log('setConnected()');
    setConnected();
  } else {
    console.log('setDisconnected()');
    setDisconnected();
  }
}

export function formatError(msg, error) {
  return "Error toggling MQTT: " + error + "\n"
    "\tname: " + error.name; + "\n"
    "\tlineNumber: " + error.lineNumber + "\n"
    "\tcolumnNumber: " + error.columnNumber + "\n"
    "\tmessage: " + error.message | "\n"
    "\tcause: " + error.cause;
}

export async function updateButtonsFromStatus() {
  const response = await fetch('/status');
  const state = await response.json();
  console.log("updateButtonsFromStatus: "+JSON.stringify(state));

  if (state.Error.length !== 0 || (state.Discovered && !state.Connected)) {
    setDisabled(mqttToggle());
  }
  if (!state.Connected || state.Error.length !== 0) {
    setDisabled(discoveryToggle());
  }

  // Optionally show error
  if (state.Error.length !== 0) {
    setErrorMessage(state.Error);
    resyncState(state);
  } else {
    setErrorMessage(null);
  }

}

fetch('/status', {
  method: 'GET',
  headers: { 'Content-type': 'application/json' }
})
.then(response => response.json())
.then(data => {
  if(data.Error.length != 0) {
    setErrorMessage(data.Error);
    resyncState(data);
  }
  if (data.Connected) {
    setConnected();
    if (data.Discovered) {
      setDiscovered();
    }
    else {
      setUndiscovered();
    }
  }
  else {
    setDisconnected();
  }
});

document.addEventListener('DOMContentLoaded', updateButtonsFromStatus);

document.addEventListener('DOMContentLoaded', function () {

  mqttToggle().addEventListener('click', function () {
    const mqttState = getStatus(mqttToggle());
    const discoveryState = getStatus(discoveryToggle());
    if (isMQTTProcessing()) {
      mqttDescription().textContent = 'Wait until Discovery turned off';
      return;
    }
    const state = getState([]);
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
      if (data.Error.length !== 0) {
        setErrorMessage(data.Error);
        resyncState(data);
      }
      if (data.Connected) {
        setConnected();
      } else {
        setDisconnected();
      }
    })
    .catch(error => {
      if (error instanceof TypeError) {
          console.log(error instanceof TypeError); // true
          console.log(error.message); // "null has no properties"
          console.log(error.name); // "TypeError"
          console.log(error.stack); // Stack of the error
      } else {
        console.error(error);
        console.error(formatError("Error Toggling MQTT", error.constructor));
      }
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
    const state = getState([])
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
      if (data.Error.length !== 0) {
        console.error('Error: '+data.Error.join('\n'));
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
