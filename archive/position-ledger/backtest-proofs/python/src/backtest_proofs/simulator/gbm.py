"""Re-export shim: GBM simulator lives in quant_core."""

from quant_core.simulator.gbm import simulate_gbm

__all__ = ["simulate_gbm"]
