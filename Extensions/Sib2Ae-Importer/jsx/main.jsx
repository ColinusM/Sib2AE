// Sib2Ae Importer ExtendScript Functions
// Main script for importing pipeline results into After Effects

// Global variables
var sib2ae = {
    projectPath: "",
    importedFiles: [],
    composition: null
};

/**
 * Browse for folder containing Sib2Ae pipeline outputs
 */
function browsePipelineFolder() {
    try {
        var folder = Folder.selectDialog("Select Sib2Ae Pipeline Output Folder");
        if (folder) {
            return folder.fsName;
        }
        return null;
    } catch (error) {
        return "Error: " + error.message;
    }
}

/**
 * Scan folder for Sib2Ae pipeline files
 */
function scanPipelineFiles(folderPath) {
    try {
        var folder = new Folder(folderPath);
        if (!folder.exists) {
            return "Error: Folder does not exist";
        }

        var files = {
            svg: [],
            audio: [],
            json: [],
            other: []
        };

        // Scan main folder and subfolders
        scanFolderRecursive(folder, files);

        return JSON.stringify(files);
    } catch (error) {
        return "Error: " + error.message;
    }
}

/**
 * Recursively scan folders for files
 */
function scanFolderRecursive(folder, files) {
    var folderContents = folder.getFiles();

    for (var i = 0; i < folderContents.length; i++) {
        var item = folderContents[i];

        if (item instanceof Folder) {
            // Recursively scan subfolders
            scanFolderRecursive(item, files);
        } else if (item instanceof File) {
            var fileName = item.name.toLowerCase();
            var relativePath = item.fsName.replace(folder.parent.fsName, "");

            if (fileName.match(/\.svg$/)) {
                files.svg.push({
                    name: item.name,
                    path: item.fsName,
                    relativePath: relativePath
                });
            } else if (fileName.match(/\.(wav|mp3|aiff|aif)$/)) {
                files.audio.push({
                    name: item.name,
                    path: item.fsName,
                    relativePath: relativePath
                });
            } else if (fileName.match(/\.json$/)) {
                files.json.push({
                    name: item.name,
                    path: item.fsName,
                    relativePath: relativePath
                });
            } else {
                files.other.push({
                    name: item.name,
                    path: item.fsName,
                    relativePath: relativePath
                });
            }
        }
    }
}

/**
 * Create a new composition for Sib2Ae imports
 */
function createSib2aeComposition(name) {
    try {
        if (!name) {
            name = "Sib2Ae_Import_" + new Date().getTime();
        }

        var comp = app.project.items.addComp(
            name,
            1920, // width
            1080, // height
            1.0,  // pixel aspect ratio
            30,   // duration in seconds
            30    // frame rate
        );

        sib2ae.composition = comp;
        return "Success: Created composition '" + name + "'";
    } catch (error) {
        return "Error: " + error.message;
    }
}

/**
 * Import SVG files into After Effects
 */
function importSVGFiles(svgFiles) {
    try {
        var imported = [];
        var errors = [];

        for (var i = 0; i < svgFiles.length; i++) {
            try {
                var file = new File(svgFiles[i].path);
                if (file.exists) {
                    var importOptions = new ImportOptions(file);
                    var footageItem = app.project.importFile(importOptions);

                    if (footageItem) {
                        imported.push({
                            name: svgFiles[i].name,
                            item: footageItem
                        });

                        // Add to composition if one exists
                        if (sib2ae.composition) {
                            var layer = sib2ae.composition.layers.add(footageItem);
                            layer.name = svgFiles[i].name.replace(/\.svg$/i, "");
                        }
                    }
                }
            } catch (fileError) {
                errors.push("Failed to import " + svgFiles[i].name + ": " + fileError.message);
            }
        }

        var result = {
            imported: imported.length,
            errors: errors
        };

        return JSON.stringify(result);
    } catch (error) {
        return "Error: " + error.message;
    }
}

/**
 * Import audio files into After Effects
 */
function importAudioFiles(audioFiles) {
    try {
        var imported = [];
        var errors = [];

        for (var i = 0; i < audioFiles.length; i++) {
            try {
                var file = new File(audioFiles[i].path);
                if (file.exists) {
                    var importOptions = new ImportOptions(file);
                    var footageItem = app.project.importFile(importOptions);

                    if (footageItem) {
                        imported.push({
                            name: audioFiles[i].name,
                            item: footageItem
                        });

                        // Add to composition if one exists
                        if (sib2ae.composition) {
                            var layer = sib2ae.composition.layers.add(footageItem);
                            layer.name = audioFiles[i].name.replace(/\.(wav|mp3|aiff|aif)$/i, "");
                        }
                    }
                }
            } catch (fileError) {
                errors.push("Failed to import " + audioFiles[i].name + ": " + fileError.message);
            }
        }

        var result = {
            imported: imported.length,
            errors: errors
        };

        return JSON.stringify(result);
    } catch (error) {
        return "Error: " + error.message;
    }
}

/**
 * Apply keyframe data from JSON files
 */
function applyKeyframeData(jsonFiles) {
    try {
        var applied = [];
        var errors = [];

        for (var i = 0; i < jsonFiles.length; i++) {
            try {
                var file = new File(jsonFiles[i].path);
                if (file.exists) {
                    file.open("r");
                    var jsonContent = file.read();
                    file.close();

                    var keyframeData = JSON.parse(jsonContent);

                    // Basic keyframe application (extend based on your JSON structure)
                    if (keyframeData && sib2ae.composition) {
                        applied.push("Processed " + jsonFiles[i].name);
                    }
                }
            } catch (fileError) {
                errors.push("Failed to process " + jsonFiles[i].name + ": " + fileError.message);
            }
        }

        var result = {
            applied: applied.length,
            errors: errors
        };

        return JSON.stringify(result);
    } catch (error) {
        return "Error: " + error.message;
    }
}

/**
 * Get current project information
 */
function getProjectInfo() {
    try {
        var info = {
            name: app.project.file ? app.project.file.name : "Untitled Project",
            items: app.project.items.length,
            activeComp: app.project.activeItem ? app.project.activeItem.name : "None"
        };

        return JSON.stringify(info);
    } catch (error) {
        return "Error: " + error.message;
    }
}

/**
 * Clear imported items (cleanup function)
 */
function clearImportedItems() {
    try {
        sib2ae.importedFiles = [];
        sib2ae.composition = null;
        sib2ae.projectPath = "";

        return "Success: Cleared import session";
    } catch (error) {
        return "Error: " + error.message;
    }
}