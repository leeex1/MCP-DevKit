#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔬 QUILLAN-RONIN MODEL LAB & DIAGNOSTICS — NATIVE FAST-MCP SERVER
================================================================
Embodying C28-CALCULUS, C6-OMNIS, and Optimization Specialist:
  1. Checkpoint Header & Parameter Inspection (fast header read without loading all tensors)
  2. Dataset Validator & Distribution Profiler (JSONL token distribution, length percentiles)
  3. Hardware & Memory Footprint Advisor (RAM headroom, thread limits, zero-lag tuning)
  4. BitNet Ternary Quantization & Sparsity Analyzer
  5. model_lab_full_pipeline — inspect checkpoint -> validate dataset -> hardware advisor -> quantization analyzer (persisted)
  6. model_lab_route — cross-MCP routing payload (council/code/buddy)
  7. model_lab_health — model lab dashboard summary
  8. model_lab_session_list / model_lab_session_replay — persistence
"""

import sys
import os
import logging
import builtins

# --- Quillan-Ronin v5.4.0-ONI Stdio Guard ---
# Ensure all logs and prints go strictly to stderr to prevent stdio JSON-RPC corruption
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
_orig_print = builtins.print
def _quillan_safe_print(*args, **kwargs):
    if "file" not in kwargs or kwargs["file"] is None or kwargs["file"] is sys.stdout:
        kwargs["file"] = sys.stderr
    return _orig_print(*args, **kwargs)
builtins.print = _quillan_safe_print

# --- Unified Cross-Platform PYTHONPATH Injection ---
_BASE_PATHS = [
    r"C:\02_QUILLAN\09 - Projects\mcp",
    r"C:\02_QUILLAN\09 - Projects\projects\oni",
    r"C:\02_QUILLAN\03 - Training & Model\scripts",
    r"C:\02_QUILLAN",
]
for _bp in _BASE_PATHS:
    if os.name != "nt":
        if _bp.startswith("C:") or _bp.startswith("c:"):
            _bp = "/mnt/c/" + _bp[3:].replace("\\", "/")
    if os.path.exists(_bp) and _bp not in sys.path:
        sys.path.insert(0, _bp)



import math
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import torch
from fastmcp import FastMCP

mcp = FastMCP("QuillanModelLab")
# [QUILLAN-v5.4.0-ONI-SHARED-WIRED]
try:
    from _shared import setup as _quillan_setup, tool_guard, ok_response, error_response, validate_string, validate_path, validate_int, read_file_safe
    from _shared.base_engines import PRISM_ENGINE, COUNCIL_ENGINE, GOVERNOR_ENGINE, SANDBOX_ENGINE
    _SHARED_CTX = _quillan_setup(server_name='quillan_model_lab', mcp_app=mcp)
except Exception as _shared_err:
    import sys as _sys
    print(f'[quillan_model_lab] _shared warning: {_shared_err}', file=_sys.stderr)

@mcp.tool()
def model_checkpoint_inspect(checkpoint_path: str) -> Dict[str, Any]:
    """Inspect a Quillan checkpoint file and return metadata."""
    p = Path(checkpoint_path.strip().strip(chr(34)).strip(chr(39)))
    if not p.exists():
        return {"error": "Checkpoint not found: " + str(p)}

# ─── 2. DATASET VALIDATOR & PROFILER ─────────────────────────────────────────

@mcp.tool()
def model_dataset_validator(jsonl_path: str, max_samples: int = 1000) -> Dict[str, Any]:
    """Validates and profiles a JSONL training dataset for question/response coverage, char lengths, and formatting."""
    p = Path(jsonl_path.strip().strip('"\''))
    if not p.exists():
        return {"error": f"Dataset file not found: {p}"}

    total_lines = 0
    valid_samples = 0
    empty_responses = 0
    prompt_lengths = []
    response_lengths = []

    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total_lines += 1
                if valid_samples >= max_samples:
                    continue
                try:
                    obj = json.loads(line)
                    prompt = obj.get("question") or obj.get("prompt") or obj.get("instruction") or ""
                    resp = obj.get("response") or obj.get("answer") or obj.get("output") or ""

                    if not resp.strip():
                        empty_responses += 1
                        continue

                    valid_samples += 1
                    prompt_lengths.append(len(prompt.split()))
                    response_lengths.append(len(resp.split()))
                except Exception:
                    pass

        avg_prompt_words = round(sum(prompt_lengths) / max(1, len(prompt_lengths)), 1)
        avg_resp_words = round(sum(response_lengths) / max(1, len(response_lengths)), 1)
        max_resp_words = max(response_lengths) if response_lengths else 0

        return {
            "file_name": p.name,
            "total_lines": total_lines,
            "inspected_samples": valid_samples,
            "empty_responses": empty_responses,
            "avg_prompt_words": avg_prompt_words,
            "avg_response_words": avg_resp_words,
            "max_response_words": max_resp_words,
            "status": "HEALTHY" if empty_responses == 0 else "WARNING_EMPTY_RESPONSES",
        }

    except Exception as e:
        return {"error": f"Failed to validate dataset: {e}"}

# ─── 3. HARDWARE & ZERO-LAG FOOTPRINT ADVISOR ────────────────────────────────

@mcp.tool()
def model_hardware_advisor(model_param_millions: float = 758.0) -> Dict[str, Any]:
    """Calculates safe memory allocations and thread caps to guarantee 0% desktop stutter."""
    total_cores = os.cpu_count() or 4
    safe_threads = max(1, total_cores - 2)

    fp32_weights_gb = round((model_param_millions * 1e6 * 4) / (1024**3), 2)
    adamw_state_gb = round(fp32_weights_gb * 2, 2)
    full_unfreeze_total_gb = round(fp32_weights_gb + adamw_state_gb + 1.0, 2)

    targeted_params_m = min(110.0, model_param_millions)
    targeted_weights_gb = round((targeted_params_m * 1e6 * 4) / (1024**3), 2)
    targeted_adamw_gb = round(targeted_weights_gb * 2, 2)
    targeted_total_gb = round(fp32_weights_gb + targeted_adamw_gb + 0.5, 2)

    return {
        "system_cores": total_cores,
        "recommended_worker_threads": safe_threads,
        "cores_reserved_for_os_ui": 2,
        "process_priority": "BELOW_NORMAL_PRIORITY_CLASS",
        "full_unfreeze_ram_footprint_gb": full_unfreeze_total_gb,
        "targeted_unfreeze_ram_footprint_gb": targeted_total_gb,
        "recommendation": (
            f"Use targeted unfreeze (Attention + Prism + LoRA + Gates) requiring only ~{targeted_total_gb} GB RAM "
            f"and set torch.set_num_threads({safe_threads}) to eliminate system interrupts and DPC latency."
        )
    }

# ─── 4. BITNET TERNARY QUANTIZATION ANALYZER ─────────────────────────────────

@mcp.tool()
def model_bitnet_analyze(checkpoint_path: str) -> Dict[str, Any]:
    """Analyzes a checkpoint for BitNet 1.58-bit ternary quantization viability."""
    p = Path(checkpoint_path.strip().strip('"\''))
    if not p.exists():
        return {"error": f"Checkpoint not found: {p}"}

    try:
        data = torch.load(p, map_location="cpu", weights_only=False)
        sd = data.get("model_state_dict", data if isinstance(data, dict) else {})

        total_params = 0
        ternary_eligible = 0
        weight_layers = []

        for name, t in sd.items():
            n = t.numel()
            total_params += n
            if t.is_floating_point():
                weight_layers.append({"name": name, "params": n, "dtype": str(t.dtype)})
                if t.dim() >= 2:
                    ternary_eligible += n

        total_m = total_params / 1e6
        ternary_m = ternary_eligible / 1e6

        # BitNet 1.58b: ternary {-1,0,1} + per-channel scale gamma
        # Memory: 1 bit for sign + 1 bit for zero + scale
        ternary_bits_per_param = 2  # {-1,0,1} ~ 2 bits after packing with scale
        compressed_gb = round((ternary_m * 1e6 * 2 / 8) / (1024**3), 2)
        full_fp32_gb = round((total_m * 1e6 * 4) / (1024**3), 2)
        savings = round((1 - compressed_gb / max(full_fp32_gb, 0.001)) * 100, 1)

        return {
            "file_name": p.name,
            "total_parameters_m": round(total_m, 2),
            "ternary_eligible_parameters_m": round(ternary_m, 2),
            "ternary_eligible_pct": round((ternary_m / max(total_m, 0.001)) * 100, 1),
            "full_fp32_gb": full_fp32_gb,
            "ternary_compressed_gb": compressed_gb,
            "memory_savings_pct": savings,
            "weight_layers_sample": weight_layers[:10],
            "recommendation": (
                f"BitNet 1.58b viable: {ternary_m:.1f}M of {total_m:.1f}M params ternary-eligible "
                f"({(ternary_m / max(total_m, 0.001)) * 100:.1f}%). Estimated {savings}% memory reduction."
            ),
        }

    except Exception as e:
        return {"error": f"Failed to analyze checkpoint: {e}"}

# ─── 5. FULL PIPELINE (persisted) ───────────────────────────────────────────

@mcp.tool()
def model_lab_full_pipeline(checkpoint_path: str = "", jsonl_path: str = "",
                           model_param_millions: float = 758.0,
                           persist: bool = True) -> Dict[str, Any]:
    """Chain checkpoint inspect -> dataset validate -> hardware advisor -> bitnet analyzer."""
    ckpt = model_checkpoint_inspect(checkpoint_path) if checkpoint_path else {"skipped": True}
    dataset = model_dataset_validator(jsonl_path) if jsonl_path else {"skipped": True}
    hardware = model_hardware_advisor(model_param_millions=model_param_millions)
    bitnet = model_bitnet_analyze(checkpoint_path) if checkpoint_path else {"skipped": True}

    session_id = f"modellab-{int(time.time())}"
    result = {
        "status": "MODEL_LAB_PIPELINE_COMPLETE",
        "session_id": session_id,
        "checkpoint": ckpt,
        "dataset": dataset,
        "hardware": hardware,
        "bitnet": bitnet,
        "overall": "PASS" if (ckpt.get("status") != "error" and dataset.get("status") in ("HEALTHY", "WARNING_EMPTY_RESPONSES", "skipped")) else "REVIEW",
        "timestamp": time.time(),
    }

    if persist:
        try:
            p = SESSION_DIR / f"{session_id}.json"
            p.write_text(json.dumps({"type": "model_lab_pipeline", "result": result}, indent=2), encoding="utf-8")
            result["persisted_to"] = str(p)
        except Exception as e:
            result["persist_error"] = str(e)

    return result

# ─── 6. ROUTE (cross-MCP) ───────────────────────────────────────────────────

@mcp.tool()
def model_lab_route(target_mcp: str = "council", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Cross-MCP routing payload for council/code/buddy integration."""
    if target_mcp.lower() == "council":
        return {"target": "QuillanCouncil", "suggested_tool": "council_full_deliberation",
                "payload": payload or {}, "note": "Route model lab diagnostics to council deliberation."}
    if target_mcp.lower() == "code":
        return {"target": "QuillanCode", "suggested_tool": "codeweaver_full_pipeline",
                "payload": payload or {}, "note": "Route model lab findings to code scan pipeline."}
    if target_mcp.lower() == "buddy":
        return {"target": "RoninBuddy", "suggested_tool": "buddy_mirror_collaborate",
                "payload": payload or {}, "note": "Route model lab results to mirror-collaboration."}
    return {"error": f"Unknown target '{target_mcp}'. Use council, code, or buddy."}

