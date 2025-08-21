#!/usr/bin/env python3
"""
SWE-bench to SBV Database Merger

This script merges SWE-bench evaluation results into the existing SBV_Database_Bug_Fix_Status.csv file.
"""

import csv
import json
import sys
from pathlib import Path


# Removed unused JSON-based functions since we now work directly with CSV files


def parse_test_results(test_results_str):
    """
    Parse test results string to extract PASS_TO_PASS and FAIL_TO_PASS values.
    
    Args:
        test_results_str (str): String like "PASS_TO_PASS: 19/20, FAIL_TO_PASS: 0/1"
        
    Returns:
        tuple: (pass_to_pass, fail_to_pass) as strings
    """
    pass_to_pass = ''
    fail_to_pass = ''
    
    if test_results_str:
        # Split by comma and process each part
        parts = test_results_str.split(',')
        for part in parts:
            part = part.strip()
            if 'PASS_TO_PASS:' in part:
                pass_to_pass = part.replace('PASS_TO_PASS:', '').strip()
            elif 'FAIL_TO_PASS:' in part:
                fail_to_pass = part.replace('FAIL_TO_PASS:', '').strip()
    
    return pass_to_pass, fail_to_pass


def load_swe_bench_csv(csv_file):
    """
    Load SWE-bench results from CSV file.
    
    Args:
        csv_file (str): Path to the SWE-bench results CSV file
        
    Returns:
        dict: SWE-bench results data keyed by instance_id
    """
    results = {}
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                instance_id = row.get('instance_id', '').strip()
                if instance_id:
                    test_results = row.get('test_results', '')
                    pass_to_pass, fail_to_pass = parse_test_results(test_results)
                    
                    results[instance_id] = {
                        'test_results': test_results,
                        'resolved_status': row.get('resolved_status', ''),
                        'project_guide_url': row.get('project_guide_url', ''),
                        'pr_url': row.get('pr_url', ''),
                        'pr_title': row.get('pr_title', ''),
                        'pass_to_pass': pass_to_pass,
                        'fail_to_pass': fail_to_pass
                    }
    except Exception as e:
        print(f"Error loading SWE-bench CSV: {e}")
    
    return results


