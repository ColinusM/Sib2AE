#!/usr/bin/env python3
"""
Test script for MIDI Matcher functionality

This script demonstrates and validates the MIDI matching engine using
the existing master timing data and simulated MusicXML notes.
"""

import json
from pathlib import Path
from Synchronizer.utils.midi_matcher import (
    MIDIMatcher, 
    MIDINote, 
    MusicXMLNote, 
    create_midi_notes_from_master_timing
)


def create_test_xml_notes() -> list:
    """Create simulated MusicXML notes for testing"""
    test_xml_notes = [
        MusicXMLNote(
            pitch="B3", duration=480, beat_position=1.0, measure_number=4,
            part_id="Violon", voice=1, tie_type=None, tied_group_id=None,
            onset_time=6.0  # Should match first MIDI note
        ),
        MusicXMLNote(
            pitch="A4", duration=480, beat_position=1.0, measure_number=5,
            part_id="Flûte", voice=1, tie_type=None, tied_group_id=None,
            onset_time=7.5  # Should match second MIDI note
        ),
        MusicXMLNote(
            pitch="G4", duration=480, beat_position=1.5, measure_number=5,
            part_id="Flûte", voice=1, tie_type=None, tied_group_id=None,
            onset_time=8.25  # Should match third MIDI note
        ),
        MusicXMLNote(
            pitch="C4", duration=480, beat_position=1.0, measure_number=6,
            part_id="Violon", voice=1, tie_type=None, tied_group_id=None,
            onset_time=10.0  # Timing mismatch test (no exact MIDI match)
        ),
        MusicXMLNote(
            pitch="F4", duration=480, beat_position=1.0, measure_number=7,
            part_id="Test", voice=1, tie_type=None, tied_group_id=None,
            onset_time=15.0  # Pitch mismatch test
        )
    ]
    return test_xml_notes


def test_exact_matching():
    """Test matching with exact timing and pitch"""
    print("🧪 TEST 1: Exact Matching")
    print("=" * 40)
    
    # Load master timing data
    timing_file = Path("Base/Saint-Saens Trio No 2_master_timing.json")
    with open(timing_file, 'r') as f:
        timing_data = json.load(f)
    
    # Create MIDI notes and test XML notes
    midi_notes = create_midi_notes_from_master_timing(timing_data)
    xml_notes = create_test_xml_notes()
    
    # Initialize matcher with tight tolerance for exact matching
    matcher = MIDIMatcher(tolerance_ms=50.0, strict_pitch=True)
    
    # Perform matching
    matches = matcher.match_notes_with_tolerance(xml_notes, midi_notes, min_confidence=0.8)
    
    # Validate results
    print(f"Expected exact matches: 3")
    print(f"Actual matches: {len(matches)}")
    
    for match in matches:
        print(f"✅ {match.xml_note.pitch} @ {match.xml_note.onset_time:.3f}s → "
              f"{match.midi_note.pitch_name} @ {match.midi_note.start_time:.3f}s "
              f"(confidence: {match.confidence:.3f}, type: {match.match_type})")
    
    return len(matches) >= 3


def test_tolerance_matching():
    """Test matching with timing tolerance"""
    print("\n🧪 TEST 2: Tolerance Matching")
    print("=" * 40)
    
    # Load master timing data
    timing_file = Path("Base/Saint-Saens Trio No 2_master_timing.json")
    with open(timing_file, 'r') as f:
        timing_data = json.load(f)
    
    midi_notes = create_midi_notes_from_master_timing(timing_data)
    
    # Create XML notes with slight timing offsets
    offset_xml_notes = [
        MusicXMLNote(
            pitch="B3", duration=480, beat_position=1.0, measure_number=4,
            part_id="Violon", voice=1, tie_type=None, tied_group_id=None,
            onset_time=6.08  # 80ms offset from 6.0s
        ),
        MusicXMLNote(
            pitch="A4", duration=480, beat_position=1.0, measure_number=5,
            part_id="Flûte", voice=1, tie_type=None, tied_group_id=None,
            onset_time=7.55  # 50ms offset from 7.5s
        )
    ]
    
    # Test with 100ms tolerance
    matcher = MIDIMatcher(tolerance_ms=100.0, strict_pitch=True)
    matches = matcher.match_notes_with_tolerance(offset_xml_notes, midi_notes, min_confidence=0.5)
    
    print(f"Expected tolerance matches: 2")
    print(f"Actual matches: {len(matches)}")
    
    for match in matches:
        print(f"✅ {match.xml_note.pitch} @ {match.xml_note.onset_time:.3f}s → "
              f"{match.midi_note.pitch_name} @ {match.midi_note.start_time:.3f}s "
              f"(error: {match.time_difference*1000:.1f}ms, confidence: {match.confidence:.3f})")
    
    return len(matches) >= 2


