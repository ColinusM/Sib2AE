---
name: "Smart Verbose Shell Output Enhancement"
description: "Replace repetitive orchestrator output with intelligent aggregation and anomaly detection"
---

# Smart Verbose Shell Output Enhancement PRP

## Original Story

```
Enhance orchestrator shell output with smart verbose logging that aggregates data intelligently instead of repetitive line-by-line output. Current: 35 lines for 9 notes with repetitive patterns. Goal: Dense, intelligent summaries with anomaly detection, rich context, and smart aggregation while maintaining zero console pollution with --quiet flag.
```

## Story Metadata

- **Story Type**: Enhancement
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: Universal Orchestrator logging, Progress tracking, Shell output capture

## Context References

- `Brain/orchestrator/universal_orchestrator.py` - Main logging implementation with _log() and _print_and_log() methods
- `Brain/orchestrator/progress_tracker.py` - Existing performance metrics and stage completion tracking
- `universal_output/shell_output/execution_output.log` - Current repetitive output format (35 lines for 9 notes)
- `universal_output/universal_notes_registry.json` - Rich data structures for aggregation (Universal ID records, match confidence, coordinates)
- `universal_output/coordination_metadata.json` - Existing statistical aggregation patterns to extend
- `Brain/orchestrator/pipeline_stage.py` - Shell output folder creation and directory structure

## Implementation Tasks

### CREATE Brain/orchestrator/smart_log_aggregator.py:

- **IMPLEMENT**: SmartLogAggregator class with pattern recognition and statistical analysis
- **PATTERN**: Follow Brain/orchestrator/progress_tracker.py structure for metrics collection
- **IMPORTS**: `from collections import defaultdict, Counter; import statistics; import re; from pathlib import Path`
- **COMPONENTS**:
  - OutputPatternAnalyzer for repetitive message detection
  - PerformanceAnomalyDetector for bottleneck identification
  - IntelligentOutputSummarizer for dense summary generation
