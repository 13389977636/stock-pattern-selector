#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日线形态特征提取模块
纯价格形态分析，不使用技术指标
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta

class PricePatternFeatureExtractor:
    """日线价格形态特征提取器"""
    
    def __init__(self):
        self.feature_names = [
            'normalized_price_curve',
            'price_trend',
            'volatility_profile', 
            'shape_context',
            'key_points_pattern'
        ]
    
    def normalize_price_series(self, prices: np.ndarray) -> np.ndarray:
        """
        标准化价格序列（消除绝对价格影响）
        将价格归一化到[0,1]区间
        """
        if len(prices) == 0:
            return np.array([])
        
        min_price = np.min(prices)
        max_price = np.max(prices)
        
        if max_price - min_price == 0:
            return np.zeros_like(prices)
        
        normalized = (prices - min_price) / (max_price - min_price)
        return normalized
    
    def calculate_price_trend(self, prices: np.ndarray) -> float:
        """
        计算价格趋势（线性回归斜率）
        """
        if len(prices) < 2:
            return 0.0
        
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        return float(slope)
    
    def calculate_volatility_profile(self, prices: np.ndarray) -> np.ndarray:
        """
        计算波动率特征
        """
        if len(prices) < 2:
            return np.array([0.0])
        
        # 计算每日收益率
        returns = np.diff(prices) / prices[:-1]
        # 滚动波动率（5日窗口）
        window_size = min(5, len(returns))
        if window_size <= 1:
            return np.array([np.std(returns)])
        
        vol_profile = []
        for i in range(len(returns) - window_size + 1):
            window_vol = np.std(returns[i:i+window_size])
            vol_profile.append(window_vol)
        
        # 如果结果为空，返回整体波动率
        if not vol_profile:
            vol_profile = [np.std(returns)]
            
        return np.array(vol_profile)
    
    def extract_shape_context(self, normalized_prices: np.ndarray, 
                            num_bins: int = 10) -> np.ndarray:
        """
        提取形状上下文特征（简化版）
        将价格曲线分段统计
        """
        if len(normalized_prices) == 0:
            return np.zeros(num_bins)
        
        # 将时间轴分成num_bins段
        segment_size = max(1, len(normalized_prices) // num_bins)
        shape_features = []
        
        for i in range(num_bins):
            start_idx = i * segment_size
            end_idx = min((i + 1) * segment_size, len(normalized_prices))
            if start_idx >= len(normalized_prices):
                segment_mean = 0.0
            else:
                segment_data = normalized_prices[start_idx:end_idx]
                segment_mean = np.mean(segment_data) if len(segment_data) > 0 else 0.0
            shape_features.append(segment_mean)
        
        return np.array(shape_features)
    
    def identify_key_points(self, prices: np.ndarray, 
                          window_size: int = 3) -> Dict[str, List[int]]:
        """
        识别关键点位（局部高点、低点）
        """
        if len(prices) < window_size * 2 + 1:
            return {'peaks': [], 'troughs': []}
        
        peaks = []
        troughs = []
        
        for i in range(window_size, len(prices) - window_size):
            # 检查是否为局部高点
            is_peak = True
            is_trough = True
            
            for j in range(1, window_size + 1):
                if prices[i] <= prices[i-j] or prices[i] <= prices[i+j]:
                    is_peak = False
                if prices[i] >= prices[i-j] or prices[i] >= prices[i+j]:
                    is_trough = False
            
            if is_peak:
                peaks.append(i)
            if is_trough:
                troughs.append(i)
        
        return {'peaks': peaks, 'troughs': troughs}
    
    def extract_comprehensive_features(self, df: pd.DataFrame, 
                                    lookback_days: int = 60) -> Dict[str, any]:
        """
        提取综合形态特征
        
        Args:
            df: 包含 OHLCV 数据的DataFrame
            lookback_days: 回溯天数
            
        Returns:
            包含所有特征的字典
        """
        # 确保数据按日期排序
        df = df.sort_index() if isinstance(df.index, pd.DatetimeIndex) else df.sort_values('date')
        
        # 取最近lookback_days天的数据
        if len(df) > lookback_days:
            df_recent = df.tail(lookback_days).copy()
        else:
            df_recent = df.copy()
        
        if len(df_recent) == 0:
            return {}
        
        # 提取收盘价序列
        close_prices = df_recent['close'].values.astype(float)
        volume_series = df_recent.get('volume', pd.Series(np.ones(len(close_prices)))).values.astype(float)
        
        # 1. 标准化价格曲线
        normalized_prices = self.normalize_price_series(close_prices)
        
        # 2. 价格趋势
        price_trend = self.calculate_price_trend(close_prices)
        
        # 3. 波动率特征
        volatility_profile = self.calculate_volatility_profile(close_prices)
        
        # 4. 形状上下文
        shape_context = self.extract_shape_context(normalized_prices)
        
        # 5. 关键点模式
        key_points = self.identify_key_points(close_prices)
        
        # 6. 成交量标准化（如果存在）
        normalized_volume = self.normalize_price_series(volume_series) if len(volume_series) > 0 else np.array([])
        
        features = {
            'normalized_price_curve': normalized_prices.tolist(),
            'price_trend': price_trend,
            'volatility_profile': volatility_profile.tolist(),
            'shape_context': shape_context.tolist(),
            'key_points': key_points,
            'normalized_volume': normalized_volume.tolist() if len(normalized_volume) > 0 else [],
            'data_length': len(close_prices),
            'extraction_date': datetime.now().isoformat()
        }
        
        return features
    
    def compare_patterns(self, pattern1: Dict, pattern2: Dict, 
                       weights: Optional[Dict] = None) -> float:
        """
        比较两个形态的相似度
        
        Args:
            pattern1, pattern2: 两个形态特征字典
            weights: 各特征的权重
            
        Returns:
            相似度分数 [0, 1]，越高越相似
        """
        if weights is None:
            weights = {
                'normalized_price_curve': 0.4,
                'price_trend': 0.2,
                'shape_context': 0.3,
                'volatility_profile': 0.1
            }
        
        similarity_score = 0.0
        total_weight = 0.0
        
        # 1. 标准化价格曲线相似度（动态时间规整简化版）
        if 'normalized_price_curve' in pattern1 and 'normalized_price_curve' in pattern2:
            curve1 = np.array(pattern1['normalized_price_curve'])
            curve2 = np.array(pattern2['normalized_price_curve'])
            
            # 简化：截断到相同长度
            min_len = min(len(curve1), len(curve2))
            if min_len > 0:
                curve1_trunc = curve1[:min_len]
                curve2_trunc = curve2[:min_len]
                curve_similarity = 1.0 - np.mean(np.abs(curve1_trunc - curve2_trunc))
                similarity_score += weights['normalized_price_curve'] * max(0, curve_similarity)
                total_weight += weights['normalized_price_curve']
        
        # 2. 趋势相似度
        if 'price_trend' in pattern1 and 'price_trend' in pattern2:
            trend1, trend2 = pattern1['price_trend'], pattern2['price_trend']
            # 归一化趋势值
            max_trend = max(abs(trend1), abs(trend2), 0.01)
            trend_similarity = 1.0 - abs(trend1 - trend2) / max_trend
            similarity_score += weights['price_trend'] * max(0, trend_similarity)
            total_weight += weights['price_trend']
        
        # 3. 形状上下文相似度
        if 'shape_context' in pattern1 and 'shape_context' in pattern2:
            sc1 = np.array(pattern1['shape_context'])
            sc2 = np.array(pattern2['shape_context'])
            min_len = min(len(sc1), len(sc2))
            if min_len > 0:
                sc1_trunc = sc1[:min_len]
                sc2_trunc = sc2[:min_len]
                sc_similarity = 1.0 - np.mean(np.abs(sc1_trunc - sc2_trunc))
                similarity_score += weights['shape_context'] * max(0, sc_similarity)
                total_weight += weights['shape_context']
        
        # 4. 波动率相似度
        if 'volatility_profile' in pattern1 and 'volatility_profile' in pattern2:
            vol1 = np.array(pattern1['volatility_profile'])
            vol2 = np.array(pattern2['volatility_profile'])
            min_len = min(len(vol1), len(vol2))
            if min_len > 0:
                vol1_trunc = vol1[:min_len]
                vol2_trunc = vol2[:min_len]
                vol_similarity = 1.0 - np.mean(np.abs(vol1_trunc - vol2_trunc))
                similarity_score += weights['volatility_profile'] * max(0, vol_similarity)
                total_weight += weights['volatility_profile']
        
        if total_weight == 0:
            return 0.0
        
        return similarity_score / total_weight

def main():
    """测试函数"""
    extractor = PricePatternFeatureExtractor()
    
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=60, freq='D')
    test_prices = np.sin(np.linspace(0, 4*np.pi, 60)) * 10 + 100  # 正弦波模拟价格
    
    test_df = pd.DataFrame({
        'date': dates,
        'open': test_prices,
        'high': test_prices + 1,
        'low': test_prices - 1,
        'close': test_prices,
        'volume': np.random.randint(1000000, 5000000, 60)
    })
    
    features = extractor.extract_comprehensive_features(test_df)
    print("✅ 特征提取完成!")
    print(f"  数据长度: {features.get('data_length', 0)}")
    print(f"  价格趋势: {features.get('price_trend', 0):.4f}")
    print(f"  形状上下文维度: {len(features.get('shape_context', []))}")
    
    # 测试相似度比较
    features2 = extractor.extract_comprehensive_features(test_df)
    similarity = extractor.compare_patterns(features, features2)
    print(f"  自相似度: {similarity:.4f}")

if __name__ == "__main__":
    main()