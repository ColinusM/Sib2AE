#!/usr/bin/env python3
"""
Synchronization Coordinator - Master Pipeline Orchestrator

This module orchestrates the complete Sib2Ae pipeline execution with master MIDI timing reference.
It coordinates both symbolic (SVG) and audio pipelines to merge at the end with consistent timing,
supporting both sequential and parallel execution modes while preserving timing integrity.

Critical Features:
- Master MIDI timing preservation throughout entire pipeline
- Dual-pipeline orchestration (Separators/ + Audio Separators/)
- Sequential ("symbolic separators first") and parallel execution modes
- Context-driven synchronization using master relationship data
- Final master_synchronization.json output generation
- Backward compatibility with existing pipeline functionality
- Performance optimization with parallel processing coordination

Pipeline Integration:
- Context Gatherer: Pre-analysis of XML-MIDI-SVG relationships
- Master MIDI Extractor: Authoritative timing reference preservation
- Symbolic Pipeline: Separators/ tools with timing coordination
- Audio Pipeline: Audio Separators/ tools with shared timing reference
- Tied Note Processor: Visual-temporal mismatch handling (3:1 noteheads)
- Final Output: Complete After Effects compatible synchronization data
"""

import sys
import os
import json
import time
import subprocess
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple, Any, Union
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import traceback
import shutil