- **DATA_STRUCTURES**: Universal ID analytics, stage performance trends, file creation statistics
- **GOTCHA**: Must preserve all original data while creating summaries (don't lose information)
- **VALIDATE**: `python -c "from Brain.orchestrator.smart_log_aggregator import SmartLogAggregator; print('✓ Import successful')"`

### UPDATE Brain/orchestrator/universal_orchestrator.py:

- **ENHANCE**: `_print_and_log()` method (lines 682-693) to route through smart aggregator
- **ADD**: Smart aggregator initialization in `__init__` method after `self.output_file` assignment
- **INTEGRATION**:
  - Initialize aggregator: `self.smart_aggregator = SmartLogAggregator(self.output_file)`
  - Route messages: `self.smart_aggregator.process_message(message)`
  - Generate summaries at stage completion points
- **PRESERVE**: Existing quiet/verbose console behavior - aggregator only affects file output
- **GOTCHA**: Don't break nuclear termination logic (lines 291-297) - ensure summaries complete before exit
- **VALIDATE**: `python -m Brain.orchestrator.universal_orchestrator --help | grep -q quiet && echo "✓ CLI preserved"`

### ADD Statistical Analysis Components to smart_log_aggregator.py:

- **IMPLEMENT**:
  - `analyze_velocity_patterns()` - velocity distribution analysis from MIDI data
  - `analyze_match_patterns()` - match confidence statistics by method type
  - `analyze_coordinate_ranges()` - SVG coordinate spatial distribution
  - `detect_performance_anomalies()` - stage execution time outlier detection
- **PATTERN**: Follow existing statistical patterns in coordination_metadata.json structure
- **ALGORITHMS**:
  - Z-score analysis for execution time anomalies (threshold: abs(z) > 2.0)
  - Quartile analysis for velocity distributions
  - Trend detection for processing rates across stages
- **DATA_SOURCES**: Universal notes registry, stage completion metrics, subprocess output
- **VALIDATE**: `python -c "from Brain.orchestrator.smart_log_aggregator import SmartLogAggregator; agg = SmartLogAggregator('/tmp/test.log'); print('✓ Statistical components loaded')"`

### CREATE Intelligent Summary Generation in smart_log_aggregator.py:

- **IMPLEMENT**:
  - `generate_execution_digest()` - headline performance summary with key insights
  - `create_stage_performance_summary()` - replace repetitive stage completion messages
  - `generate_anomaly_alerts()` - highlight performance outliers and bottlenecks
  - `format_file_creation_summary()` - aggregate file generation statistics
- **AGGREGATION_RULES**:
  - Stage completions: aggregate after 5+ similar messages into performance digest
  - File creation: summarize by type (wav/svg/json) with counts and sizes
  - Progress updates: batch Universal ID operations into summary statements
- **OUTPUT_FORMAT**: Dense summaries with emojis for visual hierarchy, statistical insights, actionable recommendations
- **EXAMPLE_TRANSFORMATION**:
  - Before: 8 lines of "Stage completed: X (9/9 Universal IDs, Y notes/s, Z.Zs)"
  - After: "🎯 PIPELINE DIGEST: 8 stages completed, bottleneck: audio_to_keyframes (1.9 notes/s), avg: 185.3 notes/s"
- **VALIDATE**: `python -c "from Brain.orchestrator.smart_log_aggregator import SmartLogAggregator; agg = SmartLogAggregator('/tmp/test.log'); summary = agg.generate_execution_digest({}); print('✓ Summary generation works')"`

### UPDATE Brain/orchestrator/universal_orchestrator.py integration points:

- **ENHANCE**: `_execute_single_stage()` method to trigger smart summaries at completion
- **ADD**: Summary generation calls:
  - After stage completion: `self.smart_aggregator.complete_stage(stage.name, metrics)`
  - At pipeline end: `self.smart_aggregator.generate_final_summary()`
- **SUBPROCESS_OUTPUT**: Enhance lines 400-405 to capture full stdout for analysis (not just last 3 lines)
- **TIMING_INTEGRATION**: Pass stage execution metrics to aggregator for trend analysis
- **PRESERVE**: All existing nuclear termination logic while ensuring summaries are written before exit
- **VALIDATE**: `cd "/Users/colinmignot/Claude Code/Sib2Ae" && python -m Brain.orchestrator.universal_orchestrator "Brain/Base/SS 9.musicxml" "Brain/Base/Saint-Saens Trio No 2.mid" --quiet && wc -l universal_output/shell_output/execution_output.log`

### ADD Progress Tracking Integration:

- **ENHANCE**: `Brain/orchestrator/progress_tracker.py` to feed metrics to smart aggregator
- **INTEGRATION**: Leverage existing `get_overall_progress()` method for summary data
- **DATA_FLOW**: Pass stage completion rates, Universal ID processing stats, performance metrics
- **EXTEND**: Existing stage summary format to include anomaly detection insights
- **PATTERN**: Follow existing progress callback pattern in OrchestrationConfig
- **VALIDATE**: `python -c "from Brain.orchestrator.progress_tracker import ProgressTracker; print('✓ Progress integration ready')"`

### CREATE Validation and Testing:

- **TEST_SCENARIOS**:
  - Quiet mode behavior: Verify zero console pollution with enhanced file output
  - Verbose mode preservation: Ensure existing behavior unchanged
  - Smart aggregation quality: Validate summary accuracy vs raw data
  - Performance impact: Ensure no significant overhead added
- **REGRESSION_TESTS**:
  - Console output matching: `--quiet` produces no output
  - File output enhancement: line count reduction with information density increase
  - Pipeline functionality: All existing features work unchanged
- **VALIDATE**:
  ```bash
  # Test quiet mode (should produce no console output)
  cd "/Users/colinmignot/Claude Code/Sib2Ae" && python -m Brain.orchestrator.universal_orchestrator "Brain/Base/SS 9.musicxml" "Brain/Base/Saint-Saens Trio No 2.mid" --quiet 2>&1 | wc -l | grep -q "^0$" && echo "✓ Quiet mode preserved"

  # Test enhanced file output
  cd "/Users/colinmignot/Claude Code/Sib2Ae" && [ -f universal_output/shell_output/execution_output.log ] && echo "✓ Enhanced file output generated"

  # Test smart aggregation
  cd "/Users/colinmignot/Claude Code/Sib2Ae" && grep -q "PIPELINE DIGEST" universal_output/shell_output/execution_output.log && echo "✓ Smart aggregation working"
  ```

## Completion Checklist

- [ ] SmartLogAggregator class created with pattern recognition
- [ ] Universal orchestrator integration completed
- [ ] Statistical analysis components implemented
- [ ] Intelligent summary generation working
- [ ] Progress tracking integration added
- [ ] Quiet mode behavior preserved (zero console pollution)
- [ ] Enhanced file output with smart aggregation
- [ ] All validation commands pass
- [ ] Backward compatibility maintained
- [ ] Performance impact minimal

## Success Criteria

**Implementation Ready**: Complete context for autonomous execution without additional research
**Pattern Consistent**: Follows existing codebase conventions and logging architecture
**Validation Complete**: All tasks have executable validation commands that verify functionality
**Console Behavior Preserved**: Zero impact on --quiet flag behavior, maintains clean Claude Code sessions
**Intelligence Added**: Replaces repetitive output with actionable insights and anomaly detection