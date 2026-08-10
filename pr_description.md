🎯 **What:**
Reduced cyclomatic complexity of `ScheduledJobExecutor.dispatch()` by replacing a deep `if-elif` chain with a dictionary-based dispatch mapping. Extracted specific dispatch logic into corresponding helper methods.

💡 **Why:**
The original implementation had an increasing cyclomatic complexity as more `ScheduledJobType`s were added to the system. Converting this to a dictionary map and splitting handlers into individual helper functions vastly improves maintainability and readability by keeping the core `dispatch()` method concise, making it trivial to add new job handlers without growing the `if-elif` block.

✅ **Verification:**
Verified correctness by running `test_scheduler_executor.py` logic which validates that execution matches previous behavior. Checked all `ScheduledJobType` endpoints properly route by mocking their implementations in a standalone test.

✨ **Result:**
`dispatch` is simpler, more readable, and scalable to support further job types without scaling structural complexity.
