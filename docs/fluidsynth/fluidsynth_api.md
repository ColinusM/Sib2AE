# FluidSynth API Reference for Sib2Ae

Essential FluidSynth functionality for instrument-specific audio generation.

## Core Functions

### Program Selection
```c
// Select instrument by SoundFont ID, bank, and program
int fluid_synth_program_select(fluid_synth_t* synth, int chan, int sfont_id, int bank_num, int preset_num);

// Send program change on MIDI channel
int fluid_synth_program_change(fluid_synth_t* synth, int chan, int program);

// Set bank number before program change
int fluid_synth_bank_select(fluid_synth_t* synth, int chan, int bank);
```

### Note Control
```c
// Play note
int fluid_synth_noteon(fluid_synth_t* synth, int chan, int key, int vel);

// Stop note
int fluid_synth_noteoff(fluid_synth_t* synth, int chan, int key);
```

### SoundFont Management
```c
// Load SoundFont
int fluid_synth_sfload(fluid_synth_t* synth, const char* filename, int reset_presets);

// Unload SoundFont
int fluid_synth_sfunload(fluid_synth_t* synth, int id, int reset_presets);
```

## Command Line Usage

### Basic Instrument Selection
```bash
# Single instrument
fluidsynth -ni soundfont.sf2 --prog 0 74 midifile.mid

# Multiple instruments on different channels
fluidsynth -ni soundfont.sf2 \
  --prog 0 74 \
  --prog 1 41 \
  --prog 2 1 \
  midifile.mid
```

### Channel Configuration
```bash
# Channel assignment examples
--prog 0 74    # Channel 0: Flute
--prog 1 41    # Channel 1: Violin
--prog 2 1     # Channel 2: Piano
--prog 3 42    # Channel 3: Viola
```

### Audio Output Options
```bash
# Render to file with specific settings
fluidsynth -ni soundfont.sf2 \
  midifile.mid \
  -F output.wav \
  -r 22050 \
  -g 0.5
```

## Instrument Detection Strategy

### 1. MIDI Channel Mapping
- Each instrument gets its own MIDI channel
- Program change message sets instrument per channel
- Maintains separation between instruments

### 2. File-based Detection
```python
def detect_instrument_from_filename(filename):
    """Extract instrument name from MIDI filename."""
    # Example: "note_001_Flûte_G4_vel76.mid"
    parts = filename.split('_')
    if len(parts) >= 3:
        return parts[2]  # "Flûte"
    return "Piano"  # Default fallback
```

### 3. Instrument-to-Program Mapping
```python
INSTRUMENT_PROGRAM_MAP = {
    "Flûte": 74,        # Flute
    "Violon": 41,       # Violin
    "Piano": 1,         # Acoustic Grand Piano
    "Viola": 42,        # Viola
    "Cello": 43,        # Cello
    "Contrebasse": 44,  # Contrabass
    "Clarinette": 72,   # Clarinet
    "Trompette": 57,    # Trumpet
    "Trombone": 58,     # Trombone
}
```

## Implementation for Sib2Ae

### Enhanced MIDI Rendering
```python
def render_midi_with_instrument(midi_file, output_file, soundfont, instrument_name):
    """Render MIDI with specific instrument program."""

    # Get program number for instrument
    program = INSTRUMENT_PROGRAM_MAP.get(instrument_name, 1)  # Default to piano

    # Build FluidSynth command
    cmd = [
        "fluidsynth", "-ni",
        soundfont,
        "--prog", "0", str(program),  # Set program on channel 0
        midi_file,
        "-F", output_file,
        "-r", "22050",
        "-g", "0.5"
    ]

    return subprocess.run(cmd, capture_output=True, text=True)
```

### Multi-Instrument Support
```python
def render_multi_instrument_midi(midi_files, output_file, soundfont):
    """Render multiple instruments to single audio file."""

    cmd = ["fluidsynth", "-ni", soundfont]

    # Add program changes for each instrument
    for channel, (midi_file, instrument) in enumerate(midi_files):
        program = INSTRUMENT_PROGRAM_MAP.get(instrument, 1)
        cmd.extend(["--prog", str(channel), str(program)])

    # Add all MIDI files
    cmd.extend([mf[0] for mf in midi_files])

    # Output settings
    cmd.extend(["-F", output_file, "-r", "22050", "-g", "0.5"])

    return subprocess.run(cmd, capture_output=True, text=True)
```

## Error Handling

### Common Issues
1. **Invalid Program Number**: Use default (Piano = 1)
2. **Missing SoundFont**: Fallback to system default
3. **Channel Overflow**: Wrap around 16 MIDI channels

### Validation
```python
def validate_program_number(program):
    """Ensure program number is valid (1-128)."""
    return max(1, min(128, program))

def validate_channel(channel):
    """Ensure channel is valid (0-15)."""
    return channel % 16
```

## Performance Considerations

### Channel Efficiency
- Use dedicated channels for each instrument
- Avoid channel conflicts in multi-instrument scenarios
- Reset programs when switching SoundFonts

### Memory Management
- Load SoundFonts once, reuse for multiple renderings
- Unload unused SoundFonts to free memory
- Use smaller SoundFonts for development/testing

## Integration Points

### With MIDI Note Separator
- Extract instrument name from track metadata
- Preserve instrument information in output filenames
- Maintain channel assignments across note separation

### With Audio Renderer
- Auto-detect instrument from filename
- Apply appropriate program change
- Generate instrument-specific audio characteristics

### With Keyframe Generator
- Inherit instrument characteristics in analysis
- Apply instrument-specific frequency ranges
- Customize animation parameters per instrument type

## References

- [FluidSynth API Documentation](https://www.fluidsynth.org/api/)
- [MIDI Channel Messages](https://www.fluidsynth.org/api/group__midi__messages.html)
- [SoundFont Management](https://www.fluidsynth.org/api/LoadingSoundfonts.html)