def test_confidence_scoring():
    """Test confidence scoring system"""
    print("\n🧪 TEST 3: Confidence Scoring")
    print("=" * 40)
    
    # Load master timing data
    timing_file = Path("Base/Saint-Saens Trio No 2_master_timing.json")
    with open(timing_file, 'r') as f:
        timing_data = json.load(f)
    
    midi_notes = create_midi_notes_from_master_timing(timing_data)
    
    # Create XML notes with varying match quality
    varied_xml_notes = [
        # Perfect match
        MusicXMLNote(
            pitch="B3", duration=480, beat_position=1.0, measure_number=4,
            part_id="Violon", voice=1, tie_type=None, tied_group_id=None,
            onset_time=6.0
        ),
        # Good match with slight timing offset
        MusicXMLNote(
            pitch="A4", duration=480, beat_position=1.0, measure_number=5,
            part_id="Flûte", voice=1, tie_type=None, tied_group_id=None,
            onset_time=7.53  # 30ms offset
        ),
        # Poor match with large timing offset
        MusicXMLNote(
            pitch="G4", duration=480, beat_position=1.0, measure_number=5,
            part_id="Flûte", voice=1, tie_type=None, tied_group_id=None,
            onset_time=8.35  # 100ms offset (at tolerance limit)
        )
    ]
    
    matcher = MIDIMatcher(tolerance_ms=100.0, strict_pitch=True)
    matches = matcher.match_notes_with_tolerance(varied_xml_notes, midi_notes, min_confidence=0.3)
    
    print(f"Expected varied confidence matches: 3")
    print(f"Actual matches: {len(matches)}")
    
    # Sort by confidence for analysis
    matches.sort(key=lambda x: x.confidence, reverse=True)
    
    for i, match in enumerate(matches):
        quality = "Excellent" if match.confidence > 0.9 else "Good" if match.confidence > 0.7 else "Fair"
        print(f"  {i+1}. {match.xml_note.pitch}: {quality} match (confidence: {match.confidence:.3f})")
    
    # Validate confidence ordering
    confidence_decreasing = all(
        matches[i].confidence >= matches[i+1].confidence 
        for i in range(len(matches)-1)
    )
    
    return len(matches) >= 3 and confidence_decreasing


def test_statistics_and_output():
    """Test statistics generation and JSON output"""
    print("\n🧪 TEST 4: Statistics and Output")
    print("=" * 40)
    
    # Load master timing data
    timing_file = Path("Base/Saint-Saens Trio No 2_master_timing.json")
    with open(timing_file, 'r') as f:
        timing_data = json.load(f)
    
    midi_notes = create_midi_notes_from_master_timing(timing_data)
    xml_notes = create_test_xml_notes()
    
    matcher = MIDIMatcher(tolerance_ms=100.0, strict_pitch=True)
    matches = matcher.match_notes_with_tolerance(xml_notes, midi_notes, min_confidence=0.5)
    
    # Generate statistics
    stats = matcher.get_match_statistics(matches)
    
    print("📊 Generated Statistics:")
    print(f"  Total matches: {stats['total_matches']}")
    print(f"  Average confidence: {stats['average_confidence']:.3f}")
    print(f"  Average timing error: {stats['average_timing_error_ms']:.1f}ms")
    print(f"  Pitch accuracy: {stats['pitch_accuracy']:.1%}")
    
    # Test JSON output
    output_path = Path("Synchronizer/outputs/test_matches.json")
    matcher.save_matches_to_json(matches, output_path)
    
    # Verify JSON file was created and is valid
    if output_path.exists():
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        print(f"✅ JSON output saved and verified: {output_path}")
        return True
    else:
        print(f"❌ JSON output failed")
        return False


def main():
    """Run all MIDI matcher tests"""
    print("🎯 MIDI MATCHER COMPREHENSIVE TEST SUITE")
    print("=" * 50)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Exact Matching", test_exact_matching()))
    test_results.append(("Tolerance Matching", test_tolerance_matching()))
    test_results.append(("Confidence Scoring", test_confidence_scoring()))
    test_results.append(("Statistics & Output", test_statistics_and_output()))
    
    # Summary
    print("\n📋 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MIDI Matcher is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check implementation.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)