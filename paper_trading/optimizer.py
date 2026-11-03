
import pandas as pd

from indicators.technical import calculate_indicators
from paper_trading.simulator import (
    run_simulation,
    calculate_statistics
)


def optimize_ema(
    raw_df,
    fast_values,
    slow_values
):

    results = []

    total_combinations = 0

    for fast in fast_values:

        for slow in slow_values:

            if fast >= slow:
                continue

            total_combinations += 1

    if total_combinations == 0:
        raise ValueError(
            "Tidak ada kombinasi EMA yang valid."
        )

    for fast in fast_values:

        for slow in slow_values:

            if fast >= slow:
                continue

            # Calculate indicators for this combination
            df = calculate_indicators(
                raw_df,
                ema_fast=fast,
                ema_slow=slow
            )

            # Historical simulation
            simulation = run_simulation(
                df,
                ema_fast=fast,
                ema_slow=slow
            )

            stats = calculate_statistics(simulation)

            initial = simulation["initial_balance"]
            final = simulation["final_balance"]

            return_pct = (
                (final - initial) / initial
            ) * 100

            results.append({

                "EMA Fast": fast,

                "EMA Slow": slow,

                "Total Trades": stats["total_trades"],

                "Win Rate (%)": round(
                    stats["win_rate"], 2
                ),

                "Profit Factor": round(
                    stats["profit_factor"], 3
                ) if stats["profit_factor"] != float("inf")
                else float("inf"),

                "Net Profit (USDT)": round(
                    stats["net_profit"], 2
                ),

                "Return (%)": round(
                    return_pct, 2
                ),

                "Max Drawdown (%)": round(
                    stats["max_drawdown"], 2
                )

            })

    result_df = pd.DataFrame(results)

    # Rank using Profit Factor and Return,
    # while penalizing excessive drawdown.
    result_df = result_df.sort_values(
        by=[
            "Net Profit (USDT)",
            "Profit Factor",
            "Max Drawdown (%)"
        ],
        ascending=[
            False,
            False,
            True
        ]
    ).reset_index(drop=True)

    result_df.insert(
        0,
        "Rank",
        range(1, len(result_df) + 1)
    )

    return result_df
