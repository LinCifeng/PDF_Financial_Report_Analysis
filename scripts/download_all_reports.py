#!/usr/bin/env python3
"""
高效批量下载所有财报
Efficiently download all financial reports
"""
import os
import csv
import subprocess
import time
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 全局锁用于线程安全的打印
print_lock = threading.Lock()

def safe_print(message):
    """线程安全的打印"""
    with print_lock:
        print(message)

def determine_file_extension(url, company, year):
    """根据URL和内容类型确定文件扩展名"""
    # 常见的HTML财报网站
    html_sites = ['investors.', 'ir.', 'investor-relations', 'annual-report']
    
    # 检查URL是否明确指向PDF
    if url.lower().endswith('.pdf'):
        return '.pdf'
    
    # 检查是否是已知的HTML财报网站
    for site in html_sites:
        if site in url.lower():
            return '.html'
    
    # 默认尝试PDF
    return '.pdf'

def clean_filename(text):
    """清理文件名"""
    # 替换非法字符
    illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r', '\t']
    for char in illegal_chars:
        text = text.replace(char, '_')
    # 替换空格和括号
    text = text.replace(' ', '_').replace('(', '_').replace(')', '_')
    # 移除多余的下划线
    while '__' in text:
        text = text.replace('__', '_')
    return text.strip('_')

