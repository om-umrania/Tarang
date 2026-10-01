import test from 'node:test';
import assert from 'node:assert/strict';
import {normalise} from './filter.mjs';
test('reject unrelated direct messages and other groups',()=>{
 for(const remoteJid of ['personal@s.whatsapp.net','other@g.us']) assert.equal(normalise({key:{remoteJid,id:'x'},message:{conversation:'private'}},'chosen@g.us'),null);
});
test('selected group text is normalised',()=>{
 const m=normalise({key:{remoteJid:'chosen@g.us',id:'x',participant:'sender'},messageTimestamp:123,message:{conversation:'Proposed 12 November'}},'chosen@g.us');
 assert.equal(m.source_id,'x');assert.equal(m.kind,'text');assert.equal(m.text,'Proposed 12 November');
});
test('media content is not invented',()=>{
 const m=normalise({key:{remoteJid:'chosen@g.us',id:'x'},messageTimestamp:123,message:{audioMessage:{}}},'chosen@g.us');assert.equal(m.kind,'unsupported');assert.equal(m.text,'');
});
