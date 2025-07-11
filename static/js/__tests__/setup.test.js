import '@testing-library/jest-dom';

fetchMock.enableMocks();

//import * as scripts from '../scripts.js';

beforeEach(() => {
  jest.resetModules();
  fetchMock.resetMocks();
  fetchMock.mockResponseOnce(JSON.stringify({
    Connected: false,
    Discovered: false,
    rc: 0,
    Error: []
  }));
  
  document.body.innerHTML = `
    <div class="error-msg">
      <span id="error_msg>&nbsp;</span>
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

test('MQTTStatus', async () => {
  const scripts = await import('../scripts.js');
  expect(scripts.MQTTStatus.DISCONNECTED).toEqual('disconnected');
  expect(scripts.MQTTStatus.PROCESSING).toEqual('processing');
  expect(scripts.MQTTStatus.CONNECTED).toEqual('connected');
});

test('DiscoveryStatus', async () => {
  const scripts = await import('../scripts.js');
  expect(scripts.DiscoveryStatus.UNDISCOVERED).toEqual('undiscovered');
  expect(scripts.DiscoveryStatus.PROCESSING).toEqual('processing');
  expect(scripts.DiscoveryStatus.DISCOVERED).toEqual('discovered');
});
