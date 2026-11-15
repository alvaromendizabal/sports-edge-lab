const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
function verifyHostedHtml(received,expected,route){
  const raw=Buffer.isBuffer(received)?received:Buffer.from(received), observed=digest(raw);
  if(observed===expected) return observed;
  // Match only the single appended Cloudflare JavaScript challenge already recognized by the NFL publication tests.
  const text=raw.toString('utf8');
  const pattern=/<script>\(function\(\)\{function c\(\)\{var b=a\.contentDocument[\s\S]*?<\/script>(?=<\/body>\s*<\/html>\s*$)/g;
  const matches=[...text.matchAll(pattern)];
  assert.equal(matches.length,1,'Unexpected alteration to '+route+'; observed '+observed);
  const script=matches[0][0];
  assert(script.length<4096 && script.includes('/cdn-cgi/challenge-platform/scripts/jsd/main.js') && script.includes('window.__CF$cv$params'),'Unexpected appended code on '+route);
  const normalized=text.slice(0,matches[0].index)+text.slice(matches[0].index+script.length);
  assert.equal(digest(normalized),expected,'Authored HTML changed on '+route);
  console.log(JSON.stringify({route,host_appended_bytes:Buffer.byteLength(script),received_sha256:observed,authored_sha256:expected}));
  return expected;
}
module.exports={verifyHostedHtml};
