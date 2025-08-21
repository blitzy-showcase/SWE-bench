#!/usr/bin/env python3
"""
SWE-bench Resolved Instance Finder

This script searches through all Blitzy 3.0.swe_bench_predictions*.json files
to find which specified instance IDs have "resolved" status.
"""

import json
import os
import sys
from pathlib import Path
import glob

def load_target_instances(instances_file):
    """Load the list of target instance IDs from a file."""
    target_instances = []
    try:
        with open(instances_file, 'r', encoding='utf-8') as f:
            for line in f:
                instance_id = line.strip()
                if instance_id:  # Skip empty lines
                    target_instances.append(instance_id)
        print(f"Loaded {len(target_instances)} target instances from {instances_file}")
        return set(target_instances)
    except Exception as e:
        print(f"Error loading instances from {instances_file}: {e}")
        return set()


def find_evaluation_files(base_dir):
    """Find all Blitzy 3.0.swe_bench_predictions*.json files."""
    pattern = os.path.join(base_dir, "Blitzy 3.0.swe_bench_predictions*.json")
    files = glob.glob(pattern)
    return sorted(files)


def load_json_file(file_path):
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def search_resolved_instances(json_files, target_instances):
    """
    Search through JSON files for resolved instances.
    
    Args:
        json_files (list): List of JSON file paths
        target_instances (set): Set of target instance IDs to search for
        
    Returns:
        dict: Results containing resolved instances and their sources
    """
    # Track all occurrences of each instance
    instance_occurrences = {}
    
    results = {
        'resolved_instances': {},
        'unresolved_instances': {},
        'not_found_instances': set(target_instances.copy()),
        'files_processed': 0,
        'total_files': len(json_files)
    }
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            results['files_processed'] += 1
            
            # Look specifically in the resolved_ids array
            resolved_ids = data.get('resolved_ids', [])
            
            # Check each target instance
            for instance_id in target_instances:
                # Track this file for this instance
                if instance_id not in instance_occurrences:
                    instance_occurrences[instance_id] = []
                
                is_resolved = instance_id in resolved_ids
                instance_occurrences[instance_id].append({
                    'file': os.path.basename(json_file),
                    'resolved': is_resolved
                })
                
                # If found in any capacity, remove from not_found
                if is_resolved:
                    results['not_found_instances'].discard(instance_id)
        
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading {json_file}: {e}")
            continue
    
    # Process all occurrences and determine final status
    for instance_id, occurrences in instance_occurrences.items():
        # Check if any occurrence shows resolved=True (prioritize resolved)
        resolved_in_any = any(occ['resolved'] for occ in occurrences)
        
        if resolved_in_any:
            # Find the first file where it's resolved
            resolved_file = next(occ['file'] for occ in occurrences if occ['resolved'])
            results['resolved_instances'][instance_id] = {
                'primary_file': resolved_file,
                'all_files': [occ['file'] for occ in occurrences if occ['resolved']],
                'total_occurrences': len([occ for occ in occurrences if occ['resolved']])
            }
            # Remove from not_found since we found it resolved
            results['not_found_instances'].discard(instance_id)
        else:
            # Not found in any resolved_ids arrays
            results['unresolved_instances'][instance_id] = {
                'primary_file': 'Not found in resolved_ids',
                'all_files': [],
                'total_occurrences': 0
            }
    
    return results, instance_occurrences


def print_summary(results, target_instances):
    """Print a comprehensive summary of the search results."""
    print("\n" + "="*80)
    print("SEARCH RESULTS SUMMARY")
    print("="*80)
    
    resolved_count = len(results['resolved_instances'])
    unresolved_count = len(results['unresolved_instances'])
    not_found_count = len(results['not_found_instances'])
    total_targets = len(target_instances)
    
    print(f"Files processed: {results['files_processed']}/{results['total_files']}")
    print(f"Target instances: {total_targets}")
    print(f"Resolved instances: {resolved_count}")
    print(f"Unresolved instances: {unresolved_count}")
    print(f"Not found instances: {not_found_count}")
    print(f"Resolution rate: {resolved_count/total_targets*100:.1f}%")
    
    if results['resolved_instances']:
        print(f"\n🎉 RESOLVED INSTANCES ({resolved_count}):")
        print("-" * 50)
        for instance_id, info in sorted(results['resolved_instances'].items()):
            print(f"  ✅ {instance_id}")
            print(f"     Primary source: {info['primary_file']}")
            if len(info.get('all_files', [])) > 1:
                print(f"     Total files with resolved status: {len(info['all_files'])}")
                other_files = [f for f in info['all_files'] if f != info['primary_file']]
                if other_files:
                    print(f"     Also resolved in: {', '.join(other_files)}")
    
    if results['unresolved_instances']:
        print(f"\n❌ UNRESOLVED INSTANCES ({unresolved_count}):")
        print("-" * 50)
        for instance_id, info in sorted(results['unresolved_instances'].items()):
            print(f"  ❌ {instance_id}")
            print(f"     Status: {info['primary_file']}")
    
    if results['not_found_instances']:
        print(f"\n❓ NOT FOUND INSTANCES ({not_found_count}):")
        print("-" * 50)
        for instance_id in sorted(results['not_found_instances']):
            print(f"  ❓ {instance_id}")
    
    print("="*80)


def save_results_to_file(results, output_file):
    """Save detailed results to a JSON file."""
    # Convert sets to lists for JSON serialization
    resolved_instances_clean = {}
    for instance_id, info in results['resolved_instances'].items():
        resolved_instances_clean[instance_id] = {
            'status': 'resolved',
            'primary_file': info['primary_file'],
            'all_files': info['all_files'],
            'total_occurrences': info['total_occurrences']
        }
    
    unresolved_instances_clean = {}
    for instance_id, info in results['unresolved_instances'].items():
        unresolved_instances_clean[instance_id] = {
            'status': 'unresolved',
            'primary_file': info['primary_file'],
            'all_files': info['all_files'],
            'total_occurrences': info['total_occurrences']
        }
    
    output_data = {
        'search_summary': {
            'files_processed': results['files_processed'],
            'total_files': results['total_files'],
            'resolved_count': len(results['resolved_instances']),
            'unresolved_count': len(results['unresolved_instances']),
            'not_found_count': len(results['not_found_instances']),
            'instances_with_multiple_occurrences': 0,
            'total_occurrences': 0
        },
        'resolved_instances': resolved_instances_clean,
        'unresolved_instances': unresolved_instances_clean,
        'not_found_instances': list(results['not_found_instances'])
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving results to {output_file}: {e}")


def main():
    """Main function to search for resolved instances."""
    
    # Configuration
    base_dir = "/Users/jackblundin/Modal_Run_Environment/SWE-bench"
    instances_file = os.path.join(base_dir, "search_instances.txt")
    output_file = os.path.join(base_dir, "resolved_instances_search_results.json")
    
    print("SWE-bench Resolved Instance Finder")
    print("=" * 50)
    
    # Load target instances from file
    target_instances = load_target_instances(instances_file)
    if not target_instances:
        print("No target instances loaded!")
        return 1
    
    # Find evaluation files
    json_files = find_evaluation_files(base_dir)
    if not json_files:
        print("No evaluation JSON files found!")
        return 1
    
    print(f"Found {len(json_files)} evaluation files to search")
    
    # Search for resolved instances
    results, instance_occurrences = search_resolved_instances(json_files, target_instances)
    
    # Print summary
    print_summary(results, target_instances)
    
    # Save detailed results
    save_results_to_file(results, output_file)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
