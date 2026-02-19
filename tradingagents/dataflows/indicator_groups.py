#!/usr/bin/env python3
"""
统一指标组配置
所有数据源都使用这个配置来确定指标组包含哪些指标
"""

INDICATOR_GROUPS = {
    'macd': ['macd', 'macds', 'macdh'],
    'boll': ['boll', 'boll_ub', 'boll_lb', 'boll_width'],
    'adx': ['adx', 'plus_di', 'minus_di'],
    'volume': ['volume_sma_5', 'volume_sma_10', 'volume_sma_20', 'volume_sma_50', 
               'volume_ratio_5', 'volume_ratio_20', 'volume_change_pct', 'volume_acceleration'],
    'support': ['support_20', 'support_50', 'resistance_20', 'resistance_50', 'mid_range_20', 'position_in_range_20'],
    'trend': ['trend_slope_10', 'trend_slope_20', 'lr_pred_20', 'price_to_sma_20', 'price_to_sma_50'],
    'momentum': ['roc_5', 'roc_10', 'roc_20', 'cci_20', 'cmo_14', 'mfi_14'],
    'volatility': ['volatility_20', 'volatility_50', 'atr_pct', 'boll_width'],
    'cross': ['sma_5_20_cross', 'sma_20_50_cross', 'macd_cross', 
             'rsi_overbought', 'rsi_oversold', 'boll_breakout_up', 'boll_breakout_down'],
    'divergence': ['price_new_high_20', 'rsi_new_high_20', 'price_new_low_20', 'rsi_new_low_20'],
}

COMMON_BASE_INDICATORS = [
    'close_20_sma', 'close_50_sma', 'close_200_sma',
    'close_20_ema', 'close_50_ema',
    'rsi', 'atr', 'vwma', 'obv'
]

BASE_COLUMNS = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close']


def get_indicator_columns(indicator: str, df_columns: list) -> list:
    """
    获取指定指标需要的所有列
    
    Args:
        indicator: 指标名称或指标组名称
        df_columns: DataFrame 的所有列
        
    Returns:
        需要保留的列列表
    """
    keep_cols = []
    
    for col in BASE_COLUMNS:
        if col in df_columns:
            keep_cols.append(col)
    
    if indicator in df_columns:
        keep_cols.append(indicator)
    
    for group_name, group_cols in INDICATOR_GROUPS.items():
        if indicator.startswith(group_name) or indicator in group_cols:
            for col in group_cols:
                if col in df_columns and col not in keep_cols:
                    keep_cols.append(col)
            break
    
    for col in COMMON_BASE_INDICATORS:
        if col in df_columns and col not in keep_cols:
            keep_cols.append(col)
    
    return keep_cols


def is_indicator_group(indicator: str) -> bool:
    """判断是否是指标组"""
    return indicator in INDICATOR_GROUPS


def get_all_indicator_groups() -> list:
    """获取所有指标组名称"""
    return list(INDICATOR_GROUPS.keys())
