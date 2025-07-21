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

test("handleMqttTogglePost-Connected", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = true;
  state = scripts.handleMqttTogglePost(state);
  expect(scripts.mqttToggle()).toHaveClass("connected");
  expect(scripts.discoveryToggle()).toHaveClass("undiscovered");
});

test("handleMqttTogglePost-Disconnected", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = false;
  state = scripts.handleMqttTogglePost(state);
  expect(scripts.mqttToggle()).toHaveClass("disconnected");
  expect(scripts.discoveryToggle()).toHaveClass("undiscovered");
});

test("handleDiscoveryTogglePost-Discovered", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = true;
  state.Discovered = true;
  state = scripts.handleDiscoveryTogglePost(state);
  expect(scripts.mqttToggle()).toHaveClass("connected");
  expect(scripts.discoveryToggle()).toHaveClass("discovered");
});

test("handleDiscoveryTogglePost-Undiscovered", async () => {
  const scripts = await import("../scripts.js");
  let state = JSON.parse(JSON.stringify(STATE));
  state.Connected = true;
  state.Discovered = false;
  state = scripts.handleDiscoveryTogglePost(state);
  expect(scripts.mqttToggle()).toHaveClass("connected");
  expect(scripts.discoveryToggle()).toHaveClass("undiscovered");
});
