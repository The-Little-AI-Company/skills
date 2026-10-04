#!/usr/bin/env python3
"""Offline provider fixtures; no network or paid generation."""
import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import media_queue as m

class QueueTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.dbpath=Path(self.tmp.name)/'jobs.sqlite';self.ledger=m.Ledger(self.dbpath)
  self.env=patch.dict(os.environ,{'FAL_KEY':'test-fal','HF_API_KEY_ID':'test-id','HF_API_KEY_SECRET':'test-secret'});self.env.start()
 def tearDown(self):
  self.ledger.close();self.tmp.cleanup();self.env.stop()
 def receipt(self,provider='fal'):
  base='https://'+m.HOSTS[provider]+'/requests/id'
  return {'request_id':'id','status_url':base+'/status','cancel_url':base+'/cancel','response_url':base+'/result'}
 def submit(self,provider='fal',**kw):
  return m.submit(self.ledger,provider,'vendor/model',{'prompt':'demo'},'op',1.0,**kw)
 def seed(self,provider='fal'):
  with patch.object(m,'request',return_value=(200,self.receipt(provider))):return self.submit(provider,authorized=True)
 def test_authority_required(self):
  with patch.object(m,'request') as call:
   with self.assertRaises(ValueError):self.submit()
   call.assert_not_called()
 def test_submit_and_repeat_no_second_post(self):
  with patch.object(m,'request',return_value=(200,self.receipt())) as call:
   first=self.submit(authorized=True);second=self.submit(authorized=True)
   self.assertEqual(first['request_id'],second['request_id']);self.assertEqual(call.call_count,1)
 def test_changed_input_blocked(self):
  self.seed()
  with self.assertRaises(ValueError):m.submit(self.ledger,'fal','vendor/model',{'prompt':'changed'},'op',1,True)
 def test_distinct_intents_use_distinct_provider_keys(self):
  with patch.object(m,'request',return_value=(200,self.receipt('higgsfield'))) as call:
   first=self.submit('higgsfield',authorized=True)
   second=m.submit(self.ledger,'higgsfield','vendor/model',{'prompt':'demo'},'op-two',1,True)
   self.assertNotEqual(first['idempotency_key'],second['idempotency_key'])
   self.assertEqual(call.call_args_list[0].args[5]['Idempotency-Key'],first['idempotency_key'])
   self.assertEqual(self.ledger.get('op')['idempotency_key'],first['idempotency_key'])
 def test_ambiguous_higgsfield_key_survives_restart(self):
  with patch.object(m,'request',side_effect=RuntimeError('network')) as call:
   with self.assertRaises(RuntimeError):self.submit('higgsfield',authorized=True)
   key=call.call_args.args[5]['Idempotency-Key']
  self.ledger.close();self.ledger=m.Ledger(self.dbpath)
  self.assertEqual(self.ledger.get('op')['idempotency_key'],key)
 def test_ambiguous_post_not_retried(self):
  with patch.object(m,'request',side_effect=RuntimeError('network')) as call:
   with self.assertRaises(RuntimeError):self.submit(authorized=True)
   with self.assertRaises(ValueError):self.submit(authorized=True)
   self.assertEqual(call.call_count,1);self.assertEqual(self.ledger.get('op')['state'],'submission_unknown')
 def test_restart_uses_existing_request(self):
  self.seed();self.ledger.close();self.ledger=m.Ledger(self.dbpath)
  with patch.object(m,'request',return_value=(200,{'status':'IN_PROGRESS'})) as call:
   self.assertEqual(m.status(self.ledger,'op')['state'],'running');self.assertEqual(call.call_args.args[1],'GET')
 def test_fal_terminal_error_is_failure(self):
  self.seed()
  with patch.object(m,'request',return_value=(200,{'status':'COMPLETED','error':'failed'})) as call:
   self.assertEqual(m.status(self.ledger,'op')['state'],'failed');self.assertEqual(call.call_count,1)
 def test_fal_result_retrieval(self):
  self.seed()
  with patch.object(m,'request',side_effect=[(200,{'status':'COMPLETED'}),(200,{'video':{'url':'https://cdn.example/video.mp4'}})]):
   d=m.status(self.ledger,'op');self.assertEqual(d['state'],'completed');self.assertFalse(d['artifact_verified']);self.assertIn('video',d['result'])
 def test_result_failure_is_recoverable(self):
  self.seed()
  with patch.object(m,'request',side_effect=[(200,{'status':'COMPLETED'}),RuntimeError('network')]):
   with self.assertRaises(RuntimeError):m.status(self.ledger,'op')
  self.assertEqual(self.ledger.get('op')['state'],'waiting_result')
  with patch.object(m,'request',side_effect=[(200,{'status':'COMPLETED'}),(200,{'images':[]})]):self.assertEqual(m.status(self.ledger,'op')['state'],'completed')
 def test_higgsfield_states(self):
  for raw,want in [('queued','queued'),('in_progress','running'),('completed','completed'),('failed','failed'),('nsfw','rejected'),('canceled','canceled')]:self.assertEqual(m.normalize('higgsfield',{'status':raw}),want)
 def test_higgsfield_completion(self):
  self.seed('higgsfield')
  with patch.object(m,'request',return_value=(200,{'status':'completed','request_id':'id','images':[{'url':'https://cdn.example/x.jpg'}]})) as call:
   self.assertEqual(m.status(self.ledger,'op')['state'],'completed');self.assertEqual(call.call_count,1)
 def test_cancel_methods_and_states(self):
  self.seed()
  with patch.object(m,'request',return_value=(202,{})) as call:
   self.assertEqual(m.cancel(self.ledger,'op')['state'],'cancel_requested');self.assertEqual(call.call_args.args[1],'PUT')
  self.ledger.db.execute('DELETE FROM jobs');self.ledger.db.commit();self.seed('higgsfield')
  with patch.object(m,'request',return_value=(202,{})) as call:
   self.assertEqual(m.cancel(self.ledger,'op')['state'],'canceled');self.assertEqual(call.call_args.args[1],'POST')
 def test_cancel_denied_not_marked_canceled(self):
  self.seed('higgsfield')
  with patch.object(m,'request',side_effect=m.ApiError(400)):
   with self.assertRaises(m.ApiError):m.cancel(self.ledger,'op')
  self.assertNotEqual(self.ledger.get('op')['state'],'canceled')
 def test_pending_cancel_preserved(self):
  self.seed()
  with patch.object(m,'request',return_value=(202,{})):m.cancel(self.ledger,'op')
  with patch.object(m,'request',return_value=(200,{'status':'IN_PROGRESS'})):self.assertEqual(m.status(self.ledger,'op')['state'],'cancel_requested')
 def test_safe_url_blocks_secret_exfiltration(self):
  for url in ['https://evil.test/x','http://queue.fal.run/x','https://queue.fal.run.evil.test/x','https://user:pass@queue.fal.run/x','https://queue.fal.run:123/x','https://127.0.0.1/x']:
   with self.assertRaises(ValueError):m.safe_url('fal',url)
 def test_bad_receipt_keeps_request_id(self):
  r=self.receipt();r['status_url']='https://evil.test/x'
  with patch.object(m,'request',return_value=(200,r)):
   with self.assertRaises(ValueError):self.submit(authorized=True)
  self.assertEqual(self.ledger.get('op')['request_id'],'id')
 def test_account_change_blocked(self):
  self.seed()
  with patch.dict(os.environ,{'FAL_KEY':'different'}):
   with self.assertRaises(ValueError):m.status(self.ledger,'op')
 def test_invalid_cost_and_model(self):
  for cost in [-1,float('nan'),float('inf')]:
   with self.assertRaises(ValueError):m.submit(self.ledger,'fal','vendor/model',{},'op',cost,True)
  for model in ['../secret','vendor/../x','vendor//x','https://evil.test','vendor/x?url=y']:
   with self.assertRaises(ValueError):m.model_path(model)
 def test_missing_request_id_is_ambiguous(self):
  with patch.object(m,'request',return_value=(200,{})):
   with self.assertRaises(ValueError):self.submit(authorized=True)
  self.assertEqual(self.ledger.get('op')['state'],'submission_unknown')
 def test_bad_auth_is_rejected(self):
  with patch.object(m,'request',side_effect=m.ApiError(401)):
   with self.assertRaises(m.ApiError):self.submit(authorized=True)
  self.assertEqual(self.ledger.get('op')['state'],'rejected')
 def test_terminal_status_no_network(self):
  d=self.seed();d['state']='completed';self.ledger.save(d)
  with patch.object(m,'request') as call:m.status(self.ledger,'op');call.assert_not_called()

if __name__=='__main__':unittest.main()
