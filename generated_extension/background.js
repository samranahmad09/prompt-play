/*
  QR Link - Background Service Worker (MV3)
  Minimal: logs install/update and keeps service worker warm when needed.
*/
'use strict';

chrome.runtime.onInstalled.addListener((details) => {
  console.log('QR Link installed/updated:', details.reason);
});
