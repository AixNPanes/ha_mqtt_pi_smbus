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
  fetchMock.mockResponse(JSON.stringify(STATE));
  document.body.innerHTML = DOCUMENT_BODY_INNERHTML;
});

afterEach(() => {
  jest.resetModules();
  fetch.resetMocks();
});

test("init", async () => {
  const domInit = jest.fn(() => Promise.resolve());
  const onUpdate = jest.fn();
  const onMqttClick = jest.fn();
  const onDiscoveryClick = jest.fn();

  const scripts = await import("../scripts.js");

  await scripts.init({
    domInit,
    onUpdate,
    onMqttClick,
    onDiscoveryClick,
  });

  document.dispatchEvent(new Event("DOMContentLoaded"));

  document.getElementById("mqtt-toggle").click();
  document.getElementById("discovery-toggle").click();

  expect(domInit).toHaveBeenCalled();
  expect(onUpdate).toHaveBeenCalled();
  expect(onMqttClick).toHaveBeenCalled();
  expect(onDiscoveryClick).toHaveBeenCalled();
});
