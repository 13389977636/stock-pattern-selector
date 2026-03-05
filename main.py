#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票形态选股系统 - 主控制器
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import AStockDataFetcher
from stock_filter import StockFilter
from feature_extractor import PatternFeatureExtractor
from similarity_search import SimilaritySearcher

class StockPatternSelector:
    def __init__(self, data_dir="/root/.copaw/stock_pattern_selector/data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 初始化各模块
        self.data_fetcher = AStockDataFetcher()
        self.stock_filter = StockFilter()
        self.feature_extractor = PatternFeatureExtractor()
        self.similarity_searcher = SimilaritySearcher()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(data_dir, 'system.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize_system(self):
        """初始化系统 - 获取基础数据"""
        self.logger.info("🚀 开始初始化股票形态选股系统...")
        
        # 1. 获取A股基础列表
        self.logger.info("📥 获取A股股票列表...")
        stock_list = self.data_fetcher.get_a_stock_list()
        self.logger.info(f"✅ 获取到 {len(stock_list)} 只A股股票")
        
        # 2. 获取最近5年日线数据（用于后续筛选）
        self.logger.info("📊 获取A股日线数据（最近5年）...")
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
        
        all_data = {}
        for i, stock_code in enumerate(stock_list[:10]):  # 先测试10只股票
            try:
                df = self.data_fetcher.get_stock_daily(stock_code, start_date, end_date)
                if not df.empty:
                    all_data[stock_code] = df
                if i % 100 == 0:
                    self.logger.info(f"   已处理 {i}/{len(stock_list)} 只股票")
            except Exception as e:
                self.logger.warning(f"   股票 {stock_code} 数据获取失败: {e}")
        
        self.logger.info(f"✅ 成功获取 {len(all_data)} 只股票的日线数据")
        
        # 3. 应用过滤条件
        self.logger.info("🧹 应用股票过滤条件（停牌/ST/亏损）...")
        filtered_stocks = self.stock_filter.filter_stocks(all_data)
        self.logger.info(f"✅ 过滤后剩余 {len(filtered_stocks)} 只股票")
        
        # 4. 提取形态特征
        self.logger.info("🔍 提取日线形态特征...")
        features = {}
        for stock_code, df in filtered_stocks.items():
            try:
                feature_vector = self.feature_extractor.extract_features(df)
                features[stock_code] = feature_vector
            except Exception as e:
                self.logger.warning(f"   股票 {stock_code} 特征提取失败: {e}")
        
        self.logger.info(f"✅ 成功提取 {len(features)} 只股票的形态特征")
        
        # 5. 建立相似性搜索索引
        self.logger.info("⚡ 建立相似性搜索索引...")
        self.similarity_searcher.build_index(features)
        self.logger.info("✅ 相似性搜索索引建立完成")
        
        self.logger.info("🎉 股票形态选股系统初始化完成！")
        return True
    
    def find_similar_stocks(self, template_stock_code, start_date, end_date, top_k=10):
        """基于模板股票查找相似股票"""
        self.logger.info(f"🎯 查找与 {template_stock_code} 在 {start_date}-{end_date} 期间相似的股票...")
        
        # 获取模板股票数据
        template_data = self.data_fetcher.get_stock_daily(template_stock_code, start_date, end_date)
        if template_data.empty:
            raise ValueError(f"模板股票 {template_stock_code} 数据为空")
        
        # 提取模板特征
        template_features = self.feature_extractor.extract_features(template_data)
        
        # 搜索相似股票
        similar_stocks = self.similarity_searcher.search(template_features, top_k)
        
        self.logger.info(f"✅ 找到 {len(similar_stocks)} 只相似股票")
        return similar_stocks

def main():
    """系统初始化测试"""
    selector = StockPatternSelector()
    selector.initialize_system()

if __name__ == "__main__":
    main()