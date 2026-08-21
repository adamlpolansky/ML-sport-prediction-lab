"""Leakage-safe, chronological football features."""

from .chronological import ChronologicalConfig, FeatureRow, build_chronological_features
from .context import ManagerContextRow, ManagerSpell, build_manager_context
from .elo import (
    TIER_ELO_EMPIRICAL_STATUS,
    TIER_ELO_IMPLEMENTATION_STATUS,
    TIER_ELO_PROMOTION_STATUS,
    EloConfig,
    EloFeatureRow,
    TierSeedConfig,
    run_fixed_elo,
    run_tier_seeded_elo,
)

__all__ = [
    "ChronologicalConfig",
    "EloConfig",
    "EloFeatureRow",
    "FeatureRow",
    "ManagerContextRow",
    "ManagerSpell",
    "TIER_ELO_EMPIRICAL_STATUS",
    "TIER_ELO_IMPLEMENTATION_STATUS",
    "TIER_ELO_PROMOTION_STATUS",
    "TierSeedConfig",
    "build_chronological_features",
    "build_manager_context",
    "run_fixed_elo",
    "run_tier_seeded_elo",
]
