"""Model restriction, gateway isolation and actual request reasoning; no paid calls."""
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import Mock, patch

from common.models import MODEL_PROFILES, FORMULATION_MODEL, completion_options, credentials, reasoning_mode
from codegen.service import CodegenService, CodegenError
from problem_selection_agent.service import SelectionError
from tests.fixtures import AuthoringFixture, response
from web.host import HostService, UserError

IDS = ['moonshotai/kimi-k2.5','deepseek/deepseek-v4-flash','qwen/qwen3.5-27b',
       'google/gemini-3-flash-preview','anthropic/claude-haiku-4.5','gpt-5.4-mini']


class ModelProfilesTests(TestCase):
    def test_catalog_is_fixed_without_catalog_api_calls_and_clients_are_separate(self):
        native=Mock(api_key='native-test-key');router=Mock(api_key='router-test-key')
        with tempfile.TemporaryDirectory() as folder:
            host=HostService(folder,client=native,router_client=router)
            self.assertEqual(host.config()['models'],IDS)
            self.assertEqual(host.config()['formulation_profile']['id'],FORMULATION_MODEL)
            for model in IDS[:5]:self.assertIs(host.client(model),router)
            self.assertIs(host.client('gpt-5.4-mini'),native)
            self.assertIs(host.client('gpt-5.5'),native)
            native.models.list.assert_not_called();router.models.list.assert_not_called()
            self.assertEqual(host.redact_error('native-test-key / router-test-key'),'[REDACTED] / [REDACTED]')

    def test_missing_router_key_does_not_fall_back_to_openai(self):
        with tempfile.TemporaryDirectory() as folder,patch('web.host.credentials',return_value=''):
            host=HostService(folder,client=Mock())
            with self.assertRaisesRegex(UserError,'OPENROUTER_API_KEY'):host.client(IDS[0])
            self.assertIsNone(host._router_client)

    def test_native_and_gateway_requests_encode_the_selected_modes(self):
        self.assertEqual([p['id'] for p in MODEL_PROFILES],IDS)
        modes=({'enabled':True},{'enabled':True,'effort':'high'},
               {'enabled':True},{'enabled':True,'effort':'low'})
        for model,mode in zip(IDS[:4],modes):
            options=completion_options(model)
            self.assertEqual(options['extra_body']['reasoning'],mode)
            self.assertTrue(options['extra_body']['provider']['require_parameters'])
            self.assertNotIn('reasoning_effort',options);self.assertNotIn('store',options)
            self.assertNotIn('exclude',options['extra_body']['reasoning'])
        self.assertEqual(completion_options(IDS[4])['extra_body']['reasoning'],{'enabled':True,'max_tokens':4096})
        self.assertEqual(completion_options(IDS[5])['reasoning_effort'],'low')
        self.assertEqual(completion_options(FORMULATION_MODEL)['reasoning_effort'],'medium')

    def test_old_settings_are_migrated_but_new_unlisted_models_are_rejected(self):
        fixture=AuthoringFixture();fixture.setUp();self.addCleanup(fixture.tearDown)
        legacy={'classifier_model':'gpt-5-mini','classifier_reasoning':'default',
                'formulation_model':'gpt-5.4','formulation_reasoning':'low'}
        before=dict(legacy);settings=fixture.service.settings({},legacy)
        self.assertEqual(legacy,before)
        self.assertEqual(settings['classifier_model'],'gpt-5.4-mini')
        self.assertEqual(settings['formulation_model'],'gpt-5.5')
        self.assertEqual(settings['formulation_reasoning'],'medium')
        for model in ('gpt-5','gpt-5.4','gpt-5.5','qwen/qwen3-32b','unknown/model'):
            with self.subTest(model=model):
                with self.assertRaises(SelectionError):fixture.service.settings({'settings':{'classifier_model':model}})
                with self.assertRaises(CodegenError):CodegenService.settings({'model':model})

    def test_each_hitl_model_reaches_the_correct_client_and_keeps_the_json_schema(self):
        fixture=AuthoringFixture();fixture.setUp();self.addCleanup(fixture.tearDown)
        with tempfile.TemporaryDirectory() as folder:
            router=Mock();router.chat.completions.create.return_value=response(fixture.proposal(fixture.elastic))
            host=HostService(folder,client=fixture.client,router_client=router)
            fixture.service.host=host
            schema={'type':'object','properties':{},'additionalProperties':False}
            for model in IDS:
                raw,meta=fixture.service._ask({'id':'c'*32},'selection',model,[],schema,{})
                client=fixture.client if model=='gpt-5.4-mini' else router
                request=client.chat.completions.create.call_args.kwargs
                self.assertEqual(request['model'],model)
                self.assertEqual(request['response_format']['json_schema']['schema'],schema)
                self.assertTrue(request['response_format']['json_schema']['strict'])
                from problem_selection_agent.questions import wire_assessment
                self.assertEqual(json.loads(raw),{'response':wire_assessment(fixture.proposal(fixture.elastic)['response'])})
                if model!='gpt-5.4-mini':self.assertEqual(meta['reasoning_request'],request['extra_body']['reasoning'])
                self.assertEqual(CodegenService.settings({'model':model})['reasoning'],meta['reasoning_effort'])

    def test_coder_uses_same_mode_as_hitl_and_records_gateway_settings(self):
        path=Path(__file__).resolve().parents[1]/'coder/coder.py'
        spec=importlib.util.spec_from_file_location('model_profile_coder_test',path)
        coder=importlib.util.module_from_spec(spec);spec.loader.exec_module(coder)
        client=Mock(api_key='fixture-key');client.chat.completions.create.return_value=response('code')
        coder.CODER_CLIENT=client;events=[];coder.TRACE=lambda kind,**data:events.append((kind,data))
        for model in IDS:
            coder.CODER_MODEL=model
            for mode in next(p for p in MODEL_PROFILES if p['id']==model)['reasoning_options']:
                with patch.dict('os.environ',{'CODER_REASONING':mode}):
                    coder.ask('fixture prompt','fixture system',max_tokens=32000)
                request=client.chat.completions.create.call_args.kwargs
                expected=completion_options(model,32000,reasoning=mode)
                for key,value in expected.items():self.assertEqual(request[key],value)
                self.assertEqual(events[-2][1]['extra_body'],request['extra_body'])

    def test_selected_modes_survive_settings_and_reach_hitl_and_coder_requests(self):
        fixture=AuthoringFixture();fixture.setUp();self.addCleanup(fixture.tearDown)
        schema={'type':'object','properties':{},'additionalProperties':False}
        for p in MODEL_PROFILES:
            for mode in p['reasoning_options']:
                with self.subTest(model=p['id'],mode=mode):
                    requested={'classifier_model':p['id'],'classifier_reasoning':mode}
                    state={'id':'d'*32,'settings':fixture.service.settings({'settings':requested})}
                    model,actual=fixture.service.model_settings(state,'classifier')
                    self.assertEqual(actual,mode)
                    self.assertEqual(fixture.service.settings({},state['settings'])['classifier_reasoning'],mode)
                    fixture.service._ask(state,'selection',model,[],schema,{},reasoning=actual)
                    request=fixture.client.chat.completions.create.call_args.kwargs
                    expected=completion_options(model,reasoning=mode)
                    for key,value in expected.items():self.assertEqual(request[key],value)
                    self.assertEqual(CodegenService.settings({'model':model,'reasoning':mode})['reasoning'],mode)

    def test_invalid_new_modes_are_rejected_and_legacy_modes_fall_back_without_rewriting(self):
        fixture=AuthoringFixture();fixture.setUp();self.addCleanup(fixture.tearDown)
        for model,mode in [(IDS[0],'high'),(IDS[1],'low'),(IDS[3],'none'),(IDS[4],'low'),(IDS[5],'enabled')]:
            with self.subTest(model=model,mode=mode):
                with self.assertRaises(SelectionError):
                    fixture.service.settings({'settings':{'classifier_model':model,'classifier_reasoning':mode}})
                with self.assertRaises(CodegenError):CodegenService.settings({'model':model,'reasoning':mode})
        legacy={'classifier_model':IDS[3],'classifier_reasoning':'none'}
        before=dict(legacy)
        self.assertEqual(fixture.service.settings({},legacy)['classifier_reasoning'],'low')
        self.assertEqual(legacy,before)
        changed=fixture.service.settings({'settings':{'classifier_model':IDS[0]}},
            {'classifier_model':IDS[5],'classifier_reasoning':'high'})
        self.assertEqual(changed['classifier_reasoning'],'enabled')
        self.assertEqual(reasoning_mode(IDS[5],'default'),'low')
