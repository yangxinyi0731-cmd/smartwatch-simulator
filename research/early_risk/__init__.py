"""E0-only early-risk research foundation.

This package validates contracts, deterministic fixtures, temporal leakage
guards, metrics, and dry-run policy behavior.  It does not contain a trained
prospective prediction model and must not emit real alerts.
"""

from research.early_risk.target_contract import (
    EvidenceLevel,
    TargetContract,
    load_target_contract,
)

__all__ = ["EvidenceLevel", "TargetContract", "load_target_contract"]