def download_file(url, filepath, timeout=60):
    """使用curl下载文件，支持重定向和各种格式"""
    try:
        cmd = [
            'curl', '-L',  # 跟随重定向
            '-o', str(filepath),
            '--connect-timeout', '30',
            '--max-time', str(timeout),
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.8,*/*;q=0.7',
            '--compressed',  # 接受压缩内容
            '--silent', '--show-error',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and filepath.exists():
            # 检查文件大小
            size = filepath.stat().st_size
            if size < 500:  # 小于500字节可能是错误页面
                return False, f"File too small ({size} bytes)"
            
            # 检查文件类型
            with open(filepath, 'rb') as f:
                header = f.read(512)
                
            # 检查是否是PDF
            if filepath.suffix == '.pdf':
                if header.startswith(b'%PDF'):
                    return True, "PDF downloaded"
                else:
                    # 可能是HTML，改名
                    new_path = filepath.with_suffix('.html')
                    filepath.rename(new_path)
                    return True, "HTML downloaded (renamed)"
            
            # HTML文件检查
            elif filepath.suffix == '.html':
                if b'<html' in header.lower() or b'<!doctype' in header.lower():
                    return True, "HTML downloaded"
                elif header.startswith(b'%PDF'):
                    # 实际是PDF，改名
                    new_path = filepath.with_suffix('.pdf')
                    filepath.rename(new_path)
                    return True, "PDF downloaded (renamed)"
            
            return True, "Downloaded"
        else:
            return False, f"Curl error: {result.stderr}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def download_report(row, output_dir, existing_files):
    """下载单个报告"""
    company = row['name']
    year = row['Fiscal_year']
    quarter = row.get('Quarter', '')
    url = row['Report_link']
    
    # 生成文件名
    company_clean = clean_filename(company)
    ext = determine_file_extension(url, company, year)
    
    if quarter and quarter.strip() not in ['', 'None', 'nan']:
        filename = f"{company_clean}_{year}_{clean_filename(quarter)}{ext}"
    else:
        filename = f"{company_clean}_{year}_Annual{ext}"
    
    filepath = output_dir / filename
    
    # 检查是否已存在（包括不同扩展名）
    base_name = filepath.stem
    for ext in ['.pdf', '.html']:
        check_path = output_dir / f"{base_name}{ext}"
        if check_path.exists() or f"{base_name}{ext}" in existing_files:
            return None, f"Already exists: {base_name}{ext}"
    
    # 下载文件
    success, message = download_file(url, filepath)
    
    if success:
        return filepath.name, message
    else:
        # 清理失败的文件
        if filepath.exists():
            os.remove(filepath)
        return None, message

def main():
    # 设置路径
    project_root = Path(__file__).parent.parent
    csv_path = project_root / 'data' / 'Company_Financial_report.csv'
    output_dir = project_root / 'data' / 'raw_reports'
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取已存在的文件
    existing_files = set(os.listdir(output_dir))
    safe_print(f"Current files in directory: {len(existing_files)}")
    
    # 读取所有待下载的报告
    all_reports = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Financial Report(Y/N)') == 'Y' and row.get('Report_link'):
                # 清理URL
                url = row['Report_link'].strip()
                if url and not url.startswith('#') and url != 'N/A':
                    row['Report_link'] = url
                    all_reports.append(row)
    
    safe_print(f"Total reports to process: {len(all_reports)}")
    
    # 过滤出需要下载的报告
    reports_to_download = []
    for row in all_reports:
        company = row['name']
        year = row['Fiscal_year']
        quarter = row.get('Quarter', '')
        
        # 检查是否已存在
        company_clean = clean_filename(company)
        if quarter and quarter.strip() not in ['', 'None', 'nan']:
            base_name = f"{company_clean}_{year}_{clean_filename(quarter)}"
        else:
            base_name = f"{company_clean}_{year}_Annual"
        
        exists = False
        for ext in ['.pdf', '.html']:
            if f"{base_name}{ext}" in existing_files:
                exists = True
                break
        
        if not exists:
            reports_to_download.append(row)
    
    safe_print(f"Reports to download: {len(reports_to_download)}")
    
    if not reports_to_download:
        safe_print("No new reports to download!")
        return
    
    # 使用线程池并行下载
    max_workers = 5  # 同时下载的线程数
    downloaded = []
    failed = []
    
    safe_print("\nStarting parallel download...")
    safe_print("=" * 60)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有下载任务
        future_to_report = {
            executor.submit(download_report, row, output_dir, existing_files): row
            for row in reports_to_download
        }
        
        # 处理完成的任务
        completed = 0
        for future in as_completed(future_to_report):
            completed += 1
            row = future_to_report[future]
            company = row['name']
            year = row['Fiscal_year']
            
            try:
                filename, message = future.result()
                if filename:
                    downloaded.append({
                        'company': company,
                        'year': year,
                        'filename': filename,
                        'message': message
                    })
                    safe_print(f"[{completed}/{len(reports_to_download)}] ✓ {company} {year}: {message}")
                else:
                    if "Already exists" not in message:
                        failed.append({
                            'company': company,
                            'year': year,
                            'error': message
                        })
                        safe_print(f"[{completed}/{len(reports_to_download)}] ✗ {company} {year}: {message}")
            except Exception as e:
                failed.append({
                    'company': company,
                    'year': year,
                    'error': str(e)
                })
                safe_print(f"[{completed}/{len(reports_to_download)}] ✗ {company} {year}: Error - {str(e)}")
            
            # 避免请求过快
            time.sleep(0.5)
    
    # 生成详细报告
    safe_print("\n" + "=" * 60)
    safe_print("Download Summary:")
    safe_print(f"- Successfully downloaded: {len(downloaded)}")
    safe_print(f"- Failed downloads: {len(failed)}")
    safe_print(f"- Total files now: {len(os.listdir(output_dir))}")
    
    # 保存详细报告
    report_data = {
        'summary': {
            'total_in_csv': len(all_reports),
            'already_downloaded': len(all_reports) - len(reports_to_download),
            'newly_downloaded': len(downloaded),
            'failed': len(failed),
            'total_files': len(os.listdir(output_dir))
        },
        'downloaded': downloaded,
        'failed': failed
    }
    
    report_path = project_root / 'output' / 'download_report.json'
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    safe_print(f"\nDetailed report saved to: {report_path}")
    
    # 显示一些失败的例子
    if failed:
        safe_print("\nSome failed downloads:")
        for item in failed[:5]:
            safe_print(f"  - {item['company']} {item['year']}: {item['error']}")
        if len(failed) > 5:
            safe_print(f"  ... and {len(failed) - 5} more")

if __name__ == "__main__":
    main()