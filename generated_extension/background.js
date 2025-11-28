(function(){
  const STATE_KEY = 'deepworkEnabled';
  const START_KEY = 'deepworkStartTime';
  const RULES = [
    { id: 1001, priority: 1, action: { type: 'block' }, condition: { urlFilter: '||facebook.com^', resourceTypes: ['main_frame','sub_frame'] } },
    { id: 1002, priority: 1, action: { type: 'block' }, condition: { urlFilter: '||instagram.com^', resourceTypes: ['main_frame','sub_frame'] } },
    { id: 1003, priority: 1, action: { type: 'block' }, condition: { urlFilter: '||reddit.com^', resourceTypes: ['main_frame','sub_frame'] } }
  ];

  let listenersBound = false;

  async function setBadge(enabled){
    try {
      await chrome.action.setBadgeText({ text: enabled ? 'ON' : '' });
      await chrome.action.setBadgeBackgroundColor({ color: enabled ? '#7c4dff' : '#000000' });
    } catch(e){}
  }

  function now(){ return Date.now(); }

  function minutesBetween(start, end){ return Math.max(0, Math.round((end - start) / 60000)); }

  async function updateRules(enable){
    try {
      await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: RULES.map(r=>r.id) });
      if(enable){ await chrome.declarativeNetRequest.updateDynamicRules({ addRules: RULES }); }
    } catch(e){ /* ignore */ }
  }

  async function muteAllExcept(activeId){
    try {
      const tabs = await chrome.tabs.query({});
      await Promise.all(tabs.map(t => {
        const muted = (t.id !== activeId);
        if(t.id == null) return Promise.resolve();
        return chrome.tabs.update(t.id, { muted }).catch(()=>{});
      }));
    } catch(e){}
  }

  async function unmuteAll(){
    try {
      const tabs = await chrome.tabs.query({});
      await Promise.all(tabs.map(t => chrome.tabs.update(t.id, { muted: false }).catch(()=>{})));
    } catch(e){}
  }

  async function insertCSSAllTabs(){
    const tabs = await chrome.tabs.query({ url: ['http://*/*','https://*/*'] });
    await Promise.all(tabs.map(t => chrome.scripting.insertCSS({ target: { tabId: t.id, allFrames: true }, files: ['styles.css'] }).catch(()=>{})));
  }

  async function removeCSSAllTabs(){
    const tabs = await chrome.tabs.query({ url: ['http://*/*','https://*/*'] });
    await Promise.all(tabs.map(t => chrome.scripting.removeCSS({ target: { tabId: t.id, allFrames: true }, files: ['styles.css'] }).catch(()=>{})));
  }

  async function broadcastDark(enabled){
    try {
      const tabs = await chrome.tabs.query({ url: ['http://*/*','https://*/*'] });
      await Promise.all(tabs.map(t => chrome.tabs.sendMessage(t.id, { type: 'deepwork:applyDark', enabled }).catch(()=>{})));
    } catch(e){}
  }

  async function enable(){
    await updateRules(true);
    const [active] = await chrome.tabs.query({ active: true, currentWindow: true });
    await muteAllExcept(active ? active.id : -1);
    bindListeners();
    await insertCSSAllTabs();
    await broadcastDark(true);
    await setBadge(true);
    await new Promise(res=> chrome.storage.local.set({ [STATE_KEY]: true, [START_KEY]: now() }, res));
    chrome.runtime.sendMessage({ type:'deepwork:state', enabled: true });
  }

  async function disable(){
    await updateRules(false);
    await unmuteAll();
    unbindListeners();
    await broadcastDark(false);
    await removeCSSAllTabs();
    await setBadge(false);

    const data = await new Promise(res=> chrome.storage.local.get([START_KEY], res));
    const start = data[START_KEY] || now();
    const mins = minutesBetween(start, now());
    await new Promise(res=> chrome.storage.local.set({ [STATE_KEY]: false, [START_KEY]: null }, res));

    try {
      chrome.notifications.create('deepwork-summary-' + Date.now(), {
        type: 'basic',
        iconUrl: 'icon.svg',
        title: 'Focus Session Complete',
        message: `You focused for ${mins} minutes`,
        priority: 2
      });
    } catch(e){}

    chrome.runtime.sendMessage({ type:'deepwork:state', enabled: false });
  }

  function onActivated(activeInfo){
    chrome.tabs.get(activeInfo.tabId, (tab)=>{
      if(chrome.runtime.lastError) return;
      muteAllExcept(tab?.id);
    });
  }

  function onCreated(tab){
    // Ensure new tabs start muted unless they are active
    chrome.tabs.query({ active: true, currentWindow: true }).then(([active])=>{
      const shouldMute = !active || tab.id !== active.id;
      if(tab.id != null) chrome.tabs.update(tab.id, { muted: shouldMute }).catch(()=>{});
    }).catch(()=>{});
  }

  function onUpdated(tabId, changeInfo, tab){
    if(changeInfo.status === 'complete'){
      // Re-apply CSS and dark overlay to refreshed pages
      chrome.storage.local.get([STATE_KEY], (res)=>{
        if(res[STATE_KEY]){
          chrome.scripting.insertCSS({ target: { tabId, allFrames: true }, files: ['styles.css'] }).catch(()=>{});
          chrome.tabs.sendMessage(tabId, { type: 'deepwork:applyDark', enabled: true }).catch(()=>{});
        }
      });
    }
  }

  function bindListeners(){
    if(listenersBound) return;
    chrome.tabs.onActivated.addListener(onActivated);
    chrome.tabs.onCreated.addListener(onCreated);
    chrome.tabs.onUpdated.addListener(onUpdated);
    listenersBound = true;
  }

  function unbindListeners(){
    if(!listenersBound) return;
    try { chrome.tabs.onActivated.removeListener(onActivated); } catch(e){}
    try { chrome.tabs.onCreated.removeListener(onCreated); } catch(e){}
    try { chrome.tabs.onUpdated.removeListener(onUpdated); } catch(e){}
    listenersBound = false;
  }

  chrome.runtime.onMessage.addListener((msg, sender, sendResponse)=>{
    if(!msg) return;
    if(msg.type === 'deepwork:toggle'){
      (async ()=>{ (msg.enabled ? enable() : disable()); })();
    }
    if(msg.type === 'deepwork:ensureCSS'){
      if(sender.tab && sender.tab.id != null){
        chrome.storage.local.get([STATE_KEY], (res)=>{
          if(res[STATE_KEY]){
            chrome.scripting.insertCSS({ target: { tabId: sender.tab.id, allFrames: true }, files: ['styles.css'] }).catch(()=>{});
          }
        });
      }
    }
  });

  chrome.runtime.onInstalled.addListener(async ()=>{
    // Initialize state
    await new Promise(res=> chrome.storage.local.set({ [STATE_KEY]: false, [START_KEY]: null }, res));
    setBadge(false);
  });

  chrome.runtime.onStartup.addListener(async ()=>{
    // Restore if previously enabled
    const data = await new Promise(res=> chrome.storage.local.get([STATE_KEY], res));
    if(data[STATE_KEY]){
      // Re-apply everything
      await enable();
      // Keep original start time if it exists
      const s = await new Promise(res=> chrome.storage.local.get([START_KEY], res));
      if(!s[START_KEY]){ await new Promise(res=> chrome.storage.local.set({ [START_KEY]: now() }, res)); }
    }
  });
})();