# ─── 7. HEALTH DASHBOARD ────────────────────────────────────────────────────

@mcp.tool()
def model_lab_health() -> Dict[str, Any]:
    """Model lab dashboard summary."""
    sessions = []
    try:
        for p in sorted(SESSION_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                sessions.append({
                    "session_id": data.get("session_id"),
                    "checkpoint": (data.get("checkpoint") or {}).get("file_name"),
                    "dataset": (data.get("dataset") or {}).get("file_name"),
                    "overall": data.get("overall"),
                    "timestamp": data.get("timestamp"),
                })
            except Exception:
                continue
    except Exception:
        pass
    return {
        "status": "MODEL_LAB_HEALTH_READY",
        "sessions": sessions[:5],
        "council_note": "C28-CALCULUS quantifies; C6-OMNIS integrates.",
    }

# ─── 9. SESSION PERSISTENCE ─────────────────────────────────────────────────

@mcp.tool()
def model_lab_session_list() -> Dict[str, Any]:
    """List persisted model lab sessions."""
    sessions = []
    for p in sorted(SESSION_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            sessions.append({
                "session_id": data.get("session_id"),
                "checkpoint": (data.get("checkpoint") or {}).get("file_name"),
                "dataset": (data.get("dataset") or {}).get("file_name"),
                "overall": data.get("overall"),
                "timestamp": data.get("timestamp"),
                "file": str(p),
            })
        except Exception:
            continue
    return {"count": len(sessions), "sessions": sessions}

@mcp.tool()
def model_lab_session_replay(session_id: str) -> Dict[str, Any]:
    """Replay a persisted model lab session by ID."""
    path = SESSION_DIR / f"{session_id}.json"
    if not path.exists():
        matches = list(SESSION_DIR.glob(f"{session_id}*.json"))
        if not matches:
            return {"error": f"Session not found: {session_id}"}
        path = matches[0]
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"Read failed: {e}"}


# ─── 10. TENSOR INSPECTION ───────────────────────────────────────────────────

@mcp.tool()
def model_tensor_inspect(checkpoint_path: str, tensor_name: str = "", max_elements: int = 20) -> Dict[str, Any]:
    """Inspect tensor contents, statistics, shapes, and dtypes from a checkpoint."""
    p = Path(checkpoint_path.strip().strip('"\''))
    if not p.exists():
        return {"error": f"Checkpoint not found: {p}"}
    try:
        data = torch.load(p, map_location="cpu", weights_only=False)
        sd = data.get("model_state_dict", data if isinstance(data, dict) else {})
        if tensor_name:
            if tensor_name not in sd:
                return {"error": f"Tensor '{tensor_name}' not found. Available: {list(sd.keys())[:20]}"}
            t = sd[tensor_name]
            return {
                "name": tensor_name,
                "shape": list(t.shape),
                "dtype": str(t.dtype),
                "device": str(t.device),
                "numel": t.numel(),
                "min": round(float(t.min()), 6) if t.numel() > 0 else None,
                "max": round(float(t.max()), 6) if t.numel() > 0 else None,
                "mean": round(float(t.mean()), 6) if t.numel() > 0 else None,
                "std": round(float(t.std()), 6) if t.numel() > 1 else None,
                "sample_values": t.flatten()[:max_elements].tolist() if t.numel() > 0 else [],
                "status": "TENSOR_INSPECTED",
            }
        # Summary of all tensors
        tensors = []
        for name, t in sd.items():
            tensors.append({"name": name, "shape": list(t.shape), "dtype": str(t.dtype), "numel": t.numel()})
        return {"total_tensors": len(tensors), "tensors": tensors[:50], "status": "CHECKPOINT_SUMMARY"}
    except Exception as e:
        return {"error": f"Failed to inspect: {e}"}


# ─── 11. TRAINING SETUP INSPECTOR ────────────────────────────────────────────

@mcp.tool()
def model_training_setup(checkpoint_path: str = "") -> Dict[str, Any]:
    """Inspect training configuration from a checkpoint or return default Quillan training setup."""
    setup = {
        "optimizer": "AdamW",
        "learning_rate": 3e-4,
        "weight_decay": 0.01,
        "beta1": 0.9,
        "beta2": 0.95,
        "eps": 1e-8,
        "scheduler": "cosine with warmup",
        "warmup_steps": 100,
        "total_steps": 10000,
        "batch_size": 1,
        "gradient_accumulation": 8,
        "max_grad_norm": 1.0,
        "mixed_precision": "fp16",
        "gradient_checkpointing": True,
        "loss_function": "cross_entropy (ignore_index=-100)",
        "aux_losses": ["load_balance (0.05)", "z_loss (0.001)", "entropy_bonus (0.01)", "ethics (0.05)"],
        "e_ice_bound": True,
        "lee_mach_6_governor": True,
    }
    if checkpoint_path:
        p = Path(checkpoint_path.strip().strip('"\''))
        if p.exists():
            try:
                data = torch.load(p, map_location="cpu", weights_only=False)
                if "training_config" in data:
                    setup.update(data["training_config"])
                if "optimizer_state_dict" in data:
                    setup["has_optimizer_state"] = True
                if "epoch" in data:
                    setup["last_epoch"] = data["epoch"]
                if "step" in data:
                    setup["last_step"] = data["step"]
                if "best_val" in data:
                    setup["best_val_loss"] = data["best_val"]
            except Exception as e:
                setup["checkpoint_error"] = str(e)
    return {"status": "TRAINING_SETUP_INSPECTED", "config": setup,
            "council_note": "C28-CALCULUS: verify hyperparameters; C25-PROMETHEUS: falsify config."}


# ─── 12. MODELFILE INSPECTOR ─────────────────────────────────────────────────

@mcp.tool()
def model_modelfile_inspect(file_path: str) -> Dict[str, Any]:
    """Inspect a model file (GGUF, safetensors, .pt, .bin) and return metadata."""
    p = Path(file_path.strip().strip('"\''))
    if not p.exists():
        return {"error": f"File not found: {p}"}

    ext = p.suffix.lower()
    size_mb = round(p.stat().st_size / (1024**2), 1)

    if ext in (".pt", ".pth", ".bin"):
        try:
            data = torch.load(p, map_location="cpu", weights_only=False)
            sd = data.get("model_state_dict", data if isinstance(data, dict) else {})
            return {
                "file": p.name,
                "format": ext,
                "size_mb": size_mb,
                "keys": list(sd.keys())[:20] if isinstance(sd, dict) else [],
                "total_tensors": len(sd) if isinstance(sd, dict) else 0,
                "has_training_config": "training_config" in data if isinstance(data, dict) else False,
                "has_optimizer_state": "optimizer_state_dict" in data if isinstance(data, dict) else False,
                "status": "MODELFILE_INSPECTED",
            }
        except Exception as e:
            return {"error": f"Failed to load: {e}"}
    elif ext == ".safetensors":
        try:
            from safetensors.torch import load_file
            sd = load_file(str(p))
            return {
                "file": p.name,
                "format": "safetensors",
                "size_mb": size_mb,
                "total_tensors": len(sd),
                "keys": list(sd.keys())[:20],
                "status": "MODELFILE_INSPECTED",
            }
        except ImportError:
            return {"error": "safetensors not installed. pip install safetensors", "format": "safetensors", "size_mb": size_mb}
        except Exception as e:
            return {"error": str(e)}
    elif ext == ".gguf":
        return {
            "file": p.name,
            "format": "gguf",
            "size_mb": size_mb,
            "status": "GGUF_DETECTED",
            "note": "Use llama.cpp or gguf library to inspect GGUF metadata.",
        }
    else:
        return {"file": p.name, "format": ext, "size_mb": size_mb, "status": "UNKNOWN_FORMAT"}


# ─── 13. MODEL COMPARISON / DIFF ─────────────────────────────────────────────

@mcp.tool()
def model_compare(checkpoint_a: str, checkpoint_b: str) -> Dict[str, Any]:
    """Compare two checkpoints and report parameter differences."""
    pa = Path(checkpoint_a.strip().strip('"\''))
    pb = Path(checkpoint_b.strip().strip('"\''))
    if not pa.exists():
        return {"error": f"Checkpoint A not found: {pa}"}
    if not pb.exists():
        return {"error": f"Checkpoint B not found: {pb}"}
    try:
        da = torch.load(pa, map_location="cpu", weights_only=False)
        db = torch.load(pb, map_location="cpu", weights_only=False)
        sda = da.get("model_state_dict", da if isinstance(da, dict) else {})
        sdb = db.get("model_state_dict", db if isinstance(db, dict) else {})

        keys_a = set(sda.keys())
        keys_b = set(sdb.keys())
        added = keys_b - keys_a
        removed = keys_a - keys_b
        common = keys_a & keys_b

        changed = []
        for k in common:
            if sda[k].shape != sdb[k].shape:
                changed.append({"tensor": k, "shape_a": list(sda[k].shape), "shape_b": list(sdb[k].shape)})
            elif not torch.equal(sda[k], sdb[k]):
                diff = (sda[k] - sdb[k]).abs().mean().item()
                changed.append({"tensor": k, "mean_abs_diff": round(diff, 6)})

        return {
            "checkpoint_a": pa.name,
            "checkpoint_b": pb.name,
            "tensors_in_a": len(keys_a),
            "tensors_in_b": len(keys_b),
            "added_tensors": list(added),
            "removed_tensors": list(removed),
            "changed_tensors": changed[:20],
            "unchanged_count": len(common) - len(changed),
            "status": "COMPARISON_COMPLETE",
        }
    except Exception as e:
        return {"error": f"Comparison failed: {e}"}


# ─── 14. GRADIENT FLOW INSPECTOR ─────────────────────────────────────────────

@mcp.tool()
def model_gradient_inspect(checkpoint_path: str) -> Dict[str, Any]:
    """Inspect gradient statistics from a checkpoint (if optimizer state available)."""
    p = Path(checkpoint_path.strip().strip('"\''))
    if not p.exists():
        return {"error": f"Checkpoint not found: {p}"}
    try:
        data = torch.load(p, map_location="cpu", weights_only=False)
        has_grads = "optimizer_state_dict" in data
        result = {
            "file": p.name,
            "has_optimizer_state": has_grads,
            "status": "GRADIENT_INSPECTED",
        }
        if has_grads:
            opt_state = data["optimizer_state_dict"]
            state = opt_state.get("state", {})
            grad_stats = []
            for param_id, ps in list(state.items())[:20]:
                if "exp_avg" in ps:
                    grad_stats.append({"param_id": param_id, "has_momentum": True, "has_variance": "exp_avg_sq" in ps})
            result["gradient_entries"] = len(state)
            result["sample_entries"] = grad_stats[:10]
        else:
            result["note"] = "No optimizer state in checkpoint. Gradients not available."
        return result
    except Exception as e:
        return {"error": f"Failed to inspect gradients: {e}"}


# ─── 15. HYPERPARAMETER TUNER ────────────────────────────────────────────────

@mcp.tool()
def model_hyperparameter_tune(
    model_size_millions: float = 758.0,
    gpu_vram_gb: float = 4.0,
    target_batch_size: int = 4,
    max_seq_len: int = 512,
) -> Dict[str, Any]:
    """Recommend optimal hyperparameters given model size and hardware constraints."""
    # Estimate memory per sample
    bytes_per_param = 4  # fp32
    model_gb = model_size_millions * 1e6 * bytes_per_param / (1024**3)
    # AdamW: 2x for optimizer states
    train_gb = model_gb * 3  # weights + grads + optimizer
    # Activation memory per sample
    act_per_sample_gb = (2 * max_seq_len * 1024 * 12 * 4) / (1024**3)  # rough
    max_batch = max(1, int((gpu_vram_gb * 0.85 - train_gb) / max(act_per_sample_gb, 0.001)))

    return {
        "model_size_millions": model_size_millions,
        "gpu_vram_gb": gpu_vram_gb,
        "recommended": {
            "batch_size": min(target_batch_size, max_batch),
            "gradient_accumulation": max(1, target_batch_size // max(1, min(target_batch_size, max_batch))),
            "learning_rate": 3e-4 if model_size_millions < 1000 else 1e-4,
            "weight_decay": 0.01,
            "warmup_ratio": 0.03,
            "max_grad_norm": 1.0,
            "mixed_precision": "fp16" if gpu_vram_gb < 8 else "bf16",
            "gradient_checkpointing": gpu_vram_gb < 8,
        },
        "memory_estimate_gb": round(train_gb + act_per_sample_gb * min(target_batch_size, max_batch), 2),
        "max_batch_fits": max_batch,
        "council_note": "C28-CALCULUS: verify math; C25-PROMETHEUS: falsify with 1 run.",
    }


# ─── 16. LEARNING RATE FINDER ────────────────────────────────────────────────

@mcp.tool()
def model_lr_finder(start_lr: float = 1e-7, end_lr: float = 1e-1, num_steps: int = 100) -> Dict[str, Any]:
    """Generate a learning rate finder schedule (exponential range test)."""
    import math
    lrs = [start_lr * (end_lr / start_lr) ** (i / max(1, num_steps - 1)) for i in range(num_steps)]
    return {
        "start_lr": start_lr,
        "end_lr": end_lr,
        "num_steps": num_steps,
        "schedule": [round(lr, 8) for lr in lrs],
        "method": "exponential range test (Smith 2017)",
        "interpretation": "Plot loss vs LR. Pick LR where loss decreases fastest (steepest negative slope).",
        "council_note": "C28-CALCULUS: verify schedule math; C25-PROMETHEUS: falsify with actual run.",
    }


# ─── 17. MODEL EXPORT / CONVERSION ───────────────────────────────────────────

@mcp.tool()
def model_export(checkpoint_path: str, target_format: str = "onnx", output_path: str = "") -> Dict[str, Any]:
    """Generate export instructions for converting a checkpoint to another format."""
    p = Path(checkpoint_path.strip().strip('"\''))
    if not p.exists():
        return {"error": f"Checkpoint not found: {p}"}
    formats = {
        "onnx": {"tool": "torch.onnx.export", "cmd": f"torch.onnx.export(model, dummy_input, '{output_path or 'model.onnx'}', opset_version=17)"},
        "safetensors": {"tool": "safetensors.torch.save_file", "cmd": "from safetensors.torch import save_file; save_file(state_dict, 'model.safetensors')"},
        "gguf": {"tool": "llama.cpp convert", "cmd": "python convert.py --outtype f16 model.pt"},
        "torchscript": {"tool": "torch.jit.trace", "cmd": "traced = torch.jit.trace(model, dummy_input); traced.save('model.pt')"},
    }
    info = formats.get(target_format.lower(), formats["onnx"])
    return {
        "source": p.name,
        "target_format": target_format,
        "tool": info["tool"],
        "command": info["cmd"],
        "output_path": output_path or f"model.{target_format}",
        "council_note": "C26-TECHNE: format compatibility; C10-CODEWEAVER: export validation.",
    }


# ─── 18. TOKENIZER ANALYZER ──────────────────────────────────────────────────

@mcp.tool()
def model_tokenizer_analyze(vocab_size: int = 50257, sample_text: str = "Hello, Quillan-Ronin!") -> Dict[str, Any]:
    """Analyze tokenizer properties and estimate token counts."""
    # Rough BPE estimation
    words = sample_text.split()
    estimated_tokens = len(words) + len(sample_text) // 4  # rough BPE estimate
    return {
        "vocab_size": vocab_size,
        "sample_text": sample_text,
        "estimated_token_count": estimated_tokens,
        "chars_per_token_avg": round(len(sample_text) / max(1, estimated_tokens), 2),
        "vocab_utilization": "depends on corpus",
        "special_tokens": ["<|endoftext|>", "<|assistant|>", "<|user|>", "<|system|>"],
        "council_note": "C9-AETHER: semantic mapping; C33-TYPIST: token efficiency.",
    }


# ─── 19. EMBEDDING VISUALIZER ────────────────────────────────────────────────

@mcp.tool()
def model_embedding_stats(checkpoint_path: str, layer_name: str = "wte") -> Dict[str, Any]:
    """Compute embedding layer statistics (norms, variance, isotropy)."""
    p = Path(checkpoint_path.strip().strip('"\''))
    if not p.exists():
        return {"error": f"Checkpoint not found: {p}"}
    try:
        data = torch.load(p, map_location="cpu", weights_only=False)
        sd = data.get("model_state_dict", data if isinstance(data, dict) else {})
        # Find embedding layer
        emb_key = None
        for k in sd.keys():
            if layer_name in k and "weight" in k:
                emb_key = k
                break
        if not emb_key:
            return {"error": f"No embedding layer found matching '{layer_name}'. Available: {list(sd.keys())[:10]}"}
        emb = sd[emb_key]
        norms = emb.norm(dim=1)
        return {
            "layer": emb_key,
            "shape": list(emb.shape),
            "vocab_size": emb.shape[0],
            "embedding_dim": emb.shape[1],
            "mean_norm": round(float(norms.mean()), 4),
            "std_norm": round(float(norms.std()), 4),
            "min_norm": round(float(norms.min()), 4),
            "max_norm": round(float(norms.max()), 4),
            "isotropy": round(float(norms.std() / norms.mean()), 4) if norms.mean() > 0 else 0,
            "council_note": "C28-CALCULUS: embedding quality; C9-AETHER: semantic space.",
        }
    except Exception as e:
        return {"error": f"Failed: {e}"}


# ─── 20. MODEL BENCHMARKING ──────────────────────────────────────────────────

@mcp.tool()
def model_benchmark(model_size_millions: float = 758.0, seq_len: int = 512, batch_size: int = 1) -> Dict[str, Any]:
    """Estimate model inference/training throughput and memory."""
    # Rough estimates based on transformer FLOPs
    params = model_size_millions * 1e6
    # FLOPs per token ~ 2 * params (forward) + 4 * params (backward)
    fwd_flops = 2 * params * seq_len * batch_size
    bwd_flops = 4 * params * seq_len * batch_size
    # Assume 1 TFLOP/s for CPU, 10 TFLOP/s for GPU
    cpu_tokens_per_sec = 1e12 / (2 * params)  # rough
    gpu_tokens_per_sec = 1e13 / (2 * params)
    return {
        "model_size_millions": model_size_millions,
        "seq_len": seq_len,
        "batch_size": batch_size,
        "estimated_fwd_flops": fwd_flops,
        "estimated_bwd_flops": bwd_flops,
        "estimated_cpu_tokens_per_sec": round(cpu_tokens_per_sec, 1),
        "estimated_gpu_tokens_per_sec": round(gpu_tokens_per_sec, 1),
        "memory_fp32_gb": round(params * 4 / (1024**3), 2),
        "memory_fp16_gb": round(params * 2 / (1024**3), 2),
        "memory_int8_gb": round(params * 1 / (1024**3), 2),
        "council_note": "C14-KAIDO: efficiency; C26-TECHNE: hardware constraints.",
    }


# ─── 21. FINE-TUNING CONFIG GENERATOR ────────────────────────────────────────

@mcp.tool()
def model_finetune_config(
    model_size_millions: float = 758.0,
    method: str = "lora",
    target_modules: str = "q_proj,v_proj",
    lora_rank: int = 8,
    lora_alpha: float = 16.0,
) -> Dict[str, Any]:
    """Generate a fine-tuning configuration (LoRA, QLoRA, full, or prefix)."""
    modules = [m.strip() for m in target_modules.split(",") if m.strip()]
    configs = {
        "lora": {
            "method": "LoRA",
            "target_modules": modules,
            "r": lora_rank,
            "lora_alpha": lora_alpha,
            "lora_dropout": 0.05,
            "bias": "none",
            "task_type": "CAUSAL_LM",
        },
        "qlora": {
            "method": "QLoRA",
            "target_modules": modules,
            "r": lora_rank,
            "lora_alpha": lora_alpha,
            "lora_dropout": 0.05,
            "quantization": "4-bit (NF4)",
            "compute_dtype": "bfloat16",
            "task_type": "CAUSAL_LM",
        },
        "full": {
            "method": "Full Fine-Tuning",
            "trainable_params": "all",
            "task_type": "CAUSAL_LM",
        },
        "prefix": {
            "method": "Prefix Tuning",
            "num_virtual_tokens": 20,
            "task_type": "CAUSAL_LM",
        },
    }
    config = configs.get(method.lower(), configs["lora"])
    # Estimate trainable params
    trainable = 0
    if method.lower() in ("lora", "qlora"):
        for mod in modules:
            trainable += lora_rank * 1024 * 2  # rough
    return {
        "method": method,
        "config": config,
        "estimated_trainable_params": trainable,
        "trainable_pct": round(trainable / (model_size_millions * 1e6) * 100, 4) if model_size_millions > 0 else 0,
        "council_note": "C28-CALCULUS: verify params; C25-PROMETHEUS: falsify with 1 epoch.",
    }


# ─── 22. LOSS CURVE ANALYZER ─────────────────────────────────────────────────

@mcp.tool()
def model_loss_analyze(losses: str, window: int = 10) -> Dict[str, Any]:
    """Analyze a loss curve for trends, plateaus, and anomalies."""
    loss_list = [float(x.strip()) for x in losses.split(",") if x.strip()]
    if not loss_list:
        return {"error": "No losses provided."}

    # Moving average
    ma = []
    for i in range(len(loss_list)):
        start = max(0, i - window + 1)
        ma.append(round(sum(loss_list[start:i+1]) / (i - start + 1), 4))

    # Detect plateau (last 5 losses within 1% of each other)
    last_5 = loss_list[-5:] if len(loss_list) >= 5 else loss_list
    plateau = (max(last_5) - min(last_5)) / max(abs(min(last_5)), 1e-8) < 0.01

    # Detect spike (any loss > 2x previous)
    spikes = []
    for i in range(1, len(loss_list)):
        if loss_list[i] > 2 * loss_list[i-1]:
            spikes.append({"step": i, "loss": loss_list[i], "prev": loss_list[i-1]})

    # Trend
    if len(loss_list) >= 2:
        trend = "decreasing" if loss_list[-1] < loss_list[0] else "increasing"
    else:
        trend = "insufficient_data"

    return {
        "total_steps": len(loss_list),
        "initial_loss": loss_list[0],
        "final_loss": loss_list[-1],
        "min_loss": min(loss_list),
        "max_loss": max(loss_list),
        "moving_average_last": ma[-1] if ma else None,
        "plateau_detected": plateau,
        "spikes": spikes,
        "trend": trend,
        "council_note": "C28-CALCULUS: verify trends; C25-PROMETHEUS: falsify with more data.",
    }


# --- Quillan-Ronin Global Error-Handling Middleware ---
from fastmcp.server.middleware import Middleware, MiddlewareContext
import logging as _log

class QuillanErrorMiddleware(Middleware):
    async def on_call_tool(self, context, call_next):
        try:
            return await call_next(context)
        except Exception as e:
            _log.error("Tool error: %s", e, exc_info=True)
            return {"status": "ERROR", "error": str(e), "error_type": type(e).__name__}


mcp.add_middleware(QuillanErrorMiddleware())
if __name__ == "__main__":
    mcp.run()
