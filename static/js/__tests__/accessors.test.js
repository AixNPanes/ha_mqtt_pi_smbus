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

test("mqttToggle", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.mqttToggle()).toHaveClass("disconnected");
});

test("mqttStatus", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.mqttStatus().textContent).toEqual("Not Connected");
});

test("mqttDescription", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.mqttDescription().textContent).toEqual("Click to connect");
});

test("discoveryToggle", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.discoveryToggle()).toHaveClass("undiscovered");
});

test("discoveryStatus", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.discoveryStatus().textContent).toEqual("Not discovered");
});

test("discoveryDescription", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.discoveryDescription().textContent).toEqual(
    "Click to start Discovery",
  );
});

test("errorMsg", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.errorMsg().textContent).toEqual("\u00a0");
});

test("isConnected", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.isConnected()).toBeFalsy();
});

test("isMQTTProcessing", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.isMQTTProcessing()).toBeFalsy();
});

test("isDisconnected", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.isDisconnected()).toBeTruthy();
});

test("isDiscovered", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.isDiscovered()).toBeFalsy();
});

test("isDiscoveryProcessing", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.isDiscoveryProcessing()).toBeFalsy();
});

test("isUndiscovered", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.isUndiscovered()).toBeTruthy();
});

test("getState", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.getState([]).Connected).toBeFalsy();
  expect(scripts.getState([]).Discovered).toBeFalsy();
  expect(scripts.getState([]).Error).toEqual([]);
});

test("getStatus-OK", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.getStatus(scripts.mqttToggle())).toEqual("disconnected");
});

test("getStatus-DiscoveryStatus", async () => {
  const scripts = await import("../scripts.js");
  expect(scripts.getStatus(scripts.discoveryToggle())).toEqual("undiscovered");
});

test("getStatus-extra-classes", async () => {
  const scripts = await import("../scripts.js");
  scripts
    .mqttToggle()
    .classList.add(
      scripts.MQTTStatus.DISCONNECTED,
      scripts.MQTTStatus.CONNECTED,
    );
  expect(() => scripts.getStatus(scripts.mqttToggle())).toThrow(
    new Error("Invalid status for toggle: disconnected,connected"),
  );
});

test("getStatus-no-classes", async () => {
  const scripts = await import("../scripts.js");
  scripts.mqttToggle().className = "";
  expect(scripts.getStatus(scripts.mqttToggle())).toEqual("disconnected");
});
