'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const labels = {open:'Open',closed:'Closed',collect:'Gathering details',review:'Plan review',intake:'Planning',investigated:'Options review',feedback:'Preference recorded',paused:'Paused',pending:'Queued',processing:'Processing',done:'Processed',received:'Received',sent:'Sent to Telegram',sending:'Sending',unknown:'Delivery uncertain',failed:'Failed',cancelled:'Cancelled',held:'Held',approval:'Needs approval',operator_pending:'Awaiting operator',succeeded:'Recorded success',rejected:'Rejected',expired:'Expired'};
  const human = s => labels[s] || String(s || 'Not recorded').replaceAll('_',' ');
  const date = seconds => seconds ? new Date(seconds * 1000).toLocaleString('en-IN',{timeZone:'Asia/Kolkata',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}) + ' IST' : 'Time not recorded';
  const money = paise => new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:2}).format(paise / 100);
  function el(tag, text, cls) { const node=document.createElement(tag); if(text!==undefined)node.textContent=text; if(cls)node.className=cls; return node; }
  function empty(target,text){ target.replaceChildren(el('p',text,'empty')); }
  function badge(text, warning=false){ return el('span',text,'badge'+(warning?' warn':'')); }
  function card(title,body,status){const node=el('article',undefined,'card');if(status)node.append(badge(status));node.append(el('h3',title),el('p',body));return node;}
  function facts(node,data){const dl=el('dl');for(const [key,value] of Object.entries(data)){dl.append(el('dt',key.replaceAll('_',' ')),el('dd',value || 'Not recorded'));}node.append(dl);}
  function detail(node,title,data){const d=el('details');d.append(el('summary',title),el('pre',JSON.stringify(data,null,2)));node.append(d);}
  let token='', selection=null, snapshot=null, timer=null, controller=null, epoch=0, lastSuccess=0, lastSignature='', listSignature='', failure=false;
  function freshness(){
    if(!token)return;
    const age=lastSuccess?Math.max(0,Math.floor((Date.now()-lastSuccess)/1000)):null;
    $('connection').textContent=document.hidden?'Updates paused':failure?'Connection interrupted':age===null?'Connecting…':age>20?'Snapshot stale':'Connected';
    $('connection').className='badge '+(!failure&&age!==null&&age<=20&&!document.hidden?'ok':'warn');
    $('freshness').textContent=age===null?'Waiting for the backend; it may need to wake up.':`Last successful sync ${age}s ago. ${document.hidden?'Return to this tab to refresh.':failure?'Showing the last known state.':'Reading persisted Telegram activity.'}`;
  }
  function reset(){epoch++;token='';selection=null;snapshot=null;lastSuccess=0;lastSignature='';listSignature='';failure=false;clearTimeout(timer);controller?.abort();controller=null;$('token').value='';$('connect').hidden=false;$('dashboard').hidden=true;$('welcome').hidden=false;$('error').hidden=true;$('connection').textContent='Disconnected';$('connection').className='badge';$('freshness').textContent='Connect to view the latest recorded state.';$('connect-button').disabled=false;for(const id of ['conversations','messages','decisions','activity','metrics'])$(id).replaceChildren();$('title').textContent='Nothing to track yet';$('context').textContent='Send a message in Telegram to begin.';}
  function conversationList(){
    if(!snapshot)return;
    const list=$('conversations'), q=$('search').value.toLowerCase(), filter=$('scope').value;
    const nextList=JSON.stringify([snapshot.conversations,selection,q,filter]);
    if(nextList===listSignature)return;listSignature=nextList;
    const rows=snapshot.conversations.filter(c=>(filter==='all'||c.scope===filter)&&`${c.title} ${c.chat}`.toLowerCase().includes(q));
    list.replaceChildren();$('conversation-count').textContent=snapshot.conversations.length+(snapshot.conversations_truncated?'+':'');
    for(const c of rows){const b=el('button',undefined,'conversation');b.type='button';b.setAttribute('aria-pressed',String(selection?.scope===c.scope&&selection?.chat===c.chat));b.append(el('small',c.scope==='demo'?'FICTIONAL REHEARSAL':'WEDDING WORKSPACE'),el('strong',c.title||'Getting started'),el('small',`Chat ${c.chat} · ${human(c.stage)}`));b.addEventListener('click',()=>{selection={scope:c.scope,chat:c.chat};lastSignature='';controller?.abort();epoch++;empty($('messages'),'Loading selected conversation…');empty($('decisions'),'Loading decisions…');empty($('activity'),'Loading activity…');$('metrics').replaceChildren();$('title').textContent=c.title||'Getting started';$('mode').textContent=c.scope==='demo'?'FICTIONAL REHEARSAL':'WEDDING WORKSPACE';$('context').textContent='Loading current state…';conversationList();refresh();});list.append(b);}
    if(!rows.length)empty(list,'No matching conversations.');
  }
  function metric(label,value,note){const node=el('div',undefined,'metric');node.append(el('span',label),el('strong',String(value)),el('small',note));return node;}
  function render(data){
    snapshot=data;selection=data.selected?{scope:data.selected.scope,chat:data.selected.chat}:null;
    $('connect').hidden=true;$('welcome').hidden=true;$('dashboard').hidden=false;
    $('runtime').textContent=`Telegram ${data.transport} · ${data.telegram_configured?'Bot configured':'Bot not configured'} · ${data.model_configured?'Model configured':'Model not configured'}${data.free_host?' · Free host: checks can be delayed after sleep':''}`;
    conversationList();
    const signature=JSON.stringify([data.selected,data.messages,data.operations,data.decisions,data.evidence,data.commitment,data.intake,data.processing,data.delivery,data.voice,data.history_limited,data.commitment?.next_check<data.generated_at,data.operations.map(op=>op.expires<data.generated_at)]);
    if(signature===lastSignature)return;lastSignature=signature;
    const demo=data.selected?.scope==='demo', c=data.commitment;
    $('mode').textContent=demo?'FICTIONAL REHEARSAL · NO REAL ACTIONS':'WEDDING WORKSPACE';
    $('title').textContent=data.selected?.title||'Nothing to track yet';
    $('context').textContent=data.selected?`Chat ${data.selected.chat} · ${demo?'Preferences and scenario choices do not authorise spending.':'Approval, partner execution and outcome verification are tracked separately.'}`:'Send a message in Telegram to begin.';
    const pending=(data.processing.pending||0)+(data.processing.processing||0), uncertain=(data.delivery.unknown||0)+(data.delivery.failed||0);
    $('metrics').replaceChildren(metric('Current stage',demo?human(data.intake?.phase||data.selected.stage):c?(c.paused?'Paused':human(c.state)):'No conversation',demo?'Fictional scenario':c?`Owner: ${c.owner}`:'Waiting for Telegram'),metric('Processing',pending,`${data.processing.failed||0} failed · ${data.processing.held||0} held`),metric('Delivery review',uncertain,`${data.delivery.pending||0} queued · ${data.delivery.sent||0} sent`));
    const msgs=$('messages'), nearBottom=msgs.scrollHeight-msgs.scrollTop-msgs.clientHeight<70, oldScroll=msgs.scrollTop;
    msgs.replaceChildren();
    for(const m of data.messages){const b=el('article',undefined,`message ${m.direction}`);b.append(el('strong',m.direction==='in'?'You · Telegram':`Tarang${m.kind==='voice'?' · Voice reply':''}`),el('p',m.text),el('small',`${date(m.created)} · ${human(m.status)}`));msgs.append(b);}
    if(!data.messages.length)empty(msgs,'No recorded messages for this conversation yet.');
    msgs.scrollTop=nearBottom?msgs.scrollHeight:oldScroll;
    $('history-note').textContent=(data.history_limited?'Showing bounded recent history (up to 100 per record type). ':'')+'Older demo buttons and message timestamps may not have been captured. This is not a complete Telegram archive.';
    const decisions=$('decisions');decisions.replaceChildren();
    if(demo){const intake=data.intake;if(intake){const node=card('The plan so far','Recorded conversational preferences; no vendor action or payment is confirmed.',human(intake.phase));facts(node,intake.facts);if(intake.feedback)node.append(el('p',`Latest preference: ${intake.feedback}`));decisions.append(node);}else decisions.append(card('Guided scenario',`Scenario: ${data.selected.title||'not selected'}. Current step: ${data.selected.stage}. The Telegram transcript contains the simulated choices and outcomes.`,'Simulation only'));if(data.voice){decisions.append(card('Voice transcript',data.voice.transcript||'No transcript recorded.',human(data.voice.status)));}}
    else if(c){decisions.append(card('Outcome & next observation',c.outcome,c.paused?'Paused':human(c.state)));facts(decisions.lastChild,{owner:c.owner,next_check:c.state==='closed'?'Outcome closed; see evidence':c.paused?'Monitoring paused':date(c.next_check)+(c.next_check<data.generated_at?' · Overdue':'')});for(const op of data.operations){const p=op.proposal,node=card(`${human(p.kind)} · ${money(op.amount)}`,p.specification,op.state==='approval'&&op.expires<data.generated_at?'Approval expired · awaiting scheduler':human(op.state));facts(node,{recipient:p.recipient,category:op.category,approval_valid_until:date(op.expires)});node.append(el('small',`Operation #${op.id} · Recorded success requires source evidence; it does not alone close the outcome.`));decisions.append(node);}}
    else empty(decisions,'No decisions recorded yet.');
    const activity=$('activity');activity.replaceChildren();
    for(const e of data.evidence){const node=card(e.source,e.content,e.mode);node.append(el('small',`${date(e.created)} · ${e.verifies?'Attested outcome evidence':'Observation'} · Evidence #${e.id}`));activity.append(node);}
    for(const entry of data.decisions){const d=entry.data, summary=d.runtime_notes?.join('\n')||d.decision?.reason||(d.decision&&typeof d.decision==='string'?d.decision:'Recorded runtime event');const node=card(human(entry.kind),summary);node.append(el('small',date(entry.created)));detail(node,'View recorded details',d);activity.append(node);}
    if(!activity.childNodes.length)empty(activity,demo?'Rehearsal progress is shown in the conversation and plan. There is no real vendor or payment evidence.':'No evidence or decision events recorded yet.');
  }
  async function refresh(){
    clearTimeout(timer);if(!token||document.hidden)return;
    const current=++epoch;controller?.abort();controller=new AbortController();const active=controller;const timeout=setTimeout(()=>active.abort(),25000);
    $('refresh').disabled=true;freshness();
    try{
      const query=selection?'?'+new URLSearchParams(selection):'';
      const response=await fetch('/api/dashboard'+query,{headers:{Authorization:'Bearer '+token},cache:'no-store',signal:active.signal});
      if(current!==epoch)return;
      if(response.status===401||response.status===403){reset();$('error').textContent='Access denied. Enter a valid operator token.';$('error').hidden=false;return;}
      if(!response.ok)throw new Error(response.status===404?'The dashboard API is not available yet. The bot backend and website must both receive this update.':`Backend unavailable (HTTP ${response.status}).`);
      let data;try{data=await response.json();}catch{throw new Error('The website did not return dashboard data. Check the API route.');}
      if(!Array.isArray(data.conversations)||!Array.isArray(data.messages)||!Number.isFinite(data.generated_at))throw new Error('Unexpected dashboard response. Check the backend version.');
      if(current!==epoch)return;
      render(data);lastSuccess=Date.now();failure=false;$('error').hidden=true;
    }catch(error){if(current!==epoch)return;failure=true;$('error').textContent=(error.name==='AbortError'?'The backend did not respond in time. It may be waking up.':error.message)+' Retrying automatically; the last successful view is retained.';$('error').hidden=false;}
    finally{clearTimeout(timeout);if(current===epoch){controller=null;$('refresh').disabled=false;$('connect-button').disabled=false;freshness();if(token&&!document.hidden)timer=setTimeout(refresh,failure?15000:5000);}}
  }
  $('connect').addEventListener('submit',event=>{event.preventDefault();token=$('token').value.trim();$('token').value='';if(token){$('connect-button').disabled=true;lastSuccess=0;failure=false;refresh();}});
  $('refresh').addEventListener('click',refresh);$('disconnect').addEventListener('click',reset);$('search').addEventListener('input',conversationList);$('scope').addEventListener('change',conversationList);
  document.addEventListener('visibilitychange',()=>{if(document.hidden){clearTimeout(timer);controller?.abort();epoch++;}else if(token)refresh();freshness();});
  window.addEventListener('pagehide',reset);setInterval(freshness,1000);
})();
