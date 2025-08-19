#!/usr/bin/env python3
"""
SWE-bench to SBV Database Merger

This script merges SWE-bench evaluation results into the existing SBV_Database_Bug_Fix_Status.csv file.
"""

import csv
import json
import sys
from pathlib import Path


def load_swe_bench_results(results_file):
    """
    Load the SWE-bench results JSON file.
    
    Args:
        results_file (str): Path to the results JSON file
        
    Returns:
        dict: SWE-bench results data keyed by instance_id
    """
    try:
        with open(results_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading SWE-bench results: {e}")
        return {}


def load_pr_urls(pr_urls_file, pr_urls_updated_file):
    """
    Load PR URLs from both JSON files and create a mapping from base_branch to PR info.
    
    Args:
        pr_urls_file (str): Path to pr_urls.json
        pr_urls_updated_file (str): Path to pr_urls_updated.json
        
    Returns:
        dict: Mapping from base_branch (instance_id) to PR info
    """
    pr_mapping = {}
    
    # Load both PR URL files
    for file_path in [pr_urls_file, pr_urls_updated_file]:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            for pr in data.get('prs', []):
                base_branch = pr.get('base_branch')
                if base_branch:
                    pr_mapping[base_branch] = {
                        'url': pr.get('url', ''),
                        'head_branch': pr.get('head_branch', ''),
                        'repo': pr.get('repo', ''),
                        'number': pr.get('number', ''),
                        'title': pr.get('title', '')
                    }
                    
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
    
    return pr_mapping


def generate_project_guide_url(pr_info):
    """
    Generate the project guide URL from PR information.
    
    Args:
        pr_info (dict): PR information containing repo, head_branch, etc.
        
    Returns:
        str: URL to the project guide markdown file
    """
    if not pr_info or not pr_info.get('repo') or not pr_info.get('head_branch'):
        return ""
    
    repo = pr_info['repo']
    head_branch = pr_info['head_branch']
    
    # Format: https://github.com/{repo}/blob/{head_branch}/blitzy/documentation/Project%20Guide.md
    project_guide_url = f"https://github.com/{repo}/blob/{head_branch}/blitzy/documentation/Project%20Guide.md"
    
    return project_guide_url


def merge_csv_files(sbv_file, swe_bench_results, pr_mapping, output_file):
    """
    Merge SWE-bench results into the SBV Database Bug Fix Status CSV.
    
    Args:
        sbv_file (str): Path to the SBV_Database_Bug_Fix_Status.csv file
        swe_bench_results (dict): SWE-bench results data
        pr_mapping (dict): PR URL mapping data
        output_file (str): Path to output merged CSV file
    """
    
    merged_rows = []
    header_row = None
    matched_instances = 0
    total_rows = 0
    
    try:
        # Read the existing SBV CSV file
        with open(sbv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            for row_num, row in enumerate(reader):
                if row_num == 0:
                    # Header row - add new columns
                    header_row = row + [
                        'SWE_Resolved_Status',
                        'LATEST_PASS_TO_PASS',
                        'LATEST_FAIL_TO_PASS',
                        'SWE_Project_Guide_URL'
                    ]
                    merged_rows.append(header_row)
                    continue
                
                total_rows += 1
                
                # Extract instance_id from column 2 (0-indexed)
                if len(row) >= 3:
                    instance_id = row[2].strip()
                    
                    # Look up SWE-bench results for this instance_id
                    swe_data = swe_bench_results.get(instance_id, {})
                    pr_info = pr_mapping.get(instance_id, {})
                    
                    if swe_data:
                        matched_instances += 1
                        resolved_status = swe_data.get('resolved_status', '')
                        pass_to_pass = swe_data.get('PASS_TO_PASS', '')
                        fail_to_pass = swe_data.get('FAIL_TO_PASS', '')
                        project_guide_url = generate_project_guide_url(pr_info)
                    else:
                        # No SWE-bench data for this instance
                        resolved_status = ''
                        pass_to_pass = ''
                        fail_to_pass = ''
                        project_guide_url = ''
                    
                    # Add the new columns to the row
                    merged_row = row + [
                        resolved_status,
                        pass_to_pass,
                        fail_to_pass,
                        project_guide_url
                    ]
                    
                else:
                    # Row doesn't have enough columns, add empty values
                    merged_row = row + ['', '', '', '']
                
                merged_rows.append(merged_row)
        
        # Write the merged CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(merged_rows)
        
        print(f"Merged CSV file created successfully: {output_file}")
        print(f"Total rows processed: {total_rows}")
        print(f"Instances matched with SWE-bench data: {matched_instances}")
        print(f"Match rate: {matched_instances/total_rows*100:.1f}%" if total_rows > 0 else "No data rows found")
        
        # Show some examples of merged data
        if matched_instances > 0:
            print("\nExample merged rows with SWE-bench data:")
            count = 0
            for row in merged_rows[1:]:  # Skip header
                if len(row) >= 5 and row[-4]:  # Has SWE data
                    instance_id = row[2] if len(row) >= 3 else "N/A"
                    resolved_status = row[-4]
                    pass_to_pass = row[-3]
                    fail_to_pass = row[-2]
                    print(f"  {instance_id}: {resolved_status}")
                    print(f"    LATEST_PASS_TO_PASS: {pass_to_pass}")
                    print(f"    LATEST_FAIL_TO_PASS: {fail_to_pass}")
                    count += 1
                    if count >= 3:
                        break
        
        return True
        
    except Exception as e:
        print(f"Error merging CSV files: {e}")
        return False


def main():
    """Main function to merge the files."""
    
    # File paths
    sbv_file = "/Users/jackblundin/Modal_Run_Environment/SBV_Database_Bug_Fix_Status.csv"
    swe_bench_results_file = "/Users/jackblundin/Modal_Run_Environment/swe_bench_results_summary.json"
    pr_urls_file = "/Users/jackblundin/Modal_Run_Environment/SWE-bench/patch_file_creation_process/PR_fetch_results/pr_urls.json"
    pr_urls_updated_file = "/Users/jackblundin/Modal_Run_Environment/SWE-bench/patch_file_creation_process/PR_fetch_results/pr_urls_updated.json"
    output_file = "/Users/jackblundin/Modal_Run_Environment/SBV_Database_Bug_Fix_Status_merged.csv"
    
    print("Loading SWE-bench results...")
    swe_bench_results = load_swe_bench_results(swe_bench_results_file)
    
    if not swe_bench_results:
        print("Error: Could not load SWE-bench results")
        return 1
    
    print("Loading PR URL mappings...")
    pr_mapping = load_pr_urls(pr_urls_file, pr_urls_updated_file)
    
    print(f"Loaded {len(swe_bench_results)} SWE-bench results")
    print(f"Loaded {len(pr_mapping)} PR mappings")
    
    print("Merging CSV files...")
    success = merge_csv_files(sbv_file, swe_bench_results, pr_mapping, output_file)
    
    if success:
        print("CSV merge completed successfully!")
        print(f"Output file: {output_file}")
        return 0
    else:
        print("CSV merge failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
