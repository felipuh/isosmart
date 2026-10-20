import assert from 'node:assert/strict';
import fs from 'node:fs';
const text=fs.readFileSync('src/context/AuthContext.jsx','utf8');
const begin=text.indexOf('  const login =');
const end=text.indexOf('  // Logout',begin);
const loginSource=text.slice(begin,end);
const med=process.cwd().includes('ISO_Smart_MedSupplier');
let tests=0;
for(const scenario of ['challenge','incomplete','denied','complete']) {
  const events=[]; const storage=new Map([['access_token','previous'],['refresh_token','previous']]);
  const payload=scenario==='challenge'?{requires_2fa:true,challenge_token:'synthetic-challenge'}:
    scenario==='complete'?{requires_2fa:false,user:{id:1},profile:{id:2},organizations:[],access:'synthetic-access',refresh:'synthetic-refresh'}:
    scenario==='incomplete'?{requires_2fa:false}:null;
  const api={get:async()=>({data:{}}),post:async()=>{if(scenario==='denied')throw {response:{status:403,data:{detail:'Denied'}}};return {data:payload}},defaults:{headers:{common:{}}}};
  const clearAuth=()=>{events.push(['clear']);storage.clear();delete api.defaults.headers.common.Authorization};
  const setters=['setUser','setProfile','setOrganizations','setSecurityAlert','setCurrentOrganization','setIsAuthenticated'];
  const localStorage={setItem:(k,v)=>storage.set(k,v)};
  const construct=new Function('api','clearAuth','t','localStorage',...setters,loginSource+'\nreturn login;');
  const login=construct(api,clearAuth,x=>x,localStorage,...setters.map(n=>v=>events.push([n,v])));
  const result=await login('person@example.invalid','password');
  if(scenario==='complete') { assert.equal(result.success,true);assert.ok(events.some(([n,v])=>n==='setIsAuthenticated'&&v===true));if(med)assert.equal(storage.get('access_token'),'synthetic-access'); }
  else {assert.equal(result.success,false);assert.ok(!events.some(([n,v])=>n==='setIsAuthenticated'&&v===true));assert.equal(storage.size,0);if(scenario==='challenge')assert.equal(result.challenge_token,'synthetic-challenge');}
  tests++;
}
console.log(JSON.stringify({tests,passed:tests,scope:'offline production login closure; NOT browser E2E'}));
