Deep Work - Chrome Extension (Manifest V3)

Overview
- A single toggle activates Deep Work mode: blocks Facebook, Instagram, and Reddit; mutes all tabs except the active one; applies a dark grey page theme; logs start time; and shows a completion notification when disabled.
- Built with vanilla JavaScript and CSS. No external libraries.

How it works
1) Blocking: Uses declarativeNetRequest dynamic rules to block facebook.com, instagram.com, and reddit.com while enabled.
2) Muting: Mutes every tab except the active one. Listeners keep it enforced for tab activation/creation/refresh.
3) Dark Theme: Injects styles.css into tabs and toggles a dark overlay via content script. This simulates a browser-wide dark grey theme on pages (Chrome’s actual UI theme can’t be programmatically changed by regular extensions).
4) Timer + Notification: Start time stored on enable; on disable, shows a notification: “You focused for X minutes”.

Install
1) Save all files as provided in this JSON to a folder.
2) Open chrome://extensions
3) Enable Developer mode (top-right).
4) Load unpacked -> select the folder.

Usage
- Click the extension icon to open the popup.
- Toggle the switch to turn Deep Work ON/OFF.
- Optional: Use the “Active Tab Audio” button to quickly unmute/mute the active tab if you want to hear it during Deep Work.

Notes & Limitations
- Theme: Regular extensions cannot change the Chrome UI theme. This extension darkens web pages instead by injecting CSS and a soft overlay.
- File URLs: For file:// pages, Chrome requires extra user permission (chrome://extensions -> allow access to file URLs) for the dark overlay to work.
- Audio: Sites that programmatically unmute themselves may briefly play; listeners re-enforce muting.

Permissions
- declarativeNetRequest: Runtime blocking of specific sites.
- tabs: Mute/unmute tabs and query active tab.
- scripting: Inject/remove CSS into pages.
- storage: Save enabled state and timer.
- notifications: Show focus session summary.

Structure
- popup.html: UI with a neon glassmorphism design and a toggle switch.
- styles.css: All UI and content styling, including animations and dark overlay.
- popup.js: Handles toggle state and minimal UI interactions.
- background.js: Core logic (blocking, muting, CSS injection, time logging, notification).
- content.js: Applies/removes dark overlay on pages; ensures CSS is present after reloads; responds to messages.
- icon.svg: Vector cyberpunk brain/icon.

Customization
- To add more blocked sites, extend RULES in background.js and add more dynamic rules with unique IDs.
- Adjust visual theme by editing CSS variables at the top of styles.css.

Troubleshooting
- If some pages don’t darken after enabling, reload the page; content script will request CSS injection again.
- If the notification doesn’t appear on disable, ensure notifications are allowed for your browser profile.
