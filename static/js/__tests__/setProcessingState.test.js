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
  fetch.resetMocks();
});

test("setMqttProcessingState-Connecting", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  fetchMock.resetMocks();
  scripts.setMQTTProcessingState();
  expect(scripts.mqttToggle()).toHaveClass("disabled");
  expect(scripts.mqttStatus().textContent).toEqual("Connection in process");
  expect(scripts.isMQTTProcessing()).toBeTruthy();
  expect(scripts.isConnected()).toBeFalsy();
});

test("setMqttProcessingState-Disconnecting", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  scripts.setConnected();
  expect(scripts.isConnected()).toBeTruthy();
  fetchMock.resetMocks();
  scripts.setMQTTProcessingState();
  expect(scripts.mqttToggle()).toHaveClass("disabled");
  expect(scripts.mqttStatus().textContent).toEqual("Disconnection in process");
  expect(scripts.isMQTTProcessing()).toBeTruthy();
  expect(scripts.isConnected()).toBeFalsy();
});

test("setDiscoveryProcessingState-Discovering", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  scripts.setConnected();
  fetchMock.resetMocks();
  scripts.setDiscoveryProcessingState();
  expect(scripts.isMQTTProcessing()).toBeFalsy();
  expect(scripts.isConnected()).toBeTruthy();
  expect(scripts.discoveryToggle()).toHaveClass("disabled");
  expect(scripts.discoveryStatus().textContent).toEqual("Discovery in process");
  expect(scripts.isDiscoveryProcessing()).toBeTruthy();
  expect(scripts.isDiscovered()).toBeFalsy();
});

test("setDiscoveryProcessingState-Undisconnecting", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  scripts.setConnected();
  scripts.setDiscovered();
  expect(scripts.isConnected()).toBeTruthy();
  fetchMock.resetMocks();
  scripts.setDiscoveryProcessingState();
  expect(scripts.isMQTTProcessing()).toBeFalsy();
  expect(scripts.isConnected()).toBeTruthy();
  expect(scripts.discoveryToggle()).toHaveClass("disabled");
  expect(scripts.discoveryStatus().textContent).toEqual(
    "Un-Discovery in process",
  );
  expect(scripts.isDiscoveryProcessing()).toBeTruthy();
  expect(scripts.isDiscovered()).toBeFalsy();
});
