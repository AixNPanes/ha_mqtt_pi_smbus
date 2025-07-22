export const MQTTStatus = {
  DISCONNECTED: "disconnected",
  PROCESSING: "processing",
  CONNECTED: "connected",
};

export const DiscoveryStatus = {
  UNDISCOVERED: "undiscovered",
  PROCESSING: "processing",
  DISCOVERED: "discovered",
};

export function mqttToggle() {
  return document.getElementById("mqtt-toggle");
}

export function mqttStatus() {
  return document.getElementById("mqtt-status");
}

export function mqttDescription() {
  return document.getElementById("mqtt-description");
}

export function discoveryToggle() {
  return document.getElementById("discovery-toggle");
}

export function discoveryStatus() {
  return document.getElementById("discovery-status");
}

export function discoveryDescription() {
  return document.getElementById("discovery-description");
}

export function errorMsg() {
  return document.getElementById("error-msg");
}

export function isConnected() {
  return mqttToggle().classList.contains(MQTTStatus.CONNECTED);
}

export function isDiscovered() {
  return discoveryToggle().classList.contains(DiscoveryStatus.DISCOVERED);
}

export function isMQTTProcessing() {
  return mqttToggle().classList.contains(MQTTStatus.PROCESSING);
}

export function isDiscoveryProcessing() {
  return discoveryToggle().classList.contains(DiscoveryStatus.PROCESSING);
}

export function isDisconnected() {
  return mqttToggle().classList.contains(MQTTStatus.DISCONNECTED);
}

export function isUndiscovered() {
  return discoveryToggle().classList.contains(DiscoveryStatus.UNDISCOVERED);
}

export function getState(error) {
  return {
    Connected: isConnected(),
    Discovered: isDiscovered(),
    Error: error,
  };
}

export function getStatus(toggle) {
  const cList = toggle.classList;
  const isMqtt = toggle == mqttToggle();
  const stat = isMqtt ? MQTTStatus : DiscoveryStatus;
  const defaultStatus = isMqtt
    ? MQTTStatus.DISCONNECTED
    : DiscoveryStatus.UNDISCOVERED;
  let list = [];
  for (let key in stat) {
    if (cList.contains(stat[key])) {
      list.push(stat[key]);
    }
  }
  if (list.length > 1) {
    console.error("Invalid status for toggle: " + list);
    throw new Error("Invalid status for toggle: " + list);
  }
  if (list.length == 0) {
    list.push(defaultStatus);
  }
  return list[0];
}

export function setMQTTState(state) {
  for (let key in MQTTStatus) {
    mqttToggle().classList.remove(MQTTStatus[key]);
  }
  mqttToggle().classList.add(state);
}

export function setDiscoveryState(state) {
  for (let key in DiscoveryStatus) {
    discoveryToggle().classList.remove(DiscoveryStatus[key]);
  }
  discoveryToggle().classList.add(state);
}

export function setDisabled(toggle) {
  toggle.classList.add("disabled");
}

export function setEnabled(toggle) {
  toggle.classList.remove("disabled");
}

export function setDisconnected() {
  mqttStatus().textContent = "Not Connected";
  mqttDescription().textContent = "Click to Connect";
  discoveryStatus().textContent = "Not discovered";
  discoveryDescription().textContent = "You must Connect before Discovery";
  setMQTTState(MQTTStatus.DISCONNECTED);
  setEnabled(mqttToggle());
  setDisabled(discoveryToggle());
}