def merge_csv_files(sbv_file, swe_bench_csv, output_file):
    """
    Merge SWE-bench results into the SBV Database Bug Fix Status CSV by updating existing rows
    and appending new rows based on instance_id matching.
    
    Args:
        sbv_file (str): Path to the SBV_Database_Bug_Fix_Status.csv file
        swe_bench_csv (str): Path to the swe_bench_results.csv file
        output_file (str): Path to output merged CSV file
    """
    
    # Load SWE-bench results from CSV
    swe_bench_data = load_swe_bench_csv(swe_bench_csv)
    
    merged_rows = []
    header_row = None
    matched_instances = 0
    updated_instances = 0
    new_instances = 0
    total_sbv_rows = 0
    processed_instance_ids = set()
    
    try:
        # Read the existing SBV CSV file
        with open(sbv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            for row_num, row in enumerate(reader):
                if row_num == 0:
                    # Keep the original header row unchanged
                    header_row = row[:]
                    merged_rows.append(header_row)
                    continue
                
                total_sbv_rows += 1
                
                # Extract instance_id from column 2 (0-indexed)
                if len(row) >= 3:
                    instance_id = row[2].strip()
                    processed_instance_ids.add(instance_id)
                    
                    # Look up SWE-bench results for this instance_id
                    swe_data = swe_bench_data.get(instance_id)
                    
                    if swe_data:
                        matched_instances += 1
                        # Update the row with SWE-bench data
                        updated_row = row[:]
                        
                        # Ensure row has enough columns (extend if necessary)
                        while len(updated_row) < 17:  # Extend to accommodate all columns
                            updated_row.append('')
                        
                        # Update status column (column 7, 0-indexed) if SWE-bench has resolved status
                        if swe_data.get('resolved_status'):
                            # Extract just the emoji from resolved_status (✅ or ❌)
                            resolved_status = swe_data['resolved_status']
                            if '✅' in resolved_status:
                                updated_row[7] = 'Pass'
                                updated_instances += 1
                            elif '❌' in resolved_status:
                                updated_row[7] = 'Fail'
                                updated_instances += 1
                        
                        # Update LATEST_PASS_TO_PASS column (column 9, 0-indexed)
                        if swe_data.get('pass_to_pass'):
                            updated_row[9] = swe_data['pass_to_pass']
                        
                        # Update LATEST_FAIL_TO_PASS column (column 10, 0-indexed)
                        if swe_data.get('fail_to_pass'):
                            updated_row[10] = swe_data['fail_to_pass']
                        
                        # Update Project_Guide_URL column (column 11, 0-indexed)
                        if swe_data.get('project_guide_url'):
                            updated_row[11] = swe_data['project_guide_url']
                        
                        merged_rows.append(updated_row)
                    else:
                        # No SWE-bench data for this instance, keep original row
                        merged_rows.append(row)
                else:
                    # Row doesn't have enough columns, keep as is
                    merged_rows.append(row)
        
        # Add any new instances from SWE-bench that weren't in the original SBV file
        for instance_id, swe_data in swe_bench_data.items():
            if instance_id not in processed_instance_ids:
                new_instances += 1
                # Create a new row with basic structure
                # Format: #, Repo Name, instance_id, Solve Rates, # Correct, Last Run Time, Current Attempt #, Status, Comments, ...
                repo_name = instance_id.split('__')[0].title() if '__' in instance_id else 'Unknown'
                status = 'Pass' if '✅' in swe_data.get('resolved_status', '') else 'Fail'
                
                new_row = [
                    '',  # # (will be filled manually if needed)
                    repo_name,  # Repo Name
                    instance_id,  # instance_id
                    '',  # Solve Rates / Top 26 Models
                    '',  # # Correct / Top 26 Models
                    '',  # Last Run Time
                    '',  # Current Attempt #
                    status,  # Status (Pass/Fail)
                    '',  # OVERALL UNIT TESTS
                    swe_data.get('pass_to_pass', ''),  # LATEST_PASS_TO_PASS
                    swe_data.get('fail_to_pass', ''),  # LATEST_FAIL_TO_PASS
                    swe_data.get('project_guide_url', ''),  # Project_Guide_URL
                    f"Added from SWE-bench results: {swe_data.get('resolved_status', '')}",  # Comments
                    '',  # Project Guide Analysis
                    '',  # Project Python Version
                    '',  # Additional columns...
                    ''
                ]
                merged_rows.append(new_row)
        
        # Write the merged CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(merged_rows)
        
        print(f"Merged CSV file created successfully: {output_file}")
        print(f"Total SBV rows processed: {total_sbv_rows}")
        print(f"Instances matched with SWE-bench data: {matched_instances}")
        print(f"Instances with updated status: {updated_instances}")
        print(f"New instances added: {new_instances}")
        print(f"Match rate: {matched_instances/total_sbv_rows*100:.1f}%" if total_sbv_rows > 0 else "No data rows found")
        
        # Show some examples of updated data
        if updated_instances > 0:
            print("\nExample updated rows:")
            count = 0
            for row in merged_rows[1:]:  # Skip header
                if len(row) >= 3:
                    instance_id = row[2]
                    if instance_id in swe_bench_data:
                        status = row[7] if len(row) >= 8 else 'N/A'
                        swe_status = swe_bench_data[instance_id].get('resolved_status', '')
                        print(f"  {instance_id}: Status = {status} (from SWE-bench: {swe_status})")
                        count += 1
                        if count >= 3:
                            break
        
        if new_instances > 0:
            print(f"\nAdded {new_instances} new instances from SWE-bench results")
        
        return True
        
    except Exception as e:
        print(f"Error merging CSV files: {e}")
        return False


def main():
    """Main function to merge the files."""
    
    # File paths
    sbv_file = "/Users/jackblundin/Modal_Run_Environment/SWE-bench/Evaluation_Post_Processing/SBV_Database_Bug_Fix Status.csv"
    swe_bench_csv_file = "/Users/jackblundin/Modal_Run_Environment/SWE-bench/Evaluation_Post_Processing/swe_bench_results.csv"
    output_file = "/Users/jackblundin/Modal_Run_Environment/SWE-bench/Evaluation_Post_Processing/SBV_Database_Bug_Fix_Status_merged_3.csv"
    
    # Check if input files exist
    if not Path(sbv_file).exists():
        print(f"Error: SBV file not found: {sbv_file}")
        return 1
    
    if not Path(swe_bench_csv_file).exists():
        print(f"Error: SWE-bench CSV file not found: {swe_bench_csv_file}")
        return 1
    
    print("Merging CSV files...")
    print(f"Source SBV file: {sbv_file}")
    print(f"Source SWE-bench file: {swe_bench_csv_file}")
    print(f"Output file: {output_file}")
    
    success = merge_csv_files(sbv_file, swe_bench_csv_file, output_file)
    
    if success:
        print("\nCSV merge completed successfully!")
        print(f"Updated file saved as: {output_file}")
        return 0
    else:
        print("CSV merge failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
