(function(){
  const $ = (sel)=>document.querySelector(sel);
  const switchEl = $('#dwSwitch');
  const chipEl = $('#statusChip');
  const hintEl = $('#dwHint');
  const btnActive = $('#openActive');

  function setUI(enabled){
    switchEl.checked = !!enabled;
    chipEl.textContent = enabled ? 'ON' : 'OFF';
    chipEl.style.background = enabled ? 'linear-gradient(135deg, rgba(0,255,209,.24), rgba(124,77,255,.18))' : 'linear-gradient(135deg, rgba(124,77,255,.24), rgba(0,255,209,.18))';
    hintEl.textContent = enabled ? 'Deep Work is ON. Distracting sites blocked, other tabs muted, pages darkened.' : 'Toggle to enter Deep Work mode.';
  }

  function getState(){
    return new Promise((resolve)=>{
      chrome.storage.local.get(['deepworkEnabled'], (res)=> resolve(!!res.deepworkEnabled));
    });
  }

  async function init(){
    const enabled = await getState();
    setUI(enabled);

    switchEl.addEventListener('change', ()=>{
      const enabled = switchEl.checked;
      chrome.runtime.sendMessage({type:'deepwork:toggle', enabled});
      setUI(enabled);
    });

    btnActive.addEventListener('click', async ()=>{
      // Quick: toggle mute state of current tab only (for users who want to let a second tab speak)
      let [tab] = await chrome.tabs.query({active:true, currentWindow:true});
      if(!tab) return;
      chrome.tabs.update(tab.id, {muted: !tab.mutedInfo?.muted});
    });

    chrome.runtime.onMessage.addListener((msg)=>{
      if(msg && msg.type==='deepwork:state'){ setUI(!!msg.enabled); }
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();