"""DeepEval `BaseMetric` classes (structural + semantic) that wrap StructuredJudgeBackend, plus DeepEval LLMTestCase construction."""
from __future__ import annotations

from typing import Any

from scripts.judge.geval_support import StructuredJudgeBackend, TaskArtifacts
from scripts.judge.judge_schema import (
    semantics_score_from_observations,
    structural_score_from_observations,
)


def require_deepeval_base_metric() -> tuple[Any, Any]:
    """Import deepeval's BaseMetric and LLMTestCase, or raise a friendly error if deepeval isn't installed."""
    try:
        from deepeval.metrics import BaseMetric
        from deepeval.test_case import LLMTestCase
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing DeepEval dependency. Install project dependencies with `uv sync`."
        ) from exc
    return BaseMetric, LLMTestCase


def build_metric_classes() -> tuple[type[Any], type[Any]]:
    """Build the StructuralJudgeMetric/SemanticJudgeMetric BaseMetric subclasses (defined dynamically since BaseMetric only exists once deepeval is importable)."""
    BaseMetric, LLMTestCase = require_deepeval_base_metric()

    class StructuralJudgeMetric(BaseMetric):
        """DeepEval metric: harness-computed score from comparing the judge's structural observations against assertions.json."""

        def __init__(self, backend: StructuredJudgeBackend, threshold: float = 1.0, round_index: int = 0):
            self.backend = backend
            self.threshold = threshold
            self.round_index = round_index
            self.score = None
            self.success = None
            self.reason = None
            self.error = None

        def measure(self, test_case: LLMTestCase) -> float:
            """Judge the task (or reuse the cached round) and score its structural observations."""
            cached = self.backend.judge(test_case.name, self.round_index)
            structural_score, _ = structural_score_from_observations(
                self.backend.artifacts_by_task_id[test_case.name].task_dir,
                cached.result.structural_observations,
            )
            self.score = structural_score
            self.reason = cached.result.reason
            self.success = self.score >= self.threshold
            return self.score

        async def a_measure(self, test_case: LLMTestCase) -> float:
            """Async form required by BaseMetric; delegates to the synchronous measure()."""
            return self.measure(test_case)

        def is_successful(self) -> bool:
            """Whether the last measured score met the threshold."""
            if self.error is not None:
                self.success = False
            else:
                self.success = bool((self.score or 0.0) >= self.threshold)
            return self.success

        @property
        def __name__(self) -> str:
            return "Structural Evidence Metric"

    class SemanticJudgeMetric(BaseMetric):
        """DeepEval metric: the judge model's own direct semantics_score (connections, text placement, layout, spelling, arrow alignment)."""

        def __init__(self, backend: StructuredJudgeBackend, threshold: float = 1.0, round_index: int = 0):
            self.backend = backend
            self.threshold = threshold
            self.round_index = round_index
            self.score = None
            self.success = None
            self.reason = None
            self.error = None

        def measure(self, test_case: LLMTestCase) -> float:
            """Judge the task (or reuse the cached round) and return its direct semantics_score."""
            cached = self.backend.judge(test_case.name, self.round_index)
            semantics_score, _ = semantics_score_from_observations(
                cached.result.semantics,
            )
            self.score = semantics_score
            self.reason = cached.result.reason
            self.success = self.score >= self.threshold
            return self.score

        async def a_measure(self, test_case: LLMTestCase) -> float:
            """Async form required by BaseMetric; delegates to the synchronous measure()."""
            return self.measure(test_case)

        def is_successful(self) -> bool:
            """Whether the last measured score met the threshold."""
            if self.error is not None:
                self.success = False
            else:
                self.success = bool((self.score or 0.0) >= self.threshold)
            return self.success

        @property
        def __name__(self) -> str:
            return "Semantic GEval Style Metric"

    return StructuralJudgeMetric, SemanticJudgeMetric


def build_test_case(task_id: str, artifacts: TaskArtifacts) -> Any:
    """Build the DeepEval LLMTestCase for a task (prompt as input, generated text as actual_output, reference.ascii as expected_output)."""
    _, LLMTestCase = require_deepeval_base_metric()
    return LLMTestCase(
        name=task_id,
        input=(artifacts.task_dir / "prompt.txt").read_text().strip(),
        actual_output=artifacts.output_text,
        expected_output=(artifacts.task_dir / "reference.ascii").read_text().strip()
        if (artifacts.task_dir / "reference.ascii").exists()
        else "",
    )
