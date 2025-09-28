#!/usr/bin/env python3
"""
Smart Log Aggregator - Intelligent shell output aggregation with anomaly detection

This module replaces repetitive orchestrator output with intelligent summaries,
statistical analysis, and anomaly detection while preserving all original data.
"""

from collections import defaultdict, Counter
import statistics
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime
import threading


class OutputPatternAnalyzer:
    """Analyzes output patterns to detect repetitive messages for aggregation"""

    def __init__(self):
        self.pattern_counts = Counter()
        self.message_templates = {}
        self.repetitive_threshold = 3  # Messages appearing 3+ times are considered repetitive

    def analyze_message(self, message: str) -> Tuple[str, bool]:
        """
        Analyze a message to determine if it's repetitive.

        Returns:
            Tuple of (pattern_key, is_repetitive)
        """
        # Extract patterns for common orchestrator messages
        patterns = [
            (r'Stage completed: (\w+) \((\d+)/(\d+) Universal IDs, ([\d.]+) notes/s, ([\d.]+)s.*\)', 'stage_completion'),
            (r'\[[\d:]+\] ✅ (.+) completed', 'phase_completion'),
            (r'🎯 SUCCESS! (.+)', 'success_message'),
            (r'note_\d+_(\w+)_([A-G][#b]?\d+)_vel\d+\.(wav|json)', 'file_creation'),
            (r'(.+) → SVG\((\d+),(\d+)\)', 'coordinate_mapping'),
        ]

        for pattern, pattern_type in patterns:
            match = re.search(pattern, message)
            if match:
                pattern_key = f"{pattern_type}_{hash(pattern) % 1000}"
                self.pattern_counts[pattern_key] += 1
                self.message_templates[pattern_key] = {
                    'template': pattern,
                    'type': pattern_type,
                    'sample_message': message
                }
                return pattern_key, self.pattern_counts[pattern_key] >= self.repetitive_threshold

        # Default pattern for unmatched messages
        return "misc", False


class PerformanceAnomalyDetector:
    """Detects performance bottlenecks and execution time outliers"""

    def __init__(self):
        self.stage_times = defaultdict(list)
        self.stage_rates = defaultdict(list)
        self.anomaly_threshold = 2.0  # Z-score threshold for anomalies

    def record_stage_performance(self, stage_name: str, duration: float, items_processed: int):
        """Record performance metrics for a stage"""
        self.stage_times[stage_name].append(duration)
        if duration > 0:
            rate = items_processed / duration
            self.stage_rates[stage_name].append(rate)

    def detect_performance_anomalies(self) -> List[Dict[str, Any]]:
        """Detect performance anomalies using Z-score analysis"""
        anomalies = []

        for stage_name, times in self.stage_times.items():
            if len(times) < 2:
                continue

            mean_time = statistics.mean(times)
            if len(times) > 1:
                stdev_time = statistics.stdev(times)

                for i, time_val in enumerate(times):
                    if stdev_time > 0:
                        z_score = abs((time_val - mean_time) / stdev_time)
                        if z_score > self.anomaly_threshold:
                            anomalies.append({
                                'type': 'execution_time_outlier',
                                'stage': stage_name,
                                'value': time_val,
                                'mean': mean_time,
                                'z_score': z_score,
                                'severity': 'high' if z_score > 3.0 else 'medium'
                            })

        # Detect bottlenecks (stages with consistently low rates)
        for stage_name, rates in self.stage_rates.items():
            if len(rates) >= 2:
                mean_rate = statistics.mean(rates)
                overall_mean = statistics.mean([rate for rate_list in self.stage_rates.values() for rate in rate_list])

                if mean_rate < overall_mean * 0.5:  # 50% below average
                    anomalies.append({
                        'type': 'bottleneck',
                        'stage': stage_name,
                        'rate': mean_rate,
                        'overall_mean': overall_mean,
                        'severity': 'high' if mean_rate < overall_mean * 0.25 else 'medium'
                    })

        return anomalies


