"""
批量提取管理器
Batch Extraction Manager

作者: Lin Cifeng
创建: 2025-08-12
"""

import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

from .smart_extractor import smart_extract


def load_master_table() -> Dict:
    """加载主控制表"""
    master_file = Path("output/extraction_master.json")
    if master_file.exists():
        with open(master_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "metadata": {
            "total_files": 0,
            "processed": 0,
            "successful": 0,
            "partial": 0,
            "failed": 0,
            "last_update": None,
            "batches": {}
        },
        "files": {}
    }


def show_status():
    """显示提取进度"""
    master = load_master_table()
    meta = master["metadata"]
    
    print("\n" + "="*80)
    print("财报提取进度监控")
    print("="*80)
    
    # 总体进度
    total = meta["total_files"]
    processed = meta["processed"]
    
    if total > 0:
        progress_pct = processed / total * 100
        progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
        print(f"\n总进度: [{progress_bar}] {progress_pct:.1f}% ({processed}/{total})")
    else:
        print("\n尚未开始提取")
    
    # 质量统计
    print(f"\n提取质量:")
    print(f"  ✅ 完全成功: {meta['successful']} 份")
    print(f"  ⚠️  部分成功: {meta['partial']} 份")
    print(f"  ❌ 失败: {meta['failed']} 份")
    
    # 批次进度
    if meta["batches"]:
        print(f"\n批次进度:")
        for batch_id, batch_info in sorted(meta["batches"].items(), key=lambda x: int(x[0])):
            status_icon = "✅" if batch_info["status"] == "completed" else "⏸️" if batch_info["status"] == "processing" else "⏳"
            print(f"  批次 {batch_id}: {status_icon} {batch_info['status']} ({batch_info['size']} 份)")
    
    # 最近更新
    if meta["last_update"]:
        update_time = datetime.fromisoformat(meta["last_update"])
        print(f"\n最后更新: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 建议下一步
    if processed < total:
        remaining = total - processed
        next_batch = (processed // 200) + 1
        print(f"\n💡 建议:")
        print(f"  还有 {remaining} 份待处理")
        print(f"  下一批次: python main.py extract --batch {next_batch}")


def retry_failed(failed_only: bool = True, partial_only: bool = False, mode: str = "llm_only"):
    """重试失败或部分成功的文件"""
    master = load_master_table()
    
    # 筛选需要重试的文件
    retry_files = []
    for filename, info in master["files"].items():
        if failed_only and info["status"] == "failed":
            retry_files.append(filename)
        elif partial_only and info["status"] == "partial":
            retry_files.append(filename)
        elif not failed_only and not partial_only and info["status"] in ["failed", "partial"]:
            retry_files.append(filename)
    
    if not retry_files:
        print("没有需要重试的文件")
        return
    
    print(f"\n准备重试 {len(retry_files)} 个文件")
    print(f"使用模式: {mode}")
    
    # 分批重试
    batch_size = 50
    for i in range(0, len(retry_files), batch_size):
        batch = retry_files[i:i+batch_size]
        print(f"\n重试批次 {i//batch_size + 1}: {len(batch)} 个文件")
        
        # 调用smart_extract重试
        stats = smart_extract(
            extraction_mode=mode,
            use_llm=True if "llm" in mode else False,
            max_workers=2 if "llm" in mode else 4,
            use_cache=True,
            limit=len(batch)
        )
        
        print(f"重试结果: 成功={stats['successful']}, 部分={stats['partial']}, 失败={stats['failed']}")


def generate_quality_report():
    """生成质量报告"""
    master = load_master_table()
    
    print("\n" + "="*80)
    print("财报提取质量报告")
    print("="*80)
    
    # 按质量分组
    high_quality = []   # 4/4 字段
    medium_quality = [] # 2-3 字段
    low_quality = []    # 0-1 字段
    
    for filename, info in master["files"].items():
        fields = info.get("extracted_fields", 0)
        if fields == 4:
            high_quality.append(filename)
        elif fields >= 2:
            medium_quality.append(filename)
        else:
            low_quality.append(filename)
    
    # 统计
    total = len(master["files"])
    if total > 0:
        print(f"\n质量分布:")
        print(f"  🌟 高质量 (4/4字段): {len(high_quality)} ({len(high_quality)/total*100:.1f}%)")
        print(f"  ⭐ 中质量 (2-3字段): {len(medium_quality)} ({len(medium_quality)/total*100:.1f}%)")
        print(f"  ⚪ 低质量 (0-1字段): {len(low_quality)} ({len(low_quality)/total*100:.1f}%)")
    
    # 批次分析
    if master["metadata"]["batches"]:
        print(f"\n批次分析:")
        for batch_id, batch_info in sorted(master["metadata"]["batches"].items(), key=lambda x: int(x[0])):
            if batch_info["status"] == "completed":
                # 统计该批次的成功率
                batch_files = [f for f, info in master["files"].items() 
                             if info.get("batch_id") == int(batch_id)]
                if batch_files:
                    batch_success = sum(1 for f in batch_files 
                                      if master["files"][f]["status"] == "completed")
                    success_rate = batch_success / len(batch_files) * 100
                    print(f"  批次 {batch_id}: {success_rate:.1f}% 完全成功率")
    
    # 需要人工复核的文件
    review_needed = [f for f in low_quality if master["files"][f]["status"] == "partial"]
    if review_needed:
        print(f"\n⚠️ 需要人工复核: {len(review_needed)} 份")
        print("  建议使用LLM模式重试或手动检查")
        
        # 保存需要复核的列表
        review_file = Path("output/files_need_review.txt")
        with open(review_file, 'w', encoding='utf-8') as f:
            for filename in review_needed[:20]:  # 显示前20个
                f.write(f"{filename}\n")
        print(f"  详细列表已保存至: {review_file}")
    
    # 生成报告文件
    report_file = Path("output/extraction_quality_report.json")
    report_data = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "high_quality": len(high_quality),
            "medium_quality": len(medium_quality),
            "low_quality": len(low_quality)
        },
        "files": {
            "high_quality": high_quality[:100],  # 保存前100个
            "medium_quality": medium_quality[:100],
            "low_quality": low_quality[:100]
        }
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细报告已保存至: {report_file}")


def batch_extract_all(batch_size: int = 200, mode: str = "regex_only", max_workers: int = 4):
    """批量提取所有文件"""
    # 获取总文件数
    pdf_dir = Path("data/raw_reports")
    all_pdfs = list(pdf_dir.glob("*.pdf"))
    total_files = len(all_pdfs)
    
    print(f"\n准备批量提取 {total_files} 份财报")
    print(f"批次大小: {batch_size}")
    print(f"提取模式: {mode}")
    print(f"并行线程: {max_workers}")
    
    # 计算批次数
    num_batches = (total_files + batch_size - 1) // batch_size
    
    print(f"将分为 {num_batches} 个批次处理")
    
    # 逐批处理
    for batch_id in range(1, num_batches + 1):
        print(f"\n{'='*60}")
        print(f"处理批次 {batch_id}/{num_batches}")
        print(f"{'='*60}")
        
        stats = smart_extract(
            batch_id=batch_id,
            batch_size=batch_size,
            extraction_mode=mode,
            use_llm="llm" in mode,
            max_workers=max_workers,
            use_cache=True,
            skip_processed=True
        )
        
        print(f"批次 {batch_id} 完成: 成功={stats['successful']}, 部分={stats['partial']}, 失败={stats['failed']}")
        
        # 每5个批次显示一次总进度
        if batch_id % 5 == 0:
            show_status()
    
    # 最终报告
    print("\n" + "="*80)
    print("批量提取完成！")
    show_status()
    generate_quality_report()


def monitor_extraction():
    """实时监控提取进度"""
    print("\n" + "="*70)
    print("📊 财报全量提取实时监控")
    print("="*70)
    
    last_count = 0
    monitor_start = time.time()
    
    while True:
        try:
            # 读取主控制表
            master = load_master_table()
            
            # 实际统计文件状态
            total = len([f for f in Path('data/raw_reports').glob('*.pdf')])
            all_files = master.get('files', {})
            processed = len(all_files)
            successful = len([f for f, d in all_files.items() if d.get('status') == 'completed'])
            partial = len([f for f, d in all_files.items() if d.get('status') == 'partial'])
            failed = len([f for f, d in all_files.items() if d.get('status') == 'failed'])
            
            # 计算速度
            elapsed = time.time() - monitor_start
            if processed > last_count and elapsed > 0:
                recent_speed = (processed - last_count) / 5  # 最近5秒的速度
                overall_speed = processed / (elapsed / 60)  # 整体速度（文件/分钟）
                eta = (total - processed) / recent_speed if recent_speed > 0 else 0
                eta_min = int(eta / 60)
                eta_sec = int(eta % 60)
            else:
                recent_speed = 0
                overall_speed = 0
                eta_min = 0
                eta_sec = 0
            
            # 获取当前批次信息
            batches = master.get('metadata', {}).get('batches', {})
            current_batch = None
            for bid, info in batches.items():
                if info.get('status') == 'processing':
                    current_batch = bid
                    break
            
            # 清屏并显示
            print("\033[2J\033[H")  # 清屏
            print("="*70)
            print("📊 财报全量提取实时监控")
            print("="*70)
            print(f"总文件数: {total}")
            print(f"已处理: {processed} ({processed/total*100:.1f}%)")
            print(f"  ✅ 成功: {successful} ({successful/total*100:.1f}%)")
            print(f"  ⚠️ 部分: {partial} ({partial/total*100:.1f}%)")
            print(f"  ❌ 失败: {failed} ({failed/total*100:.1f}%)")
            
            if current_batch:
                print(f"当前批次: {current_batch}")
            
            print("-"*70)
            print(f"瞬时速度: {recent_speed*60:.1f} 文件/分钟")
            print(f"平均速度: {overall_speed:.1f} 文件/分钟")
            print(f"预计剩余: {eta_min}分{eta_sec}秒")
            print(f"运行时间: {int(elapsed/60)}分{int(elapsed%60)}秒")
            print("-"*70)
            
            # 显示进度条
            bar_length = 50
            filled = int(bar_length * processed / total) if total > 0 else 0
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"进度: [{bar}] {processed}/{total}")
            
            # 显示最近处理的文件
            recent_files = []
            for name, info in all_files.items():
                if 'last_update' in info:
                    recent_files.append((name, info['last_update'], info.get('status')))
            
            if recent_files:
                recent_files.sort(key=lambda x: x[1], reverse=True)
                print("\n最近处理:")
                for name, _, status in recent_files[:3]:
                    emoji = '✅' if status == 'completed' else '⚠️' if status == 'partial' else '❌'
                    print(f"  {emoji} {name[:50]}")
            
            last_count = processed
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n监控已停止")
            break
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(5)


