#!/usr/bin/env python3
"""Lucy: local model evolution utility.

- Optional conversion hook for HF -> GGUF (external converter expected).
- Stubbed local QLoRA trigger command builder for Unsloth/LLaMA-Factory.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def apply_dkd_profile(payload: dict) -> dict:
    payload.setdefault("distillation", {})
    payload["distillation"].update(
        {
            "teacher_weight": 0.7,
            "student_weight": 0.3,
            "curriculum": ["easy", "medium", "hard"],
        }
    )
    return payload


def apply_nlq_profile(payload: dict) -> dict:
    payload.setdefault("quantization", {})
    payload["quantization"].update(
        {
            "bucket_edges": [0.0, 0.02, 0.08, 0.2, 0.5, 1.0],
            "bit_allocation": [2, 3, 4, 6, 8],
        }
    )
    return payload


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def convert_hf_to_gguf(converter: Path, model_dir: Path, out_file: Path) -> None:
    run(["python", str(converter), "--model", str(model_dir), "--outfile", str(out_file)])


def trigger_lora_training(config_file: Path, use_dkd: bool = False, use_nlq: bool = False) -> None:
    data = json.loads(config_file.read_text())
    if use_dkd:
        data = apply_dkd_profile(data)
    if use_nlq:
        data = apply_nlq_profile(data)

    effective = config_file.with_suffix(".effective.json")
    effective.write_text(json.dumps(data, indent=2))

    trainer = data.get("trainer", "unsloth")

    if trainer == "unsloth":
        run(["python", "-m", "unsloth.cli", "train", "--config", str(effective)])
    else:
        run(["llamafactory-cli", "train", str(effective)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Lucy evolution utility")
    sub = parser.add_subparsers(dest="cmd", required=True)

    convert = sub.add_parser("convert")
    convert.add_argument("--converter", type=Path, required=True)
    convert.add_argument("--model-dir", type=Path, required=True)
    convert.add_argument("--out", type=Path, required=True)

    train = sub.add_parser("train")
    train.add_argument("--config", type=Path, required=True)
    train.add_argument("--use-dkd", action="store_true", help="Apply dense-knowledge-distillation style profile")
    train.add_argument("--use-nlq", action="store_true", help="Apply non-linear quantization profile")

    args = parser.parse_args()

    if args.cmd == "convert":
        convert_hf_to_gguf(args.converter, args.model_dir, args.out)
    elif args.cmd == "train":
        trigger_lora_training(args.config, use_dkd=args.use_dkd, use_nlq=args.use_nlq)


if __name__ == "__main__":
    main()
