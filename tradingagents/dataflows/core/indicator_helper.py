"""指标辅助模块"""

import pandas as pd


def collect_all_needed_indicators() -> set:
    """收集所有分组需要的指标（去重）
    
    Returns:
        所有需要计算的指标集合
    """
    from ..indicator_groups import INDICATOR_GROUPS, BASE_COLUMNS
    
    all_needed_indicators = set()
    for group_name, indicators in INDICATOR_GROUPS.items():
        for ind in indicators:
            if ind not in BASE_COLUMNS:
                all_needed_indicators.add(ind)
    return all_needed_indicators


def build_grouped_results(df_with_indicators: pd.DataFrame, look_back_days: int) -> dict:
    """按分组构建结果字典
    
    Args:
        df_with_indicators: 包含所有指标的DataFrame
        look_back_days: 回溯天数
        
    Returns:
        分组结果字典，key为组名，value为CSV字符串
    """
    from ..indicator_groups import INDICATOR_GROUPS
    
    result = {}
    for group_name, indicators in INDICATOR_GROUPS.items():
        group_df = df_with_indicators[[col for col in indicators if col in df_with_indicators.columns]]
        group_df = group_df.tail(look_back_days + 10)
        result[group_name] = group_df.to_csv(index=False)
    return result
