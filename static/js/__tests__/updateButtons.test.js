
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

test("checkStateError-OK-not-connected", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  let state = scripts.checkStateError(STATE);
  expect(scripts.mqttToggle()).not.toHaveClass('disabled');
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("checkStateError-Error", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  let state = JSON.parse(JSON.stringify(STATE));
  state.Error = ['Error'];
  let checkstate = scripts.checkStateError(state);
  expect(scripts.mqttToggle()).toHaveClass('disabled');
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("checkStateError-Discovered-not-Connected", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  let state = JSON.parse(JSON.stringify(STATE));
  state.Discovered = true;
  let checkstate = scripts.checkStateError(state);
  expect(scripts.mqttToggle()).toHaveClass('disabled');
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("fetchStatus", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  let state = scripts.fetchStatus();
  expect(scripts.mqttToggle()).not.toHaveClass('disabled');
  expect(scripts.discoveryToggle()).toHaveClass('disabled');
});

test("updateButtonsFromStatus-OK", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  scripts.setConnected();
  fetchMock.resetMocks();
  const stat = JSON.parse(JSON.stringify(STATE));
  stat.Connected = true;
  fetchMock.mockResponseOnce(JSON.stringify(stat));
  let state = await scripts.updateButtonsFromStatus();
  expect(scripts.errorMsg().textContent).toEqual('\u00a0');
});
