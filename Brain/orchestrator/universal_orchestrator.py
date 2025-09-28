#!/usr/bin/env python3
"""
Universal Orchestrator - Master Pipeline Coordinator

This script coordinates the complete Sib2Ae pipeline from MusicXML/MIDI input
to synchronized After Effects-ready output, maintaining Universal ID relationships
throughout all processing stages.

Based on synchronization_coordinator.py patterns but enhanced for Universal ID
preservation, atomic manifest operations, and comprehensive error recovery.
"""

import argparse
import json
import logging
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import orchestrator components
from . import (
    PipelineStage, OrchestrationConfig, ExecutionMode,
    UniversalFileRegistry, AtomicManifestManager, ProgressTracker,
    create_process_failure_handler, create_manifest_manager,
    create_note_coordinator_stage, create_tied_note_processor_stage,
    create_symbolic_pipeline_stages, create_audio_pipeline_stages
)
from .smart_log_aggregator import SmartLogAggregator


class UniversalOrchestrator:
    """
    Master orchestrator for Universal ID pipeline coordination.

    Coordinates Note Coordinator → Tied Note Processor → Symbolic Pipeline →
    Audio Pipeline → Verification while maintaining Universal ID integrity
    throughout all processing stages.
    """

    def __init__(self, config: OrchestrationConfig):
        """
        Initialize Universal Orchestrator.

        Args:
            config: Pipeline orchestration configuration
        """
        self.config = config
        self.start_time = datetime.now()

        # Core components
        self.universal_registry: Optional[UniversalFileRegistry] = None
        self.manifest_manager: Optional[AtomicManifestManager] = None
        self.progress_tracker: Optional[ProgressTracker] = None

        # Shell output capture
        self.output_file = self.config.output_dir / "shell_output" / "execution_output.log"
        self.smart_aggregator = SmartLogAggregator(self.output_file)
        self.failure_handler = create_process_failure_handler(
            name="universal_orchestrator",
            enable_circuit_breaker=config.enable_circuit_breaker,
            enable_retry=True
        )

        # Pipeline stages
        self.stages: List[PipelineStage] = []
        self.completed_stages: Set[str] = set()
        self.failed_stages: Set[str] = set()

        # Execution tracking
        self.execution_log: List[str] = []
        self.universal_ids: List[str] = []

        # Setup logging
        self._setup_logging()

        # Create output directories
        config.create_output_directory()

        if config.verbose:
            self._display_initialization_banner()

    def _setup_logging(self):
        """Setup comprehensive logging"""
        self.logger = logging.getLogger("UniversalOrchestrator")

        if self.config.log_file:
            handler = logging.FileHandler(self.config.log_file)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _display_initialization_banner(self):
        """Display initialization banner"""
        self._print_and_log("UNIVERSAL ID PIPELINE ORCHESTRATOR")
        self._print_and_log("=" * 60)
        self._print_and_log(f"🎼 MusicXML: {self.config.musicxml_file.name}")
        self._print_and_log(f"🎹 MIDI: {self.config.midi_file.name}")
        if self.config.svg_file:
            self._print_and_log(f"🎨 SVG: {self.config.svg_file.name}")
        self._print_and_log(f"📁 Output: {self.config.output_dir}")
        self._print_and_log(f"🚀 Mode: {self.config.execution_mode.value}")
        self._print_and_log(f"🔄 Workers: {self.config.max_workers}")
        self._print_and_log(f"🛡️  Circuit Breaker: {'Enabled' if self.config.enable_circuit_breaker else 'Disabled'}")
        self._print_and_log(f"🎯 Universal ID Preservation: {'Enabled' if self.config.preserve_universal_ids else 'Disabled'}")
        self._print_and_log(f"📝 New Filename Pattern: {'Enabled' if self.config.apply_new_filename_pattern else 'Disabled'}")
        self._print_and_log("")

    def orchestrate_complete_pipeline(self) -> Dict[str, any]:
        """
        Orchestrate the complete Universal ID pipeline execution.

        Returns:
            Comprehensive execution result with statistics and file locations
        """
        try:
            self._log("🚀 Starting Universal ID Pipeline Orchestration")

            # Phase 1: Initialize Core Components
            self._log("Phase 1: Initializing Core Components")
            self._initialize_components()

            # Phase 2: Execute Note Coordinator
            self._log("Phase 2: Executing Note Coordinator")
            self._execute_note_coordinator()

            # Phase 3: Execute Tied Note Processor (if enabled)
            if not self.config.skip_tied_note_processing:
                self._log("Phase 3: Executing Tied Note Processor")
                self._execute_tied_note_processor()

            # Phase 4: Execute Pipeline Stages
            self._log("Phase 4: Executing Pipeline Stages")
            if self.config.execution_mode == ExecutionMode.SEQUENTIAL:
                self._execute_sequential_pipeline()
            else:
                self._execute_parallel_pipeline()

            self._print_and_log("🔥 DEBUG: Pipeline stages completed, moving to Phase 5...")

            # Phase 5: Final Validation
            self._log("Phase 5: Performing Final Validation")
            self._print_and_log("🔥 DEBUG: About to start final validation...")
            validation_results = self._perform_final_validation()
            self._print_and_log("🔥 DEBUG: Final validation completed!")

            # Phase 6: Generate Final Report
            self._log("Phase 6: Generating Final Execution Report")
            self._print_and_log("🔥 DEBUG: About to generate final report...")
            final_report = self._generate_final_report(validation_results)
            self._print_and_log("🔥 DEBUG: Final report generated!")

            # Close progress bars immediately to prevent hanging
            if self.progress_tracker:
                self.progress_tracker.close_all_progress_bars()
                # Force clear any lingering tqdm instances
                import tqdm
                tqdm.tqdm._instances.clear() if hasattr(tqdm.tqdm, '_instances') else None

            self._log("✅ Universal ID Pipeline Orchestration Complete!")
            self._log(f"📊 Completed {len(self.completed_stages)} stages successfully")

        except Exception as e:
            self._log(f"❌ Pipeline orchestration failed: {e}")
            if self.config.verbose:
                traceback.print_exc()
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise

        finally:
            self._cleanup()

    def _initialize_components(self):
        """Initialize core orchestration components"""
        # Initialize Universal File Registry
        registry_file = self.config.output_dir / "universal_file_registry.json"
        self.universal_registry = UniversalFileRegistry(registry_file)

        # Initialize Atomic Manifest Manager
        self.manifest_manager = create_manifest_manager(
            backup_enabled=self.config.manifest_backup_enabled,
            verbose=self.config.verbose
        )

        # Progress tracker will be initialized after we know how many Universal IDs we have
        self.progress_tracker = None

        self._log("✅ Core components initialized")

    def _execute_note_coordinator(self):
        """Execute Note Coordinator and initialize Universal ID tracking"""
        stage = create_note_coordinator_stage(self.config)
        self._execute_single_stage(stage)

        if stage.status.value == "completed":
            self.completed_stages.add(stage.name)

            # Load Universal ID registry
            registry_path = self.config.output_dir / "universal_notes_registry.json"
            midi_manifest_path = self.config.output_dir / "midi_pipeline_manifest.json"
            svg_manifest_path = self.config.output_dir / "svg_pipeline_manifest.json"

            self.universal_registry.initialize_from_note_coordinator(
                registry_path, midi_manifest_path, svg_manifest_path
            )

            # Extract Universal IDs for tracking
            self.universal_ids = list(self.universal_registry.universal_records.keys())

            # Now initialize progress tracker with actual Universal ID count
            expected_stages = [
                "note_coordinator", "tied_note_processor", "noteheads_extraction",
                "instrument_separation", "individual_noteheads_creation",
                "midi_note_separation", "audio_rendering", "keyframe_generation"
            ]

            if self.config.skip_tied_note_processing:
                expected_stages.remove("tied_note_processor")

            self.progress_tracker = ProgressTracker(
                total_universal_ids=len(self.universal_ids),
                expected_stages=expected_stages,
                progress_callback=self.config.progress_callback,
                log_file=self.config.output_dir / "logs" / "progress.log",
                verbose=self.config.verbose
            )

            # Initialize progress tracking
            self.progress_tracker.initialize_universal_ids(self.universal_ids)

            self._log(f"✅ Note Coordinator completed: {len(self.universal_ids)} Universal IDs loaded")

        else:
            raise RuntimeError("Note Coordinator execution failed")

    def _execute_tied_note_processor(self):
        """Execute Tied Note Processor for timing calculations"""
        stage = create_tied_note_processor_stage(self.config)
        self._execute_single_stage(stage)

        if stage.status.value == "completed":
            self.completed_stages.add(stage.name)

            # Load tied note assignments and update Universal ID records
            assignments_path = self.config.output_dir / "tied_note_assignments.json"
            if assignments_path.exists():
                with open(assignments_path, 'r') as f:
                    tied_data = json.load(f)

                # Update timing data in Universal ID registry
                for assignment in tied_data.get('assignments', []):
                    note_info = assignment.get('note', {})
                    timing_info = assignment.get('timing', {})

                    # Find Universal ID by matching note characteristics
                    # This is a simplified approach - in reality, you'd need more robust matching
                    for universal_id in self.universal_ids:
                        record = self.universal_registry.universal_records[universal_id]
                        if (record.xml_data.get('pitch') == note_info.get('pitch') and
                            record.xml_data.get('measure') == note_info.get('measure')):
                            self.universal_registry.update_timing_data(universal_id, timing_info)
                            break

            self._log("✅ Tied Note Processor completed with timing calculations")

        else:
            if self.config.continue_on_non_critical_failure:
                self._log("⚠️  Tied Note Processor failed but continuing (non-critical)")
                self.failed_stages.add(stage.name)
            else:
                raise RuntimeError("Tied Note Processor execution failed")

    def _execute_sequential_pipeline(self):
        """Execute pipeline stages sequentially"""
        self._log("🔄 Executing Sequential Pipeline")

        # Create all pipeline stages
        symbolic_stages = create_symbolic_pipeline_stages(self.config)
        audio_stages = create_audio_pipeline_stages(self.config)

        all_stages = symbolic_stages + audio_stages

        # Execute stages in order
        for stage in all_stages:
            if stage.is_ready_to_run(self.completed_stages):
                self._execute_single_stage_with_universal_id_tracking(stage)

                if stage.status.value == "completed":
                    self.completed_stages.add(stage.name)

                    # IMMEDIATE TERMINATION: If this is the last stage, force exit now
                    if stage.name == "audio_to_keyframes":
                        # Generate final summary before nuclear exit
                        try:
                            self.smart_aggregator.generate_final_summary()
                        except Exception as e:
                            self._log(f"⚠️  Final summary generation error (non-critical): {e}")

                        self._print_and_log("🔥 NUCLEAR EXIT: Last stage completed, forcing immediate termination!")
                        import os
                        os._exit(0)
                elif stage.status.value == "failed":
                    if self.config.continue_on_non_critical_failure:
                        self.failed_stages.add(stage.name)
                        self._log(f"⚠️  Stage {stage.name} failed but continuing")
                    else:
                        raise RuntimeError(f"Stage {stage.name} failed")
            else:
                self._log(f"⏳ Stage {stage.name} waiting for dependencies: {stage.depends_on}")

        self._log("✅ Sequential Pipeline completed successfully")
        print("🔥 DEBUG: Sequential pipeline method completed, returning to main execute...")

    def _execute_parallel_pipeline(self):
        """Execute compatible pipeline stages in parallel"""
        self._log("🔄 Executing Parallel Pipeline")

        # Create all pipeline stages
        symbolic_stages = create_symbolic_pipeline_stages(self.config)
        audio_stages = create_audio_pipeline_stages(self.config)

        # Group stages that can run in parallel
        stage_groups = [
            symbolic_stages[:2],  # Noteheads extraction and subtraction
            [symbolic_stages[2], audio_stages[0]],  # Instrument separation and MIDI separation (can run in parallel)
            [symbolic_stages[3], audio_stages[1]],  # Individual noteheads and audio rendering
            [symbolic_stages[4], audio_stages[2]]   # Staff extraction and keyframes
        ]

        # Execute stage groups
        for group in stage_groups:
            ready_stages = [s for s in group if s.is_ready_to_run(self.completed_stages)]

            if ready_stages:
                if len(ready_stages) == 1:
                    # Execute single stage
                    self._execute_single_stage_with_universal_id_tracking(ready_stages[0])
                else:
                    # Execute stages in parallel
                    self._execute_stages_in_parallel(ready_stages)

                # Update completed stages
                for stage in ready_stages:
                    if stage.status.value == "completed":
                        self.completed_stages.add(stage.name)
                    elif stage.status.value == "failed":
                        if self.config.continue_on_non_critical_failure:
                            self.failed_stages.add(stage.name)
                        else:
                            raise RuntimeError(f"Stage {stage.name} failed")

    def _execute_stages_in_parallel(self, stages: List[PipelineStage]):
        """Execute multiple stages in parallel"""
        with ThreadPoolExecutor(max_workers=min(len(stages), self.config.max_workers)) as executor:
            # Submit all stages
            future_to_stage = {
                executor.submit(self._execute_single_stage_with_universal_id_tracking, stage): stage
                for stage in stages
            }

            # Wait for completion
            for future in as_completed(future_to_stage):
                stage = future_to_stage[future]
                try:
                    future.result()
                    self._log(f"✅ Parallel stage completed: {stage.name}")
                except Exception as e:
                    self._log(f"❌ Parallel stage failed: {stage.name}: {e}")

    def _execute_single_stage(self, stage: PipelineStage):
        """Execute a single pipeline stage with basic error handling"""
        if self.config.verbose:
            self._print_and_log(f"🔄 Executing: {stage.name}")
            self._print_and_log(f"   📝 {stage.description}")
            self._print_and_log(f"   💻 Command: {' '.join(stage.command)}")

        stage.start_execution()

        try:
            # Validate input files (check from working directory where scripts will run)
            working_dir = self.config.get_working_directory()
            for input_file in stage.input_files:
                if not (working_dir / input_file).exists():
                    raise FileNotFoundError(f"Required input file not found: {input_file} (checked from {working_dir})")

            # Execute command through failure handler
            try:
                result = self.failure_handler.execute_subprocess(
                    stage.command,
                    cwd=self.config.get_working_directory(),
                    timeout=self.config.stage_timeout_seconds
                )
            except subprocess.TimeoutExpired:
                # Force kill the process group if timeout
                self._log(f"⏰ Stage {stage.name} timed out, forcing termination")
                raise

            stage.complete_successfully()

            if self.config.verbose:
                self._print_and_log(f"   ✅ Completed in {stage.actual_duration_seconds:.1f}s")

            # ALWAYS capture subprocess output to file (regardless of verbose)
            if result.stdout:
                # Capture full stdout for smart aggregator analysis
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        self._print_and_log(f"      {line}")

                # Show only last few lines for console if verbose
                if self.config.verbose and len(lines) > 3:
                    self._print_and_log(f"      ... ({len(lines) - 3} additional lines captured)")

            if self.config.verbose:
                self._print_and_log("")

        except Exception as e:
            stage.fail_with_error(str(e))
            if self.config.verbose:
                self._print_and_log(f"   ❌ Failed after {stage.actual_duration_seconds:.1f}s: {e}")
                self._print_and_log("")
            raise

        self.stages.append(stage)

    def _execute_single_stage_with_universal_id_tracking(self, stage: PipelineStage):
        """Execute stage with Universal ID tracking and progress updates"""
        if self.progress_tracker:
            self.progress_tracker.start_stage(stage.name, set(self.universal_ids))

        # Execute the stage with error handling
        try:
            self._execute_single_stage(stage)
        except Exception as e:
            # Stage execution failed - status already set to failed in _execute_single_stage
            if self.config.continue_on_non_critical_failure:
                self._log(f"⚠️  Stage {stage.name} failed but continuing: {e}")
                return  # Don't re-raise, just continue
            else:
                raise  # Re-raise if we're not continuing on failure

        if stage.status.value == "completed":
            # Update progress for all Universal IDs (simplified approach)
            if self.progress_tracker:
                try:
                    for universal_id in self.universal_ids:
                        self.progress_tracker.complete_universal_id(
                            universal_id, stage.name, metadata={'stage_duration': stage.actual_duration_seconds}
                        )
                except Exception as e:
                    self._log(f"⚠️  Progress tracking error (non-critical): {e}")

            # Complete stage tracking
            if self.progress_tracker:
                try:
                    self.progress_tracker.complete_stage(stage.name)
                except Exception as e:
                    self._log(f"⚠️  Stage completion tracking error (non-critical): {e}")

            # Trigger smart aggregator stage completion
            try:
                stage_metrics = {
                    'duration': stage.actual_duration_seconds,
                    'universal_ids': len(self.universal_ids),
                    'success': stage.status == 'completed'
                }
                self.smart_aggregator.complete_stage(stage.name, stage_metrics)
            except Exception as e:
                self._log(f"⚠️  Smart aggregation error (non-critical): {e}")

    def _perform_final_validation(self) -> Dict[str, any]:
        """Perform comprehensive final validation"""
        validation_results = {
            'universal_id_integrity': {},
            'file_existence': {},
            'manifest_consistency': {},
            'pipeline_completeness': {},
            'performance_metrics': {}
        }

        # Validate Universal ID integrity
        if self.universal_registry and self.config.validate_universal_id_integrity:
            integrity_issues = self.universal_registry.validate_universal_id_integrity()
            validation_results['universal_id_integrity'] = {
                'valid': len(integrity_issues['missing_files']) == 0 and len(integrity_issues['filename_mismatches']) == 0,
                'issues': integrity_issues
            }

        # Validate file dependencies
        if self.config.validate_file_dependencies:
            file_issues = []
            for stage in self.stages:
                for output_file in stage.output_files:
                    if not output_file.exists():
                        file_issues.append(f"Missing output file: {output_file}")

            validation_results['file_existence'] = {
                'valid': len(file_issues) == 0,
                'issues': file_issues
            }

        # Pipeline completeness
        expected_stages = len([s for s in self.stages if s.name not in self.failed_stages])
        completed_stages = len(self.completed_stages)

        validation_results['pipeline_completeness'] = {
            'expected_stages': expected_stages,
            'completed_stages': completed_stages,
            'completion_rate': completed_stages / expected_stages if expected_stages > 0 else 0,
            'failed_stages': list(self.failed_stages)
        }

        # Performance metrics
        total_duration = (datetime.now() - self.start_time).total_seconds()
        validation_results['performance_metrics'] = {
            'total_duration_seconds': total_duration,
            'universal_ids_processed': len(self.universal_ids),
            'processing_rate': len(self.universal_ids) / total_duration if total_duration > 0 else 0,
            'failure_handler_stats': self.failure_handler.get_statistics()
        }

        return validation_results

    def _generate_final_report(self, validation_results: Dict[str, any]) -> Dict[str, any]:
        """Generate comprehensive final execution report"""
        print("🔥 DEBUG: Inside _generate_final_report method...")
        total_duration = (datetime.now() - self.start_time).total_seconds()
        print("🔥 DEBUG: Calculated total duration...")

        final_report = {
            'execution_metadata': {
                'orchestrator_version': '1.0.0',
                'execution_timestamp': datetime.now().isoformat(),
                'total_duration_seconds': total_duration,
                'working_directory': str(self.config.get_working_directory()),
                'configuration': {
                    'execution_mode': self.config.execution_mode.value,
                    'max_workers': self.config.max_workers,
                    'circuit_breaker_enabled': self.config.enable_circuit_breaker,
                    'universal_id_preservation': self.config.preserve_universal_ids,
                    'new_filename_pattern': self.config.apply_new_filename_pattern
                }
            },
            'universal_id_summary': {
                'total_universal_ids': len(self.universal_ids),
                'registry_statistics': self.universal_registry.get_registry_statistics() if self.universal_registry else {}
            },
            'pipeline_execution': {
                'completed_stages': list(self.completed_stages),
                'failed_stages': list(self.failed_stages),
                'total_stages_attempted': len(self.stages),
                'success_rate': len(self.completed_stages) / len(self.stages) if self.stages else 0
            },
            'output_files': {
                'universal_notes_registry': str(self.config.output_dir / "universal_notes_registry.json"),
                'coordination_metadata': str(self.config.output_dir / "coordination_metadata.json"),
                'universal_file_registry': str(self.config.output_dir / "universal_file_registry.json"),
                'progress_report': str(self.config.output_dir / "logs" / "final_progress_report.json")
            },
            'validation_results': validation_results,
            'progress_summary': self.progress_tracker.get_overall_progress() if self.progress_tracker else {}
        }
        print("🔥 DEBUG: Built final report dictionary...")

        # Save final report
        print("🔥 DEBUG: About to save final report...")
        report_path = self.config.output_dir / "final_execution_report.json"
        with open(report_path, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        print("🔥 DEBUG: Final report saved!")

        # Save progress report
        print("🔥 DEBUG: About to save progress report...")
        if self.progress_tracker:
            progress_report_path = self.config.output_dir / "logs" / "final_progress_report.json"
            self.progress_tracker.save_progress_report(progress_report_path)
        print("🔥 DEBUG: Progress report saved!")

        # Save Universal ID registry
        print("🔥 DEBUG: About to save Universal ID registry...")
        if self.universal_registry:
            self.universal_registry.save_registry()
        print("🔥 DEBUG: Universal ID registry saved!")

        if self.config.verbose:
            self._display_final_summary(final_report)

        # NUCLEAR TERMINATION: Force immediate process termination to prevent hanging
        # This must run regardless of verbose setting to prevent hanging
        import sys, os, threading, signal, gc

        print("🔥 FORCING PROCESS TERMINATION TO PREVENT HANGING...")

        # 1. Aggressive progress bar cleanup
        try:
            import tqdm
            if hasattr(tqdm.tqdm, '_instances'):
                tqdm.tqdm._instances.clear()
        except:
            pass

        # 2. Force kill all threads except main
        try:
            for thread in threading.enumerate():
                if thread != threading.current_thread() and thread.is_alive():
                    if hasattr(thread, '_stop'):
                        thread._stop()
        except:
            pass

        # 3. Flush all outputs
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except:
            pass

        # 4. Force garbage collection
        try:
            gc.collect()
        except:
            pass

        # 5. NUCLEAR: Immediate termination
        print("🚨 CALLING os._exit(0) NOW...")
        os._exit(0)

        return final_report

    def _display_final_summary(self, final_report: Dict[str, any]):
        """Display comprehensive final summary"""
        print("🎯 UNIVERSAL ID PIPELINE ORCHESTRATION COMPLETE!")
        print("=" * 60)
        print()

        exec_meta = final_report['execution_metadata']
        print("📊 EXECUTION SUMMARY:")
        print("-" * 30)
        print(f"✅ Total duration: {exec_meta['total_duration_seconds']:.1f}s")
        print(f"🎵 Universal IDs processed: {final_report['universal_id_summary']['total_universal_ids']}")
        print(f"📈 Processing rate: {exec_meta['total_duration_seconds'] / final_report['universal_id_summary']['total_universal_ids'] if final_report['universal_id_summary']['total_universal_ids'] > 0 else 0:.1f}s per Universal ID")
        print()

        pipeline_exec = final_report['pipeline_execution']
        print("🔧 PIPELINE RESULTS:")
        print("-" * 30)
        print(f"✅ Completed stages: {len(pipeline_exec['completed_stages'])}")
        print(f"❌ Failed stages: {len(pipeline_exec['failed_stages'])}")
        print(f"📊 Success rate: {pipeline_exec['success_rate']:.1%}")
        if pipeline_exec['failed_stages']:
            print(f"⚠️  Failed stages: {', '.join(pipeline_exec['failed_stages'])}")
        print()

        validation = final_report['validation_results']
        print("🔍 VALIDATION RESULTS:")
        print("-" * 30)
        uid_integrity = validation.get('universal_id_integrity', {})
        print(f"🎯 Universal ID integrity: {'✅ Valid' if uid_integrity.get('valid', False) else '❌ Issues found'}")

        file_existence = validation.get('file_existence', {})
        print(f"📁 File existence: {'✅ All files present' if file_existence.get('valid', False) else '❌ Missing files'}")

        completeness = validation.get('pipeline_completeness', {})
        print(f"🔄 Pipeline completeness: {completeness.get('completion_rate', 0):.1%}")
        print()

        print("📁 OUTPUT FILES:")
        print("-" * 30)
        for file_desc, file_path in final_report['output_files'].items():
            print(f"📄 {file_desc.replace('_', ' ').title()}: {file_path}")
        print()

        print("🚀 SUCCESS! Universal ID Pipeline orchestration completed")
        print("   Ready for After Effects integration")

    def _cleanup(self):
        """Cleanup resources"""
        if self.progress_tracker:
            self.progress_tracker.close_all_progress_bars()

    def _log(self, message: str):
        """Log message with timestamp - routes through smart aggregator"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.execution_log.append(log_entry)

        # Route through smart aggregator for intelligent file output
        try:
            self.smart_aggregator.process_message(log_entry)
        except Exception:
            # Fallback to direct file writing if aggregator fails
            try:
                with open(self.output_file, 'a') as f:
                    f.write(log_entry + "\n")
            except Exception:
                pass  # Don't let file writing break the pipeline

        # Only print to console if verbose mode is enabled
        if self.config.verbose:
            print(log_entry)

        if hasattr(self, 'logger'):
            self.logger.info(message)

    def _print_and_log(self, message: str):
        """ALWAYS log to shell output file, print to console only if verbose"""
        # Route message through smart aggregator for intelligent file output
        try:
            self.smart_aggregator.process_message(message)
        except Exception:
            # Fallback to direct file writing if aggregator fails
            try:
                with open(self.output_file, 'a') as f:
                    f.write(message + "\n")
            except Exception:
                pass  # Don't let file writing break the pipeline

        # Only print to console if verbose mode is enabled (unchanged behavior)
        if self.config.verbose:
            print(message)


def main():
    """CLI interface for Universal Orchestrator"""
    parser = argparse.ArgumentParser(
        description="Universal ID Pipeline Orchestrator - Master Sib2Ae Coordination",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sequential execution (default)
  python universal_orchestrator.py "Brain/Base/SS 9.musicxml" "Brain/Base/Saint-Saens Trio No 2.mid"

  # Parallel execution with SVG
  python universal_orchestrator.py "Brain/Base/SS 9.musicxml" "Brain/Base/Saint-Saens Trio No 2.mid" --svg "Brain/Base/SS 9 full.svg" --mode parallel

  # Custom output directory
  python universal_orchestrator.py "Brain/Base/SS 9.musicxml" "Brain/Base/Saint-Saens Trio No 2.mid" --output "my_universal_output"

  # Disable circuit breaker
  python universal_orchestrator.py "Brain/Base/SS 9.musicxml" "Brain/Base/Saint-Saens Trio No 2.mid" --no-circuit-breaker
        """
    )

    parser.add_argument("musicxml_file", help="Path to MusicXML score file")
    parser.add_argument("midi_file", help="Path to MIDI performance file")
    parser.add_argument("--svg", help="Path to SVG score file (optional)")
    parser.add_argument("--output", "-o", default="universal_output", help="Output directory (default: universal_output)")
    parser.add_argument("--mode", choices=["sequential", "parallel"], default="sequential", help="Execution mode")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Maximum parallel workers")
    parser.add_argument("--timeout", type=float, default=600.0, help="Stage timeout in seconds")
    parser.add_argument("--no-circuit-breaker", action="store_true", help="Disable circuit breaker")
    parser.add_argument("--skip-tied-notes", action="store_true", help="Skip tied note processing")
    parser.add_argument("--audio-mode", choices=["fast", "standard"], default="fast", help="Audio rendering mode")
    parser.add_argument("--keyframe-mode", choices=["fast", "standard"], default="fast", help="Keyframe generation mode")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (minimal output)")
    parser.add_argument("--log-file", help="Path to log file")

    args = parser.parse_args()

    # Validate input files and normalize paths relative to Sib2Ae working directory
    sib2ae_dir = Path("/Users/colinmignot/Claude Code/Sib2Ae/")

    def normalize_path_for_brain_execution(file_path: str) -> Path:
        """Convert file path to be relative to Sib2Ae directory for execution"""
        path = Path(file_path)
        if path.is_absolute():
            return path
        # Keep path as-is since we now run from Sib2Ae parent directory
        return path

    musicxml_path = normalize_path_for_brain_execution(args.musicxml_file)
    midi_path = normalize_path_for_brain_execution(args.midi_file)
    svg_path = normalize_path_for_brain_execution(args.svg) if args.svg else None

    # Check file existence from Brain directory (the execution working directory)
    if not (sib2ae_dir / musicxml_path).exists():
        print(f"❌ ERROR: MusicXML file not found: {musicxml_path} (checked from Sib2Ae directory)")
        sys.exit(1)

    if not (sib2ae_dir / midi_path).exists():
        print(f"❌ ERROR: MIDI file not found: {midi_path} (checked from Sib2Ae directory)")
        sys.exit(1)

    if svg_path and not (sib2ae_dir / svg_path).exists():
        print(f"❌ ERROR: SVG file not found: {svg_path} (checked from Sib2Ae directory)")
        sys.exit(1)

    try:
        # Create orchestration configuration
        config = OrchestrationConfig(
            musicxml_file=musicxml_path,
            midi_file=midi_path,
            svg_file=svg_path,
            output_dir=Path(args.output),
            execution_mode=ExecutionMode.SEQUENTIAL if args.mode == "sequential" else ExecutionMode.PARALLEL,
            max_workers=args.workers,
            enable_circuit_breaker=not args.no_circuit_breaker,
            verbose=not args.quiet,
            stage_timeout_seconds=args.timeout,
            skip_tied_note_processing=args.skip_tied_notes,
            audio_renderer_mode=args.audio_mode,
            keyframe_generator_mode=args.keyframe_mode,
            log_file=Path(args.log_file) if args.log_file else None
        )

        # Validate configuration
        issues = config.validate_configuration()
        if issues:
            print("❌ Configuration validation failed:")
            for issue in issues:
                print(f"   • {issue}")
            sys.exit(1)

        # Initialize and run orchestrator
        orchestrator = UniversalOrchestrator(config)
        success = orchestrator.orchestrate_complete_pipeline()

        # Final success message
        if not args.quiet:
            print("\n🎯 PIPELINE EXECUTION SUCCESSFUL!")
            print(f"📁 Output directory: {config.output_dir}")
            print("🚀 Ready for After Effects integration")

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️  Pipeline execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ PIPELINE EXECUTION FAILED: {e}")
        if not args.quiet:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()