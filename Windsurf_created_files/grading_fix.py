# Fixed version of get_logs_eval function for SWE-Bench Modal evaluations
# This file contains the corrected implementation that resolves test output capture issues

def get_logs_eval(test_spec: TestSpec, log_fp: str) -> tuple[dict[str, str], bool]:
    """
    Retrieve evaluation results for a task instance from its corresponding log file

    Args:
        log_fp (str): path to log file
    Returns:
        bool: whether the patch applied successfully
        dict: status map

    FIXED: Added fallback parsing for Modal environments where pytest output
    may not be captured between START_TEST_OUTPUT and END_TEST_OUTPUT markers
    """
    repo = test_spec.repo
    version = test_spec.version
    log_parser = MAP_REPO_TO_PARSER[repo]
    test_cmd = MAP_REPO_VERSION_TO_SPECS[repo][version]["test_cmd"]
    if isinstance(test_cmd, list):
        test_cmd = test_cmd[-1]

    with open(log_fp) as f:
        content = f.read()
        # TODO fix constant here
        bad_codes = list(
            filter(
                lambda x: x in content,
                [
                    APPLY_PATCH_FAIL,
                    RESET_FAILED,
                    TESTS_ERROR,
                    TESTS_TIMEOUT,
                ],
            )
        )
        if bad_codes:
            return {}, False
        elif not (START_TEST_OUTPUT in content and END_TEST_OUTPUT in content):
            # Test patch did not apply (should not happen at all)
            return {}, False

        # Get status map of evaluation results
        test_content = content.split(START_TEST_OUTPUT)[1].split(END_TEST_OUTPUT)[0]
        
        # Try parsing the content between markers first
        status_map = log_parser(test_content, test_spec)
        
        # If no test results found between markers (common in Modal environment),
        # try parsing the entire log content as fallback
        if not status_map:
            # Look for pytest output patterns in the entire log content
            # This handles cases where pytest output goes to stderr and isn't captured between markers
            status_map = log_parser(content, test_spec)
        
        return status_map, True


# ORIGINAL BROKEN VERSION (for reference):
def get_logs_eval_original(test_spec: TestSpec, log_fp: str) -> tuple[dict[str, str], bool]:
    """
    ORIGINAL VERSION - BROKEN IN MODAL ENVIRONMENTS
    This version only looks for test output between markers, which fails in Modal
    """
    repo = test_spec.repo
    version = test_spec.version
    log_parser = MAP_REPO_TO_PARSER[repo]
    test_cmd = MAP_REPO_VERSION_TO_SPECS[repo][version]["test_cmd"]
    if isinstance(test_cmd, list):
        test_cmd = test_cmd[-1]

    with open(log_fp) as f:
        content = f.read()
        bad_codes = list(
            filter(
                lambda x: x in content,
                [
                    APPLY_PATCH_FAIL,
                    RESET_FAILED,
                    TESTS_ERROR,
                    TESTS_TIMEOUT,
                ],
            )
        )
        if bad_codes:
            return {}, False
        elif not (START_TEST_OUTPUT in content and END_TEST_OUTPUT in content):
            return {}, False

        # PROBLEM: Only looks between markers, misses stderr output in Modal
        content = content.split(START_TEST_OUTPUT)[1].split(END_TEST_OUTPUT)[0]
        return log_parser(content, test_spec), True
