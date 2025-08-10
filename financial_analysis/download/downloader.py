"""
财报下载模块
Financial Report Download Module
"""
import os
import csv
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


def clean_filename(text: str) -> str:
    """清理文件名中的特殊字符"""
    import re
    # 移除特殊字符
    text = re.sub(r'[^\w\s-]', '_', str(text))
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')


def download_file(url: str, output_path: Path) -> Tuple[bool, str]:
    """下载单个文件"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # 保存文件
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True, "Success"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP {e.response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


class Downloader:
    """财报下载器"""
    
    def __init__(self, output_dir: str = "data/raw_reports", max_workers: int = 5):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
    
    def download(self, url: str, filename: str) -> Tuple[bool, str]:
        """下载单个文件"""
        output_path = self.output_dir / filename
        return download_file(url, output_path)
    
    def batch_download(self, csv_path: str, limit: Optional[int] = None) -> Dict:
        """批量下载"""
        return download_reports(
            csv_path=csv_path,
            output_dir=str(self.output_dir),
            limit=limit,
            max_workers=self.max_workers
        )


# 保留原函数以兼容
def batch_download(
    csv_path: str = "data/Company_Financial_report.csv",
    output_dir: str = "data/raw_reports",
    limit: Optional[int] = None,
    max_workers: int = 5
) -> Dict:
    """批量下载财报（兼容接口）"""
    return download_reports(csv_path, output_dir, limit, max_workers)


def download_reports(
    csv_path: str = "data/Company_Financial_report.csv",
    output_dir: str = "data/raw_reports", 
    max_workers: int = 5,
    limit: Optional[int] = None
) -> Dict:
    """
    下载财报主函数
    
    Args:
        csv_path: CSV数据库路径
        output_dir: 输出目录
        max_workers: 并发下载数
        limit: 限制下载数量
        
    Returns:
        下载统计
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 读取CSV
    reports_to_download = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Financial Report(Y/N)') == 'Y' and row.get('Report_link'):
                url = row['Report_link'].strip()
                if url and not url.startswith('#') and url != 'N/A':
                    reports_to_download.append({
                        'company': row['name'],
                        'year': row['Fiscal_year'],
                        'quarter': row.get('Quarter', ''),
                        'url': url
                    })
    
    if limit:
        reports_to_download = reports_to_download[:limit]
    
    print(f"Found {len(reports_to_download)} reports to download")
    
    # 并发下载
    downloaded = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_report = {}
        
        for report in reports_to_download:
            # 生成文件名
            company = clean_filename(report['company'])
            year = str(report['year']).replace('/', '_')
            quarter = report['quarter']
            
            if quarter and quarter.strip() not in ['', 'None', 'nan']:
                filename = f"{company}_{year}_{clean_filename(quarter)}.pdf"
            else:
                filename = f"{company}_{year}_Annual.pdf"
            
            output_file = output_path / filename
            
            # 检查是否已存在
            if not output_file.exists():
                future = executor.submit(download_file, report['url'], output_file)
                future_to_report[future] = (report, output_file)
        
        # 处理结果
        for future in as_completed(future_to_report):
            report, output_file = future_to_report[future]
            success, message = future.result()
            
            if success:
                downloaded += 1
                print(f"✓ Downloaded: {output_file.name}")
            else:
                failed += 1
                print(f"✗ Failed: {report['company']} - {message}")
    
    # 统计
    stats = {
        'total': len(reports_to_download),
        'downloaded': downloaded,
        'failed': failed,
        'success_rate': downloaded / len(reports_to_download) * 100 if reports_to_download else 0
    }
    
    print(f"\n{'='*60}")
    print(f"Download completed!")
    print(f"Total: {stats['total']}")
    print(f"Downloaded: {stats['downloaded']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    
    return stats