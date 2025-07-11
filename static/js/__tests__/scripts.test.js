/**
 * @jest-environment jsdom
 */

import '@testing-library/jest-dom';
import fetchMock from 'jest-fetch-mock';

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

test('MQTTStatus constants are correct', async () => {
  const scripts = await import('../scripts.js');
  expect(scripts.MQTTStatus.DISCONNECTED).toBe('disconnected');
  expect(scripts.MQTTStatus.PROCESSING).toBe('processing');
  expect(scripts.MQTTStatus.CONNECTED).toBe('connected');
});

test('DiscoveryStatus constants are correct', async () => {
  const scripts = await import('../scripts.js');
  expect(scripts.DiscoveryStatus.UNDISCOVERED).toBe('undiscovered');
  expect(scripts.DiscoveryStatus.PROCESSING).toBe('processing');
  expect(scripts.DiscoveryStatus.DISCOVERED).toBe('discovered');
});

test('updateButtonsFromStatus disables discovery when not connected', async () => {
  const scripts = await import('../scripts.js');

  fetchMock.mockResponseOnce(JSON.stringify({
    Connected: false,
    Discovered: false,
    Error: []
  }));

  await scripts.updateButtonsFromStatus();

  expect(document.getElementById('discovery-toggle').classList.contains('disabled')).toBe(true);
});

test('mqttToggleClickEventListener sends fetch POST', async () => {
  const scripts = await import('../scripts.js');

  // Initially: simulate the toggle is disconnected
  const toggle = document.getElementById('mqtt-toggle');
  toggle.classList.remove('connected');
  toggle.classList.add('disconnected');

  fetchMock.mockResponseOnce(JSON.stringify({
    Connected: true,
    Discovered: false,
    Error: []
  }));

  scripts.mqttToggleClickEventListener();

  // Let the promise resolve
  await new Promise(r => setTimeout(r, 10));

  expect(fetchMock).toHaveBeenCalledWith('/mqtt-toggle', expect.objectContaining({
    method: 'POST'
  }));
});

