# Simple Shell Output Capture Plan

## Goal
Capture the basic 250-line shell output from the orchestrator pipeline into a simple file in a new folder inside `universal_output`.

## Simple Implementation

### 1. Create New Folder
- Add `shell_output/` folder inside `universal_output/`
- Just one file: `execution_output.log`

### 2. Minimal Changes Required

**File 1: `Brain/orchestrator/pipeline_stage.py`**
```python
# In create_output_directory() method, add:
(self.output_dir / "shell_output").mkdir(exist_ok=True)
```

**File 2: `Brain/orchestrator/universal_orchestrator.py`**
```python
# In __init__, add:
self.output_file = self.config.output_dir / "shell_output" / "execution_output.log"

# Modify _log() method to write to file:
def _log(self, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    self.execution_log.append(log_entry)

    # Write to shell output file
    with open(self.output_file, 'a') as f:
        f.write(log_entry + "\n")

    if self.config.verbose:
        print(log_entry)
```

### 3. Result
- Run pipeline normally: `python -m Brain.orchestrator.universal_orchestrator ...`
- All 250 lines of output saved to: `universal_output/shell_output/execution_output.log`
- No CLI flags needed, works automatically

## File Structure
```
universal_output/
├── logs/
│   └── progress.log
└── shell_output/  (NEW)
    └── execution_output.log  (250 lines of basic shell output)
```

That's it. Simple and effective.