# Import synchronizer components
from .context_gatherer import ContextGatherer, ContextAnalysis
from .utils.master_midi_extractor import MasterMIDIExtractor, MasterMIDITiming
from .utils.xml_temporal_parser import XMLTemporalParser, MusicXMLNote
from .utils.midi_matcher import MIDIMatcher, NoteMatch
from .utils.tied_note_processor import TiedNoteProcessor, TiedNoteAssignment


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution"""
    mode: str                           # "sequential" or "parallel"
    preserve_outputs: bool = True       # Keep existing pipeline outputs
    timing_tolerance_ms: float = 100.0  # MIDI matching tolerance
    parallel_workers: int = 4           # Number of parallel workers
    verbose: bool = True                # Detailed logging
    performance_tracking: bool = True   # Track execution times
    backup_existing: bool = True        # Backup existing outputs


@dataclass
class PipelineStage:
    """Represents a single pipeline execution stage"""
    name: str                          # Stage identifier
    description: str                   # Human-readable description
    command: List[str]                 # Command to execute
    input_files: List[Path]           # Required input files
    output_files: List[Path]          # Expected output files
    depends_on: List[str] = None       # Dependencies (stage names)
    estimated_duration_seconds: float = 0.0  # Performance tracking
    actual_duration_seconds: float = 0.0     # Measured execution time
    status: str = "pending"            # "pending", "running", "completed", "failed"
    error_message: str = ""            # Error details if failed


@dataclass
class PipelineExecution:
    """Complete pipeline execution result"""
    config: PipelineConfig
    stages: List[PipelineStage]
    total_duration_seconds: float
    master_timing_reference: MasterMIDITiming
    context_analysis: ContextAnalysis
    final_synchronization_path: Path
    execution_summary: Dict
    performance_metrics: Dict


class SynchronizationCoordinator:
    """
    Master orchestrator for synchronized music animation pipeline.
    
    Coordinates both symbolic (Separators/) and audio (Audio Separators/) pipelines
    with master MIDI timing reference, supporting both sequential and parallel execution.
    """
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize synchronization coordinator.
        
        Args:
            config: Pipeline configuration with execution mode and parameters
        """
        self.config = config
        self.start_time = time.time()
        self.stages: List[PipelineStage] = []
        self.master_timing: Optional[MasterMIDITiming] = None
        self.context_analysis: Optional[ContextAnalysis] = None
        self.execution_log: List[str] = []
        
        # Create outputs directory
        self.outputs_dir = Path("Synchronizer/outputs")
        self.outputs_dir.mkdir(exist_ok=True)
        
        if self.config.verbose:
            print("SYNCHRONIZATION COORDINATOR INITIALIZED")
            print("=" * 60)
            print(f"🎯 Execution mode: {self.config.mode}")
            print(f"⏱️  Timing tolerance: {self.config.timing_tolerance_ms}ms")
            print(f"🔄 Parallel workers: {self.config.parallel_workers}")
            print(f"💾 Preserve outputs: {self.config.preserve_outputs}")
            print(f"📊 Performance tracking: {self.config.performance_tracking}")
            print()
    
    def orchestrate_full_pipeline(
        self,
        musicxml_path: Path,
        midi_path: Path,
        svg_path: Path,
        output_dir: Optional[Path] = None
    ) -> PipelineExecution:
        """
        Orchestrate complete synchronized music animation pipeline.
        
        Args:
            musicxml_path: Path to MusicXML score file
            midi_path: Path to master MIDI file (before note separation)
            svg_path: Path to complete SVG score file
            output_dir: Optional custom output directory
            
        Returns:
            PipelineExecution with complete results and timing data
        """
        if self.config.verbose:
            print("SYNCHRONIZED MUSIC ANIMATION PIPELINE")
            print("=" * 60)
            print(f"🎼 MusicXML: {musicxml_path.name}")
            print(f"🎹 Master MIDI: {midi_path.name}")
            print(f"🎨 SVG: {svg_path.name}")
            print(f"🚀 Mode: {self.config.mode}")
            print()
        
        try:
            # Phase 1: Context Gathering and Master Timing Extraction
            self._log("Phase 1: Context Gathering and Master Timing Extraction")
            context_analysis = self._execute_context_gathering(musicxml_path, midi_path, svg_path)
            self.context_analysis = context_analysis
            self.master_timing = context_analysis.master_midi_timing
            
            # Phase 2: Pipeline Execution (Sequential or Parallel)
            self._log(f"Phase 2: Pipeline Execution ({self.config.mode.title()} Mode)")
            if self.config.mode == "sequential":
                self._execute_sequential_pipeline(musicxml_path, midi_path, svg_path, output_dir)
            elif self.config.mode == "parallel":
                self._execute_parallel_pipeline(musicxml_path, midi_path, svg_path, output_dir)
            else:
                raise ValueError(f"Unknown execution mode: {self.config.mode}")
            
            # Phase 3: Tied Note Processing and Timing Coordination
            self._log("Phase 3: Tied Note Processing and Timing Coordination")
            tied_assignments = self._execute_tied_note_processing()
            
            # Phase 4: Master Synchronization Generation
            self._log("Phase 4: Master Synchronization Generation")
            final_sync_path = self._generate_master_synchronization(tied_assignments, output_dir)
            
            # Phase 5: Validation and Performance Analysis
            self._log("Phase 5: Validation and Performance Analysis")
            execution_summary = self._generate_execution_summary()
            performance_metrics = self._calculate_performance_metrics()
            
            total_duration = time.time() - self.start_time
            
            # Create final execution result
            execution_result = PipelineExecution(
                config=self.config,
                stages=self.stages,
                total_duration_seconds=total_duration,
                master_timing_reference=self.master_timing,
                context_analysis=self.context_analysis,
                final_synchronization_path=final_sync_path,
                execution_summary=execution_summary,
                performance_metrics=performance_metrics
            )
            
            if self.config.verbose:
                self._display_completion_summary(execution_result)
            
            return execution_result
            
        except Exception as e:
            self._log(f"❌ PIPELINE EXECUTION FAILED: {e}")
            if self.config.verbose:
                traceback.print_exc()
            raise
    
    def _execute_context_gathering(
        self,
        musicxml_path: Path,
        midi_path: Path,
        svg_path: Path
    ) -> ContextAnalysis:
        """Execute context gathering phase with master timing extraction"""
        stage = PipelineStage(
            name="context_gathering",
            description="Extract master timing and create XML-MIDI-SVG relationships",
            command=["python", "context_gatherer.py", str(musicxml_path), str(midi_path), str(svg_path)],
            input_files=[musicxml_path, midi_path, svg_path],
            output_files=[self.outputs_dir / "master_relationship.json"]
        )
        
        start_time = time.time()
        stage.status = "running"
        self.stages.append(stage)
        
        try:
            # Initialize context gatherer
            gatherer = ContextGatherer(musicxml_path, midi_path, svg_path)
            
            # Perform comprehensive analysis
            context_analysis = gatherer.analyze_and_create_relationships()
            
            # Save context analysis
            output_path = self.outputs_dir / "master_relationship.json"
            gatherer.save_context_analysis(context_analysis, output_path)
            
            stage.actual_duration_seconds = time.time() - start_time
            stage.status = "completed"
            
            self._log(f"✅ Context gathering complete ({stage.actual_duration_seconds:.1f}s)")
            self._log(f"   📊 {len(context_analysis.synchronized_notes)} synchronized notes")
            self._log(f"   🎯 {context_analysis.timing_accuracy['match_rate']:.1%} match rate")
            
            return context_analysis
            
        except Exception as e:
            stage.status = "failed"
            stage.error_message = str(e)
            stage.actual_duration_seconds = time.time() - start_time
            raise
    
    def _execute_sequential_pipeline(
        self,
        musicxml_path: Path,
        midi_path: Path,
        svg_path: Path,
        output_dir: Optional[Path]
    ):
        """Execute pipeline in sequential mode: symbolic separators first, then audio separators"""
        self._log("🔄 Executing Sequential Pipeline (Symbolic → Audio)")
        
        # Step 1: Symbolic Separators Pipeline
        self._log("Step 1: Symbolic Separators Pipeline")
        symbolic_stages = self._create_symbolic_pipeline_stages(musicxml_path, svg_path, output_dir)
        self._execute_stages_sequentially(symbolic_stages)
        
        # Step 2: Audio Separators Pipeline
        self._log("Step 2: Audio Separators Pipeline")
        audio_stages = self._create_audio_pipeline_stages(midi_path)
        self._execute_stages_sequentially(audio_stages)
        
        self._log("✅ Sequential pipeline execution complete")
    
    def _execute_parallel_pipeline(
        self,
        musicxml_path: Path,
        midi_path: Path,
        svg_path: Path,
        output_dir: Optional[Path]
    ):
        """Execute pipeline in parallel mode: coordinate both pipelines with shared timing reference"""
        self._log("🔄 Executing Parallel Pipeline (Symbolic ∥ Audio)")
        
        # Create both pipeline stages
        symbolic_stages = self._create_symbolic_pipeline_stages(musicxml_path, svg_path, output_dir)
        audio_stages = self._create_audio_pipeline_stages(midi_path)
        
        # Execute pipelines in parallel using thread pool for I/O coordination
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both pipeline executions
            symbolic_future = executor.submit(self._execute_stages_sequentially, symbolic_stages)
            audio_future = executor.submit(self._execute_stages_sequentially, audio_stages)
            
            # Wait for both to complete
            try:
                symbolic_future.result()
                audio_future.result()
                self._log("✅ Parallel pipeline execution complete")
            except Exception as e:
                self._log(f"❌ Parallel execution failed: {e}")
                raise
    
    def _create_symbolic_pipeline_stages(
        self,
        musicxml_path: Path,
        svg_path: Path,
        output_dir: Optional[Path]
    ) -> List[PipelineStage]:
        """Create symbolic (SVG) pipeline stages with timing coordination"""
        stages = []
        
        # Stage 1: Noteheads Extraction
        stages.append(PipelineStage(
            name="noteheads_extraction",
            description="Extract noteheads from MusicXML with timing",
            command=[
                "python", "Separators/truly_universal_noteheads_extractor.py",
                str(musicxml_path)
            ],
            input_files=[musicxml_path],
            output_files=[Path(f"{musicxml_path.stem}_noteheads_universal.svg")],
            estimated_duration_seconds=10.0
        ))
        
        # Stage 2: Noteheads Subtraction
        noteheads_svg = Path(f"{musicxml_path.stem}_noteheads_universal.svg")
        stages.append(PipelineStage(
            name="noteheads_subtraction",
            description="Remove noteheads from full SVG score",
            command=[
                "python", "Separators/truly_universal_noteheads_subtractor.py",
                str(musicxml_path), str(svg_path)
            ],
            input_files=[musicxml_path, svg_path],
            output_files=[Path(f"{svg_path.stem}_without_noteheads.svg")],
            depends_on=["noteheads_extraction"],
            estimated_duration_seconds=8.0
        ))
        
        # Stage 3: Instrument Separation
        output_base = output_dir if output_dir else Path("noteheads_separated")
        stages.append(PipelineStage(
            name="instrument_separation",
            description="Separate instruments into individual SVG files",
            command=[
                "python", "Separators/xml_based_instrument_separator.py",
                str(musicxml_path), str(noteheads_svg), str(output_base)
            ],
            input_files=[musicxml_path, noteheads_svg],
            output_files=[output_base / "Flute" / "Flute_noteheads_only.svg",
                         output_base / "Violin" / "Violin_noteheads_only.svg"],
            depends_on=["noteheads_extraction"],
            estimated_duration_seconds=12.0
        ))
        
        # Stage 4: Staff/Barlines Extraction
        stages.append(PipelineStage(
            name="staff_barlines_extraction",
            description="Extract staff lines and barlines framework",
            command=[
                "python", "staff_barlines_extractor.py",
                str(musicxml_path), str(svg_path)
            ],
            input_files=[musicxml_path, svg_path],
            output_files=[Path(f"{svg_path.stem}_staff_barlines.svg")],
            estimated_duration_seconds=5.0
        ))
        
        return stages
    
    def _create_audio_pipeline_stages(self, midi_path: Path) -> List[PipelineStage]:
        """Create audio pipeline stages with master timing coordination"""
        stages = []
        
        # Stage 1: MIDI Note Separation
        notes_dir = Path(f"{midi_path.stem}_individual_notes")
        stages.append(PipelineStage(
            name="midi_note_separation",
            description="Split MIDI into individual note files",
            command=[
                "python", "Audio Separators/midi_note_separator.py",
                str(midi_path)
            ],
            input_files=[midi_path],
            output_files=[notes_dir],
            estimated_duration_seconds=15.0
        ))
        
        # Stage 2: MIDI to Audio Rendering (Fast)
        audio_dir = Path("Audio")
        stages.append(PipelineStage(
            name="midi_to_audio_rendering",
            description="Convert MIDI notes to audio files (optimized)",
            command=[
                "python", "Audio Separators/midi_to_audio_renderer_fast.py",
                str(notes_dir)
            ],
            input_files=[notes_dir],
            output_files=[audio_dir],
            depends_on=["midi_note_separation"],
            estimated_duration_seconds=45.0
        ))
        
        # Stage 3: Audio to Keyframes (Fast)
        keyframes_dir = audio_dir / "Keyframes"
        stages.append(PipelineStage(
            name="audio_to_keyframes",
            description="Generate After Effects keyframe data (optimized)",
            command=[
                "python", "Audio Separators/audio_to_keyframes_fast.py",
                str(audio_dir)
            ],
            input_files=[audio_dir],
            output_files=[keyframes_dir],
            depends_on=["midi_to_audio_rendering"],
            estimated_duration_seconds=20.0
        ))
        
        return stages
    
    def _execute_stages_sequentially(self, stages: List[PipelineStage]):
        """Execute a list of pipeline stages sequentially with dependency handling"""
        for stage in stages:
            self._execute_single_stage(stage)
            self.stages.append(stage)
    
    def _execute_single_stage(self, stage: PipelineStage):
        """Execute a single pipeline stage with error handling and timing"""
        if self.config.verbose:
            print(f"🔄 Executing: {stage.name}")
            print(f"   📝 {stage.description}")
            print(f"   💻 Command: {' '.join(stage.command)}")
        
        start_time = time.time()
        stage.status = "running"
        
        try:
            # Validate input files
            for input_file in stage.input_files:
                if not input_file.exists():
                    raise FileNotFoundError(f"Required input file not found: {input_file}")
            
            # Execute command
            result = subprocess.run(
                stage.command,
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
                timeout=300  # 5 minute timeout per stage
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Command failed with code {result.returncode}: {result.stderr}")
            
            # Validate output files (for file outputs, not directories)
            for output_file in stage.output_files:
                if not output_file.is_dir() and not output_file.exists():
                    self._log(f"⚠️  Expected output file not found: {output_file}")
            
            stage.actual_duration_seconds = time.time() - start_time
            stage.status = "completed"
            
            if self.config.verbose:
                print(f"   ✅ Completed in {stage.actual_duration_seconds:.1f}s")
                if stage.estimated_duration_seconds > 0:
                    ratio = stage.actual_duration_seconds / stage.estimated_duration_seconds
                    print(f"   📊 Performance: {ratio:.1f}x estimated time")
                print()
            
        except Exception as e:
            stage.status = "failed"
            stage.error_message = str(e)
            stage.actual_duration_seconds = time.time() - start_time
            
            if self.config.verbose:
                print(f"   ❌ Failed after {stage.actual_duration_seconds:.1f}s: {e}")
                print()
            
            raise RuntimeError(f"Stage '{stage.name}' failed: {e}")
    
    def _execute_tied_note_processing(self) -> List[TiedNoteAssignment]:
        """Execute tied note processing to handle visual-temporal mismatches"""
        if not self.context_analysis:
            raise ValueError("Context analysis required for tied note processing")
        
        self._log("🔗 Processing tied note relationships...")
        
        # Extract tied note groups from context analysis
        tied_groups_data = {}
        xml_notes = []
        
        # Convert synchronized notes back to required format
        for sync_note in self.context_analysis.synchronized_notes:
            xml_notes.append(sync_note.xml_note)
            if sync_note.tied_group_id:
                if sync_note.tied_group_id not in tied_groups_data:
                    tied_groups_data[sync_note.tied_group_id] = []
                tied_groups_data[sync_note.tied_group_id].append(sync_note.xml_note)
        
        # Create NoteMatch objects for matched notes
        note_matches = []
        for sync_note in self.context_analysis.synchronized_notes:
            if sync_note.midi_note:
                # Create a simplified NoteMatch for processing
                match = type('NoteMatch', (), {
                    'xml_note': sync_note.xml_note,
                    'midi_note': sync_note.midi_note,
                    'confidence': sync_note.match_confidence
                })()
                note_matches.append(match)
        
        # Extract tempo map from master timing
        tempo_map = self.master_timing.tempo_map if self.master_timing else [(0.0, 120.0)]
        
        # Initialize tied note processor
        processor = TiedNoteProcessor(
            beats_per_minute=tempo_map[0][1] if tempo_map else 120.0,
            verbose=self.config.verbose
        )
        
        # Process tied relationships
        assignments = processor.process_tied_relationships(
            xml_notes=xml_notes,
            tied_groups_data=tied_groups_data,
            note_matches=note_matches,
            tempo_map=tempo_map
        )
        
        # Save tied note assignments
        assignments_path = self.outputs_dir / "tied_note_assignments.json"
        processor.save_assignments_to_json(assignments_path)
        
        self._log(f"✅ Tied note processing complete: {len(assignments)} assignments")
        self._log(f"   💾 Saved to: {assignments_path}")
        
        return assignments
    
    def _generate_master_synchronization(
        self,
        tied_assignments: List[TiedNoteAssignment],
        output_dir: Optional[Path]
    ) -> Path:
        """Generate final master synchronization JSON for After Effects integration"""
        self._log("🎯 Generating master synchronization data...")
        
        # Collect all synchronized timing data
        synchronized_data = {
            'project_metadata': {
                'pipeline_mode': self.config.mode,
                'timing_tolerance_ms': self.config.timing_tolerance_ms,
                'execution_timestamp': time.time(),
                'total_execution_time_seconds': time.time() - self.start_time,
                'pipeline_version': '1.0.0'
            },
            'master_midi_timing': self.master_timing.to_dict() if self.master_timing else {},
            'context_analysis_summary': {
                'total_synchronized_notes': len(self.context_analysis.synchronized_notes) if self.context_analysis else 0,
                'timing_accuracy': self.context_analysis.timing_accuracy if self.context_analysis else {},
                'tied_note_analysis': self.context_analysis.tied_note_analysis if self.context_analysis else {},
                'svg_analysis_summary': {
                    'total_noteheads': self.context_analysis.svg_analysis.get('total_noteheads', 0) if self.context_analysis else 0,
                    'staff_structure': self.context_analysis.svg_analysis.get('staff_structure', {}) if self.context_analysis else {}
                }
            },
            'tied_note_assignments': [],
            'after_effects_data': {
                'composition_settings': {
                    'frame_rate': 30,
                    'duration_seconds': self.master_timing.total_duration_seconds if self.master_timing else 60.0,
                    'resolution': [1920, 1080]
                },
                'layer_timing': [],
                'keyframe_references': {}
            },
            'pipeline_execution': {
                'stages_completed': [stage.name for stage in self.stages if stage.status == "completed"],
                'stages_failed': [stage.name for stage in self.stages if stage.status == "failed"],
                'total_stages': len(self.stages),
                'execution_mode': self.config.mode,
                'performance_summary': self._calculate_performance_metrics()
            }
        }
        
        # Add tied note assignments data
        for assignment in tied_assignments:
            assignment_data = {
                'note_id': f"{assignment.note.part_id}_{assignment.note.measure_number}_{assignment.note.pitch}",
                'pitch': assignment.note.pitch,
                'measure': assignment.note.measure_number,
                'part_id': assignment.note.part_id,
                'start_time_seconds': assignment.calculated_start_time,
                'master_start_time_seconds': assignment.master_start_time,
                'is_primary_note': assignment.is_primary,
                'tied_group_id': assignment.tied_group_id,
                'timing_confidence': assignment.timing_confidence,
                'timing_source': 'midi_exact' if assignment.is_primary else 'calculated_approximation',
                'position_in_tied_group': assignment.position_in_group
            }
            synchronized_data['tied_note_assignments'].append(assignment_data)
        
        # Generate After Effects layer timing data
        for assignment in tied_assignments:
            layer_data = {
                'layer_name': f"{assignment.note.part_id}_{assignment.note.pitch}_M{assignment.note.measure_number}",
                'start_time': assignment.calculated_start_time,
                'in_point': assignment.calculated_start_time,
                'out_point': assignment.calculated_start_time + 2.0,  # Default 2-second duration
                'instrument': assignment.note.part_id,
                'pitch': assignment.note.pitch,
                'is_tied_note': not assignment.is_primary,
                'keyframe_file': f"Audio/Keyframes/{assignment.note.part_id}_{assignment.note.pitch}_keyframes.json"
            }
            synchronized_data['after_effects_data']['layer_timing'].append(layer_data)
        
        # Save master synchronization data
        output_path = self.outputs_dir / "master_synchronization.json"
        if output_dir:
            output_path = output_dir / "master_synchronization.json"
        
        with open(output_path, 'w') as f:
            json.dump(synchronized_data, f, indent=2)
        
        self._log(f"✅ Master synchronization generated")
        self._log(f"   💾 Saved to: {output_path}")
        self._log(f"   🎵 Total synchronized notes: {len(tied_assignments)}")
        self._log(f"   ⏱️  Timeline duration: {synchronized_data['after_effects_data']['composition_settings']['duration_seconds']:.1f}s")
        
        return output_path
    
    def _generate_execution_summary(self) -> Dict:
        """Generate comprehensive execution summary"""
        completed_stages = [s for s in self.stages if s.status == "completed"]
        failed_stages = [s for s in self.stages if s.status == "failed"]
        
        return {
            'total_stages': len(self.stages),
            'completed_stages': len(completed_stages),
            'failed_stages': len(failed_stages),
            'success_rate': len(completed_stages) / len(self.stages) if self.stages else 0,
            'total_execution_time': time.time() - self.start_time,
            'execution_mode': self.config.mode,
            'timing_preservation': 'master_midi_authoritative',
            'tied_note_handling': 'visual_temporal_mismatch_processed',
            'pipeline_merge_strategy': 'end_merge_with_master_timing',
            'stage_details': [
                {
                    'name': stage.name,
                    'status': stage.status,
                    'duration': stage.actual_duration_seconds,
                    'estimated_vs_actual': (
                        stage.actual_duration_seconds / stage.estimated_duration_seconds
                        if stage.estimated_duration_seconds > 0 else None
                    )
                }
                for stage in self.stages
            ]
        }
    
    def _calculate_performance_metrics(self) -> Dict:
        """Calculate detailed performance metrics"""
        if not self.stages:
            return {}
        
        completed_stages = [s for s in self.stages if s.status == "completed"]
        
        if not completed_stages:
            return {'no_completed_stages': True}
        
        total_actual_time = sum(s.actual_duration_seconds for s in completed_stages)
        total_estimated_time = sum(s.estimated_duration_seconds for s in completed_stages if s.estimated_duration_seconds > 0)
        
        symbolic_stages = [s for s in completed_stages if 'noteheads' in s.name or 'instrument' in s.name or 'staff' in s.name]
        audio_stages = [s for s in completed_stages if 'midi' in s.name or 'audio' in s.name or 'keyframes' in s.name]
        
        return {
            'total_pipeline_time': time.time() - self.start_time,
            'total_stage_time': total_actual_time,
            'overhead_time': (time.time() - self.start_time) - total_actual_time,
            'performance_ratio': total_actual_time / total_estimated_time if total_estimated_time > 0 else None,
            'symbolic_pipeline_time': sum(s.actual_duration_seconds for s in symbolic_stages),
            'audio_pipeline_time': sum(s.actual_duration_seconds for s in audio_stages),
            'average_stage_time': total_actual_time / len(completed_stages),
            'slowest_stage': max(completed_stages, key=lambda s: s.actual_duration_seconds).name,
            'fastest_stage': min(completed_stages, key=lambda s: s.actual_duration_seconds).name,
            'parallel_efficiency': (
                max(
                    sum(s.actual_duration_seconds for s in symbolic_stages),
                    sum(s.actual_duration_seconds for s in audio_stages)
                ) / total_actual_time
                if self.config.mode == "parallel" and total_actual_time > 0 else None
            )
        }
    
    def _display_completion_summary(self, execution: PipelineExecution):
        """Display comprehensive completion summary"""
        print("🎯 SYNCHRONIZED MUSIC ANIMATION PIPELINE COMPLETE!")
        print("=" * 60)
        print()
        
        print("📊 EXECUTION SUMMARY:")
        print("-" * 30)
        summary = execution.execution_summary
        print(f"✅ Stages completed: {summary['completed_stages']}/{summary['total_stages']}")
        print(f"🎯 Success rate: {summary['success_rate']:.1%}")
        print(f"⏱️  Total execution time: {summary['total_execution_time']:.1f}s")
        print(f"🚀 Execution mode: {summary['execution_mode']}")
        print()
        
        print("📈 PERFORMANCE METRICS:")
        print("-" * 30)
        metrics = execution.performance_metrics
        if 'total_pipeline_time' in metrics:
            print(f"⏱️  Pipeline time: {metrics['total_pipeline_time']:.1f}s")
            print(f"🔧 Stage time: {metrics['total_stage_time']:.1f}s")
            print(f"💾 Overhead time: {metrics['overhead_time']:.1f}s")
            if metrics.get('performance_ratio'):
                print(f"📊 Performance vs estimate: {metrics['performance_ratio']:.1f}x")
            if metrics.get('parallel_efficiency'):
                print(f"🔄 Parallel efficiency: {metrics['parallel_efficiency']:.1%}")
        print()
        
        print("🎵 SYNCHRONIZATION RESULTS:")
        print("-" * 30)
        if execution.context_analysis:
            timing_acc = execution.context_analysis.timing_accuracy
            print(f"🎼 Total synchronized notes: {len(execution.context_analysis.synchronized_notes)}")
            print(f"🎯 Match rate: {timing_acc['match_rate']:.1%}")
            print(f"📈 Average confidence: {timing_acc['average_confidence']:.3f}")
            print(f"⏱️  Average timing error: {timing_acc['average_timing_error_ms']:.1f}ms")
            
            tied_analysis = execution.context_analysis.tied_note_analysis
            print(f"🔗 Tied groups processed: {tied_analysis['total_tied_groups']}")
            print(f"🎵 Tied notes handled: {tied_analysis['total_tied_notes']}")
        print()
        
        print("📁 OUTPUT FILES:")
        print("-" * 30)
        print(f"🎯 Master synchronization: {execution.final_synchronization_path}")
        print(f"📊 Context analysis: {self.outputs_dir / 'master_relationship.json'}")
        print(f"🔗 Tied note assignments: {self.outputs_dir / 'tied_note_assignments.json'}")
        print()
        
        print("🚀 AFTER EFFECTS INTEGRATION:")
        print("-" * 30)
        print(f"✅ Master timing preserved from original MIDI")
        print(f"✅ Visual-temporal mismatches handled (tied notes)")
        print(f"✅ Universal coordinate system maintained")
        print(f"✅ Frame-accurate synchronization data generated")
        print(f"✅ Ready for After Effects import")
        print()
        
        print(f"🎯 SUCCESS! Synchronized music animation pipeline complete")
        print(f"   Use {execution.final_synchronization_path} for After Effects integration")
    
    def _log(self, message: str):
        """Add message to execution log with timestamp"""
        timestamp = time.time() - self.start_time
        log_entry = f"[{timestamp:6.1f}s] {message}"
        self.execution_log.append(log_entry)
        
        if self.config.verbose:
            print(log_entry)


def create_default_config(mode: str = "sequential") -> PipelineConfig:
    """Create default pipeline configuration"""
    return PipelineConfig(
        mode=mode,
        preserve_outputs=True,
        timing_tolerance_ms=100.0,
        parallel_workers=4,
        verbose=True,
        performance_tracking=True,
        backup_existing=True
    )


def main():
    """CLI interface for synchronization coordinator"""
    parser = argparse.ArgumentParser(
        description="Synchronization Coordinator - Master Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sequential execution (symbolic separators first)
  python synchronization_coordinator.py sequential "Base/SS 9.musicxml" "Base/Saint-Saens Trio No 2.mid" "Base/SS 9 full.svg"
  
  # Parallel execution (both pipelines simultaneously)
  python synchronization_coordinator.py parallel "Base/SS 9.musicxml" "Base/Saint-Saens Trio No 2.mid" "Base/SS 9 full.svg"
  
  # With custom output directory
  python synchronization_coordinator.py sequential "Base/SS 9.musicxml" "Base/Saint-Saens Trio No 2.mid" "Base/SS 9 full.svg" --output-dir "my_output"
  
  # With custom timing tolerance
  python synchronization_coordinator.py parallel "Base/SS 9.musicxml" "Base/Saint-Saens Trio No 2.mid" "Base/SS 9 full.svg" --tolerance 50
        """
    )
    
    parser.add_argument(
        "mode",
        choices=["sequential", "parallel"],
        help="Pipeline execution mode"
    )
    parser.add_argument(
        "musicxml_file",
        help="Path to MusicXML score file"
    )
    parser.add_argument(
        "midi_file", 
        help="Path to master MIDI file (before note separation)"
    )
    parser.add_argument(
        "svg_file",
        help="Path to complete SVG score file"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        help="Custom output directory for results"
    )
    parser.add_argument(
        "--tolerance", "-t",
        type=float,
        default=100.0,
        help="MIDI timing tolerance in milliseconds (default: 100ms)"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (minimal output)"
    )
    parser.add_argument(
        "--no-preserve",
        action="store_true",
        help="Don't preserve existing pipeline outputs"
    )
    
    args = parser.parse_args()
    
    # Validate input files
    input_files = [
        (args.musicxml_file, "MusicXML"),
        (args.midi_file, "MIDI"),
        (args.svg_file, "SVG")
    ]
    
    for file_path, file_type in input_files:
        if not os.path.exists(file_path):
            print(f"❌ ERROR: {file_type} file not found: {file_path}")
            sys.exit(1)
    
    try:
        # Create pipeline configuration
        config = PipelineConfig(
            mode=args.mode,
            preserve_outputs=not args.no_preserve,
            timing_tolerance_ms=args.tolerance,
            parallel_workers=args.workers,
            verbose=not args.quiet,
            performance_tracking=True,
            backup_existing=True
        )
        
        # Initialize coordinator
        coordinator = SynchronizationCoordinator(config)
        
        # Execute full pipeline
        execution_result = coordinator.orchestrate_full_pipeline(
            musicxml_path=Path(args.musicxml_file),
            midi_path=Path(args.midi_file),
            svg_path=Path(args.svg_file),
            output_dir=Path(args.output_dir) if args.output_dir else None
        )
        
        # Final success message
        if not args.quiet:
            print(f"\n🎯 PIPELINE EXECUTION SUCCESSFUL!")
            print(f"📁 Master synchronization file: {execution_result.final_synchronization_path}")
            print(f"⏱️  Total execution time: {execution_result.total_duration_seconds:.1f}s")
            print(f"🚀 Ready for After Effects integration")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Pipeline execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ PIPELINE EXECUTION FAILED: {e}")
        if not args.quiet:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()