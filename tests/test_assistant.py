import os
from unittest import TestCase
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from workforce_knowledge.answer import answer, ollama_select
from workforce_knowledge.api import app
from workforce_knowledge.evaluate import evaluate
from workforce_knowledge.search import catalog, retrieve


class KnowledgeTests(TestCase):
    def test_ranking_and_access_scope(self):
        query = "reconcile delayed terminal batches"
        self.assertEqual(retrieve(query, True)[0]['id'], 'internal.reconcile')
        self.assertFalse(any(p['scope'] == 'support' for p in retrieve(query, False)))
        self.assertEqual(answer("monthly bicycle insurance")['status'], 'abstained')

    def test_quote_and_citation_must_match_authorized_evidence(self):
        query = "offline clock entries"
        self.assertEqual(answer(query, selector=lambda *_: {'source': 'clock.offline', 'quote': 'invented'})['reason'],
                         'unverified_citation')
        self.assertEqual(answer(
            query, selector=lambda *_: {'source': 'internal.freeze', 'quote': 'no'})['status'], 'abstained')

        def valid(_query, candidates):
            return dict(source=candidates[0]['id'], quote=candidates[0]['text'])
        self.assertEqual(answer(query, selector=valid)['citation'], 'clock.offline')

    def test_ollama_boundary_success_and_outage(self):
        passage = next(p for p in catalog() if p['id'] == 'clock.offline')
        import json
        model = json.dumps(dict(source=passage['id'], quote=passage['text']))
        response = httpx.Response(200, request=httpx.Request(
            'POST', 'http://localhost'), json={'response': model})
        with patch('workforce_knowledge.answer.httpx.post', return_value=response):
            self.assertEqual(answer('offline clock entries', selector=ollama_select)[
                             'citation'], 'clock.offline')
        with patch('workforce_knowledge.answer.httpx.post', side_effect=httpx.ConnectError('offline')):
            self.assertEqual(answer('offline clock entries', selector=ollama_select)[
                             'status'], 'abstained')

    def test_api_role_and_contract(self):
        with TestClient(app) as client, patch.dict(os.environ, SUPPORT_KEY="unit-test-only", ANSWER_MODE='extractive'):
            q = {'question': 'reconcile delayed terminal batches'}
            self.assertEqual(client.post(
                '/v1/answer', json={**q, 'role': 'support'}).status_code, 422)
            self.assertEqual(client.post('/v1/answer', json=q,
                             headers={'x-support-key': 'wrong'}).status_code, 403)
            self.assertEqual(client.post(
                '/v1/answer', json=q, headers={'x-support-key': 'unit-test-only'}).json()['citation'], 'internal.reconcile')

    def test_evaluation_covers_answerable_and_unanswerable_cases(self):
        report = evaluate()
        self.assertEqual(report['total'], 18)
        self.assertGreater(report['answerable'], 0)
        self.assertGreater(report['expected_abstentions'], 0)
        self.assertGreaterEqual(report['top1_correct'], 8)
