# Sib2Ae Orchestrator Patterns and Integration Guide

## File Naming and Universal ID Patterns

### Current Sib2Ae File Naming Conventions

Based on codebase analysis, all pipeline scripts follow these patterns:

**MIDI Pipeline:**
```
note_{seq:03d}_{instrument}_{pitch}_vel{velocity}.mid
note_{seq:03d}_{instrument}_{pitch}_vel{velocity}.wav
note_{seq:03d}_{instrument}_{pitch}_vel{velocity}_keyframes.json
```

**SVG Pipeline:**
```
notehead_{uuid_first8}_{part_id}_{pitch}_M{measure}.svg
{instrument}_{part_id}.svg
```

**New Orchestrator Pattern (User Requested):**
```
{instrument}_{pitch}_vel{velocity}_{uuid_first4}.wav
{instrument}_{pitch}_vel{velocity}_{uuid_first4}_keyframes.json
```

### Universal Constants (From Codebase)

All coordinate transformations use these constants:
```python
X_SCALE = 3.206518      # Universal X scaling factor
X_OFFSET = 564.93       # Universal X offset
STAFF_BASE_Y_START = 1037  # First staff base Y
STAFF_SEPARATION = 380  # Y separation between staves
```

## Manifest Update Patterns

### Living Document Approach

Manifests start as predictions and get enhanced through pipeline stages:

**Stage 1 - Note Coordinator Output:**
```json
{
  "universal_id": "2584802d-2469-4e45-8cf0-ff934e1032d7",
  "audio_filename": "note_000_Flûte_A4_vel76.wav",  // Predicted
  "actual_filename": null,                           // To be filled
  "created_at": null,                               // To be filled
  "file_exists": false                              // To be updated
}
```

**Stage 2 - After Audio Pipeline:**
```json
{
  "universal_id": "2584802d-2469-4e45-8cf0-ff934e1032d7",
  "audio_filename": "note_000_Flûte_A4_vel76.wav",  // Original prediction
  "actual_filename": "Flûte_A4_vel76_2584.wav",     // Actual generated
  "created_at": "2025-01-15T10:30:45Z",            // Timestamp
  "file_exists": true,                              // Verified
  "file_size": 245760                               // Additional metadata
}
```

### Tied Note Enhanced Manifests

When tied notes are detected, create enhanced manifests:

```json
{
  "universal_id": "2584802d-2469-4e45-8cf0-ff934e1032d7",
  "is_primary": true,
  "tied_group_id": "tied_group_1",
  "calculated_start_time": 7.5,
  "timing_confidence": 1.0,
  "position_in_group": 0,
  "timing_source": "midi_exact"
}
```

## Orchestration Integration Patterns

### Dependency Management (From SynchronizationCoordinator)

```python
@dataclass
class PipelineStage:
    name: str                    # Stage identifier
    command: List[str]           # Command to execute
    input_files: List[Path]      # Required input files
    output_files: List[Path]     # Expected output files
    depends_on: List[str]        # Dependencies (stage names)
    status: str                  # "pending", "running", "completed", "failed"
```

### Progress Tracking Pattern

```python
def track_universal_id_progress(self, universal_id: str, stage: str, status: str):
    """Track Universal ID through pipeline stages"""
    if universal_id not in self.progress_registry:
        self.progress_registry[universal_id] = {}

    self.progress_registry[universal_id][stage] = {
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'files_created': []
    }
```

### Error Handling Pattern (Circuit Breaker)

```python
class ProcessCircuitBreaker:
    def execute_with_breaker(self, process_func, *args):
        try:
            if self.state == CircuitState.OPEN:
                raise Exception("Circuit breaker OPEN - too many failures")

            result = process_func(*args)
            self.reset_failure_count()
            return result

        except Exception as e:
            self.record_failure()
            self.log_error(f"Process failed: {e}")
            raise
```

## File Chain Preservation

### Atomic Manifest Updates

```python
from atomicwrites import atomic_write

def update_manifest_atomically(self, manifest_path: str, updates: dict):
    """Atomic manifest updates to prevent corruption during failures"""

    # Load current manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # Apply updates
    manifest.update(updates)

    # Atomic write
    with atomic_write(manifest_path, overwrite=True) as f:
        json.dump(manifest, f, indent=2)
```

### Universal ID File Registry

```python
class UniversalFileRegistry:
    def register_file_creation(self, universal_id: str, file_type: str, file_path: str):
        """Register file creation for Universal ID tracking"""

        if universal_id not in self.registry:
            self.registry[universal_id] = {'files': {}, 'created_at': time.time()}

        self.registry[universal_id]['files'][file_type] = {
            'path': file_path,
            'created_at': time.time(),
            'exists': os.path.exists(file_path),
            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }

        self.save_registry_atomically()
```

## Critical Integration Points

### 1. Note Coordinator Integration
- **Input**: MusicXML + MIDI files
- **Output**: Universal ID manifests with predictions
- **Integration**: Read manifests for Universal ID-to-file mapping

### 2. Tied Note Processor Integration
- **Input**: MusicXML + Note Coordinator outputs
- **Output**: Enhanced manifests with tied note timing
- **Integration**: Always run (detects tied notes automatically)

### 3. Pipeline Script Integration
- **Symbolic Scripts**: Read manifests, create files, update manifests
- **Audio Scripts**: Follow filename patterns, preserve Universal ID chains
- **Integration**: Wrapper approach with manifest updates

### 4. Error Recovery Patterns
- **Partial Failures**: Skip failed Universal IDs, continue with others
- **Manifest Corruption**: Atomic writes prevent partial updates
- **Process Failures**: Circuit breaker prevents cascade failures
- **File Verification**: Validate file creation before marking complete

## Performance Patterns

### Parallel Processing Strategy
- **CPU-bound tasks**: multiprocessing (audio rendering)
- **I/O-bound tasks**: asyncio (file operations, manifest updates)
- **Mixed workloads**: Hybrid with ProcessPoolExecutor + asyncio

### Resource Management
```python
class ResourceManager:
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)

    async def run_parallel_with_universal_id_tracking(self, tasks_with_ids):
        """Run parallel tasks while maintaining Universal ID tracking"""
        futures = []
        for universal_id, task in tasks_with_ids:
            future = self.loop.run_in_executor(
                self.process_pool,
                self.track_universal_id_task,
                universal_id,
                task
            )
            futures.append(future)

        return await asyncio.gather(*futures, return_exceptions=True)
```