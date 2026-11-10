from app.generators import REGISTRY
from app.generators.seed_bank import SEEDS


def test_every_seed_passes_its_own_validator() -> None:
    for task_type, difficulty, payload in SEEDS:
        gen = REGISTRY[task_type]
        item = gen.item_model.model_validate(payload)
        assert gen.validate(item, gen.params(difficulty)) == [], (task_type, payload)
