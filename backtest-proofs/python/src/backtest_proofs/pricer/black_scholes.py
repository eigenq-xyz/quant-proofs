"""Re-export shim: Black-Scholes pricing lives in quant_core."""

from quant_core.pricer.black_scholes import (  # noqa: F401
    BSGreeks,
    BSPrice,
    OptionType,
    bs_greeks,
    bs_price,
)
