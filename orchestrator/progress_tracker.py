#!/usr/bin/env python3
"""
Progress Tracker - Real-time progress reporting with Universal ID granularity

This module provides comprehensive progress tracking throughout pipeline execution,
with Universal ID-level granularity for detailed progress reporting and user feedback.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from tqdm import tqdm
import threading


@dataclass
class ProgressMetrics:
    """Progress metrics for a specific tracking context"""

    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_operation: str = ""

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_items == 0:
            return 100.0
        return min(100.0, (self.completed_items / self.total_items) * 100.0)

    @property
    def elapsed_time(self) -> timedelta:
        """Calculate elapsed time"""
        end = self.end_time or datetime.now()
        return end - (self.start_time or datetime.now())

    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Estimate remaining time based on current progress"""
        if self.completed_items == 0 or self.total_items == 0:
            return None

        elapsed = self.elapsed_time.total_seconds()
        progress_rate = self.completed_items / elapsed
        remaining_items = self.total_items - self.completed_items

        if progress_rate > 0:
            remaining_seconds = remaining_items / progress_rate
            return timedelta(seconds=remaining_seconds)

        return None


@dataclass
class UniversalIDProgress:
    """Progress tracking for a specific Universal ID"""

    universal_id: str
    stages_completed: Set[str] = field(default_factory=set)
    stages_failed: Set[str] = field(default_factory=set)
    current_stage: str = ""
    files_created: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProgressTracker:
    """
    Comprehensive progress tracker for Universal ID pipeline orchestration.

    Provides real-time progress reporting with Universal ID-level granularity,
    following patterns from script_runner.py for logging callbacks and tqdm
    for progress visualization.
    """

    def __init__(
        self,
        total_universal_ids: int = 0,
        expected_stages: Optional[List[str]] = None,
        progress_callback: Optional[Callable] = None,
        log_file: Optional[Path] = None,
        verbose: bool = True,
    ):
        """
        Initialize Progress Tracker.

        Args:
            total_universal_ids: Total number of Universal IDs to track
            expected_stages: List of expected pipeline stages
            progress_callback: Callback function for progress updates
            log_file: Path to log file for progress events
            verbose: Whether to show detailed console output
        """
        self.total_universal_ids = total_universal_ids
        self.expected_stages = expected_stages or [
            "note_coordinator",
            "tied_note_processor",
            "noteheads_extraction",
            "instrument_separation",
            "midi_note_separation",
            "audio_rendering",
            "keyframe_generation",
        ]
        self.progress_callback = progress_callback
        self.verbose = verbose

        # Progress tracking data structures
        self.universal_id_progress: Dict[str, UniversalIDProgress] = {}
        self.stage_metrics: Dict[str, ProgressMetrics] = {}
        self.overall_metrics = ProgressMetrics(total_items=total_universal_ids)

        # Progress bars
        self.progress_bars: Dict[str, tqdm] = {}
        self.main_progress_bar: Optional[tqdm] = None

        # Threading for concurrent updates
        self.update_lock = threading.Lock()

        # Logging setup
        self.logger = logging.getLogger("ProgressTracker")
        if log_file:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def initialize_universal_ids(self, universal_ids: List[str]):
        """Initialize tracking for a list of Universal IDs"""
        with self.update_lock:
            for universal_id in universal_ids:
                if universal_id not in self.universal_id_progress:
                    self.universal_id_progress[universal_id] = UniversalIDProgress(
                        universal_id=universal_id
                    )

            # Update total count
            self.total_universal_ids = len(universal_ids)
            self.overall_metrics.total_items = self.total_universal_ids

            self._log(f"Initialized tracking for {len(universal_ids)} Universal IDs")

    def start_stage(self, stage_name: str, expected_universal_ids: Set[str]):
        """Start tracking a new pipeline stage"""
        with self.update_lock:
            if stage_name not in self.stage_metrics:
                self.stage_metrics[stage_name] = ProgressMetrics(
                    total_items=len(expected_universal_ids),
                    current_operation=f"Starting {stage_name}",
                )

            # Create progress bar for this stage
            if self.verbose:
                desc = f"{stage_name.replace('_', ' ').title()}"
                self.progress_bars[stage_name] = tqdm(
                    total=len(expected_universal_ids),
                    desc=desc,
                    unit="notes",
                    position=len(self.progress_bars),
                )

            self._log(
                f"Started stage: {stage_name} (expecting {len(expected_universal_ids)} Universal IDs)"
            )

    def complete_universal_id(
        self,
        universal_id: str,
        stage_name: str,
        files_created: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Mark a Universal ID as completed for a specific stage"""
        with self.update_lock:
            # Update Universal ID progress
            if universal_id not in self.universal_id_progress:
                self.universal_id_progress[universal_id] = UniversalIDProgress(
                    universal_id=universal_id
                )

            uid_progress = self.universal_id_progress[universal_id]
            uid_progress.stages_completed.add(stage_name)
            uid_progress.current_stage = ""
            uid_progress.last_updated = datetime.now()

            if files_created:
                uid_progress.files_created.extend(files_created)

            if metadata:
                uid_progress.metadata.update(metadata)

            # Update stage metrics
            if stage_name in self.stage_metrics:
                self.stage_metrics[stage_name].completed_items += 1
                self.stage_metrics[
                    stage_name
                ].current_operation = f"Completed {universal_id[:8]}"

            # Update overall metrics
            self._update_overall_metrics()

            # Update progress bar
            if stage_name in self.progress_bars:
                self.progress_bars[stage_name].update(1)
                self.progress_bars[stage_name].set_postfix(
                    {
                        "ID": universal_id[:8],
                        "Files": len(files_created) if files_created else 0,
                    }
                )

            # Trigger callback
            if self.progress_callback:
                self.progress_callback(
                    {
                        "type": "universal_id_completed",
                        "universal_id": universal_id,
                        "stage": stage_name,
                        "files_created": files_created,
                        "progress": self.get_overall_progress(),
                    }
                )

            # Individual Universal ID logging disabled - use stage completion summaries instead

    def fail_universal_id(
        self,
        universal_id: str,
        stage_name: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Mark a Universal ID as failed for a specific stage"""
        with self.update_lock:
            # Update Universal ID progress
            if universal_id not in self.universal_id_progress:
                self.universal_id_progress[universal_id] = UniversalIDProgress(
                    universal_id=universal_id
                )

            uid_progress = self.universal_id_progress[universal_id]
            uid_progress.stages_failed.add(stage_name)
            uid_progress.current_stage = ""
            uid_progress.last_updated = datetime.now()
            uid_progress.metadata["last_error"] = error_message

            if metadata:
                uid_progress.metadata.update(metadata)

            # Update stage metrics
            if stage_name in self.stage_metrics:
                self.stage_metrics[stage_name].failed_items += 1
                self.stage_metrics[
                    stage_name
                ].current_operation = f"Failed {universal_id[:8]}"

            # Update overall metrics
            self.overall_metrics.failed_items += 1

            # Update progress bar with error indicator
            if stage_name in self.progress_bars:
                self.progress_bars[stage_name].set_postfix(
                    {"ID": universal_id[:8], "Status": "FAILED"}
                )

            # Trigger callback
            if self.progress_callback:
                self.progress_callback(
                    {
                        "type": "universal_id_failed",
                        "universal_id": universal_id,
                        "stage": stage_name,
                        "error": error_message,
                        "progress": self.get_overall_progress(),
                    }
                )

            self._log(
                f"Universal ID {universal_id[:8]} failed stage {stage_name}: {error_message}"
            )

    def update_universal_id_operation(
        self, universal_id: str, stage_name: str, operation: str
    ):
        """Update the current operation for a Universal ID"""
        with self.update_lock:
            if universal_id in self.universal_id_progress:
                self.universal_id_progress[universal_id].current_stage = stage_name
                self.universal_id_progress[universal_id].last_updated = datetime.now()

            if stage_name in self.stage_metrics:
                self.stage_metrics[stage_name].current_operation = operation

            # Update progress bar description
            if stage_name in self.progress_bars:
                self.progress_bars[stage_name].set_description(
                    f"{stage_name.replace('_', ' ').title()}: {operation}"
                )

    def complete_stage(self, stage_name: str):
        """Mark a pipeline stage as completed"""
        with self.update_lock:
            if stage_name in self.stage_metrics:
                self.stage_metrics[stage_name].end_time = datetime.now()
                self.stage_metrics[stage_name].current_operation = "Completed"

                # Calculate stage performance metrics
                metrics = self.stage_metrics[stage_name]
                elapsed_seconds = metrics.elapsed_time.total_seconds()
                items_per_second = metrics.completed_items / elapsed_seconds if elapsed_seconds > 0 else 0

                # Enhanced stage completion summary
                stage_summary = (
                    f"Stage completed: {stage_name} "
                    f"({metrics.completed_items}/{metrics.total_items} Universal IDs, "
                    f"{items_per_second:.1f} notes/s, "
                    f"{elapsed_seconds:.1f}s"
                )

                if metrics.failed_items > 0:
                    stage_summary += f", {metrics.failed_items} failed"

                stage_summary += ")"

            # Close progress bar
            if stage_name in self.progress_bars:
                self.progress_bars[stage_name].close()
                del self.progress_bars[stage_name]

            # Trigger callback
            if self.progress_callback:
                self.progress_callback(
                    {
                        "type": "stage_completed",
                        "stage": stage_name,
                        "metrics": self.stage_metrics.get(stage_name),
                        "progress": self.get_overall_progress(),
                    }
                )

            # Log enhanced stage summary instead of simple completion message
            if stage_name in self.stage_metrics:
                self._log(stage_summary)
            else:
                self._log(f"Stage completed: {stage_name}")

    def _update_overall_metrics(self):
        """Update overall progress metrics"""
        completed_count = 0
        failed_count = 0

        for uid_progress in self.universal_id_progress.values():
            # Count as completed if it has finished all expected stages
            completed_stages = len(uid_progress.stages_completed)
            failed_stages = len(uid_progress.stages_failed)

            if completed_stages == len(self.expected_stages):
                completed_count += 1
            elif failed_stages > 0:
                failed_count += 1

        self.overall_metrics.completed_items = completed_count
        self.overall_metrics.failed_items = failed_count

    def get_overall_progress(self) -> Dict[str, Any]:
        """Get comprehensive progress information"""
        with self.update_lock:
            return {
                "total_universal_ids": self.total_universal_ids,
                "completed_universal_ids": self.overall_metrics.completed_items,
                "failed_universal_ids": self.overall_metrics.failed_items,
                "completion_percentage": self.overall_metrics.completion_percentage,
                "elapsed_time_seconds": self.overall_metrics.elapsed_time.total_seconds(),
                "estimated_remaining_seconds": (
                    self.overall_metrics.estimated_remaining_time.total_seconds()
                    if self.overall_metrics.estimated_remaining_time
                    else None
                ),
                "stages": {
                    stage_name: {
                        "completed": metrics.completed_items,
                        "failed": metrics.failed_items,
                        "total": metrics.total_items,
                        "percentage": metrics.completion_percentage,
                        "current_operation": metrics.current_operation,
                    }
                    for stage_name, metrics in self.stage_metrics.items()
                },
                "active_universal_ids": [
                    {
                        "universal_id": uid_progress.universal_id[:8],
                        "current_stage": uid_progress.current_stage,
                        "completed_stages": len(uid_progress.stages_completed),
                        "total_stages": len(self.expected_stages),
                    }
                    for uid_progress in self.universal_id_progress.values()
                    if uid_progress.current_stage
                ],
            }

    def get_universal_id_details(self, universal_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress information for a specific Universal ID"""
        with self.update_lock:
            if universal_id not in self.universal_id_progress:
                return None

            uid_progress = self.universal_id_progress[universal_id]
            return {
                "universal_id": universal_id,
                "stages_completed": list(uid_progress.stages_completed),
                "stages_failed": list(uid_progress.stages_failed),
                "current_stage": uid_progress.current_stage,
                "files_created": uid_progress.files_created,
                "completion_percentage": (
                    len(uid_progress.stages_completed) / len(self.expected_stages) * 100
                    if self.expected_stages
                    else 0
                ),
                "elapsed_time_seconds": (
                    datetime.now() - uid_progress.start_time
                ).total_seconds(),
                "last_updated": uid_progress.last_updated.isoformat(),
                "metadata": uid_progress.metadata,
            }

    def save_progress_report(self, output_path: Path):
        """Save comprehensive progress report to JSON file"""
        with self.update_lock:
            report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_universal_ids": self.total_universal_ids,
                    "expected_stages": self.expected_stages,
                },
                "overall_progress": self.get_overall_progress(),
                "universal_id_details": {
                    uid: self.get_universal_id_details(uid)
                    for uid in self.universal_id_progress.keys()
                },
                "stage_metrics": {
                    stage_name: {
                        "total_items": metrics.total_items,
                        "completed_items": metrics.completed_items,
                        "failed_items": metrics.failed_items,
                        "completion_percentage": metrics.completion_percentage,
                        "elapsed_time_seconds": metrics.elapsed_time.total_seconds(),
                        "current_operation": metrics.current_operation,
                    }
                    for stage_name, metrics in self.stage_metrics.items()
                },
            }

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

            self._log(f"Progress report saved to: {output_path}")

    def create_main_progress_bar(self, description: str = "Overall Pipeline Progress"):
        """Create main progress bar for overall pipeline progress"""
        if self.verbose:
            self.main_progress_bar = tqdm(
                total=self.total_universal_ids,
                desc=description,
                unit="notes",
                position=0,
            )

    def update_main_progress_bar(self):
        """Update main progress bar with current completion count"""
        if self.main_progress_bar:
            completed = self.overall_metrics.completed_items
            self.main_progress_bar.n = completed
            self.main_progress_bar.set_postfix(
                {
                    "Completed": completed,
                    "Failed": self.overall_metrics.failed_items,
                    "Remaining": self.total_universal_ids
                    - completed
                    - self.overall_metrics.failed_items,
                }
            )
            self.main_progress_bar.refresh()

    def close_all_progress_bars(self):
        """Close all progress bars"""
        for progress_bar in self.progress_bars.values():
            progress_bar.close()

        if self.main_progress_bar:
            self.main_progress_bar.close()

        self.progress_bars.clear()
        self.main_progress_bar = None

    def _log(self, message: str):
        """Log message to console and file"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 📊 {message}")

        if hasattr(self, "logger"):
            self.logger.info(message)

    def __enter__(self):
        """Context manager entry"""
        self.create_main_progress_bar()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_all_progress_bars()


# Factory function for creating progress trackers
def create_progress_tracker(
    total_universal_ids: int,
    expected_stages: List[str],
    progress_callback: Optional[Callable] = None,
    log_file: Optional[Path] = None,
    verbose: bool = True,
) -> ProgressTracker:
    """Create a configured ProgressTracker instance"""
    return ProgressTracker(
        total_universal_ids=total_universal_ids,
        expected_stages=expected_stages,
        progress_callback=progress_callback,
        log_file=log_file,
        verbose=verbose,
    )