export function setConnectProcessing() {
  mqttStatus().textContent = "Connection in process";
  mqttDescription().textContent = "Wait for completion";
  discoveryStatus().textContent = "Not discovered";
  discoveryDescription().textContent = "You must Connect before Discovery";
  setMQTTState(MQTTStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

export function setConnected() {
  mqttStatus().textContent = "Connected";
  mqttDescription().textContent = "Start Discovery or Click To Disconnect";
  discoveryStatus().textContent = "Not discovered";
  discoveryDescription().textContent = "Click to start Discovery";
  setMQTTState(MQTTStatus.CONNECTED);
  setEnabled(mqttToggle());
  setEnabled(discoveryToggle());
}

export function setDisconnectProcessing() {
  mqttStatus().textContent = "Disconnection in process";
  mqttDescription().textContent = "Wait for completion";
  discoveryStatus().textContent = "Not discovered";
  discoveryDescription().textContent = "You must Connect before Discovery";
  setMQTTState(MQTTStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

export function setDiscovered() {
  mqttStatus().textContent = "Connected";
  mqttDescription().textContent = "You must Undiscover before Connect";
  discoveryStatus().textContent = "Discovered";
  discoveryDescription().textContent = "Click to Undiscover";
  setMQTTState(MQTTStatus.CONNECTED);
  setDiscoveryState(DiscoveryStatus.DISCOVERED);
  setDisabled(mqttToggle());
  setEnabled(discoveryToggle());
}

export function setUndiscovered() {
  mqttStatus().textContent = "Connected";
  mqttDescription().textContent = "Start Discovery or Click To Disconnect";
  discoveryStatus().textContent = "Not discovered";
  discoveryDescription().textContent = "Click to Discover";
  setMQTTState(MQTTStatus.CONNECTED);
  setDiscoveryState(DiscoveryStatus.UNDISCOVERED);
  setEnabled(mqttToggle());
  setEnabled(discoveryToggle());
}

export function setDiscoveryProcessing() {
  mqttStatus().textContent = "Connected";
  mqttDescription().textContent = "You must Undiscover before Connect";
  discoveryStatus().textContent = "Discovery in process";
  discoveryDescription().textContent = "Wait for completion";
  setDiscoveryState(DiscoveryStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

export function setUndiscoveryProcessing() {
  mqttStatus().textContent = "Connected";
  mqttDescription().textContent = "You must Undiscover before Connect";
  discoveryStatus().textContent = "Un-Discovery in process";
  discoveryDescription().textContent = "Wait for completion";
  setDiscoveryState(DiscoveryStatus.PROCESSING);
  setDisabled(mqttToggle());
  setDisabled(discoveryToggle());
}

export function setErrorMessage(msg) {
  if (msg === null) {
    errorMsg().textContent = "\u00a0";
  } else {
    errorMsg().textContent = msg.join("<br>");
    console.error("Error->: " + msg);
  }
}

export function resyncState(state) {
  if (state === DiscoveryStatus.DISCOVERED) {
    setDiscovered();
  } else if (state === MQTTStatus.CONNECTED) {
    setConnected();
  } else {
    setDisconnected();
  }
}

export function formatError(msg, error) {
  return (
    msg +": " + error +
    "\n\t" + "name: " + error.name +
    "\n\tmessage: " + error.message
  );
}

export function checkStateError(state) {
  if (state.Error.length !== 0 || (state.Discovered && !state.Connected)) {
    setDisabled(mqttToggle());
  }
  if (state.Error.length != 0 || !state.Connected) {
    setDisabled(discoveryToggle());
  }
  return state;
}

export async function fetchStatus() {
  return await fetch("/status", {
    method: "GET",
    headers: { "Content-type": "application/json" },
  })
    .then((response) => response.json())
    .then((state) => checkStateError(state))
    .catch((error) => {
      let err = formatError("fetchStatus error", error);
      errorMsg().innerHTML = err;  
      console.error(err);
    });
}

export async function updateButtonsFromStatus() {
  const state = await fetchStatus();
  if (state.Error.length !== 0) {
    setErrorMessage(state.Error);
    resyncState(state);
  } else {
    setErrorMessage(null);
  }
  return state;
}

export async function initDom() {
  updateButtonsFromStatus().then((data) => {
    if (data.Connected) {
      setConnected();
      if (data.Discovered) {
        setDiscovered();
      } else {
        setUndiscovered();
      }
    } else {
      setDisconnected();
    }
  });
  return getState([]);
}

export function setMQTTProcessingState() {
  const state = getState([]);
  if (isConnected()) {
    setDisconnectProcessing();
  } else {
    setConnectProcessing();
  }
  return state;
}

export function setDiscoveryProcessingState() {
  const state = getState([]);
  if (isDiscovered()) {
    setUndiscoveryProcessing();
  } else {
    setDiscoveryProcessing();
  }
  return state;
}

export async function postUrl(url, state) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
  const data = await response.json();
  if (data.Error.length !== 0) {
    setErrorMessage(data.Error);
    resyncState(data);
  }
  return data;
}

export function handleMqttTogglePost(data) {
  if (data.Connected) {
    setConnected();
  } else {
    setDisconnected();
  }
  return data;
}

export function handleDiscoveryTogglePost(data) {
  if (data.Discovered) {
    setDiscovered();
  } else {
    setUndiscovered();
  }
  return data;
}

export async function mqttToggleClickEventListener() {
  if (isMQTTProcessing()) {
    mqttDescription().textContent =
      "Wait until Connection/Disconnection stops processing";
    return;
  }

  let state = setMQTTProcessingState();

  state = await postUrl("/mqtt-toggle", state)
    .then((data) => handleMqttTogglePost(data))
    .catch((error) => {
      let err = formatError("Error Toggling MQTT", error);
      errorMsg().innerHTML = err;  
      console.error(err);
    });
  return state;
}

export async function discoveryToggleClickEventListener() {
  if (!isConnected()) {
    discoveryDescription().textContent = "MQTT must be connected first";
    return;
  }

  if (isDiscoveryProcessing()) {
    discoveryDescription().textContent =
      "Wait until Discovery/Undiscovery complete";
    return;
  }

  let state = setDiscoveryProcessingState();

  state = await postUrl("/discovery-toggle", state)
    .then((data) => handleDiscoveryTogglePost(data))
    .catch((error) => {
      let err = formatError("Error toggling Discovery", error);
      errorMsg().innerHTML = err;  
      console.error(err);
    });
  return state;
}

export async function init({
  domInit = initDom,
  onUpdate = updateButtonsFromStatus,
  onMqttClick = mqttToggleClickEventListener,
  onDiscoveryClick = discoveryToggleClickEventListener,
} = {}) {
  await domInit();

  document.addEventListener("DOMContentLoaded", onUpdate);
  document.addEventListener("DOMContentLoaded", function () {
    mqttToggle().addEventListener("click", onMqttClick);
    discoveryToggle().addEventListener("click", onDiscoveryClick);
  });
}
