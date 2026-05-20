"""Re-export shim: Black-Scholes pricing lives in quant_core."""

from quant_core.pricer.black_scholes import (
    BSGreeks,
    BSPrice,
    OptionType,
    bs_greeks,
    bs_price,
)

__all__ = ["BSGreeks", "BSPrice", "OptionType", "bs_greeks", "bs_price"]
