export function normalise(message, groupId) {
  if (message?.key?.remoteJid !== groupId || !message.key.id) return null;
  let content = message.message;
  content = content?.ephemeralMessage?.message || content;
  content = content?.viewOnceMessage?.message || content;
  const text = content?.conversation ?? content?.extendedTextMessage?.text;
  return {source_id:message.key.id, sender:message.key.participant || (message.key.fromMe ? 'linked-account' : 'unknown'), text:typeof text==='string'?text:'', sent_at:Number(message.messageTimestamp), kind:typeof text==='string'?'text':'unsupported'};
}
