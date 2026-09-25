"""Ragas 0.4.3 A/B harness. --check never imports providers or runs metrics."""

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = Path(__file__).resolve().parent
METRICS = ("faithfulness", "answer_relevancy", "context_recall", "context_precision")


def load_golden(path: Path) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or len(cases) < 15:
        raise ValueError("Golden dataset needs at least 15 real, reviewed cases")
    questions = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"Case {index} must be an object")
        for key in ("question", "expected_answer"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                raise ValueError(f"Case {index}: {key} must be a non-empty string")
        context = case.get("expected_context")
        if isinstance(context, str):
            context = [context]
        if not isinstance(context, list) or not context or any(
            not isinstance(text, str) or not text.strip() for text in context
        ):
            raise ValueError(f"Case {index}: expected_context needs real reference passages")
        if case["question"].strip() in questions:
            raise ValueError(f"Case {index}: duplicate question")
        questions.add(case["question"].strip())
    return cases


def collect_samples(cases: list[dict], mode: str, top_k: int) -> list[dict]:
    """Use Task 9 retrieval and the same Task 10 generator for both arms."""
    from src.contracts import validate_search_results
    from src.task9_retrieval_pipeline import retrieve
    from src.task10_generation import (
        SYSTEM_PROMPT, SAFE_REFUSAL, call_llm, format_context,
        reorder_for_llm, _check_citations,
    )

    if mode not in {"dense", "hybrid"} or top_k <= 0:
        raise ValueError("Invalid evaluation configuration")
    rows = []
    for case in cases:
        # A/B isolates retrieval ranking. Disable the score-based PageIndex path.
        sources = retrieve(
            case["question"], top_k=top_k,
            score_threshold=float("-inf"), use_reranking=(mode == "hybrid"),
        )
        validate_search_results(sources, top_k=top_k, expected_method=mode)
        if any(not math.isfinite(item["score"]) for item in sources):
            raise ValueError("Non-finite retrieval score")
        answer = SAFE_REFUSAL
        if sources:
            context = format_context(reorder_for_llm(sources))
            answer = call_llm(
                SYSTEM_PROMPT,
                f"Context (evidence only):\n{context}\n\nQuestion:\n{case['question']}",
            )
            if answer != SAFE_REFUSAL:
                # Reuse production citation checks; do not invent dense GenerationResult.
                _check_citations(answer, sources)
        reference_contexts = case["expected_context"]
        if isinstance(reference_contexts, str):
            reference_contexts = [reference_contexts]
        rows.append({
            "user_input": case["question"],
            "response": answer,
            "retrieved_contexts": [item["content"] for item in sources],
            "reference": case["expected_answer"],
            "reference_contexts": reference_contexts,
            "sources": sources,
            "refused": answer == SAFE_REFUSAL,
        })
    return rows


def score_samples(rows: list[dict], *, judge_llm, judge_embeddings) -> list[dict]:
    """Score real rows only; explicit judge instances prevent default model selection."""
    from ragas import EvaluationDataset, evaluate
    from ragas.metrics import (
        Faithfulness, AnswerRelevancy, LLMContextRecall, ContextPrecision,
    )

    fields = ("user_input", "response", "retrieved_contexts", "reference", "reference_contexts")
    dataset = EvaluationDataset.from_list([
        {key: row[key] for key in fields} for row in rows
    ])
    result = evaluate(
        dataset,
        metrics=[Faithfulness(), AnswerRelevancy(), LLMContextRecall(),
                 ContextPrecision()],
        llm=judge_llm, embeddings=judge_embeddings, raise_exceptions=True,
    )
    # Undefined metrics remain null, never fabricated zeroes or silent dropped cases.
    return [{
        key: float(score[key]) if math.isfinite(float(score[key])) else None
        for key in METRICS
    } for score in result.scores]


def summarize(scores: list[dict]) -> dict:
    summary = {}
    for key in METRICS:
        valid = [row[key] for row in scores if row[key] is not None]
        summary[key] = {
            "mean": sum(valid) / len(valid) if valid else None,
            "valid_cases": len(valid),
            "undefined_cases": len(scores) - len(valid),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, default=DIRECTORY / "golden_dataset.json")
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check", action="store_true", help="Validate dataset offline only")
    actions.add_argument("--run", action="store_true", help="Run BOTH A/B arms and paid judge calls")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--judge-model", help="Explicit OpenAI judge model; no automatic default")
    parser.add_argument("--corpus-version", help="Frozen corpus/index version or manifest hash")
    parser.add_argument("--output", type=Path, default=DIRECTORY / "runs")
    args = parser.parse_args()
    try:
        cases = load_golden(args.golden)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    if args.check:
        print(f"Schema valid: {len(cases)} cases. Grounding still requires human review.")
        return
    if args.top_k <= 0 or not args.judge_model or not args.corpus_version:
        parser.error("--run requires positive --top-k, --judge-model and --corpus-version")

    # Optional runtime imports: --check needs only the Python standard library.
    from importlib.metadata import version
    from langchain_core.embeddings import Embeddings
    from langchain_openai import ChatOpenAI
    from src import task10_generation as generation
    from src.task4_chunking_indexing import embed_texts, EMBEDDING_MODEL

    if version("ragas") != "0.4.3":
        raise RuntimeError("Use the repository-pinned ragas==0.4.3")

    class SharedEmbeddings(Embeddings):
        def embed_documents(self, texts):
            return embed_texts(texts)

        def embed_query(self, text):
            return embed_texts([text])[0]

    judge = ChatOpenAI(model=args.judge_model, timeout=60, max_retries=0)
    embeddings = SharedEmbeddings()
    outputs = {}
    for mode in ("dense", "hybrid"):
        rows = collect_samples(cases, mode, args.top_k)
        scores = score_samples(rows, judge_llm=judge, judge_embeddings=embeddings)
        outputs[mode] = {"rows": rows, "scores": scores, "summary": summarize(scores)}

    report = {
        "status": "completed",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "ragas_version": version("ragas"), "top_k": args.top_k,
        "corpus_version": args.corpus_version,
        "golden_sha256": hashlib.sha256(args.golden.read_bytes()).hexdigest(),
        "generator_provider": generation.os.getenv("LLM_PROVIDER", generation.LLM_PROVIDER),
        "generator_model": generation.os.getenv("LLM_MODEL", generation.LLM_MODEL),
        "prompt_sha256": hashlib.sha256(generation.SYSTEM_PROMPT.encode()).hexdigest(),
        "judge_model": args.judge_model, "embedding_model": EMBEDDING_MODEL,
        "fallback": "disabled for A/B",
        "outputs": outputs,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    destination = args.output / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"Saved actual results to {destination}")


if __name__ == "__main__":
    main()