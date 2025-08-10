#!/usr/bin/env python3
"""
交叉验证系统
Cross Validation System

作者: Lin Cifeng
创建时间: 2025-08-06

对比正则和LLM提取结果，处理单位转换，提供置信度评分
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime
import numpy as np


class CrossValidator:
    """交叉验证器"""
    
    def __init__(self):
        # 定义需要验证的核心字段
        self.core_fields = ['total_assets', 'total_liabilities', 'revenue', 'net_profit']
        
        # 定义所有字段
        self.all_fields = [
            # 资产负债表
            'total_assets', 'total_liabilities', 'total_equity',
            'cash_and_equivalents', 'loans_and_advances', 'customer_deposits',
            # 损益表
            'revenue', 'net_profit', 'operating_expenses', 'ebit',
            'interest_income', 'net_interest_income', 'fee_income',
            # 现金流量表
            'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow'
        ]
        
        # 容差设置
        self.tolerance = 0.01  # 1%的容差
    
    def validate(self, regex_result: Dict, llm_result: Dict) -> Dict[str, Any]:
        """
        验证两种方法的提取结果
        
        Returns:
            Dict containing:
            - status: 'consistent', 'discrepancy', 'partial'
            - final_data: 最终确定的数据
            - confidence: 各字段的置信度
            - discrepancies: 差异详情
        """
        result = {
            'status': 'consistent',
            'final_data': {},
            'confidence': {},
            'discrepancies': {},
            'validation_details': {}
        }
        
        # 获取两种方法的数据
        regex_data = regex_result.get('data', {})
        llm_data = llm_result.get('data', {})
        
        # 获取单位乘数
        regex_unit = regex_result.get('unit_multiplier', 1)
        llm_unit = llm_result.get('unit_multiplier', 1)
        
        # 验证每个字段
        for field in self.all_fields:
            validation = self._validate_field(
                field,
                regex_data.get(field),
                llm_data.get(field),
                regex_unit,
                llm_unit
            )
            
            if validation['has_value']:
                result['final_data'][field] = validation['final_value']
                result['confidence'][field] = validation['confidence']
                result['validation_details'][field] = validation
                
                if validation['status'] == 'discrepancy':
                    result['discrepancies'][field] = validation['discrepancy_info']
        
        # 确定整体状态
        if result['discrepancies']:
            result['status'] = 'discrepancy'
        elif len(result['final_data']) < len(self.core_fields):
            result['status'] = 'partial'
        
        # 计算整体置信度
        result['overall_confidence'] = self._calculate_overall_confidence(result['confidence'])
        
        # 生成验证摘要
        result['summary'] = self._generate_summary(result)
        
        return result
    
    def _validate_field(self, field: str, regex_value: Any, llm_value: Any, 
                       regex_unit: int, llm_unit: int) -> Dict:
        """验证单个字段"""
        validation = {
            'field': field,
            'has_value': False,
            'final_value': None,
            'confidence': 0,
            'status': 'missing',
            'source': None,
            'discrepancy_info': {}
        }
        
        # 处理空值情况
        if regex_value is None and llm_value is None:
            return validation
        
        # 只有一个来源有值
        if regex_value is None:
            validation.update({
                'has_value': True,
                'final_value': llm_value,
                'confidence': 60,  # 单一来源置信度较低
                'status': 'llm_only',
                'source': 'llm'
            })
            return validation
        
        if llm_value is None:
            validation.update({
                'has_value': True,
                'final_value': regex_value,
                'confidence': 60,
                'status': 'regex_only',
                'source': 'regex'
            })
            return validation
        
        # 两个来源都有值，需要比较
        # 先进行单位转换
        regex_normalized = float(regex_value) * regex_unit
        llm_normalized = float(llm_value) * llm_unit
        
        # 计算差异
        diff = abs(regex_normalized - llm_normalized)
        avg = (regex_normalized + llm_normalized) / 2
        relative_diff = diff / avg if avg != 0 else 0
        
        if relative_diff <= self.tolerance:
            # 一致
            validation.update({
                'has_value': True,
                'final_value': avg,  # 取平均值
                'confidence': 95,  # 两个来源一致，置信度高
                'status': 'consistent',
                'source': 'both'
            })
        else:
            # 有差异
            # 判断哪个更可能正确
            final_value, source = self._resolve_discrepancy(
                field, regex_normalized, llm_normalized,
                regex_unit, llm_unit
            )
            
            validation.update({
                'has_value': True,
                'final_value': final_value,
                'confidence': 70,  # 有差异，置信度中等
                'status': 'discrepancy',
                'source': source,
                'discrepancy_info': {
                    'regex_value': regex_normalized,
                    'llm_value': llm_normalized,
                    'relative_diff': relative_diff,
                    'unit_issue': regex_unit != llm_unit
                }
            })
        
        return validation
    
    def _resolve_discrepancy(self, field: str, regex_value: float, llm_value: float,
                           regex_unit: int, llm_unit: int) -> Tuple[float, str]:
        """解决数值差异"""
        # 如果是单位问题导致的差异
        if regex_unit != llm_unit:
            # 检查是否是1000倍关系（常见的千元问题）
            if regex_value / llm_value == 1000 or llm_value / regex_value == 1000:
                # 倾向于选择较大的值（实际金额而非千元）
                if regex_value > llm_value:
                    return regex_value, 'regex'
                else:
                    return llm_value, 'llm'
        
        # 对于某些字段，可能有特定的判断逻辑
        if field in ['net_profit', 'ebit']:
            # 利润字段，如果一个是正一个是负，需要特别处理
            if regex_value * llm_value < 0:
                # 符号不同，需要更仔细的判断
                # 这里简单地选择LLM结果，因为LLM通常更好地理解上下文
                return llm_value, 'llm'
        
        # 默认情况：选择LLM结果（通常更准确）
        return llm_value, 'llm'
    
    def _calculate_overall_confidence(self, field_confidences: Dict[str, float]) -> float:
        """计算整体置信度"""
        if not field_confidences:
            return 0
        
        # 对核心字段加权
        weighted_sum = 0
        total_weight = 0
        
        for field, confidence in field_confidences.items():
            weight = 2 if field in self.core_fields else 1
            weighted_sum += confidence * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    def _generate_summary(self, result: Dict) -> Dict:
        """生成验证摘要"""
        summary = {
            'total_fields': len(result['final_data']),
            'core_fields_complete': sum(1 for f in self.core_fields if f in result['final_data']),
            'discrepancy_count': len(result['discrepancies']),
            'average_confidence': np.mean(list(result['confidence'].values())) if result['confidence'] else 0,
            'validation_status': result['status']
        }
        
        # 计算各来源的贡献
        source_counts = {'regex': 0, 'llm': 0, 'both': 0}
        for details in result['validation_details'].values():
            source = details.get('source')
            if source in source_counts:
                source_counts[source] += 1
        
        summary['source_distribution'] = source_counts
        
        return summary
    
    def batch_validate(self, results_df: pd.DataFrame) -> pd.DataFrame:
        """批量验证数据框中的结果"""
        validated_results = []
        
        for _, row in results_df.iterrows():
            # 构建正则和LLM结果
            regex_result = {
                'data': {field: row.get(f'regex_{field}') for field in self.all_fields},
                'unit_multiplier': row.get('regex_unit_multiplier', 1)
            }
            
            llm_result = {
                'data': {field: row.get(f'llm_{field}') for field in self.all_fields},
                'unit_multiplier': row.get('llm_unit_multiplier', 1)
            }
            
            # 验证
            validation = self.validate(regex_result, llm_result)
            
            # 构建输出行
            output_row = {
                'filename': row.get('filename', ''),
                'validation_status': validation['status'],
                'overall_confidence': validation['overall_confidence'],
                'discrepancy_count': len(validation['discrepancies'])
            }
            
            # 添加最终值和置信度
            for field in self.all_fields:
                if field in validation['final_data']:
                    output_row[f'final_{field}'] = validation['final_data'][field]
                    output_row[f'{field}_confidence'] = validation['confidence'][field]
            
            validated_results.append(output_row)
        
        return pd.DataFrame(validated_results)
    
    def generate_report(self, validation_results: List[Dict]) -> Dict:
        """生成交叉验证报告"""
        report = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_files': len(validation_results),
            'statistics': {
                'consistent': 0,
                'discrepancy': 0,
                'partial': 0
            },
            'field_statistics': {},
            'confidence_distribution': {},
            'common_discrepancies': []
        }
        
        # 统计各种状态
        for result in validation_results:
            status = result.get('status', 'unknown')
            if status in report['statistics']:
                report['statistics'][status] += 1
        
        # 统计各字段的验证情况
        for field in self.all_fields:
            field_stats = {
                'total': 0,
                'consistent': 0,
                'discrepancy': 0,
                'single_source': 0,
                'average_confidence': []
            }
            
            for result in validation_results:
                if field in result.get('final_data', {}):
                    field_stats['total'] += 1
                    
                    details = result.get('validation_details', {}).get(field, {})
                    status = details.get('status', '')
                    
                    if status == 'consistent':
                        field_stats['consistent'] += 1
                    elif status == 'discrepancy':
                        field_stats['discrepancy'] += 1
                    elif status in ['regex_only', 'llm_only']:
                        field_stats['single_source'] += 1
                    
                    confidence = result.get('confidence', {}).get(field, 0)
                    field_stats['average_confidence'].append(confidence)
            
            if field_stats['average_confidence']:
                field_stats['average_confidence'] = np.mean(field_stats['average_confidence'])
            else:
                field_stats['average_confidence'] = 0
            
            report['field_statistics'][field] = field_stats
        
        # 识别常见的差异模式
        discrepancy_patterns = {}
        for result in validation_results:
            for field, disc_info in result.get('discrepancies', {}).items():
                if disc_info.get('unit_issue'):
                    pattern = f"{field}_unit_issue"
                    discrepancy_patterns[pattern] = discrepancy_patterns.get(pattern, 0) + 1
        
        report['common_discrepancies'] = [
            {'pattern': k, 'count': v} 
            for k, v in sorted(discrepancy_patterns.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return report


def test_validator():
    """测试验证器"""
    validator = CrossValidator()
    
    # 模拟数据
    regex_result = {
        'data': {
            'total_assets': 1523878,
            'total_liabilities': 872431,
            'revenue': None,
            'net_profit': None
        },
        'unit_multiplier': 1000  # 千元
    }
    
    llm_result = {
        'data': {
            'total_assets': 1523878862,
            'total_liabilities': 872431000,
            'revenue': 15779693,
            'net_profit': -83221658
        },
        'unit_multiplier': 1  # 实际金额
    }
    
    print("测试交叉验证:")
    print("-" * 60)
    
    result = validator.validate(regex_result, llm_result)
    
    print(f"验证状态: {result['status']}")
    print(f"整体置信度: {result['overall_confidence']:.1f}%")
    print(f"\n最终数据:")
    for field, value in result['final_data'].items():
        confidence = result['confidence'][field]
        print(f"  {field}: {value:,.0f} (置信度: {confidence}%)")
    
    if result['discrepancies']:
        print(f"\n发现差异:")
        for field, info in result['discrepancies'].items():
            print(f"  {field}: 正则={info['regex_value']:,.0f}, LLM={info['llm_value']:,.0f}")


if __name__ == "__main__":
    test_validator()