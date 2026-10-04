#!/usr/bin/env python3
"""Read source hints and credential PRESENCE; never read .env values or call services."""
import argparse,json,os,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('repo',type=Path)
a=p.parse_args();root=a.repo.resolve()
if not (root/'package.json').is_file():p.error('No package.json at the supplied root.')
files=['src/server/dot-agent.ts','src/server/runner.ts','src/server/store.ts','src/server/headless.ts','src/server/parallel.ts','src/server/tanstack-tools.ts','src/server/computer-tools.ts','src/server/page-tools.ts','src/server/voice.ts','src/server/slack-channel.ts','SECURITY.md','docs/SETUP.md','docs/COMPUTERS.md']
texts={name:(root/name).read_text(errors='replace') if (root/name).is_file() else '' for name in files}
try:rev=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
except (subprocess.CalledProcessError,FileNotFoundError):rev=None
pkg=json.loads((root/'package.json').read_text())
hints={'interactive_timeout_ms':re.findall(r'setTimeout\([^\n]+?,\s*([\d_]+)\)',texts[files[0]]),'completion_token_settings':re.findall(r'max_completion_tokens:\s*(\d+)',texts[files[0]]),'single_active_runner_hint':'if (this.active.size) return' in texts[files[1]],'five_source_cap_hint':'slice(0, 5)' in texts[files[4]],'learned_skill_loader_hint':'copilotkit_load_skill' in texts[files[5]]}
keys=['INTELLIGENCE_API_KEY','OPENAI_API_KEY','OPENAI_MODEL','COMPUTER_SUPERVISOR_URL','COMPUTER_TOKEN','VOICE_API_KEY','SLACK_CHANNEL_NAME','PARALLEL_API_KEY','FAL_KEY','HF_API_KEY_ID','HF_API_KEY_SECRET']
print(json.dumps({'repository':str(root),'revision':rev,'package':pkg.get('name'),'node_engine':pkg.get('engines',{}).get('node'),'files_present':{k:bool(v) for k,v in texts.items()},'source_hints':hints,'process_environment_presence':{k:bool(os.environ.get(k)) for k in keys},'limits':['No .env contents read.','Presence is not validity or account authorization.','Source hints are not runtime or security verification.','All capability live statuses remain unverified.']},indent=2))