def merge_all_results(output_prefix: str = 'output/final_combined_results') -> Optional[Dict]:
    """合并所有提取结果"""
    results_dir = Path('output/results')
    archive_dir = Path('output/archive')
    all_dfs = []
    
    # 读取results目录
    for csv_file in results_dir.glob('*.csv'):
        try:
            df = pd.read_csv(csv_file)
            if len(df) > 0:
                all_dfs.append(df)
                print(f'读取 {csv_file.name}: {len(df)} 条')
        except:
            pass
    
    # 读取archive目录
    if archive_dir.exists():
        for batch_dir in archive_dir.glob('batch_results_*'):
            for csv_file in batch_dir.glob('*.csv'):
                try:
                    df = pd.read_csv(csv_file)
                    if len(df) > 0:
                        all_dfs.append(df)
                        print(f'读取归档 {csv_file.name}: {len(df)} 条')
                except:
                    pass
    
    # 合并所有数据
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # 规范化列名
        column_mapping = {
            'company': 'Company',
            'year': 'Year', 
            'total_assets': 'Total Assets',
            'total_liabilities': 'Total Liabilities',
            'revenue': 'Revenue',
            'net_profit': 'Net Profit',
            'success_level': 'Success Level',
            'method': 'Method',
            'file': 'File'
        }
        
        # 重命名列
        for old_col, new_col in column_mapping.items():
            if old_col in combined_df.columns and new_col not in combined_df.columns:
                combined_df.rename(columns={old_col: new_col}, inplace=True)
        
        # 去重（保留最新的）
        if 'File' in combined_df.columns:
            combined_df = combined_df.drop_duplicates(subset=['File'], keep='last')
        
        # 清理数据 - 只保留有效数据
        if 'Success Level' in combined_df.columns:
            combined_df = combined_df[combined_df['Success Level'].notna()]
            combined_df = combined_df[combined_df['Success Level'] != 'Failed']
        
        print(f'\n合并后总记录数: {len(combined_df)}')
        
        # 统计
        if 'Success Level' in combined_df.columns:
            print('\n成功级别分布:')
            success_counts = combined_df['Success Level'].value_counts()
            for level, count in success_counts.items():
                print(f'  {level}: {count}')
        
        # 保存最终结果
        output_file = Path(f'{output_prefix}.csv')
        combined_df.to_csv(output_file, index=False)
        
        # 保存Excel版本
        excel_file = Path(f'{output_prefix}.xlsx')
        combined_df.to_excel(excel_file, index=False)
        
        print(f'\n✅ 最终合并结果:')
        print(f'  总记录数: {len(combined_df)}')
        
        # 分析数据质量
        print(f'\n📊 数据质量分析:')
        for col in ['Total Assets', 'Total Liabilities', 'Revenue', 'Net Profit']:
            if col in combined_df.columns:
                non_null = combined_df[col].notna().sum()
                pct = non_null / len(combined_df) * 100
                print(f'  {col}: {non_null}/{len(combined_df)} ({pct:.1f}%)')
        
        # 年份分布
        if 'Year' in combined_df.columns:
            print(f'\n📅 年份分布:')
            year_counts = combined_df['Year'].value_counts().head(5)
            for year, count in year_counts.items():
                print(f'  {year}: {count}')
        
        # 公司覆盖
        if 'Company' in combined_df.columns:
            print(f'\n🏢 公司覆盖: {combined_df["Company"].nunique()} 家')
        
        print(f'\n💾 文件已保存:')
        print(f'  CSV: {output_file}')
        print(f'  Excel: {excel_file}')
        
        return {
            'total': len(combined_df),
            'companies': combined_df['Company'].nunique() if 'Company' in combined_df.columns else 0,
            'csv_file': str(output_file),
            'excel_file': str(excel_file)
        }
    else:
        print('未找到任何数据文件')
        return None


