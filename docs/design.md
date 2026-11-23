# Product requirements and operating notes

## User decision and opportunity

A support team needs a manual-backed answer with a citation that the caller is allowed to see. This local assistant filters passages by scope, retrieves candidates and returns a verified quotation or an explicit abstention.

| Stakeholder | Priority and milestone | Acceptance criterion |
|---|---|---|
| Support agent | P0 · trustworthy reply | Return a source identifier with every answer or abstain. Capture the missed paraphrase for diagnosis. |
| Platform engineer | P0 · access policy | Filter private passages before scoring and before forwarding candidates. Reject caller-supplied role fields. |
| Product manager | P1 · evaluate coverage | Report top-one source matches and correct abstentions separately. Require real support questions before using the result as a release metric. |

## Metric definitions and validation

The corpus contains 16 original synthetic manual passages. A query must share at least two terms with a candidate and pass coverage and BM25 score gates. Retrieval returns at most three scoped passages. The optional model selects a source and quote. The service checks both against those precise candidates before exposing the answer. Six development prompts are separate from 18 held-out prompts. Mean reciprocal rank is 0.923 for the answerable holdout.

The extractive mode selected the expected source for 12 of 13 answerable held-out prompts and abstained on all five unanswerable or scope-restricted prompts. Its miss was a paraphrase about retracting a holiday application. The fixture has 18 hand-authored holdout cases, so this is a regression benchmark.

## Architecture decision record

**Accepted for this local workload.** An in-memory lexical index over a tiny corpus keeps retrieval explainable. FastAPI provides the typed HTTP boundary. HTTPX calls the optional loopback Ollama service. Extractive mode runs offline. The model adapter passed controlled-response and outage tests. An actual model generation remains unverified.

Search.py filters the manual first so hidden documents cannot affect rankings. BM25 ranks eligible text with title weighting, term coverage and a minimum score. Answer.py either picks the first candidate or asks a local model to select evidence. It rejects unsupported source IDs or modified quotations. Api.py derives support scope from server configuration. Evaluate.py reports rank, source match and abstention for each labelled prompt.

The implementation lives in [the Python package](../src/workforce_knowledge). The boundaries are exercised by [the test suite](../tests).

## Operating procedure

Query the service on loopback. By default callers see public content. A local operator can set SUPPORT_KEY outside the repo and send it in X-Support-Key. Invalid credentials return 403. Logs record mode, disposition and elapsed milliseconds. Optional local model mode uses ANSWER_MODE=ollama and OLLAMA_MODEL with an installed model on 127.0.0.1:11434. Provider outages lead to abstention. Revert by restarting in extractive mode.

1. Reproduce the baseline with `python scripts/demo.py`. Compare the decision fields with the committed example.
2. Run the regression suite before changing input definitions or thresholds. Use the persistent example in the README to inspect intermediate state.
3. Run `python scripts/http_smoke.py` to test the API over TCP. The server exits at the end of the check.

### Container example

From the repository root:

```shell
docker compose up --build
```

The Compose port is bound to loopback.
This configuration awaits Docker execution. The same demo was exercised with the installed Python package.

## Constraints, reliability and delivery

A correct quotation can still be irrelevant or out of date. Lexical retrieval misses paraphrases and multilingual questions. The support key is a single local credential. Customer deployment needs identity-provider roles, document version governance and evaluation with real support staff.

Author and scope the manual, calibrate on development prompts, freeze the holdout and evaluate. Next run a real local model and compare against the extractive baseline on a larger blinded multilingual set. Establish a cost-per-resolved-ticket and escalation baseline before any pilot.

Local demo data and code are independent of former employers. Cost scenarios use declared assumptions. Operational targets describe a proposed pilot.
