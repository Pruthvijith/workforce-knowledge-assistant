"""Evaluate source selection and demonstrate an authorized answer and abstention."""
import json
from workforce_knowledge.answer import answer
from workforce_knowledge.evaluate import evaluate


def main() -> None:
    report = evaluate()
    misses = [case for case in report.pop('cases') if not case['correct']]
    results = [answer(q)
               for q in ('How can I correct a missed clock entry?', 'Book a bicycle repair')]
    assert results[0]['citation'] == 'clock.correction' and results[1]['status'] == 'abstained'
    print(json.dumps(dict(metrics=report, misses=misses, responses=results), indent=2))


if __name__ == '__main__':
    main()
