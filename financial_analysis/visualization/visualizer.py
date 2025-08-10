#!/usr/bin/env python3
"""
可视化模块
Visualization Module
"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional


class Visualizer:
    """数据可视化器"""
    
    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def create_performance_chart(self, data: Dict, output_path: Optional[str] = None) -> str:
        """创建性能对比图表"""
        return create_charts(data, output_path)
    
    def create_dashboard(self, data: pd.DataFrame, output_path: Optional[str] = None) -> str:
        """创建仪表板"""
        # TODO: 实现仪表板功能
        pass

def create_charts(data: Dict = None, output_path: Optional[str] = None) -> str:
    """
    创建性能对比图表
    """
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 默认数据
    if data is None:
        extractors = ['基础提取', '增强提取', 'LLM增强']
        metrics = ['总资产', '总负债', '营业收入', '净利润', '完整率']
        data = {
            '基础提取': [50.0, 50.0, 50.0, 12.5, 12.5],
            '增强提取': [50.0, 50.0, 75.0, 50.0, 37.5],
            'LLM增强': [50.0, 50.0, 75.0, 50.0, 37.5]
        }
    else:
        extractors = list(data.keys())
        metrics = ['总资产', '总负债', '营业收入', '净利润', '完整率']

    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('财务数据提取性能对比', fontsize=16, fontweight='bold')
    
    # 1. 柱状图对比
    ax1 = axes[0, 0]
    x = np.arange(len(metrics))
    width = 0.25
    
    for i, (extractor, values) in enumerate(data.items()):
        offset = (i - 1) * width
        bars = ax1.bar(x + offset, values, width, label=extractor)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=8)

    ax1.set_xlabel('提取指标')
    ax1.set_ylabel('提取率 (%)')
    ax1.set_title('各指标提取率对比')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 雷达图
    ax2 = plt.subplot(2, 2, 2, projection='polar')
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]
    
    for extractor, values in data.items():
        values_plot = values + values[:1]
        ax2.plot(angles, values_plot, 'o-', linewidth=2, label=extractor)
        ax2.fill(angles, values_plot, alpha=0.25)
    
    ax2.set_theta_offset(np.pi / 2)
    ax2.set_theta_direction(-1)
    ax2.set_xticks(angles[:-1])
    ax2.set_xticklabels(metrics)
    ax2.set_ylim(0, 100)
    ax2.set_title('提取能力雷达图')
    ax2.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    ax2.grid(True)
    
    # 3. 改进率图
    ax3 = axes[1, 0]
    base_values = data['基础提取']
    enhanced_values = data['增强提取']
    improvements = [(e - b) for b, e in zip(base_values, enhanced_values)]
    
    colors = ['green' if x > 0 else 'gray' for x in improvements]
    bars = ax3.bar(metrics, improvements, color=colors)
    
    for bar, imp in zip(bars, improvements):
        height = bar.get_height()
        if height != 0:
            ax3.text(bar.get_x() + bar.get_width()/2., height/2,
                    f'{imp:+.1f}%', ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax3.set_xlabel('提取指标')
    ax3.set_ylabel('改进率 (%)')
    ax3.set_title('相对基础提取的改进')
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax3.grid(True, alpha=0.3)
    
    # 4. 处理速度对比
    ax4 = axes[1, 1]
    speed_data = {
        '提取器': ['基础提取', '增强提取', 'LLM增强'],
        '平均耗时(秒)': [2.0, 2.3, 3.2],
        '相对速度': [1.0, 1.15, 1.6]
    }
    
    bars = ax4.bar(speed_data['提取器'], speed_data['平均耗时(秒)'], 
                    color=['blue', 'orange', 'green'])
    
    for bar, time, speed in zip(bars, speed_data['平均耗时(秒)'], speed_data['相对速度']):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{time:.1f}s\n({speed:.1f}x)', ha='center', va='bottom')
    
    ax4.set_xlabel('提取器')
    ax4.set_ylabel('平均处理时间 (秒)')
    ax4.set_title('处理速度对比')
    ax4.grid(True, alpha=0.3)

    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    if output_path:
        save_path = Path(output_path) / f'performance_chart_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png'
    else:
        output_dir = Path(__file__).parent.parent.parent / 'output' / 'reports'
        output_dir.mkdir(parents=True, exist_ok=True)
        save_path = output_dir / f'performance_chart_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png'
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存到: {save_path}")
    return str(save_path)

    # 创建简化的对比图
    plt.figure(figsize=(10, 6))

    # 只展示关键改进
    key_metrics = ['营业收入', '净利润', '完整率']
    base_key = [50.0, 12.5, 12.5]
    enhanced_key = [75.0, 50.0, 37.5]
    
    x = np.arange(len(key_metrics))
    width = 0.35
    
    bars1 = plt.bar(x - width/2, base_key, width, label='基础提取', color='lightblue')
    bars2 = plt.bar(x + width/2, enhanced_key, width, label='增强提取', color='darkblue')

    # 添加数值和改进箭头
    for i, (b1, b2) in enumerate(zip(bars1, bars2)):
        # 基础值
        plt.text(b1.get_x() + b1.get_width()/2., b1.get_height(),
                f'{base_key[i]:.1f}%', ha='center', va='bottom')
        # 增强值
        plt.text(b2.get_x() + b2.get_width()/2., b2.get_height(),
                f'{enhanced_key[i]:.1f}%', ha='center', va='bottom')
        
        # 改进箭头和百分比
        improvement = enhanced_key[i] - base_key[i]
        mid_x = x[i]
        mid_y = (base_key[i] + enhanced_key[i]) / 2
        plt.annotate(f'+{improvement:.1f}%', 
                    xy=(mid_x, mid_y), 
                    ha='center', 
                    fontsize=12, 
                    fontweight='bold',
                    color='green')

    plt.xlabel('关键指标', fontsize=12)
    plt.ylabel('提取成功率 (%)', fontsize=12)
    plt.title('关键指标提取率改进', fontsize=14, fontweight='bold')
    plt.xticks(x, key_metrics)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 90)
    
    # 保存简化图
    if output_path:
        simple_save_path = Path(output_path) / f'key_improvements_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png'
    else:
        simple_save_path = output_dir / f'key_improvements_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png'
    
    plt.savefig(simple_save_path, dpi=300, bbox_inches='tight')
    print(f"简化图表已保存到: {simple_save_path}")
    
    plt.show()
    return str(save_path)