# Interview preparation · Evaluated retrieval for a workforce product

Use first-person wording after you have run the demo and can explain or change the code yourself. Describe this as a portfolio implementation. Quantities below refer to the synthetic fixture.

## 30-second introduction

I built a workforce-support assistant where the product decision is whether it has enough authorized evidence to answer. Its local baseline selected the expected source for 12 of 13 answerable test questions and abstained on all five out-of-scope cases. One paraphrase exposed a vocabulary gap. I would use that case when comparing semantic retrieval against the simpler baseline.

## Two-minute technical explanation

Search.py filters the manual first so hidden documents cannot affect rankings. BM25 ranks eligible text with title weighting, term coverage and a minimum score. Answer.py either picks the first candidate or asks a local model to select evidence. It rejects unsupported source IDs or modified quotations. Api.py derives support scope from server configuration. Evaluate.py reports rank, source match and abstention for each labelled prompt.

The corpus contains 16 original synthetic manual passages. A query must share at least two terms with a candidate and pass coverage and BM25 score gates. Retrieval returns at most three scoped passages. The optional model selects a source and quote. The service checks both against those precise candidates before exposing the answer. Six development prompts are separate from 18 held-out prompts. Mean reciprocal rank is 0.923 for the answerable holdout.

The extractive mode selected the expected source for 12 of 13 answerable held-out prompts and abstained on all five unanswerable or scope-restricted prompts. Its miss was a paraphrase about retracting a holiday application. The fixture has 18 hand-authored holdout cases, so this is a regression benchmark.

A correct quotation can still be irrelevant or out of date. Lexical retrieval misses paraphrases and multilingual questions. The support key is a single local credential. Customer deployment needs identity-provider roles, document version governance and evaluation with real support staff.

## Architecture walkthrough

Open the files in this order and follow one record through the system.

[search.py](../src/workforce_knowledge/search.py) · [answer.py](../src/workforce_knowledge/answer.py) · [api.py](../src/workforce_knowledge/api.py) · [evaluate.py](../src/workforce_knowledge/evaluate.py)

Search.py filters the manual first so hidden documents cannot affect rankings. BM25 ranks eligible text with title weighting, term coverage and a minimum score. Answer.py either picks the first candidate or asks a local model to select evidence. It rejects unsupported source IDs or modified quotations. Api.py derives support scope from server configuration. Evaluate.py reports rank, source match and abstention for each labelled prompt.

## Five technical questions

**1. When are access rules applied?**

Before retrieval, including corpus statistics and candidate assembly. The optional model receives only the resulting scoped candidates.

**2. Does matching a quotation guarantee correctness?**

It guarantees that the text came from the cited allowed passage. It does not guarantee that the passage answers the question.

**3. Why BM25 here?**

Sixteen short passages can be scored on demand without index infrastructure. The failure on synonyms motivates a measured hybrid alternative.

**4. What does the Ollama test establish?**

The request adapter, response validation and timeout handling work against controlled responses. No model-quality or live inference result follows.

**5. How is the holdout scored?**

Answerable prompts require the expected citation. Unknown or restricted prompts require abstention. Reciprocal rank gives partial credit when the source appears below the top result.

## Five product and business questions

**1. Would 17/18 justify a rollout?**

The questions were authored with the system and the corpus is small. Validate on blinded real questions before a pilot.

**2. What user need comes first?**

A correct, permitted source for a support answer, with escalation when evidence is weak.

**3. Where is the risk of excess abstention?**

Paraphrases and German questions may have low lexical overlap despite a clear answer in the manual.

**4. Why return a whole quote?**

A support operator can inspect the evidence directly. Fluent paraphrases would require stronger grounding evaluation.

**5. What would justify a local language model?**

An improvement on real source selection or resolution rate sufficient to offset latency, hosting and operational effort.

## What to demonstrate live

Run `python scripts/demo.py`. Point to one input, the relevant transformation and the output that supports your decision. Add a development-set synonym for holiday and leave, then design a fresh blind set. Preserve the original holdout as a regression suite once it has informed an edit.

## Main trade-off and next test

An in-memory lexical index over a tiny corpus keeps retrieval explainable. FastAPI provides the typed HTTP boundary. HTTPX calls the optional loopback Ollama service. Extractive mode runs offline. The model adapter passed controlled-response and outage tests. An actual model generation remains unverified.

A correct quotation can still be irrelevant or out of date. Lexical retrieval misses paraphrases and multilingual questions. The support key is a single local credential. Customer deployment needs identity-provider roles, document version governance and evaluation with real support staff.

## CV wording for a portfolio section

- Built and evaluated a scoped workforce-support retrieval API with citation validation, abstention and a local-model adapter, publishing case-level results for 18 synthetic holdout prompts.
