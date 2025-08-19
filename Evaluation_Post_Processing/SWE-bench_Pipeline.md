# SWE-bench Evaluation Pipeline

## Step 1: Generate PR Numbers
**Run:** `get_pr_numbers_authenticated.py`
- **Output:** `pr_numbers.json`

## Step 2: Process Patches
**Use:** `pr_numbers.json` to run one of the batch processor files
- **Recommended:** `batch_patch_processor_fast.py`
- **Output:** Patch files in `"patches_clean"` directory

## Step 3: Generate JSONL Format
**Run:** `generate.jsonl.py` to format the patches into jsonl for SWE-bench run_evaluation
- **Output:** `swe_bench_predictions_clean.jsonl` in the jsonl directory

## Step 4: Split JSONL into Batches
**Run:** `split_jsonl.py` to split the jsonl file into smaller batches for module modal evals
- **Output:** `jsonl_filtered` directory in the "modal_run_environment" codebase, which is my version of SWE-bench

## Step 5: Run Modal Evaluations
**Run:** The `evaluate_command.txt` file to run the modal evals
- **Output:** logs directory is populated and `Blitzy 3.0.{your_run_id}.json` is created

## Step 6: Analyze Results
**Run:** `analyze_swe_bench_results.py` to scrape the logs to get a nicely formatted summary
- **Output:** `swe_bench_results_summary.json` in the "modal_run_environment" codebase

## Step 7: Generate CSV
**Run:** `generate_swe_bench_csv.py`
- **Output:** A CSV representation of the results from `swe_bench_results_summary.json`

## Step 8: Merge with SBV Database
**Run:** `merge_swe_bench_to_sbv.py`
- **Output:** Merges the data from the new eval results CSV with the current google spreadsheet CSV

## Step 9: Manual Google Sheets Update
**Action:** Manually update the google sheet with the new data
- Pull new columns from the merged CSV and paste them into the Google sheet
- They should line up with the rows in the master tracking google sheet called "Bug fix status"

---

## Pipeline Overview

This pipeline provides a complete workflow from generating PR numbers through final Google Sheets integration for SWE-bench evaluation results. Each step builds upon the previous one to create a comprehensive evaluation and tracking system for bug fix attempts.

### Key Features:
- **Automated patch processing** from PR data
- **Batch evaluation** using Modal for scalability
- **Incremental result tracking** that preserves existing data
- **Google Sheets integration** for manual review and tracking
- **Comprehensive test result analysis** with pass/fail ratios

### Prerequisites:
- Access to GitHub repositories with PR data
- Modal account for distributed evaluation
- Google Sheets for manual tracking
- SWE-bench evaluation framework setup
