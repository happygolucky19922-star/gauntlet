from __future__ import annotations


def dense_knowledge_distillation_profile() -> dict[str, object]:
    """Return a conservative local DKD-style training profile.

    This is a practical, local configuration inspired by public distillation ideas
    (teacher/student weighting, progressive curriculum).
    """
    return {
        "name": "dkd_local_profile",
        "teacher_weight": 0.7,
        "student_weight": 0.3,
        "curriculum": ["easy", "medium", "hard"],
        "epochs": 1,
        "notes": "Use successful gauntlet traces as supervised pairs for local fine-tune.",
    }


def nonlinear_quantization_profile() -> dict[str, object]:
    """Return non-linear bucket defaults for local quantization experiments."""
    return {
        "name": "nonlinear_quant_profile",
        "bucket_edges": [0.0, 0.02, 0.08, 0.2, 0.5, 1.0],
        "bit_allocation": [2, 3, 4, 6, 8],
        "target": "llama.cpp sidecar",
        "notes": "Allocate more bits to high-saliency activation ranges.",
    }


def patent_profiles() -> dict[str, dict[str, object]]:
    return {
        "dense_knowledge_distillation": dense_knowledge_distillation_profile(),
        "nonlinear_quantization": nonlinear_quantization_profile(),
    }
