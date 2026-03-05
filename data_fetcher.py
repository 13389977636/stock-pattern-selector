#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股日线数据获取模块
功能：获取全市场股票日线数据，支持过滤停牌、ST、亏损股票
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import warnings
warnings.filterwarnings('ignore')

class AStockDataFetcher:
    def __init__(self, data_dir="/root/.copaw/stock_pattern_selector/data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
    def get_stock_list(self):
        """获取A股股票列表（排除北交所）"""
        try:
            # 获取沪深A股列表
            stock_info = ak.stock_info_a_code_name()
            # 过滤北交所股票（代码以8开头）
            stock_info = stock_info[~stock_info['code'].str.startswith(('8', '4'))]
            return stock_info
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_daily_data(self, symbol, start_date=None, end_date=None):
        """获取单只股票日线数据"""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
            
        try:
            # akshare的股票代码格式：sh600000, sz000001
            if symbol.startswith(('6', '9')):
                code = f"sh{symbol}"
            elif symbol.startswith(('0', '3')):
                code = f"sz{symbol}"
            else:
                return pd.DataFrame()
                
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if df.empty:
                return df
                
            # 重命名列
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 
                         'amplitude', 'change_pct', 'change_amount', 'turnover']
            df['symbol'] = symbol
            df['date'] = pd.to_datetime(df['date'])
            return df
            
        except Exception as e:
            print(f"获取{symbol}数据失败: {e}")
            return pd.DataFrame()
    
    def get_financial_filter_data(self, symbol):
        """获取财务数据用于过滤（亏损股票）"""
        try:
            # 获取最近财报的净利润
            df = ak.stock_financial_report_sina(symbol=symbol, symbol_type="lrb")
            if not df.empty:
                # 找到最新的净利润数据
                net_profit_cols = [col for col in df.columns if '净利润' in col]
                if net_profit_cols:
                    latest_profit = df[net_profit_cols[0]].iloc[0]
                    return float(latest_profit) if pd.notna(latest_profit) else None
            return None
        except Exception as e:
            print(f"获取{symbol}财务数据失败: {e}")
            return None
    
    def is_st_stock(self, symbol):
        """判断是否为ST股票"""
        try:
            stock_info = ak.stock_info_sh_delist() if symbol.startswith('6') else ak.stock_info_sz_delist()
            # 简单判断：如果股票名称包含ST
            # 实际应用中需要更准确的判断
            return 'ST' in symbol or '*ST' in symbol
        except:
            # 如果无法获取，保守起见返回False
            return False
    
    def filter_valid_stocks(self, stock_list, check_financial=True):
        """过滤有效股票（排除停牌、ST、亏损）"""
        valid_stocks = []
        total_count = len(stock_list)
        
        print(f"开始过滤 {total_count} 只股票...")
        
        for i, (idx, row) in enumerate(stock_list.iterrows()):
            symbol = row['code']
            name = row['name']
            
            # 进度显示
            if i % 100 == 0:
                print(f"进度: {i}/{total_count}")
            
            try:
                # 1. 检查是否停牌（通过能否获取最近数据判断）
                recent_data = self.get_daily_data(symbol, 
                    start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                if recent_data.empty:
                    continue  # 停牌股票
                
                # 2. 检查是否ST股票
                if self.is_st_stock(name):
                    continue
                
                # 3. 检查是否亏损（可选）
                if check_financial:
                    profit = self.get_financial_filter_data(symbol)
                    if profit is not None and profit < 0:
                        continue
                
                valid_stocks.append({'symbol': symbol, 'name': name})
                
            except Exception as e:
                print(f"处理{symbol}时出错: {e}")
                continue
        
        print(f"过滤完成，有效股票数量: {len(valid_stocks)}")
        return valid_stocks

def main():
    """测试函数"""
    fetcher = AStockDataFetcher()
    
    # 获取股票列表
    print("获取A股股票列表...")
    stock_list = fetcher.get_stock_list()
    print(f"获取到 {len(stock_list)} 只股票")
    
    # 测试获取单只股票数据
    if not stock_list.empty:
        test_symbol = stock_list.iloc[0]['code']
        print(f"测试获取 {test_symbol} 的日线数据...")
        df = fetcher.get_daily_data(test_symbol)
        print(f"获取到 {len(df)} 条日线数据")
        if not df.empty:
            print(df.head())

if __name__ == "__main__":
    main()