def generate_final_report():
    """生成最终综合报告"""
    # 先合并所有结果
    merge_stats = merge_all_results()
    
    if merge_stats:
        # 读取合并后的数据
        df = pd.read_csv(merge_stats['csv_file'])
        
        # 生成可视化报告
        from ..visualization import create_charts
        create_charts()
        
        # 生成文本报告
        report_path = Path('output/reports/final_report.txt')
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("财务数据提取最终报告\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("一、总体统计\n")
            f.write("-"*40 + "\n")
            f.write(f"提取总数: {merge_stats['total']} 条\n")
            f.write(f"覆盖公司: {merge_stats['companies']} 家\n\n")
            
            if 'Success Level' in df.columns:
                f.write("二、成功率分析\n")
                f.write("-"*40 + "\n")
                success_counts = df['Success Level'].value_counts()
                for level, count in success_counts.items():
                    f.write(f"{level}: {count} ({count/len(df)*100:.1f}%)\n")
                f.write("\n")
            
            if 'Company' in df.columns:
                f.write("三、TOP10公司\n")
                f.write("-"*40 + "\n")
                top_companies = df['Company'].value_counts().head(10)
                for company, count in top_companies.items():
                    f.write(f"{company}: {count} 条\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("报告结束\n")
        
        print(f"\n📄 最终报告已生成: {report_path}")


if __name__ == "__main__":
    # 测试功能
    show_status()