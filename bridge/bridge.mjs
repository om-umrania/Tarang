// Standalone receive-only linked device. Never reuse another app's auth directory.
import makeWASocket, {useMultiFileAuthState, DisconnectReason} from '@whiskeysockets/baileys';
import pino from 'pino';
import qr from 'qrcode-terminal';
import {DatabaseSync} from 'node:sqlite';
import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {randomUUID} from 'node:crypto';
import {normalise} from './filter.mjs';

process.umask(0o077);
const dir=resolve('../.runtime/group-bridge');
mkdirSync(dir,{recursive:true,mode:0o700});
let groupId=process.env.WHATSAPP_GROUP_ID;
const pairOnly=process.argv.includes('--pair-only');
const groupName=process.env.WHATSAPP_GROUP_NAME;
const token=process.env.WHATSAPP_BRIDGE_TOKEN;
const endpoint=new URL('/whatsapp/group-batch',process.env.TARANG_GROUP_URL || 'http://127.0.0.1:8766');
if(pairOnly ? !(groupId || groupName) : (!groupId?.endsWith('@g.us') || !token)) throw Error('Pairing needs an exact group name or ID; running needs group ID and bridge token');
if(endpoint.protocol!=='https:' && !['127.0.0.1','localhost'].includes(endpoint.hostname)) throw Error('Remote bridge delivery requires HTTPS');
const db=new DatabaseSync(resolve(dir,'queue.sqlite3'));
db.exec('PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS latest(source_id TEXT PRIMARY KEY, signature TEXT); CREATE TABLE IF NOT EXISTS queue(id INTEGER PRIMARY KEY, payload TEXT NOT NULL);');
let connected=false, flushing=false, stopped=false;
function enqueue(m){
 if(!m || !Number.isFinite(m.sent_at) || !m.sent_at || m.text.length>12000) return;
 const signature=JSON.stringify([m.text,m.kind]);
 if(db.prepare('SELECT signature FROM latest WHERE source_id=?').get(m.source_id)?.signature===signature) return;
 db.exec('BEGIN IMMEDIATE');
 try{
  db.prepare('INSERT INTO queue(payload) VALUES(?)').run(JSON.stringify({...m,external_id:randomUUID()}));
  db.prepare('INSERT INTO latest VALUES(?,?) ON CONFLICT(source_id) DO UPDATE SET signature=excluded.signature').run(m.source_id,signature);
  db.exec('COMMIT');
 }catch(e){db.exec('ROLLBACK');throw e;}
}
async function flush(){
 if(pairOnly || flushing) return; flushing=true;
 try{
  const rows=db.prepare('SELECT * FROM queue ORDER BY id LIMIT 100').all();
  const r=await fetch(endpoint,{method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify({group_id:groupId,connected,messages:rows.map(r=>JSON.parse(r.payload))}),signal:AbortSignal.timeout(30000)});
  if(!r.ok) throw Error('delivery_failed');
  const result=await r.json(); if(!Number.isInteger(result.accepted)) throw Error('invalid_ack');
  if(rows.length) db.prepare('DELETE FROM queue WHERE id<=?').run(rows.at(-1).id);
 }catch{console.error('Bridge delivery unavailable; queued messages retained.');}
 finally{flushing=false;}
}
async function connect(){
 const {state,saveCreds}=await useMultiFileAuthState(resolve(dir,'auth'));
 const socket=makeWASocket({auth:state,logger:pino({level:'silent'}),syncFullHistory:false,markOnlineOnConnect:false});
 socket.ev.on('creds.update',saveCreds);
 socket.ev.on('messages.upsert',({messages})=>{for(const m of messages) enqueue(normalise(m,groupId));});
 socket.ev.on('messaging-history.set',({messages})=>{for(const m of messages) enqueue(normalise(m,groupId));});
 socket.ev.on('messages.update',updates=>{for(const {key,update} of updates){
  if(key.remoteJid!==groupId) continue;
  if(update.message===null) enqueue({source_id:key.id,sender:key.participant||'unknown',text:'',kind:'deleted',sent_at:Date.now()/1000});
  else if(update.message) enqueue(normalise({key,message:update.message,messageTimestamp:update.messageTimestamp||Date.now()/1000},groupId));
 }});
 socket.ev.on('connection.update',async ({connection,qr:code,lastDisconnect})=>{
  if(code) {console.log('Pair this isolated device from the intended account. Keep this QR private.');qr.generate(code,{small:true});}
  if(connection==='open') {
   try{
    if(!groupId){const groups=await socket.groupFetchAllParticipating();const matches=Object.values(groups).filter(g=>g.subject===groupName);if(matches.length!==1)throw Error('Exact group name must resolve uniquely');groupId=matches[0].id;}
    await socket.groupMetadata(groupId);
    if(pairOnly){await saveCreds();console.log('Selected group ID (configure this on both bridge and Python service): '+groupId);stopped=true;socket.end(new Error('Pairing complete'));process.exit(0);}
    connected=true;console.log('Configured group accessible; receive-only bridge connected.');
   }
   catch{connected=false;stopped=true;socket.end(new Error('Configured group inaccessible'));}
   await flush();
  }
  if(connection==='close'){
   connected=false;await flush();
   const loggedOut=lastDisconnect?.error?.output?.statusCode===DisconnectReason.loggedOut;
   if(loggedOut||stopped){console.error('Bridge stopped; account pairing or group configuration needs attention.');return;}
   setTimeout(()=>connect().catch(()=>console.error('Bridge reconnect failed. Restart required.')),10000);
  }
 });
}
if(!pairOnly) setInterval(flush,60000); // Durable intake/heartbeat each minute; Python reviews hourly.
await connect();
