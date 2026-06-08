# Test Report

## Summary

- Backend engine and API tests: 31 passed, 0 failed.
- React UI unit tests: 16 passed, 0 failed.
- Playwright e2e tests: 5 passed, 1 failed.

> The e2e failure occurred because Playwright could not connect to the backend at `http://localhost:8000`.

## Execution Results

- `cd AnomalyEngine && .\.venv\Scripts\python.exe -m pytest -q tests`
  - Result: `31 passed in 12.07s`
- `cd AnomalyUI && npm test -- --run`
  - Result: `16 passed (16)`
- `cd AnomalyUI && npx playwright test --config=playwright.config.ts --reporter=list`
  - Result: `5 passed, 1 failed`

## Backend Test Cases

| Test Case | Expected Output | Actual Result |
|---|---|---|
| `test_admin_can_create_user` | Admin user can create a new user | Passed |
| `test_admin_can_delete_user` | Admin user can delete another user | Passed |
| `test_admin_cannot_delete_self` | Admin cannot delete their own account | Passed |
| `test_run_scrape_job_calls_share_sansar_scrape` | Scrape job triggers external scrape service | Passed |
| `test_analyze_with_invalid_stock_symbol` | Invalid symbol returns validation error | Passed |
| `test_analyze_with_start_date_after_end_date` | Date validation rejects invalid range | Passed |
| `test_analyze_without_authentication` | Unauthorized analyze request is rejected | Passed |
| `test_analyze_successful_run_returns_expected_payload` | `/analyze` returns expected payload structure | Passed |
| `test_explain_endpoint_writes_artifact` | `/explain` persists explanation artifact | Passed |
| `test_register_request_sends_otp_and_verifies_email` | Register request sends OTP and verification succeeds | Passed |
| `test_register_request_duplicate_username_or_email_fails` | Duplicate registration is rejected | Passed |
| `test_login_with_username_or_email_after_verification` | Verified user can log in with username/email | Passed |
| `test_register_with_invalid_otp_fails` | Invalid OTP registration is rejected | Passed |
| `test_login_with_invalid_credentials_fails` | Login rejects bad credentials | Passed |
| `test_login_nonexistent_user_fails` | Login rejects non-existent accounts | Passed |
| `test_login_and_me_endpoint` | Login returns token and `/me` endpoint works | Passed |
| `test_user_can_access_protected_endpoint` | Authenticated user can access protected route | Passed |
| `test_static_pipeline_basic_run` | Static pipeline executes end-to-end | Passed |
| `test_anomaly_detector_service_predicts_labels` | Detector service returns anomaly labels | Passed |
| `test_preprocessor_empty_input` | Preprocessor handles empty input gracefully | Passed |
| `test_evaluator_compute_metrics` | Evaluator returns correct metrics | Passed |
| `test_train_model_basic_outputs` | Trainer produces expected outputs | Passed |
| `test_create_explanation_inserts_row` | Explanation CRUD inserts row into DB | Passed |
| `test_dbscan_two_clusters_and_noise` | DBSCAN model detects clusters and noise | Passed |
| `test_dbscan_all_noise` | DBSCAN model handles all-noise case | Passed |
| `test_isolation_forest_detects_outlier` | Isolation Forest flags an outlier | Passed |
| `test_isolation_forest_no_outliers` | Isolation Forest handles normal data | Passed |
| `test_password_hash_and_verify` | Password utilities hash and verify correctly | Passed |
| `test_token_create_and_decode` | Token utilities create and decode tokens | Passed |
| `test_zscore_zero_std_returns_zeros` | Z-score handles zero standard deviation | Passed |
| `test_zscore_standardizes_nontrivial_series` | Z-score standardizes non-zero variance series | Passed |

## React UI Unit Test Cases

| Test Case | Component / Flow | Actual Result |
|---|---|---|
| `renders recent analyses and allows selecting one` | `AnalysisHistory` | Passed |
| `renders and loads the admin symbol list` | `AdminDataPanel` | Passed |
| `shows the AI explanation button and calls the handler on click` | `ResultsPage` | Passed |
| `renders the user list after loading users` | `UsersPanel` | Passed |
| `creates a user when the form is submitted` | `UsersPanel` | Passed |
| `renders the dashboard and shows the user role` | `DashboardPage` | Passed |
| `renders the login page when unauthenticated and visiting /login` | `AnalysisResultsFlow` | Passed |
| `renders the login form and calls login with credentials` | `LoginPage` | Passed |
| `shows an error for a short password` | `RegisterPage` | Passed |
| `shows an error when the email is already registered` | `RegisterPage` | Passed |
| `renders the form and loads the symbol list` | `AnalysisPanel` | Passed |
| `renders the empty state when no results are available` | `ResultsPage` | Passed |
| `renders results summary and a working AI button` | `ResultsPage` | Passed |
| `renders the analysis page heading` | `AnalysisPage` | Passed |
| `renders an error when one is provided` | `AnalysisPage` | Passed |

## Playwright E2E Test Cases

| Test Case | End-to-End Workflow | Actual Result |
|---|---|---|
| `System test: Register -> Login -> Analysis -> Results -> AI explanation -> Sign out` | Full register/login/analysis/AI explanation/sign-out flow | Failed |
| `Register -> OTP verification -> Login` | Registration OTP flow | Passed |
| `Login -> Analysis -> Results` | Login and analysis navigation flow | Passed |
| `Results -> Analyze with AI -> explanation displayed` | Results page and AI explanation flow | Passed |
| `Sign out returns to login` | Sign-out returns to login page | Passed |

## Notes

- The backend and UI unit tests are green.
- The lone failing e2e case is due to `ECONNREFUSED ::1:8000` while Playwright attempted to access the backend API.
- To make the failing e2e case pass, start the FastAPI backend on `http://localhost:8000` before running `npx playwright test`.