class IntelligentOutputSummarizer:
    """Generates dense, intelligent summaries with emojis and statistical insights"""

    def __init__(self):
        self.aggregated_data = defaultdict(dict)
        self.file_creation_stats = defaultdict(lambda: {'count': 0, 'total_size': 0})

    def aggregate_stage_completions(self, completions: List[Dict[str, Any]]) -> str:
        """Aggregate multiple stage completion messages into a digest"""
        if not completions:
            return ""

        total_stages = len(completions)
        total_ids = sum(c.get('universal_ids', 0) for c in completions)
        rates = [c.get('rate', 0) for c in completions if c.get('rate', 0) > 0]

        if rates:
            avg_rate = statistics.mean(rates)
            min_rate = min(rates)
            bottleneck_stage = min(completions, key=lambda x: x.get('rate', float('inf')))['stage']

            return (
                f"🎯 PIPELINE DIGEST: {total_stages} stages completed, "
                f"bottleneck: {bottleneck_stage} ({min_rate:.1f} notes/s), "
                f"avg: {avg_rate:.1f} notes/s, {total_ids} Universal IDs processed"
            )
        else:
            return f"🎯 PIPELINE DIGEST: {total_stages} stages completed, {total_ids} Universal IDs processed"

    def aggregate_file_creation(self, file_messages: List[str]) -> str:
        """Aggregate file creation messages by type"""
        file_types = defaultdict(int)
        total_size = 0

        for message in file_messages:
            if '.wav' in message:
                file_types['audio'] += 1
            elif '.svg' in message:
                file_types['svg'] += 1
            elif '.json' in message:
                file_types['json'] += 1

            # Extract file size if present
            size_match = re.search(r'\(([0-9,]+) bytes\)', message)
            if size_match:
                size_str = size_match.group(1).replace(',', '')
                total_size += int(size_str)

        summary_parts = []
        for file_type, count in file_types.items():
            emoji = {'audio': '🎵', 'svg': '🎨', 'json': '📊'}.get(file_type, '📄')
            summary_parts.append(f"{emoji} {count} {file_type}")

        size_mb = total_size / (1024 * 1024) if total_size > 0 else 0

        return f"📁 FILES GENERATED: {', '.join(summary_parts)}" + (
            f" ({size_mb:.1f} MB total)" if size_mb > 0 else ""
        )

    def format_performance_summary(self, stage_metrics: Dict[str, Any]) -> str:
        """Format stage performance with insights and recommendations"""
        if not stage_metrics:
            return ""

        fastest_stage = min(stage_metrics.items(), key=lambda x: x[1].get('duration', float('inf')))
        slowest_stage = max(stage_metrics.items(), key=lambda x: x[1].get('duration', 0))

        total_time = sum(metrics.get('duration', 0) for metrics in stage_metrics.values())

        return (
            f"⚡ PERFORMANCE: {total_time:.1f}s total, "
            f"fastest: {fastest_stage[0]} ({fastest_stage[1].get('duration', 0):.1f}s), "
            f"slowest: {slowest_stage[0]} ({slowest_stage[1].get('duration', 0):.1f}s)"
        )


