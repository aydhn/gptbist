# Developer Next Feature Flow Example

This demonstrates how a developer introduces a new research metric, maintaining strict compliance with the release requirements.

1. **Write the Code & Models**
Create `bist_signal_bot/new_metric/models.py`. Use Pydantic or Dataclasses.
```python
from pydantic import BaseModel
class MetricScore(BaseModel):
    value: float
```

2. **Add Deterministic Tests**
Create `bist_signal_bot/tests/test_new_metric.py`. Ensure tests do not touch the network or real disk outside of `tmp_path`.

3. **Expose CLI Commands**
Add parsers and handlers in `bist_signal_bot/cli/commands.py` and `parsers.py`.

4. **Run Local Checks**
```bash
python -m bist_signal_bot qa release-gate
python -m bist_signal_bot final-audit run
```

5. **Generate Updated Handoff**
```bash
python -m bist_signal_bot final-handoff build --save
```
