Aegis Adblock (MV3)

Overview
- MV3 declarativeNetRequest-based adblocker. Ships with a small static ruleset for common trackers and supports dynamic updates from public lists (StevenBlack hosts or EasyPrivacy).
- Popup UI: toggle protection, see blocked counters, update list, whitelist current site, view rule stats. Modern cyberpunk/glass dark UI with red-pink gradient; no external libraries.

How it blocks
- Static rules: Provided in rules/static_rules.json. Enabled/disabled via updateEnabledRulesets.
- Dynamic rules: Fetched by background.js from a selected source and converted to DNR rules (block third-party requests). Limited to ~1500 to respect dynamic rule caps/performance.
- Counters: Uses declarativeNetRequest.onRuleMatchedDebug to count blocks, stored in chrome.storage.local.

Permissions
- declarativeNetRequest, declarativeNetRequestWithHostAccess, declarativeNetRequestFeedback: blocking + counters + dynamic rule updates.
- host_permissions: <all_urls> so the rules can match network requests and to fetch lists cross-origin.
- storage: store settings and counters. tabs/activeTab: used by the popup to get current site for whitelisting.

UI usage
- Protection toggle: Enables/disables the static ruleset; dynamic rules are cleared when disabled and retained when re-enabled.
- Update List: Pulls a public tracker list and converts it to dynamic rules (takes a few seconds). Last update timestamp is displayed.
- Whitelist This Site: Adds a high-priority allow rule for the current site's initiator domain.
- Reset Counters: Zeroes session and total counters.
- View Rules: Shows a quick count of enabled static and dynamic rules.

Notes
- Blocking rules use thirdParty domainType to reduce breakage.
- Some lists may change format or be rate-limited; if fetching fails, try again later or switch source.
- The included static rules cover many common ad/analytics networks; for maximal coverage, use dynamic updates.

Install
1) Save the files to a folder, preserving the rules/ subfolder.
2) Visit chrome://extensions, enable Developer mode.
3) Click Load unpacked and select the folder.
4) Pin Aegis Adblock and click its icon to open the popup.

License
- Rules derived from public sources (StevenBlack hosts, EasyPrivacy) are subject to their respective licenses.
