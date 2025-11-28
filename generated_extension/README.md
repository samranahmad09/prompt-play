QR Link - Chrome Extension (MV3)

Description
- Click the extension icon to open a sleek cyberpunk popup that automatically reads the active tab URL and generates a QR code using goqr.me (https://api.qrserver.com/v1/create-qr-code/).
- The QR is centered prominently with the URL displayed below. Includes Copy and Download actions.

Features
- Auto-detect active tab URL on popup open.
- Instant QR generation via remote image (no libraries).
- Modern dark/cyberpunk glass UI, neon accents, animated entrance, hover transforms, focus glows.
- Copy URL to clipboard, Download QR as PNG, Open URL in new tab.

How it works
- popup.js queries chrome.tabs for the active tab (requires activeTab/tabs). It builds a QR image URL and sets it as <img src>.
- No content script interaction is needed now (stub included for future use).

Install (Developer Mode)
1. Download the folder contents as-is.
2. Visit chrome://extensions in Chrome.
3. Enable Developer mode (top right).
4. Click "Load unpacked" and select the folder containing manifest.json and files.
5. Pin the extension and click the icon to use.

Permissions
- activeTab: Grants temporary access to the active tab when you click the extension.
- tabs: Allows reading the URL field of the active tab.
- host_permissions: https://api.qrserver.com/* to fetch the QR image.

Notes
- Some internal pages (chrome://, chrome Web Store) may restrict access to their URL. The popup will still attempt to display any available URL, but if it cannot, a message will be shown.
- If the QR fails to load (rare), use the refresh button in the popup.

Customization
- To change QR size, edit QR_SIZE in popup.js (default 280px) and CSS .qr-img width if desired.
- Theme colors can be updated via CSS variables at the top of styles.css.

Privacy
- No analytics or tracking. The current tab URL is sent only to the QR generation service to render an image.

License
- For demo purposes. Icons and UI are original and free to use for this extension.
