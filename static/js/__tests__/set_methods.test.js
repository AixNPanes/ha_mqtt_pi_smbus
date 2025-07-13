/**
 * @jest-environment jsdom
 */

import "@testing-library/jest-dom";
import fetchMock from "jest-fetch-mock";

fetchMock.enableMocks();

beforeEach(() => {
  jest.resetModules();
  fetchMock.resetMocks();

  document.body.innerHTML = `
    <div class="error-msg">
      <span id="error-msg">&nbsp;</span>
    </div>
    <div class="lozenge-group">
      <div class="lozenge disconnected" id="mqtt-toggle">
        <span id="mqtt-status">Not Connected</span>
        <span id="mqtt-description">Click to connect</span>
      </div>
      <div class="lozenge undiscovered disabled" id="discovery-toggle">
        <span id="discovery-status">Not discovered</span>
        <span id="discovery-description">Click to start Discovery</span>
      </div>
    </div>
  `;
});

test("setMQTTState", async () => {
  const scripts = await import("../scripts.js");
  scripts.setMQTTState(scripts.MQTTStatus.CONNECTED);
  expect(scripts.mqttToggle()).toHaveClass('connected');
  scripts.setMQTTState(scripts.MQTTStatus.PROCESSING);
  expect(scripts.mqttToggle()).toHaveClass('processing');
  scripts.setMQTTState(scripts.MQTTStatus.DISCONNECTED);
  expect(scripts.mqttToggle()).toHaveClass('disconnected');
});

test("setDiscoveryState", async () => {
  const scripts = await import("../scripts.js");
  scripts.setDiscoveryState(scripts.DiscoveryStatus.DISCOVERED);
  expect(scripts.discoveryToggle()).toHaveClass('discovered');
  scripts.setDiscoveryState(scripts.DiscoveryStatus.PROCESSING);
  expect(scripts.discoveryToggle()).toHaveClass('processing');
  scripts.setDiscoveryState(scripts.DiscoveryStatus.UNDISCOVERED);
  expect(scripts.discoveryToggle()).toHaveClass('undiscovered');
});

