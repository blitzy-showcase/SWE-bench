#!/usr/bin/env python3
"""
SWE-bench Evaluation Runner

This script automatically runs the SWE-bench evaluation command for every JSONL file 
in the jsonl_filtered directory, supporting parallel execution.
"""

import os
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation_runner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def find_jsonl_files(jsonl_dir):
    """
    Find all JSONL files in the specified directory.
    
    Args:
        jsonl_dir (str): Path to the directory containing JSONL files
        
    Returns:
        list: List of JSONL file paths
    """
    jsonl_path = Path(jsonl_dir)
    if not jsonl_path.exists():
        logger.error(f"Directory not found: {jsonl_dir}")
        return []
    
    jsonl_files = list(jsonl_path.glob("*.jsonl"))
    logger.info(f"Found {len(jsonl_files)} JSONL files in {jsonl_dir}")
    
    return sorted(jsonl_files)


def extract_run_id(jsonl_file):
    """
    Extract the run ID from the JSONL filename.
    
    Args:
        jsonl_file (Path): Path to the JSONL file
        
    Returns:
        str: Run ID extracted from filename
    """
    # Extract filename without extension
    filename = jsonl_file.stem
    
    # For files like "swe_bench_predictions_001-026.jsonl", use the full name as run_id
    return filename


def run_evaluation_command(jsonl_file, base_dir):
    """
    Run the SWE-bench evaluation command for a single JSONL file.
    
    Args:
        jsonl_file (Path): Path to the JSONL file
        base_dir (str): Base directory for the SWE-bench project
        
    Returns:
        tuple: (success, jsonl_file, output, error)
    """
    run_id = extract_run_id(jsonl_file)
    relative_path = f"./jsonl_filtered/{jsonl_file.name}"
    
    command = [
        "python3", "-m", "swebench.harness.run_evaluation",
        "--dataset_name", "princeton-nlp/SWE-bench_Verified",
        "--predictions_path", relative_path,
        "--modal", "true",
        "--run_id", run_id
    ]
    
    logger.info(f"Starting evaluation for {jsonl_file.name} with run_id: {run_id}")
    logger.info(f"Command: {' '.join(command)}")
    
    start_time = time.time()
    
    try:
        # Run the command in the base directory
        result = subprocess.run(
            command,
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            logger.info(f"✅ Successfully completed evaluation for {jsonl_file.name} in {duration:.2f}s")
            return True, jsonl_file, result.stdout, result.stderr
        else:
            logger.error(f"❌ Failed evaluation for {jsonl_file.name} (exit code: {result.returncode})")
            logger.error(f"Error output: {result.stderr}")
            return False, jsonl_file, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ Timeout expired for {jsonl_file.name}")
        return False, jsonl_file, "", "Timeout expired"
        
    except Exception as e:
        logger.error(f"💥 Exception occurred for {jsonl_file.name}: {e}")
        return False, jsonl_file, "", str(e)


def run_evaluations_parallel(jsonl_files, base_dir, max_workers=2):
    """
    Run evaluations for multiple JSONL files in parallel.
    
    Args:
        jsonl_files (list): List of JSONL file paths
        base_dir (str): Base directory for the SWE-bench project
        max_workers (int): Maximum number of parallel workers
        
    Returns:
        dict: Results of all evaluations
    """
    results = {}
    
    logger.info(f"Starting parallel evaluation of {len(jsonl_files)} files with {max_workers} workers")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(run_evaluation_command, jsonl_file, base_dir): jsonl_file
            for jsonl_file in jsonl_files
        }
        
        # Process completed tasks
        for future in as_completed(future_to_file):
            jsonl_file = future_to_file[future]
            try:
                success, file_path, stdout, stderr = future.result()
                results[file_path.name] = {
                    'success': success,
                    'stdout': stdout,
                    'stderr': stderr
                }
            except Exception as e:
                logger.error(f"Exception in future for {jsonl_file.name}: {e}")
                results[jsonl_file.name] = {
                    'success': False,
                    'stdout': '',
                    'stderr': str(e)
                }
    
    return results


def print_summary(results):
    """
    Print a summary of all evaluation results.
    
    Args:
        results (dict): Results from all evaluations
    """
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    logger.info("\n" + "="*60)
    logger.info("EVALUATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total files processed: {total}")
    logger.info(f"Successful evaluations: {successful}")
    logger.info(f"Failed evaluations: {total - successful}")
    logger.info(f"Success rate: {successful/total*100:.1f}%")
    
    if successful < total:
        logger.info("\nFailed evaluations:")
        for filename, result in results.items():
            if not result['success']:
                logger.error(f"  ❌ {filename}")
                if result['stderr']:
                    logger.error(f"     Error: {result['stderr'][:200]}...")
    
    logger.info("="*60)


def main():
    """Main function to run all evaluations."""
    
    # Configuration
    base_dir = "/Users/jackblundin/Modal_Run_Environment/SWE-bench"
    jsonl_dir = os.path.join(base_dir, "jsonl_filtered")
    max_workers = 2  # Run 2 evaluations simultaneously as requested
    
    logger.info("Starting SWE-bench Evaluation Runner")
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"JSONL directory: {jsonl_dir}")
    logger.info(f"Max parallel workers: {max_workers}")
    
    # Find all JSONL files
    jsonl_files = find_jsonl_files(jsonl_dir)
    
    if not jsonl_files:
        logger.error("No JSONL files found. Exiting.")
        return 1
    
    # Display files to be processed
    logger.info("Files to be evaluated:")
    for jsonl_file in jsonl_files:
        logger.info(f"  📄 {jsonl_file.name}")
    
    # Confirm before starting
    try:
        response = input(f"\nProceed with evaluating {len(jsonl_files)} files? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            logger.info("Evaluation cancelled by user.")
            return 0
    except KeyboardInterrupt:
        logger.info("\nEvaluation cancelled by user.")
        return 0
    
    # Run evaluations
    start_time = time.time()
    results = run_evaluations_parallel(jsonl_files, base_dir, max_workers)
    end_time = time.time()
    
    # Print summary
    print_summary(results)
    
    total_duration = end_time - start_time
    logger.info(f"Total execution time: {total_duration:.2f}s ({total_duration/60:.1f} minutes)")
    
    # Return appropriate exit code
    successful = sum(1 for r in results.values() if r['success'])
    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
