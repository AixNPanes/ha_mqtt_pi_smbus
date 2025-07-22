/**
 * @jest-environment jsdom
 */

import "@testing-library/jest-dom";
import fetchMock from "jest-fetch-mock";

fetchMock.enableMocks();

const STATE = {
  Connected: false,
  Discovered: false,
  rc: 0,
  Error: [],
};

const DOCUMENT_BODY_INNERHTML = `
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

beforeEach(() => {
  jest.resetModules();
  fetchMock.resetMocks();
  fetchMock.mockResponseOnce(JSON.stringify(STATE));
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
});

afterEach(() => {
  jest.resetModules();
  fetchMock.resetMocks();
});

test("mqttToggleClickEventListener-ConnectProcessing", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = false;
  scripts.setConnectProcessing();
  expect(scripts.isMQTTProcessing()).toBeTruthy();
  state = await scripts.mqttToggleClickEventListener();
  expect(scripts.isMQTTProcessing()).toBeTruthy();
  expect(scripts.mqttToggle()).not.toHaveClass("connected");
  expect(scripts.mqttToggle()).toHaveClass("disabled");
  expect(scripts.discoveryToggle()).toHaveClass("disabled");
  expect(scripts.mqttStatus().innerHTML).toEqual("Connection in process");
  expect(scripts.mqttDescription().innerHTML).toEqual(
    "Wait until Connection/Disconnection stops processing",
  );
});

test("mqttToggleClickEventListener-DisconnectProcessing", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = true;
  scripts.setDisconnectProcessing();
  expect(scripts.isMQTTProcessing()).toBeTruthy();
  state = await scripts.mqttToggleClickEventListener();
  expect(scripts.isMQTTProcessing()).toBeTruthy();
  expect(scripts.mqttToggle()).not.toHaveClass("connected");
  expect(scripts.mqttStatus().innerHTML).toEqual("Disconnection in process");
  expect(scripts.mqttDescription().innerHTML).toEqual(
    "Wait until Connection/Disconnection stops processing",
  );
});

test("mqttToggleClickEventListener-OK", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = true;
  expect(scripts.isMQTTProcessing()).toBeFalsy();
  fetchMock.resetMocks();
  fetchMock.mockResponseOnce(JSON.stringify(state));
  state = await scripts.mqttToggleClickEventListener();
  expect(scripts.isMQTTProcessing()).toBeFalsy();
  expect(scripts.isConnected()).toBeTruthy();
  expect(scripts.mqttToggle()).toHaveClass("connected");
  expect(scripts.mqttToggle()).not.toHaveClass("disabled");
  expect(scripts.mqttDescription().innerHTML).toEqual(
    "Start Discovery or Click To Disconnect",
  );
});

test("mqttToggleClickEventListener-Error", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = true;
  fetchMock.resetMocks();
  fetchMock.mockReject(new Error("Network error simulated"));
  state = await scripts.mqttToggleClickEventListener();
  expect(scripts.errorMsg().innerHTML).toEqual(
    "Error Toggling MQTT: Error: Network error simulated\n\tname: Error\n\tmessage: Network error simulated",
  );
});

test("discoveryToggleClickEventListener-DiscoveryProcessing", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = true;
  state.Discovered = false;
  fetchMock.resetMocks();
  fetchMock.mockResponseOnce(JSON.stringify(state));
  scripts.setConnected();
  scripts.setDiscoveryProcessing();
  expect(scripts.isDiscoveryProcessing()).toBeTruthy();
  state = await scripts.discoveryToggleClickEventListener();
  expect(scripts.isMQTTProcessing()).toBeFalsy();
  expect(scripts.mqttToggle()).toHaveClass("connected");
  expect(scripts.mqttToggle()).toHaveClass("disabled");
  expect(scripts.isDiscoveryProcessing()).toBeTruthy();
  expect(scripts.discoveryToggle()).not.toHaveClass("discovered");
  expect(scripts.discoveryToggle()).toHaveClass("disabled");
  expect(scripts.discoveryStatus().innerHTML).toEqual("Discovery in process");
  expect(scripts.discoveryDescription().innerHTML).toEqual(
    "Wait until Discovery/Undiscovery complete",
  );
});

test("discoveryToggleClickEventListener-UndiscoveryProcessing", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = true;
  state.Discovered = true;
  fetchMock.resetMocks();
  fetchMock.mockResponseOnce(JSON.stringify(state));
  scripts.setConnected();
  scripts.setDiscovered();
  scripts.setDiscoveryProcessing();
  expect(scripts.isDiscoveryProcessing()).toBeTruthy();
  state = await scripts.discoveryToggleClickEventListener();
  expect(scripts.isMQTTProcessing()).toBeFalsy();
  expect(scripts.mqttToggle()).toHaveClass("connected");
  expect(scripts.mqttToggle()).toHaveClass("disabled");
  expect(scripts.isDiscoveryProcessing()).toBeTruthy();
  expect(scripts.discoveryToggle()).not.toHaveClass("discovered");
  expect(scripts.discoveryToggle()).toHaveClass("disabled");
  expect(scripts.discoveryStatus().innerHTML).toEqual("Discovery in process");
  expect(scripts.discoveryDescription().innerHTML).toEqual(
    "Wait until Discovery/Undiscovery complete",
  );
});

test("discoveryToggleClickEventListener-Disconnected", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = false;
  fetchMock.resetMocks();
  fetchMock.mockResponseOnce(JSON.stringify(state));
  scripts.setDisconnected();
  expect(scripts.isDiscoveryProcessing()).toBeFalsy();
  state = await scripts.discoveryToggleClickEventListener();
  expect(scripts.isMQTTProcessing()).toBeFalsy();
  expect(scripts.mqttToggle()).not.toHaveClass("connected");
  expect(scripts.mqttToggle()).toHaveClass("disconnected");
  expect(scripts.isDiscoveryProcessing()).toBeFalsy();
  expect(scripts.discoveryToggle()).not.toHaveClass("discovered");
  expect(scripts.discoveryToggle()).toHaveClass("disabled");
  expect(scripts.discoveryStatus().innerHTML).toEqual("Not discovered");
  expect(scripts.discoveryDescription().innerHTML).toEqual(
    "MQTT must be connected first",
  );
});

test("discoveryToggleClickEventListener-OK", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = true;
  state.Discovered = true;
  fetchMock.resetMocks();
  fetchMock.mockResponseOnce(JSON.stringify(state));
  scripts.setConnected();
  expect(scripts.isDiscoveryProcessing()).toBeFalsy();
  state = await scripts.discoveryToggleClickEventListener();
  expect(scripts.isMQTTProcessing()).toBeFalsy();
  expect(scripts.mqttToggle()).toHaveClass("connected");
  expect(scripts.isDiscoveryProcessing()).toBeFalsy();
  expect(scripts.discoveryToggle()).toHaveClass("discovered");
  expect(scripts.discoveryToggle()).not.toHaveClass("disabled");
  expect(scripts.discoveryStatus().innerHTML).toEqual("Discovered");
  expect(scripts.discoveryDescription().innerHTML).toEqual(
    "Click to Undiscover",
  );
});

test("discoveryToggleClickEventListener-Error", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = true;
  scripts.setConnected();
  fetchMock.resetMocks();
  fetchMock.mockReject(new Error("Network error simulated"));
  state = await scripts.discoveryToggleClickEventListener();
  expect(scripts.errorMsg().innerHTML).toEqual(
    "Error toggling Discovery: Error: Network error simulated\n\tname: Error\n\tmessage: Network error simulated",
  );
});
