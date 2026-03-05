#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选股系统配置文件
"""

# 数据相关配置
DATA_DIR = "/root/.copaw/stock_pattern_selector/data"
LOG_DIR = "/root/.copaw/stock_pattern_selector/logs"

# 股票过滤配置
FILTER_CONFIG = {
    'exclude_st': True,      # 排除ST股票
    'exclude_suspended': True,  # 排除停牌股票  
    'exclude_loss_making': True,  # 排除亏损股票
    'min_trading_days': 60,   # 最少交易天数
}

# 形态匹配配置
PATTERN_CONFIG = {
    'lookback_days': 60,     # 回看天数
    'similarity_threshold': 0.7,  # 相似度阈值
    'top_k_results': 20,     # 返回前K个结果
}

# 更新配置
UPDATE_CONFIG = {
    'run_time': '15:30',     # 每日运行时间（收盘后）
    'timezone': 'Asia/Shanghai'
}