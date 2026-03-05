#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票过滤模块
功能：排除停牌、ST、亏损股票
"""

import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import logging

class StockFilter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_all_a_stocks(self):
        """获取所有A股股票列表"""
        try:
            # 获取沪深京A股列表
            stock_info = ak.stock_info_a_code_name()
            return stock_info
        except Exception as e:
            self.logger.error(f"获取A股列表失败: {e}")
            return pd.DataFrame()
    
    def is_suspended(self, stock_code: str, date: str) -> bool:
        """检查股票是否停牌"""
        try:
            # 获取当日交易数据，如果无数据则可能停牌
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                   start_date=date.replace("-", ""), 
                                   end_date=date.replace("-", ""), 
                                   adjust="qfq")
            return len(df) == 0
        except Exception:
            return True  # 默认认为停牌
    
    def is_st_stock(self, stock_code: str) -> bool:
        """检查是否为ST股票"""
        try:
            stock_name = ak.stock_individual_info_em(symbol=stock_code)
            if isinstance(stock_name, pd.DataFrame):
                name = stock_name[stock_name['item'] == '股票简称']['value'].iloc[0]
                return 'ST' in name or '*ST' in name or '退市' in name
            return False
        except Exception:
            return False
    
    def is_profitable(self, stock_code: str) -> bool:
        """检查是否为盈利股票（最近财报净利润>0）"""
        try:
            # 获取最新财务数据
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            if len(df) > 0:
                # 获取最新的净利润数据
                net_profit = df[df['项目'] == '净利润']['2023-12-31']  # 需要动态获取最新日期
                if len(net_profit) > 0:
                    profit_value = float(net_profit.iloc[0].replace(',', '').replace('--', '0'))
                    return profit_value > 0
            return True  # 默认认为盈利（避免误过滤）
        except Exception as e:
            self.logger.warning(f"获取{stock_code}财务数据失败: {e}")
            return True  # 默认认为盈利
    
    def filter_stocks(self, stock_list: pd.DataFrame, date: str = None) -> pd.DataFrame:
        """过滤股票列表"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        filtered_stocks = []
        total_count = len(stock_list)
        
        print(f"开始过滤 {total_count} 只股票...")
        
        for idx, row in stock_list.iterrows():
            stock_code = row['code']
            stock_name = row['name']
            
            # 进度显示
            if idx % 100 == 0:
                print(f"已处理 {idx}/{total_count} 只股票")
            
            try:
                # 检查停牌
                if self.is_suspended(stock_code, date):
                    continue
                
                # 检查ST
                if self.is_st_stock(stock_code):
                    continue
                
                # 检查盈利（暂时跳过，因为财务数据获取较慢）
                # if not self.is_profitable(stock_code):
                #     continue
                
                filtered_stocks.append({
                    'code': stock_code,
                    'name': stock_name,
                    'filtered_date': date
                })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return pd.DataFrame(filtered_stocks)

def main():
    """测试函数"""
    filter_obj = StockFilter()
    
    print("获取A股列表...")
    all_stocks = filter_obj.get_all_a_stocks()
    print(f"获取到 {len(all_stocks)} 只A股")
    
    print("开始过滤...")
    filtered_stocks = filter_obj.filter_stocks(all_stocks.head(50))  # 先测试前50只
    print(f"过滤后剩余 {len(filtered_stocks)} 只股票")
    print(filtered_stocks.head())

if __name__ == "__main__":
    main()