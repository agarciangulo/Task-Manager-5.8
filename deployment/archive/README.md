# Archived Deployment Files

This directory contains deprecated or unused deployment scripts and files.

## Files Archived

### `deploy-gmail-processor-safe.sh` and `gmail_processor_cloud_run_safe.py`
**Archived:** November 2024

**Reason:** Attempted to create a cost-controlled variant of the Gmail processor with automated budget alerts and execution time limits. The Cloud Run service (`gmail-processor-safe`) never successfully started (container health check failures), and the functionality is redundant with:
- Budget alerts now configured directly in Google Cloud Console
- Cost monitoring via Cloud Monitoring
- Resource limits already enforced in the main deployment

**Status:** Not actively used. Safe to delete if needed for space.

**Note:** The budget alert creation commands in this script were fixed and the budget is now active. The safe service itself was never successfully deployed.


