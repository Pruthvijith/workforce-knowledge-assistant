import json
from importlib.resources import files
from workforce_knowledge.answer import answer
from workforce_knowledge.search import retrieve


def evaluate(split: str = "holdout") -> dict:
    rows = json.loads(files("workforce_knowledge").joinpath("data/eval.json").read_text())
    cases = []
    for group, query, support, expected in rows:
        if group != split:
            continue
        result = answer(query, support)
        ids = [p['id'] for p in retrieve(query, support)]
        rank = ids.index(expected)+1 if expected in ids else None
        cases.append(dict(question=query, support=support, expected=expected, observed=result['citation'],
                          rank=rank, correct=result['citation'] == expected))
    known = [c for c in cases if c['expected']]
    unknown = [c for c in cases if not c['expected']]
    return dict(split=split, total=len(cases), correct=sum(c['correct'] for c in cases),
                answerable=len(known), top1_correct=sum(c['correct'] for c in known),
                mean_reciprocal_rank=sum(1/c['rank'] for c in known if c['rank'])/len(known),
                expected_abstentions=len(unknown), correct_abstentions=sum(c['correct'] for c in unknown),
                cases=cases)


def main() -> None:
    print(json.dumps(evaluate(), indent=2))
