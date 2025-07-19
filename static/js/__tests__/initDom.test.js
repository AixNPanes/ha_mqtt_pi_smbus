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

test("initDom-Disconnected-Undiscovered", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  fetchMock.resetMocks();
  const stat = JSON.parse(JSON.stringify(STATE));
  fetchMock.mockResponseOnce(JSON.stringify(stat));
  const state = await scripts.initDom();
  expect(state).toEqual({"Connected": false, "Discovered": false, "Error": []});	
  expect(scripts.getState([]).Connected).toBeFalsy();	
  expect(scripts.getState([]).Discovered).toBeFalsy();	
  expect(scripts.errorMsg().textContent).toEqual('\u00a0');
  expect(scripts.mqttToggle()).not.toHaveClass('connected');
  expect(scripts.discoveryToggle()).not.toHaveClass('discovered');
});

test("initDom-Connected-Undiscovered", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  scripts.setConnected();
  fetchMock.resetMocks();
  const stat = JSON.parse(JSON.stringify(STATE));
  stat.Connected = true;
  fetchMock.mockResponseOnce(JSON.stringify(stat));
  const state = await scripts.initDom();
  expect(scripts.errorMsg().textContent).toEqual('\u00a0');
  expect(scripts.mqttToggle()).toHaveClass('connected');
  expect(scripts.discoveryToggle()).not.toHaveClass('discovered');
});

test("initDom-Connected-Discovered", async () => {
  const scripts = await import("../scripts.js");
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
  scripts.setConnected();
  scripts.setDiscovered();
  fetchMock.resetMocks();
  const stat = JSON.parse(JSON.stringify(STATE));
  stat.Connected = true;
  stat.Discovered = true;
  fetchMock.mockResponseOnce(JSON.stringify(stat));
  const state = await scripts.initDom();
  expect(scripts.errorMsg().textContent).toEqual('\u00a0');
  expect(scripts.mqttToggle()).toHaveClass('connected');
  expect(scripts.discoveryToggle()).toHaveClass('discovered');
});

//test("initDom-Undiscovered", async () => {
//});