class SmartLogAggregator:
    """
    Smart log aggregator with pattern recognition and statistical analysis.

    Follows Brain/orchestrator/progress_tracker.py structure for metrics collection
    and provides intelligent aggregation of repetitive orchestrator output.
    """

    def __init__(self, output_file: Path):
        """
        Initialize SmartLogAggregator.

        Args:
            output_file: Path to the shell output file for writing aggregated logs
        """
        self.output_file = Path(output_file)
        self.raw_messages = []
        self.aggregated_messages = []

        # Core components
        self.pattern_analyzer = OutputPatternAnalyzer()
        self.anomaly_detector = PerformanceAnomalyDetector()
        self.summarizer = IntelligentOutputSummarizer()

        # Data structures for Universal ID analytics
        self.universal_id_stats = {}
        self.stage_performance_trends = defaultdict(list)
        self.file_creation_statistics = defaultdict(lambda: {'count': 0, 'sizes': []})

        # Message buffering for aggregation
        self.message_buffer = defaultdict(list)
        self.stage_completion_buffer = []
        self.file_creation_buffer = []

        # Threading for safe concurrent access
        self.update_lock = threading.Lock()

    def process_message(self, message: str):
        """
        Process a message through the smart aggregator.

        Args:
            message: Raw log message to process
        """
        with self.update_lock:
            self.raw_messages.append({
                'timestamp': datetime.now(),
                'message': message
            })

            # Analyze message pattern
            pattern_key, is_repetitive = self.pattern_analyzer.analyze_message(message)

            # ALWAYS write to file first, then do smart aggregation
            self._write_to_file(message)

            if is_repetitive:
                self.message_buffer[pattern_key].append(message)

                # Buffer specific message types for intelligent aggregation
                if 'stage_completion' in pattern_key:
                    self._buffer_stage_completion(message)
                elif 'file_creation' in pattern_key:
                    self.file_creation_buffer.append(message)

    def _buffer_stage_completion(self, message: str):
        """Buffer stage completion messages for aggregation"""
        # Extract stage completion data
        match = re.search(r'Stage completed: (\w+) \((\d+)/(\d+) Universal IDs, ([\d.]+) notes/s, ([\d.]+)s', message)
        if match:
            stage_name, completed, total, rate, duration = match.groups()
            self.stage_completion_buffer.append({
                'stage': stage_name,
                'universal_ids': int(completed),
                'total_ids': int(total),
                'rate': float(rate),
                'duration': float(duration)
            })

            # Record performance for anomaly detection
            self.anomaly_detector.record_stage_performance(stage_name, float(duration), int(completed))

    def complete_stage(self, stage_name: str, metrics: Dict[str, Any]):
        """
        Called when a stage completes to trigger smart summaries.

        Args:
            stage_name: Name of the completed stage
            metrics: Stage execution metrics
        """
        with self.update_lock:
            # Generate aggregated summaries if we have buffered data
            if len(self.stage_completion_buffer) >= 3:
                summary = self.summarizer.aggregate_stage_completions(self.stage_completion_buffer)
                self._write_to_file(summary)
                self.stage_completion_buffer.clear()

            if len(self.file_creation_buffer) >= 5:
                summary = self.summarizer.aggregate_file_creation(self.file_creation_buffer)
                self._write_to_file(summary)
                self.file_creation_buffer.clear()

    def generate_final_summary(self):
        """Generate final execution summary with all analytics"""
        with self.update_lock:
            # Flush any remaining buffered messages
            if self.stage_completion_buffer:
                summary = self.summarizer.aggregate_stage_completions(self.stage_completion_buffer)
                self._write_to_file(summary)

            if self.file_creation_buffer:
                summary = self.summarizer.aggregate_file_creation(self.file_creation_buffer)
                self._write_to_file(summary)

            # Generate anomaly alerts
            anomalies = self.anomaly_detector.detect_performance_anomalies()
            if anomalies:
                self._write_to_file(self._format_anomaly_alerts(anomalies))

            # Generate execution digest
            digest = self.generate_execution_digest({})
            if digest:
                self._write_to_file(digest)

    def generate_execution_digest(self, context_data: Dict[str, Any]) -> str:
        """Generate headline performance summary with key insights"""
        total_messages = len(self.raw_messages)
        unique_patterns = len(self.pattern_analyzer.pattern_counts)

        if total_messages == 0:
            return ""

        aggregation_ratio = (total_messages - len(self.aggregated_messages)) / total_messages * 100

        return (
            f"📊 EXECUTION SUMMARY: {total_messages} messages processed, "
            f"{unique_patterns} patterns identified, "
            f"{aggregation_ratio:.1f}% aggregation efficiency"
        )

    def _format_anomaly_alerts(self, anomalies: List[Dict[str, Any]]) -> str:
        """Format anomaly detection results"""
        if not anomalies:
            return ""

        alerts = []
        for anomaly in anomalies:
            if anomaly['type'] == 'bottleneck':
                alerts.append(f"🐌 BOTTLENECK: {anomaly['stage']} ({anomaly['rate']:.1f} notes/s)")
            elif anomaly['type'] == 'execution_time_outlier':
                alerts.append(f"⚠️ OUTLIER: {anomaly['stage']} ({anomaly['value']:.1f}s, z={anomaly['z_score']:.1f})")

        return "🔍 ANOMALY DETECTION: " + ", ".join(alerts) if alerts else ""

    def _write_to_file(self, message: str):
        """Write message to output file"""
        try:
            with open(self.output_file, 'a') as f:
                f.write(message + "\n")
            self.aggregated_messages.append(message)
        except Exception:
            # Don't let file writing break the pipeline
            pass

    # Statistical analysis methods following coordination_metadata.json patterns

    def analyze_velocity_patterns(self, universal_notes_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze velocity distribution from MIDI data"""
        velocities = []
        for note in universal_notes_data:
            if 'midi_data' in note and 'velocity' in note['midi_data']:
                velocities.append(note['midi_data']['velocity'])

        if not velocities:
            return {}

        return {
            'mean_velocity': statistics.mean(velocities),
            'median_velocity': statistics.median(velocities),
            'velocity_range': {'min': min(velocities), 'max': max(velocities)},
            'velocity_quartiles': {
                'q1': statistics.quantiles(velocities, n=4)[0] if len(velocities) >= 4 else None,
                'q3': statistics.quantiles(velocities, n=4)[2] if len(velocities) >= 4 else None
            }
        }

    def analyze_match_patterns(self, universal_notes_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze match confidence statistics by method type"""
        match_methods = Counter()
        confidence_by_method = defaultdict(list)

        for note in universal_notes_data:
            method = note.get('match_method', 'unknown')
            confidence = note.get('match_confidence', 0)

            match_methods[method] += 1
            confidence_by_method[method].append(confidence)

        method_stats = {}
        for method, confidences in confidence_by_method.items():
            method_stats[method] = {
                'count': len(confidences),
                'avg_confidence': statistics.mean(confidences),
                'min_confidence': min(confidences),
                'max_confidence': max(confidences)
            }

        return {
            'method_distribution': dict(match_methods),
            'method_statistics': method_stats,
            'overall_avg_confidence': statistics.mean([
                conf for confs in confidence_by_method.values() for conf in confs
            ]) if confidence_by_method else 0
        }

    def analyze_coordinate_ranges(self, universal_notes_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze SVG coordinate spatial distribution"""
        x_coords = []
        y_coords = []
        staff_distribution = Counter()

        for note in universal_notes_data:
            if 'svg_data' in note:
                svg_data = note['svg_data']
                if 'svg_x' in svg_data and 'svg_y' in svg_data:
                    x_coords.append(svg_data['svg_x'])
                    y_coords.append(svg_data['svg_y'])
                    staff_distribution[svg_data.get('staff_index', 0)] += 1

        if not x_coords:
            return {}

        return {
            'x_range': {'min': min(x_coords), 'max': max(x_coords)},
            'y_range': {'min': min(y_coords), 'max': max(y_coords)},
            'coordinate_density': {
                'x_spread': max(x_coords) - min(x_coords),
                'y_spread': max(y_coords) - min(y_coords)
            },
            'staff_distribution': dict(staff_distribution)
        }

    def detect_performance_anomalies(self) -> List[Dict[str, Any]]:
        """Stage execution time outlier detection (wrapper for anomaly detector)"""
        return self.anomaly_detector.detect_performance_anomalies()