test("setDisabled", async () => {
  const scripts = await import("../scripts.js");
  scripts.setDisabled(scripts.mqttToggle());
  expect(scripts.mqttToggle()).toHaveClass('disabled');
  scripts.setDisabled(scripts.discoveryToggle());
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("setEnabled", async () => {
  const scripts = await import("../scripts.js");
  scripts.setEnabled(scripts.mqttToggle());
  expect(scripts.mqttToggle()).not.toHaveClass('disabled');
  scripts.setEnabled(scripts.discoveryToggle());
  expect(scripts.discoveryToggle()).not.toHaveClass('disabled');
});

test("setDisconnected", async () => {
  const scripts = await import("../scripts.js");
  scripts.setDisconnected();
  expect(scripts.mqttStatus().textContent).toEqual('Not Connected');
  expect(scripts.mqttDescription().textContent).toEqual('Click to Connect');
  expect(scripts.discoveryStatus().textContent).toEqual('Not discovered');
  expect(scripts.discoveryDescription().textContent).toEqual('You must Connect before Discovery');
  expect(scripts.mqttToggle()).toHaveClass(scripts.MQTTStatus.DISCONNECTED);
  expect(scripts.mqttToggle()).not.toHaveClass('disabled');
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("setConnected", async () => {
  const scripts = await import("../scripts.js");
  scripts.setConnected();
  expect(scripts.mqttStatus().textContent).toEqual('Connected');
  expect(scripts.mqttDescription().textContent).toEqual('Start Discovery or Click To Disconnect');
  expect(scripts.discoveryStatus().textContent).toEqual('Not discovered');
  expect(scripts.discoveryDescription().textContent).toEqual('Click to start Discovery');
  expect(scripts.mqttToggle()).toHaveClass(scripts.MQTTStatus.CONNECTED);
  expect(scripts.mqttToggle()).not.toHaveClass('disabled');
  expect(scripts.discoveryToggle()).not.toHaveClass('disabled');
});

test("setMQTTConnectProcessing", async () => {
  const scripts = await import("../scripts.js");
  scripts.setMQTTConnectProcessing();
  expect(scripts.mqttStatus().textContent).toEqual('Connection in process');
  expect(scripts.mqttDescription().textContent).toEqual('Wait for completion');
  expect(scripts.discoveryStatus().textContent).toEqual('Not discovered');
  expect(scripts.discoveryDescription().textContent).toEqual('You must Connect before Discovery');
  expect(scripts.mqttToggle()).toHaveClass(scripts.MQTTStatus.PROCESSING);
  expect(scripts.mqttToggle()).toHaveClass('disabled');
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("setMQTTDisconnectProcessing", async () => {
  const scripts = await import("../scripts.js");
  scripts.setMQTTDisconnectProcessing();
  expect(scripts.mqttStatus().textContent).toEqual('Disconnection in process');
  expect(scripts.mqttDescription().textContent).toEqual('Wait for completion');
  expect(scripts.discoveryStatus().textContent).toEqual('Not discovered');
  expect(scripts.discoveryDescription().textContent).toEqual('You must Connect before Discovery');
  expect(scripts.mqttToggle()).toHaveClass(scripts.MQTTStatus.PROCESSING);
  expect(scripts.mqttToggle()).toHaveClass('disabled');
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("setUndiscovered", async () => {
  const scripts = await import("../scripts.js");
  scripts.setUndiscovered();
  expect(scripts.mqttStatus().textContent).toEqual('Connected');
  expect(scripts.mqttDescription().textContent).toEqual('Start Discovery or Click To Disconnect');
  expect(scripts.discoveryStatus().textContent).toEqual('Not discovered');
  expect(scripts.discoveryDescription().textContent).toEqual('Click to Discover');
  expect(scripts.discoveryToggle()).toHaveClass(scripts.DiscoveryStatus.UNDISCOVERED);
  expect(scripts.mqttToggle()).not.toHaveClass('disabled');
  expect(scripts.discoveryToggle()).not.toHaveClass('disabled');
});

test("setDiscovered", async () => {
  const scripts = await import("../scripts.js");
  scripts.setDiscovered();
  expect(scripts.mqttStatus().textContent).toEqual('Connected');
  expect(scripts.mqttDescription().textContent).toEqual('You must Undiscover before Connect');
  expect(scripts.discoveryStatus().textContent).toEqual('Discovered');
  expect(scripts.discoveryDescription().textContent).toEqual('Click to Undiscover');
  expect(scripts.discoveryToggle()).toHaveClass(scripts.DiscoveryStatus.DISCOVERED);
  expect(scripts.mqttToggle()).toHaveClass('disabled');
  expect(scripts.discoveryToggle()).not.toHaveClass('disabled');
});

test("setDiscoveryProcessing", async () => {
  const scripts = await import("../scripts.js");
  scripts.setDiscoveryProcessing();
  expect(scripts.mqttStatus().textContent).toEqual('Connected');
  expect(scripts.mqttDescription().textContent).toEqual('You must Undiscover before Connect');
  expect(scripts.discoveryStatus().textContent).toEqual('Discovery in process');
  expect(scripts.discoveryDescription().textContent).toEqual('Wait for completion');
  expect(scripts.discoveryToggle()).toHaveClass(scripts.DiscoveryStatus.PROCESSING);
  expect(scripts.mqttToggle()).toHaveClass('disabled');
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("setUndiscoveryProcessing", async () => {
  const scripts = await import("../scripts.js");
  scripts.setUndiscoveryProcessing();
  expect(scripts.mqttStatus().textContent).toEqual('Connected');
  expect(scripts.mqttDescription().textContent).toEqual('You must Undiscover before Connect');
  expect(scripts.discoveryStatus().textContent).toEqual('Un-Discovery in process');
  expect(scripts.discoveryDescription().textContent).toEqual('Wait for completion');
  expect(scripts.discoveryToggle()).toHaveClass(scripts.DiscoveryStatus.PROCESSING);
  expect(scripts.mqttToggle()).toHaveClass('disabled');
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("setErrorMessage", async () => {
  const scripts = await import("../scripts.js");
  scripts.setErrorMessage(null);
  expect(scripts.errorMsg().textContent).toEqual('\u00a0');
  scripts.setErrorMessage(['Error1','Error2']);
  expect(scripts.errorMsg().textContent).toEqual('Error1<br>Error2');
});

test("resyncState-Discovered", async () => {
  const scripts = await import("../scripts.js");
  scripts.resyncState(scripts.DiscoveryStatus.DISCOVERED);
  expect(scripts.mqttStatus().textContent).toEqual('Connected');
  expect(scripts.mqttDescription().textContent).toEqual('You must Undiscover before Connect');
  expect(scripts.discoveryStatus().textContent).toEqual('Discovered');
  expect(scripts.discoveryDescription().textContent).toEqual('Click to Undiscover');
  expect(scripts.discoveryToggle()).toHaveClass(scripts.DiscoveryStatus.DISCOVERED);
  expect(scripts.mqttToggle()).toHaveClass('disabled');
  expect(scripts.discoveryToggle()).not.toHaveClass('disabled');
});

test("resyncState-Connected", async () => {
  const scripts = await import("../scripts.js");
  scripts.resyncState(scripts.MQTTStatus.CONNECTED);
  expect(scripts.mqttStatus().textContent).toEqual('Connected');
  expect(scripts.mqttDescription().textContent).toEqual('Start Discovery or Click To Disconnect');
  expect(scripts.discoveryStatus().textContent).toEqual('Not discovered');
  expect(scripts.discoveryDescription().textContent).toEqual('Click to start Discovery');
  expect(scripts.mqttToggle()).toHaveClass(scripts.MQTTStatus.CONNECTED);
  expect(scripts.mqttToggle()).not.toHaveClass('disabled');
  expect(scripts.discoveryToggle()).not.toHaveClass('disabled');
});

test("resyncState-Disconnected", async () => {
  const scripts = await import("../scripts.js");
  scripts.resyncState(scripts.MQTTStatus.DISCONNECTED);
  expect(scripts.mqttStatus().textContent).toEqual('Not Connected');
  expect(scripts.mqttDescription().textContent).toEqual('Click to Connect');
  expect(scripts.discoveryStatus().textContent).toEqual('Not discovered');
  expect(scripts.discoveryDescription().textContent).toEqual('You must Connect before Discovery');
  expect(scripts.mqttToggle()).toHaveClass(scripts.MQTTStatus.DISCONNECTED);
  expect(scripts.mqttToggle()).not.toHaveClass('disabled');
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("formatError", async () => {
  const scripts = await import("../scripts.js");
  const result = scripts.formatError('message', Error('Error'));
  expect(result).toContain('Error: Error');
});
