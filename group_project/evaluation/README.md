# Evaluation preparation

Status: NOT RUN. No measured scores or grounded golden cases have been produced.

## Repository expectations

- README and docs/STEP_BY_STEP.md require at least 15 golden cases, four metrics,
  and Dense-only vs Hybrid + RRF under the same remaining configuration.
- pyproject.toml pins ragas==0.4.3. No evaluation runner was supplied.
- reports/RESULT.md is the supplied report template; acceptance tests look for
  group_project/evaluation/RESULT.md instead.
- The empty golden_dataset.json is now valid JSON ([]), not a completed dataset.

## Golden dataset

The root is an array with at least 15 reviewed objects. Required fields:

| Field | Meaning | Runner format |
| --- | --- | --- |
| question | A real question grounded in the frozen corpus | Non-empty string |
| expected_answer | Human-reviewed reference answer | Non-empty string |
| expected_context | Actual evidence passages, not a filename alone | Non-empty string or list of non-empty strings |

The acceptance test only checks the three keys and non-empty string conversions;
it does not verify grounding or specify exact value types. The runner validates
types more strictly and preserves any extra fields. No extra required field has
been added to the golden schema. Optional source IDs/URLs can help manual review.

Do not fill the golden file with placeholder strings just to pass acceptance.
Capture corpus location/page/section while reviewing each case. Freeze the same
corpus/index version for both arms. expected_answer/context never go into the
generator prompt.

## Runner

From the repository root, offline validation only:

~~~powershell
python -m group_project.evaluation.run_evaluation --check
~~~

This currently fails honestly because there are zero reviewed cases.

Only AFTER the corpus, Task 9, environment, generator and judge are ready:

~~~powershell
python -m group_project.evaluation.run_evaluation --run --top-k 5 --judge-model YOUR_APPROVED_JUDGE_MODEL --corpus-version YOUR_FROZEN_CORPUS_VERSION
~~~

Replace the two explicit placeholders; the runner does not choose a model.
--run calls providers and can incur API costs. Nothing has been run at this stage.
The prepared CLI uses the already-declared langchain-openai dependency for an
OpenAI judge (OPENAI_API_KEY); the generation provider remains the one configured
by Task 10. Judge embeddings reuse Task 4 embed_texts(), without an extra model.
No dependency or environment settings were changed.

The command runs both arms sequentially:
- A: Task 9 retrieve(..., use_reranking=False, score_threshold=-inf).
- B: Task 9 retrieve(..., use_reranking=True, score_threshold=-inf).
- Same golden, generator, system prompt, reordering, top_k, judge and embeddings.
- PageIndex is disabled for this comparison; test fallback separately.
- Returned methods must be dense for A and hybrid for B; PageIndex results cause
  an explicit failure rather than silently contaminating the experiment.
- Recheck Task 9 after merge: its threshold implementation must accept -inf.
  The starter may still execute BM25 in the dense arm; this is a ranking A/B,
  NOT a clean latency/cost benchmark for a standalone dense-only implementation.

GenerationResult does not allow retrieval_source=dense. The runner therefore
does NOT relabel dense as hybrid or patch production globals. It evaluates both
arms through the same lower-level Task 10 prompt/format/reorder/call_llm helpers
and citation checker, retaining original SearchResult records. It produces
evaluation rows, not fake production GenerationResult objects. It is a controlled
retrieval ablation, not a full production orchestration/fallback benchmark.
Provider/retrieval/citation errors abort the run instead of becoming invented
scores. Empty retrieval and genuine model refusals are retained, not dropped.

## Four metrics (Ragas 0.4.3)

| Report label | Ragas class / output key |
| --- | --- |
| Faithfulness | Faithfulness / faithfulness |
| Answer relevance | AnswerRelevancy / answer_relevancy |
| Context recall | LLMContextRecall / context_recall |
| Context precision | ContextPrecision / context_precision |

Question -> user_input; actual generated answer -> response;
actual retrieved contents in retrieval rank -> retrieved_contexts;
expected_answer -> reference; expected_context -> reference_contexts.

The selected LLM-based recall/precision metrics judge against the reference
answer; they do not directly perform text matching against expected_context.
Reference passages remain available for human verification and traceability.
Ragas evaluate() is deprecated but still provided by the repository-pinned
0.4.3; this scaffold deliberately does not upgrade dependencies.

Only a successful real run writes a timestamped JSON under runs/: full evidence,
answers, per-case scores, means, counts of valid/undefined scores and run config.
Undefined values become null, never zero; report denominators when comparing.
The Markdown report is not automatically marked complete. Record actual results,
at least three worst cases, refusal rates and grounded recommendations manually.

## Pending acceptance

golden_dataset.json intentionally has fewer than 15 cases.
RESULT.md intentionally retains TODO markers: it is not a finished report.
Both related completion tests should fail until real work is completed.