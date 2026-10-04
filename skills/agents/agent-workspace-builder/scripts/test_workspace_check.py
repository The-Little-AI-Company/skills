#!/usr/bin/env python3
"""Offline snapshots only."""
import copy
import unittest
from workspace_check import validate

BASE={'schema_version':1,'capabilities':[{'id':'local','implemented':True,'configured':True,'verified':False,'tool_binding':'local.run'}],'tasks':[{'id':'a','state':'ready','dependencies':[],'capabilities':['local']}]}
class SnapshotChecks(unittest.TestCase):
 def setUp(self): self.data=copy.deepcopy(BASE)
 def test_valid(self): self.assertEqual(validate(self.data),[])
 def test_duplicate(self):
  self.data['tasks']*=2;self.assertTrue(validate(self.data))
 def test_cycle(self):
  self.data['tasks'][0]['dependencies']=['b'];self.data['tasks'].append({'id':'b','state':'backlog','dependencies':['a']});self.assertTrue(any('cycle' in x for x in validate(self.data)))
 def test_missing_dependency(self):
  self.data['tasks'][0]['dependencies']=['missing'];self.assertTrue(validate(self.data))
 def test_unknown_capability(self):
  self.data['tasks'][0]['capabilities']=['missing'];self.assertTrue(validate(self.data))
 def test_unconfigured(self):
  self.data['capabilities'][0]['configured']=False;self.assertTrue(validate(self.data))
 def test_done_without_evidence(self):
  self.data['tasks'][0]['state']='done';self.assertTrue(validate(self.data))
 def test_done_with_supplied_evidence(self):
  self.data['tasks'][0].update(state='done',evidence=['fixture-receipt'],artifacts=['fixture-artifact']);self.assertEqual(validate(self.data),[])
 def test_claimed_verified_without_receipt(self):
  self.data['capabilities'][0]['verified']=True;self.assertTrue(validate(self.data))
 def test_cancel_outstanding(self):
  self.data['tasks'][0].update(state='canceled',outstanding_external_jobs=['job']);self.assertTrue(validate(self.data))
 def test_running_without_worker(self):
  self.data['tasks'][0]['state']='running';self.assertTrue(validate(self.data))
 def test_external_without_id(self):
  self.data['tasks'][0]['state']='waiting_external';self.assertTrue(validate(self.data))
 def test_malformed(self):
  for data in [None,[],{},dict(schema_version=1,tasks='bad',capabilities=[])]:self.assertTrue(validate(data))
 def test_blocker_reason(self):
  self.data['tasks'][0]['state']='blocked';self.assertTrue(validate(self.data))
if __name__=='__main__':unittest.main()
