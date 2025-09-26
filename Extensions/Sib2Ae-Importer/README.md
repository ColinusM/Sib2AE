# Sib2Ae Importer Extension

A CEP extension for importing Sib2Ae pipeline results directly into After Effects.

## Features

- **Browse & Preview**: Select pipeline output folders and preview files before import
- **Selective Import**: Choose which file types to import (SVG, Audio, JSON)
- **Auto-Composition**: Automatically create compositions and organize imported assets
- **Real-time Status**: Live feedback during import process
- **Theme Integration**: Matches After Effects UI theme

## Installation

### Method 1: Development Installation

1. Copy the entire `Sib2Ae-Importer` folder to your CEP extensions directory:

   **macOS:**
   ```
   /Library/Application Support/Adobe/CEP/extensions/
   ```

   **Windows:**
   ```
   C:\Program Files (x86)\Common Files\Adobe\CEP\extensions\
   ```

2. Enable debug mode for unsigned extensions:

   **macOS:**
   ```bash
   defaults write com.adobe.CSXS.12 PlayerDebugMode 1
   ```

   **Windows (Registry):**
   ```
   [HKEY_CURRENT_USER\Software\Adobe\CSXS.12]
   "PlayerDebugMode"="1"
   ```

3. Restart After Effects

4. Access the extension via: **Window > Extensions > Sib2Ae Importer**

### Method 2: ZXP Package (Future)

1. Package the extension as .zxp using ZXPSignCmd
2. Install using Adobe Extension Manager or ZXP Installer

## Usage

### Basic Import Workflow

1. **Select Pipeline Folder**: Click "Browse" to select your Sib2Ae pipeline output folder
2. **Preview Files**: Review the detected SVG, audio, and JSON files
3. **Configure Options**:
   - ✅ Import Symbolic Elements (SVG files)
   - ✅ Import Audio Files (WAV, MP3, AIFF)
   - ✅ Import Keyframe Data (JSON)
   - ☐ Create New Composition
4. **Import**: Click "Import Files" to begin the process
5. **Monitor Progress**: Watch the status log for real-time feedback

### Supported Pipeline Outputs

The extension automatically detects and imports:

- **SVG Files**: Individual noteheads, instrument parts, staff elements
- **Audio Files**: Individual note recordings (.wav, .mp3, .aiff)
- **JSON Files**: Keyframe data, coordination metadata
- **Folder Structure**: Maintains organization from pipeline output

### Expected Folder Structure

```
Pipeline_Output/
├── instruments_output/
│   ├── Flûte_P1.svg
│   └── Violon_P2.svg
├── Audio/
│   ├── Flûte/
│   │   ├── note_000_Flûte_A4_vel76.wav
│   │   └── note_001_Flûte_G4_vel76.wav
│   └── Violon/
│       ├── note_002_Violon_B3_vel65.wav
│       └── note_003_Violon_A3_vel66.wav
├── universal_output/
│   ├── coordination_metadata.json
│   └── universal_notes_registry.json
└── symbolic_output/
    └── individual_noteheads/
```

## Extension Architecture

### Files Structure

```
Sib2Ae-Importer/
├── CSXS/
│   └── manifest.xml          # Extension configuration
├── client/
│   ├── index.html           # UI interface
│   ├── styles.css           # Styling
│   ├── main.js              # Client-side logic
│   └── CSInterface.js       # Adobe CEP library
├── jsx/
│   └── main.jsx             # ExtendScript functions
└── README.md
```

### Key Functions

**ExtendScript (jsx/main.jsx):**
- `browsePipelineFolder()` - Folder selection dialog
- `scanPipelineFiles()` - Recursive file discovery
- `importSVGFiles()` - SVG asset import
- `importAudioFiles()` - Audio asset import
- `createSib2aeComposition()` - Composition creation

**Client-side (client/main.js):**
- UI event handling
- File preview generation
- Import process orchestration
- Status logging and feedback

## Customization

### Adding New File Types

1. **ExtendScript**: Extend `scanFolderRecursive()` to detect new extensions
2. **Import Function**: Create new import function in `main.jsx`
3. **UI**: Add checkbox option in `index.html`
4. **Logic**: Integrate import call in `main.js`

### Keyframe Data Processing

Current implementation provides basic JSON file import. Extend `applyKeyframeData()` to:

- Parse specific JSON schemas
- Apply keyframes to layer properties
- Synchronize timing with audio

### Custom Composition Settings

Modify `createSib2aeComposition()` parameters:

```javascript
var comp = app.project.items.addComp(
    name,
    1920, // width - customize for your output format
    1080, // height
    1.0,  // pixel aspect ratio
    30,   // duration in seconds
    30    // frame rate - match your pipeline settings
);
```

## Troubleshooting

### Extension Not Appearing

1. Verify files are in correct CEP extensions directory
2. Check debug mode is enabled: `PlayerDebugMode = 1`
3. Restart After Effects completely
4. Check After Effects version compatibility (25.0+)

### Import Failures

1. **File Permissions**: Ensure read access to pipeline output folder
2. **File Paths**: Avoid special characters in folder names
3. **File Formats**: Verify SVG and audio files are not corrupted
4. **JSON Syntax**: Check JSON files for valid syntax

### Performance Issues

1. **Large File Sets**: Import in smaller batches
2. **Memory**: Close unnecessary After Effects projects
3. **Network Drives**: Copy files locally before import

## Development

### Requirements

- After Effects 2025 (25.0+)
- CEP 12 runtime
- ExtendScript knowledge for AE API

### Testing

1. Enable CEP debug mode
2. Use browser developer tools for client-side debugging
3. Use ExtendScript Toolkit for jsx debugging (legacy)
4. Check After Effects console for errors

### Building for Distribution

1. Package as .zxp using Adobe tools
2. Code sign for production deployment
3. Test across different AE versions
4. Validate with various pipeline outputs

## Compatibility

- **After Effects**: 25.0+ (2025)
- **CEP**: 12.0+
- **Platforms**: macOS, Windows
- **Pipeline Outputs**: Sib2Ae symbolic and audio pipeline results

## License

Compatible with Sib2Ae project licensing.

## Support

For issues related to:
- **Extension functionality**: Check this README and troubleshooting
- **Pipeline integration**: Refer to main Sib2Ae documentation
- **After Effects API**: Consult Adobe ExtendScript documentation