# Literature review: LLM memory, active testing, and decision revision

**Date:** 2026-10-26  
**Status:** Research note only. No protocol change, no R1b/R2/R3 run.

## Executive finding
The literature covers many individual components relevant to Velantrim, but does not by itself replace our R1/R2/R3 series as one controlled evaluation. Avoid broad novelty claims. A possible contribution is the controlled interaction of prior history, discriminative check selection, answer revision, abstention, and a correctness-blind state gate.

## Existing coverage
- Long-context position effects and distractors: *Lost in the Middle* (TACL 2024), GSM-IC (ICML 2023).
- Active information acquisition / hypothesis testing: POPPER (ICML 2025), BED-LLM (ICLR 2026), Fisher-R1/P-Bench (2026 arXiv preprint).
- Feedback and oracle effects: Huang et al. (ICLR 2024), DiscoveryBench (ICML 2024), Reflexion (NeurIPS 2023).
- Memory conflict and abstention: LoCoMo (ACL 2024), LongMemEval (ICLR 2025), ISE (Findings EMNLP 2026).
- Multiple-choice option bias: PriDe (ICLR 2024) and related work.

## Interpretation for our series
- R1: baseline response and label/position robustness.
- R2: memory/context use, active check selection, update after observation, and abstention.
- R3: model-proposed memory mutation versus the external gate's contribution.
- Keep pre-gate and post-gate outcomes separate. Do not call context use or external storage “weight learning.”
- Behavioral results do not establish consciousness, personhood, or subjective experience.

## Open audit questions
1. Check exact novelty against ACED-Bench, NewtonBench, MemoryArena, and other near-neighbor work before claiming novelty.
2. The example task prompt explicitly instructs the model to choose a discriminative test, so selection may measure instruction following rather than spontaneous diagnostic ability.
3. If the environment returns the discriminating observation regardless of the selected action, the action→observation link is broken and active acquisition is not measured.
4. Keep the gate blind to ground truth and report its contribution separately from the model's proposal.
5. Treat exact numerical claims in AI-generated literature reviews as unverified until checked against primary sources. POPPER's official ICML 2025 title is *Automated Hypothesis Validation with Agentic Sequential Falsifications*.

## Scope
This note records a literature synthesis and methodological cautions only. It does not amend the frozen preregistration or experimental materials. No R1b/R2/R3 runs or paid API calls were made.
