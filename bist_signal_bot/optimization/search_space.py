import itertools
import random
from typing import Any
import numpy as np

from bist_signal_bot.optimization.models import ParameterSearchSpace, ParameterType
from bist_signal_bot.core.exceptions import SearchSpaceError, OptimizationValidationError

class SearchSpaceBuilder:
    @staticmethod
    def expand_space(search_spaces: list[ParameterSearchSpace], max_combinations: int | None = None) -> list[dict[str, Any]]:
        param_values_map = {}
        for space in search_spaces:
            if space.values is not None:
                param_values_map[space.name] = space.values
            elif space.param_type == ParameterType.BOOL:
                param_values_map[space.name] = [True, False]
            elif space.choices is not None:
                param_values_map[space.name] = space.choices
            elif space.min_value is not None and space.max_value is not None and space.step is not None:
                if space.param_type == ParameterType.INT:
                    param_values_map[space.name] = list(range(int(space.min_value), int(space.max_value) + 1, int(space.step)))
                else:
                    # Float range
                    param_values_map[space.name] = [float(x) for x in np.arange(space.min_value, space.max_value + space.step, space.step)]
                    # Ensure max value is included if it should be (np.arange edge cases)
                    if param_values_map[space.name][-1] > space.max_value:
                        param_values_map[space.name].pop()
                    if len(param_values_map[space.name]) == 0 or abs(param_values_map[space.name][-1] - space.max_value) > 1e-9:
                        # Simple inclusion if it aligns well, or just let arange do its job.
                        # Arange handles `max_value + step` fine usually, but precision issues can arise.
                        pass

            else:
                raise SearchSpaceError(f"Insufficient definition for parameter space: {space.name}")

        keys = list(param_values_map.keys())
        value_lists = list(param_values_map.values())

        # Calculate total combinations before generating them
        total_combinations = 1
        for v_list in value_lists:
            total_combinations *= len(v_list)

        if max_combinations is not None and total_combinations > max_combinations:
            raise OptimizationValidationError(
                f"Total combinations ({total_combinations}) exceeds max_combinations ({max_combinations})."
            )

        combinations = []
        for combo in itertools.product(*value_lists):
            combinations.append(dict(zip(keys, combo)))

        return combinations

    @staticmethod
    def sample_space(search_spaces: list[ParameterSearchSpace], n: int, seed: int) -> list[dict[str, Any]]:
        # For sample space we temporarily remove max_combinations limit to get the full population
        try:
            all_combinations = SearchSpaceBuilder.expand_space(search_spaces, max_combinations=None)
        except Exception as e:
             raise SearchSpaceError(f"Failed to expand space for sampling: {e}")

        if len(all_combinations) <= n:
            return all_combinations

        random.seed(seed)
        return random.sample(all_combinations, n)

    @staticmethod
    def parse_param_range(raw: str) -> ParameterSearchSpace:
        if "=" not in raw:
            raise SearchSpaceError(f"Invalid param range format. Expected key=values, got: {raw}")

        name, val_str = raw.split("=", 1)
        name = name.strip()
        val_str = val_str.strip()

        if ":" in val_str:
            parts = val_str.split(":")
            if len(parts) != 3:
                raise SearchSpaceError(f"Invalid range format. Expected min:max:step, got: {val_str}")
            min_val, max_val, step = parts

            try:
                # Try int first
                if all(p.lstrip('-').isdigit() for p in parts):
                    return ParameterSearchSpace(
                        name=name, param_type=ParameterType.INT,
                        min_value=int(min_val), max_value=int(max_val), step=int(step)
                    )
                else:
                    return ParameterSearchSpace(
                        name=name, param_type=ParameterType.FLOAT,
                        min_value=float(min_val), max_value=float(max_val), step=float(step)
                    )
            except ValueError:
                raise SearchSpaceError(f"Failed to parse numeric range: {val_str}")

        if "," in val_str or val_str:
            parts = [p.strip() for p in val_str.split(",")]

            # Type inference
            if all(p.lower() in ["true", "false"] for p in parts):
                values = [p.lower() == "true" for p in parts]
                return ParameterSearchSpace(name=name, param_type=ParameterType.BOOL, values=values)

            if all(p.lstrip('-').isdigit() for p in parts):
                return ParameterSearchSpace(name=name, param_type=ParameterType.INT, values=[int(p) for p in parts])

            try:
                values = [float(p) for p in parts]
                return ParameterSearchSpace(name=name, param_type=ParameterType.FLOAT, values=values)
            except ValueError:
                # Categorical
                return ParameterSearchSpace(name=name, param_type=ParameterType.CATEGORICAL, choices=parts)

        raise SearchSpaceError(f"Empty or unparseable value string: {val_str}")

    @staticmethod
    def parse_param_ranges(raw_ranges: list[str]) -> list[ParameterSearchSpace]:
        if not raw_ranges:
            return []
        return [SearchSpaceBuilder.parse_param_range(r) for r in raw_ranges]

    @staticmethod
    def default_search_space_for_strategy(strategy_name: str) -> list[ParameterSearchSpace]:
        strategy_name = strategy_name.lower().replace(" ", "_")

        if strategy_name == "moving_average_trend":
            return [
                ParameterSearchSpace(name="fast_window", param_type=ParameterType.INT, values=[10, 20, 30]),
                ParameterSearchSpace(name="slow_window", param_type=ParameterType.INT, values=[50, 100, 150]),
                ParameterSearchSpace(name="min_score", param_type=ParameterType.FLOAT, values=[50.0, 60.0, 70.0])
            ]
        elif strategy_name == "rsi_mean_reversion":
            return [
                ParameterSearchSpace(name="rsi_window", param_type=ParameterType.INT, values=[10, 14, 20]),
                ParameterSearchSpace(name="oversold", param_type=ParameterType.FLOAT, values=[25.0, 30.0, 35.0]),
                ParameterSearchSpace(name="overbought", param_type=ParameterType.FLOAT, values=[65.0, 70.0, 75.0]),
                ParameterSearchSpace(name="min_score", param_type=ParameterType.FLOAT, values=[50.0, 55.0, 60.0])
            ]
        elif strategy_name == "breakout_volume":
            return [
                ParameterSearchSpace(name="price_window", param_type=ParameterType.INT, values=[20, 40, 60]),
                ParameterSearchSpace(name="volume_window", param_type=ParameterType.INT, values=[20, 40]),
                ParameterSearchSpace(name="volume_multiplier", param_type=ParameterType.FLOAT, values=[1.2, 1.5, 2.0]),
                ParameterSearchSpace(name="min_score", param_type=ParameterType.FLOAT, values=[50.0, 60.0, 70.0])
            ]
        elif strategy_name == "composite_feature":
            return [
                ParameterSearchSpace(name="min_score", param_type=ParameterType.FLOAT, values=[55.0, 65.0, 75.0]),
                ParameterSearchSpace(name="use_trend", param_type=ParameterType.BOOL, values=[True]),
                ParameterSearchSpace(name="use_momentum", param_type=ParameterType.BOOL, values=[True]),
                ParameterSearchSpace(name="use_volume", param_type=ParameterType.BOOL, values=[True]),
                ParameterSearchSpace(name="use_volatility", param_type=ParameterType.BOOL, values=[True, False])
            ]

        return []
