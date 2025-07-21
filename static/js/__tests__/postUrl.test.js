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

test("postUrl-OK", async () => {
  const scripts = await import("../scripts.js");
  const state = JSON.parse(JSON.stringify(STATE));
  const returnState = await scripts.postUrl("/mqtt-toggle", state);
  expect(returnState).toEqual({
    Connected: false,
    Discovered: false,
    Error: [],
    rc: 0,
  });
});

test("postUrl-Error", async () => {
  const scripts = await import("../scripts.js");
  fetchMock.resetMocks();
  let state = JSON.parse(JSON.stringify(STATE));
  state.Error = ["Error"];
  fetchMock.mockResponseOnce(JSON.stringify(state));
  expect(state).toEqual({
    Connected: false,
    Discovered: false,
    Error: ["Error"],
    rc: 0,
  });
  const returnState = await scripts.postUrl("/mqtt-toggle", state);
  expect(returnState).toEqual({
    Connected: false,
    Discovered: false,
    Error: ["Error"],
    rc: 0,
  });
});
