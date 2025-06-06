document.addEventListener('DOMContentLoaded', function () {
  const mqttToggle = document.getElementById('mqtt-toggle');
  const mqttStatus = document.getElementById('mqtt-status');
  const mqttDescription = document.getElementById('mqtt-description');
  const discoveryToggle = document.getElementById('discovery-toggle');
  const discoveryStatus = document.getElementById('discovery-status');
  const discoveryDescription = document.getElementById('discovery-description')

  const Status = {
    INACTIVE: 'notactive',
    PROCESSING: 'processing',
    ACTIVE: 'isactive'
  };

  function getState(error) {
    return { Connected: isActive(mqttToggle), Discovered: isActive(discoveryToggle), error: error };
  }

  function getStatus(toggle) {
    toggleName = toggle == mqttToggle ? 'mqttToggle' : 'discoveryToggle';
    cList = toggle.classList;
    var list = [];
    for(let key in Status) {
      if (cList.contains(Status[key])) {
        list.push(Status[key]);
      }
    }
    if (list.length > 1) {
      throw new Error("Invalid status for a toggle");
    }
    if (list.length == 0) {
      list.push(Status.INACTIVE);
    }
    return list[0];
  }

  function isActive(toggle) {
    return toggle.classList.contains(Status.ACTIVE);
  }

  function isProcessing(toggle) {
    return toggle.classList.contains(Status.PROCESSING);
  }

  function isInactive(toggle) {
    return toggle.classList.contains(Status.INACTIVE);
  }

  function setMqttState(state) {
    for(let key in Status) {
      mqttToggle.classList.remove(Status[key]);
    }
    mqttToggle.classList.add(state);
  }

  function setDiscoveryState(state) {
    for(let key in Status) {
      discoveryToggle.classList.remove(Status[key]);
    }
    discoveryToggle.classList.add(state);
  }

  function setHover(toggle) {
    toggle.classList.remove('no-hover');
  }

  function setNoHover(toggle) {
    toggle.classList.add('no-hover');
  }

  console.log('jscript start');

  fetch('/mqtt-toggle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({Connected: false, Discovered: false, error:''})
  })
  .then(response => response.json())
  .then(data => {
    console.log('initial data:'+JSON.stringify(data));
  });

  mqttToggle.addEventListener('click', function () {
    mqttState = getStatus(mqttToggle);
    discoveryState = getStatus(discoveryToggle);
    if (mqttState == Status.Processing) {
      mqttDescription.textContent = 'Wait until Discovery turned off';
      return;
    }
    if (mqttState == Status.INACTIVE) {
      mqttDescription.textContent = 'Wait for Connect';
    } else {
      mqttDescription.textContent = 'Wait for Disconnection';
    }
    var state = getState('');
    setMqttState(Status.PROCESSING)
    setHover(mqttToggle);
    mqttStatus.textContent = 'Processing...';

    fetch('/mqtt-toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state)
    })
    .then(response => response.json())
    .then(data => {
      if (data.error != '') {
        console.error('Error: '+data.error);
      }
      if (data.Connected) {
        setHover(discoveryToggle);
        setMqttState(Status.ACTIVE);
        mqttStatus.textContent = 'Connected';
        mqttDescription.textContent = '\u00a0';
        discoveryDescription.textContent = 'Click to start Discovery';
      } else {
        setMqttState(Status.INACTIVE);
        mqttStatus.textContent = 'Not Connected';
        mqttDescription.textContent = 'Click to Connect';
      }
    })
    .catch(error => {
        console.error("Error toggling MQTT:", error);
        console.error("\tname:", error.name);
        console.error("\tlineNumber:", error.lineNumber);
        console.error("\tcolumnNumber:", error.columnNumber);
        console.error("\tmessage:", error.message);
        console.error("\tcause:", error.cause);
    });
  });

  discoveryToggle.addEventListener('click', function () {
    mqttState = getStatus(mqttToggle);
    discoveryState = getStatus(discoveryToggle);
    initialState = getState('');
    if (mqttState != Status.ACTIVE) {
      discoveryDescription.textContent = 'MQTT must be connected first';
      return;
    }
    if (discoveryState == Status.ACTIVE) {
      discoveryStatus.textContent = "Un-Discovery in process";
      discoveryDescription.textContent = "Wait for completion";
      setDiscoveryState(Status.PROCESSING);
      setHover(discoveryToggle);
    } else {
      discoveryStatus.textContent = "Discovery in process";
      discoveryDescription.textContent = "Wait for completion";
      setNoHover(mqttToggle);
      setDiscoveryState(Status.PROCESSING);
      setNoHover(discoveryToggle);
    }
    fetch('/discovery-toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(initialState)
    })
    .then(response => response.json())
    .then(data => {
      if (discoveryState == Status.ACTIVE) {
        discoveryStatus.textContent = "Un-Discovery complete";
        discoveryDescription.textContent = "Click to Discover";
        setDiscoveryState(Status.INACTIVE);
        setHover(discoveryToggle);
        setHover(mqttToggle);
      } else {
        discoveryStatus.textContent = "Discovery complete";
        discoveryDescription.textContent = "Click to Un-Discover";
        setDiscoveryState(Status.ACTIVE);
        setHover(discoveryToggle);
      }
    })
    .catch(error => {
      console.error("Error toggling MQTT:", error);
    });
  });
});
