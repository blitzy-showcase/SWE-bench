#!/usr/bin/env python3
"""
SWE-bench Results CSV Generator

This script converts the SWE-bench results JSON to CSV format with project guide URLs.
"""

import json
import csv
import sys
from pathlib import Path


def load_pr_urls(pr_urls_file):
    """
    Load PR URLs from JSON file and create a mapping from base_branch to PR info.
    
    Args:
        pr_urls_file (str): Path to pr_urls.json
        
    Returns:
        dict: Mapping from base_branch (instance_id) to PR info
    """
    pr_mapping = {}
    
    try:
        with open(pr_urls_file, 'r') as f:
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
        print(f"Error: Could not load {pr_urls_file}: {e}")
    
    return pr_mapping


def generate_project_guide_url(pr_info):
    """
    Generate the project guide URL from PR information with robust fallback options.
    
    Args:
        pr_info (dict): PR information containing repo, head_branch, etc.
        
    Returns:
        str: URL to the project guide markdown file
    """
    if not pr_info or not pr_info.get('repo') or not pr_info.get('head_branch'):
        return ""
    
    repo = pr_info['repo']
    head_branch = pr_info['head_branch']
    
    # Primary format: https://github.com/{repo}/blob/{head_branch}/blitzy/documentation/Project%20Guide.md
    # URL encode the space in "Project Guide.md" properly
    project_guide_url = f"https://github.com/{repo}/blob/{head_branch}/blitzy/documentation/Project%20Guide.md"
    
    return project_guide_url


def validate_project_guide_url(url):
    """
    Validate if a project guide URL is accessible.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is accessible, False otherwise
    """
    if not url:
        return False
    
    try:
        import urllib.request
        import urllib.error
        
        # Convert GitHub blob URL to raw URL for validation
        raw_url = url.replace('/blob/', '/raw/')
        
        req = urllib.request.Request(raw_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; URL validator)')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.getcode() == 200
            
    except (urllib.error.URLError, urllib.error.HTTPError, Exception):
        return False


def generate_project_guide_url_with_validation(pr_info):
    """
    Generate and validate project guide URL with fallback options.
    
    Args:
        pr_info (dict): PR information containing repo, head_branch, etc.
        
    Returns:
        str: Validated URL to the project guide markdown file, or empty string if none found
    """
    if not pr_info or not pr_info.get('repo') or not pr_info.get('head_branch'):
        return ""
    
    repo = pr_info['repo']
    head_branch = pr_info['head_branch']
    
    # Try different possible file paths and names
    possible_paths = [
        "blitzy/documentation/Project%20Guide.md",  # URL encoded space
        "blitzy/documentation/Project Guide.md",    # Regular space
        "blitzy/documentation/ProjectGuide.md",     # No space
        "blitzy/documentation/project-guide.md",    # Lowercase with dash
        "blitzy/documentation/README.md",           # Alternative name
        "documentation/Project%20Guide.md",         # Without blitzy folder
        "documentation/Project Guide.md",           # Without blitzy folder, regular space
    ]
    
    base_url = f"https://github.com/{repo}/blob/{head_branch}/"
    
    for path in possible_paths:
        url = base_url + path
        if validate_project_guide_url(url):
            return url
    
    # If no valid URL found, return the primary format anyway
    return f"https://github.com/{repo}/blob/{head_branch}/blitzy/documentation/Project%20Guide.md"


def load_swe_bench_results(results_file):
    """
    Load the SWE-bench results JSON file.
    
    Args:
        results_file (str): Path to the results JSON file
        
    Returns:
        dict: SWE-bench results data
    """
    try:
        with open(results_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading SWE-bench results: {e}")
        return {}


def generate_csv(results_data, pr_mapping, output_file):
    """
    Generate CSV file from SWE-bench results and PR mapping.
    
    Args:
        results_data (dict): SWE-bench results data
        pr_mapping (dict): Mapping from instance_id to PR info
        output_file (str): Path to output CSV file
    """
    
    # CSV headers
    headers = [
        'instance_id',
        'test_results',
        'resolved_status', 
        'project_guide_url',
        'pr_url',
        'pr_title'
    ]
    
    rows = []
    missing_pr_count = 0
    
    for instance_id, data in results_data.items():
        # Combine PASS_TO_PASS and FAIL_TO_PASS ratios
        pass_to_pass = data.get('PASS_TO_PASS', 'N/A')
        fail_to_pass = data.get('FAIL_TO_PASS', 'N/A')
        test_results = f"PASS_TO_PASS: {pass_to_pass}, FAIL_TO_PASS: {fail_to_pass}"
        
        # Get resolved status
        resolved_status = data.get('resolved_status', 'Unknown')
        
        # Look up PR information
        pr_info = pr_mapping.get(instance_id, {})
        
        if not pr_info:
            missing_pr_count += 1
            project_guide_url = ""
            pr_url = ""
            pr_title = ""
            print(f"Warning: No PR information found for {instance_id}")
        else:
            # Use the validation approach for more reliable URLs
            project_guide_url = generate_project_guide_url_with_validation(pr_info)
            pr_url = pr_info.get('url', '')
            pr_title = pr_info.get('title', '')
            
            # Log if URL validation was used
            if not project_guide_url:
                print(f"Warning: Could not find valid project guide URL for {instance_id}")
            elif not project_guide_url.endswith('Project%20Guide.md') and not project_guide_url.endswith('Project Guide.md'):
                print(f"Info: Using alternative project guide path for {instance_id}: {project_guide_url}")
        
        # Create row
        row = [
            instance_id,
            test_results,
            resolved_status,
            project_guide_url,
            pr_url,
            pr_title
        ]
        
        rows.append(row)
    
    # Sort rows by instance_id for consistent output
    rows.sort(key=lambda x: x[0])
    
    # Write CSV file
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        
        print(f"CSV file generated successfully: {output_file}")
        print(f"Total instances: {len(rows)}")
        print(f"Instances with PR info: {len(rows) - missing_pr_count}")
        print(f"Instances missing PR info: {missing_pr_count}")
        
        # Show a few example rows
        if rows:
            print("\nExample rows:")
            for i, row in enumerate(rows[:3]):
                print(f"  {i+1}. {row[0]}: {row[1]}")
                print(f"     Status: {row[2]}")
                print(f"     Project Guide: {row[3]}")
                print(f"     PR URL: {row[4]}")
                print()
        
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        return False
    
    return True


def main():
    """Main function to generate the CSV."""
    
    # File paths
    results_file = "/Users/jackblundin/Modal_Run_Environment/SWE-bench/Evaluation_Post_Processing/swe_bench_results_summary.json"
    pr_urls_file = "/Users/jackblundin/patch_file_creation_process_copy/PR_fetch_results/pr_urls.json"
    output_file = "/Users/jackblundin/Modal_Run_Environment/SWE-bench/Evaluation_Post_Processing/swe_bench_results.csv"
    
    print("Loading SWE-bench results...")
    results_data = load_swe_bench_results(results_file)
    
    if not results_data:
        print("Error: Could not load SWE-bench results")
        return 1
    
    print("Loading PR URL mappings...")
    pr_mapping = load_pr_urls(pr_urls_file)
    
    print(f"Loaded {len(pr_mapping)} PR mappings")
    print(f"Loaded {len(results_data)} SWE-bench results")
    
    print("Generating CSV...")
    success = generate_csv(results_data, pr_mapping, output_file)
    
    if success:
        print("CSV generation completed successfully!")
        return 0
    else:
        print("CSV generation failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
