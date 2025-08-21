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

## Step 6: Analyze Results (Complete Replacement)

**Run:** `update_results_summary.py` to scrape ALL logs directories and create fresh summary

- **Input:** Searches entire `/logs` directory recursively for all `report.json` files
- **Behavior:** **Completely replaces** existing summary with only current evaluation results
- **Output:** `swe_bench_results_summary.json` with fresh data (no incremental merging)
- **Note:** If logs contain 25 files, summary will have exactly 25 entries

## Step 7: Generate CSV from Summary

**Run:** `generate_swe_bench_csv.py` to convert JSON summary to CSV format

- **Input:** `swe_bench_results_summary.json`
- **PR Data Source:** Single JSON file at `/Users/jackblundin/patch_file_creation_process_copy/PR_fetch_results/pr_urls.json`
- **Output:** `swe_bench_results.csv` with columns:
  - `instance_id`, `test_results`, `resolved_status`, `project_guide_url`, `pr_url`, `pr_title`
- **Features:** Includes parsed PASS_TO_PASS and FAIL_TO_PASS ratios, project guide URLs

## Step 8: Merge with SBV Database (Value Updates)

**Run:** `merge_swe_bench_to_sbv.py` to update existing SBV spreadsheet data

- **Input:** `swe_bench_results.csv` + `SBV_Database_Bug_Fix_Status.csv`
- **Behavior:** **Updates existing rows** by matching `instance_id` (no new columns added)
- **Updates:** Status, LATEST_PASS_TO_PASS, LATEST_FAIL_TO_PASS, Project_Guide_URL columns
- **Preservation:** Rows without matching instance_id remain unchanged
- **Output:** `SBV_Database_Bug_Fix_Status_merged.csv`

## Step 9: Manual Google Sheets Update

**Action:** Replace relevant columns in Google Sheets with updated data

- Copy updated columns from `SBV_Database_Bug_Fix_Status_merged.csv`
- Paste into master tracking Google Sheet "Bug fix status"
- Data will align by instance_id with existing rows
- Only updated instances will show new values

---

## Pipeline Overview

This pipeline provides a complete workflow from generating PR numbers through final Google Sheets integration for SWE-bench evaluation results. Each step builds upon the previous one to create a comprehensive evaluation and tracking system for bug fix attempts.

### Key Features:

- **Automated patch processing** from PR data
- **Batch evaluation** using Modal for scalability
- **Complete result replacement** ensuring fresh data from latest evaluations
- **Value-based merging** that updates existing rows without adding columns
- **Comprehensive logs scanning** across all evaluation directories
- **Google Sheets integration** for manual review and tracking
- **Detailed test result analysis** with parsed PASS_TO_PASS and FAIL_TO_PASS ratios

### Prerequisites:

- Access to GitHub repositories with PR data
- Modal account for distributed evaluation
- Google Sheets for manual tracking
- SWE-bench evaluation framework setup
