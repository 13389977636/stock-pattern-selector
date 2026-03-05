#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相似性搜索模块 - 基于FAISS的高效股票形态匹配
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import faiss

class SimilaritySearch:
    def __init__(self, data_dir: str = "/root/.copaw/stock_pattern_selector/data"):
        self.data_dir = data_dir
        self.index_dir = os.path.join(data_dir, "indexes")
        self.features_dir = os.path.join(data_dir, "features")
        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.features_dir, exist_ok=True)
        
        # FAISS索引
        self.index = None
        self.stock_codes = []
        self.feature_dim = 128  # 特征向量维度
        
    def build_index_from_features(self, features_dict: Dict[str, np.ndarray]):
        """从特征字典构建FAISS索引"""
        if not features_dict:
            print("⚠️  无特征数据，无法构建索引")
            return False
            
        # 准备向量数据
        stock_codes = list(features_dict.keys())
        feature_vectors = np.array([features_dict[code] for code in stock_codes]).astype('float32')
        
        # 验证维度
        if feature_vectors.shape[1] != self.feature_dim:
            print(f"⚠️  特征维度不匹配: 期望 {self.feature_dim}, 实际 {feature_vectors.shape[1]}")
            return False
            
        # 创建FAISS索引
        self.index = faiss.IndexFlatL2(self.feature_dim)
        self.index.add(feature_vectors)
        
        # 保存索引和股票代码映射
        self.stock_codes = stock_codes
        faiss.write_index(self.index, os.path.join(self.index_dir, "stock_patterns.index"))
        
        # 保存股票代码列表
        with open(os.path.join(self.index_dir, "stock_codes.json"), 'w', encoding='utf-8') as f:
            json.dump(stock_codes, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 成功构建FAISS索引，包含 {len(stock_codes)} 只股票")
        return True
        
    def load_index(self):
        """加载已存在的FAISS索引"""
        index_path = os.path.join(self.index_dir, "stock_patterns.index")
        codes_path = os.path.join(self.index_dir, "stock_codes.json")
        
        if os.path.exists(index_path) and os.path.exists(codes_path):
            try:
                self.index = faiss.read_index(index_path)
                with open(codes_path, 'r', encoding='utf-8') as f:
                    self.stock_codes = json.load(f)
                print(f"✅ 加载FAISS索引，包含 {len(self.stock_codes)} 只股票")
                return True
            except Exception as e:
                print(f"❌ 加载索引失败: {e}")
                return False
        else:
            print("⚠️  索引文件不存在")
            return False
            
    def search_similar_stocks(self, query_vector: np.ndarray, top_k: int = 20, min_score: float = 0.1) -> List[Dict]:
        """搜索相似股票"""
        if self.index is None:
            print("❌ 索引未加载或未构建")
            return []
            
        if len(query_vector) != self.feature_dim:
            print(f"❌ 查询向量维度错误: 期望 {self.feature_dim}, 实际 {len(query_vector)}")
            return []
            
        # 执行FAISS搜索
        query_array = np.array([query_vector]).astype('float32')
        distances, indices = self.index.search(query_array, min(top_k, len(self.stock_codes)))
        
        # 转换结果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.stock_codes):
                stock_code = self.stock_codes[idx]
                # 距离转为相似度分数 (0-1)
                similarity_score = 1.0 / (1.0 + distances[0][i])
                if similarity_score >= min_score:
                    results.append({
                        'stock_code': stock_code,
                        'similarity_score': float(similarity_score),
                        'rank': i + 1
                    })
                    
        return results[:top_k]
        
    def save_features(self, stock_code: str, features: np.ndarray):
        """保存单个股票的特征向量"""
        feature_file = os.path.join(self.features_dir, f"{stock_code}.npy")
        np.save(feature_file, features)
        
    def load_features(self, stock_code: str) -> Optional[np.ndarray]:
        """加载单个股票的特征向量"""
        feature_file = os.path.join(self.features_dir, f"{stock_code}.npy")
        if os.path.exists(feature_file):
            return np.load(feature_file)
        return None
        
    def batch_save_features(self, features_dict: Dict[str, np.ndarray]):
        """批量保存特征向量"""
        for stock_code, features in features_dict.items():
            self.save_features(stock_code, features)
        print(f"✅ 批量保存 {len(features_dict)} 个股票特征")
        
    def get_all_features(self) -> Dict[str, np.ndarray]:
        """获取所有股票的特征向量"""
        features_dict = {}
        for filename in os.listdir(self.features_dir):
            if filename.endswith('.npy'):
                stock_code = filename[:-4]
                features = np.load(os.path.join(self.features_dir, filename))
                features_dict[stock_code] = features
        return features_dict

def test_similarity_search():
    """测试相似性搜索功能"""
    print("🔍 测试相似性搜索模块...")
    
    search_engine = SimilaritySearch()
    
    # 创建测试特征数据
    test_features = {
        '000001.SZ': np.random.rand(128),
        '600000.SH': np.random.rand(128),
        '000858.SZ': np.random.rand(128),
        '601318.SH': np.random.rand(128)
    }
    
    # 构建索引
    search_engine.build_index_from_features(test_features)
    
    # 测试搜索
    query_vector = np.random.rand(128)
    results = search_engine.search_similar_stocks(query_vector, top_k=3)
    
    print(f"📊 搜索结果 ({len(results)} 个):")
    for result in results:
        print(f"  {result['stock_code']}: {result['similarity_score']:.4f}")
        
    print("✅ 相似性搜索模块测试完成！")

if __name__ == "__main__":
    test_similarity_search()