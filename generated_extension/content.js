(function(){
  const STATE_KEY = 'deepworkEnabled';

  function applyDark(enabled){
    try {
      const root = document.documentElement;
      const body = document.body || document.documentElement;
      if(enabled){
        root.classList.add('deepwork-dark');
        body.classList.add('deepwork-dark');
        if(!document.getElementById('deepwork-veil')){
          const veil = document.createElement('div');
          veil.id = 'deepwork-veil';
          document.documentElement.appendChild(veil);
        }
        if(!document.getElementById('deepwork-banner')){
          const banner = document.createElement('div');
          banner.id = 'deepwork-banner';
          banner.innerHTML = '<strong>Deep Work</strong> is active';
          document.documentElement.appendChild(banner);
        }
      } else {
        root.classList.remove('deepwork-dark');
        body.classList.remove('deepwork-dark');
        const v = document.getElementById('deepwork-veil');
        if(v) v.remove();
        const b = document.getElementById('deepwork-banner');
        if(b) b.remove();
      }
    } catch(e) { /* ignore */ }
  }

  // React to background messages
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse)=>{
    if(!msg) return;
    if(msg.type === 'deepwork:applyDark'){
      applyDark(!!msg.enabled);
    }
  });

  // On load: if enabled, ensure CSS is injected and apply immediately
  chrome.storage.local.get([STATE_KEY], (res)=>{
    const enabled = !!res[STATE_KEY];
    if(enabled){
      applyDark(true);
      try { chrome.runtime.sendMessage({type:'deepwork:ensureCSS'}); } catch(e){}
    }
  });
})();