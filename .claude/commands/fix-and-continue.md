Something broke or I got an error. Help me fix it and continue.

1. First, check the current state:
   - Run `python -m src.cli health` to see what's working
   - Check `docker ps` for running services
   - Check logs/ directory for recent errors
   - Run `python -m src.cli stats` to see data state

2. Read any error messages I've shared and diagnose the root cause.

3. Fix the issue:
   - If it's a missing dependency: install it
   - If it's a code bug: fix the code
   - If it's a service not running: start it
   - If it's a configuration issue: update .env or configs/
   - If it's a data issue: re-run the relevant collection/processing step

4. Verify the fix works.

5. Tell me what was wrong, what you fixed, and what to do next.

Be specific about what commands to run. Don't just describe the fix - actually implement it.
