from pathlib import Path
import datetime,hashlib,json,os,re,subprocess
r=Path('/home/felipe/proyectos/isosmart');d=r/'docs/governance/evidence';c=d/'PHASE31_4_V2_5_V11_OPERATIONAL_DIAGNOSTIC_CYCLE_1_ATTEMPT_2_CONTROL_V1';e=d/'runs/Phase_31.4_V2.5_V11_Operational_Diagnostic_Cycle_1_Attempt_2';out=json.loads((e/'execution_outcome.json').read_text());manifest=json.loads((e/'RESOURCE_MANIFEST.json').read_text());pre=json.loads((c/'preflight.json').read_text());old=json.loads((d/'PHASE31_4_V2_5_V11_OPERATIONAL_DIAGNOSTIC_CYCLE_1_ATTEMPT_1_CONTROL_V1/preflight.json').read_text())
observations={}
for kind,args in {'containers':['podman','ps','-a','--format','{{.Names}}'],'networks':['podman','network','ls','--format','{{.Name}}'],'volumes':['podman','volume','ls','--format','{{.Name}}'],'listeners':['ss','-ltnp']}.items():
 p=subprocess.run(args,capture_output=True,text=True,check=True);observations[kind]=p.stdout
residual={kind:[] for kind in ('containers','networks','volumes')}
for plan in (pre,old):
 for resource in plan['planned_resources'].values():
  for kind,key in (('containers','container'),('networks','network'),('volumes','volume')):
   if resource[key] in observations[kind].splitlines():residual[kind].append(resource[key])
markers=[('PHASE31_RUN_ID='+x['run_id']).encode() for x in (pre,old)];processes=[]
for p in Path('/proc').glob('[0-9]*/environ'):
 try:
  env=p.read_bytes().split(b'\0')
  if any(x in env for x in markers):processes.append(int(p.parent.name))
 except (OSError,PermissionError):pass
ports=[int(x.rsplit(':',1)[-1]) for x in out['service_endpoints'].values()]
ports.extend(int(x) for x in manifest['host_ports'])
listeners=[port for port in ports if re.search(r':'+str(port)+r'\s',observations['listeners'])]
pids=[x['pid'] for x in out['service_cleanup']['services'].values()];pids.append(json.loads((c/'authority_process.json').read_text())['pid'])
existing_pids=[pid for pid in pids if Path('/proc',str(pid)).exists()]
runtime=Path(json.loads((c/'runtime_provisioning.json').read_text())['interpreter']).parents[1]
leaks=[]
for base in (c,e):
 for p in base.rglob('*'):
  if p.is_file() and '__pycache__' not in str(p):
   if re.search(rb'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',p.read_bytes()):leaks.append(str(p.relative_to(r)))
passed=not any(residual.values()) and not processes and not listeners and not existing_pids and not runtime.exists() and not leaks and out['service_cleanup']['credential_references_destroyed'].get('isosmart_bearer') is True
result={'status':'PASS' if passed else 'FAIL','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':pre['run_id'],'residual_resources':residual,'matching_run_processes':processes,'recorded_pids_still_present':existing_pids,'checked_ports':ports,'remaining_listeners':listeners,'temporary_runtime_absent':not runtime.exists(),'credential_references_destroyed':True,'raw_credential_leak_files':leaks,'RAW_CREDENTIAL_LEAKS':len(leaks),'zero_residual_resources':passed,'inventory':observations}
(e/'final_independent_residual_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='inventory'},indent=2));assert passed
