/*
Sib2Ae Importer Script for After Effects
Quick and simple import of pipeline results

Installation: Copy to After Effects Scripts folder
Usage: File > Scripts > Sib2Ae_Importer.jsx

No restart required - edit and run immediately!
*/

// Main execution
(function() {

    // Check if we're in After Effects
    if (typeof app === "undefined" || app.name !== "After Effects") {
        alert("This script must be run in After Effects");
        return;
    }

    // Global variables
    var sib2ae = {
        sourceFolder: null,
        files: {
            svg: [],
            audio: [],
            json: []
        },
        composition: null
    };

    // Create and show the main UI
    createMainUI();

    /**
     * Create the main user interface
     */
    function createMainUI() {
        var dialog = new Window("dialog", "Sib2Ae Importer");
        dialog.orientation = "column";
        dialog.alignChildren = "fill";
        dialog.spacing = 10;
        dialog.margins = 15;

        // Header
        var headerGroup = dialog.add("group");
        headerGroup.orientation = "column";
        headerGroup.alignChildren = "center";

        var titleText = headerGroup.add("statictext", undefined, "Sib2Ae Pipeline Importer");
        titleText.graphics.font = ScriptUI.newFont("Arial", "Bold", 14);

        headerGroup.add("statictext", undefined, "Import SVG, Audio, and JSON files from pipeline output");

        // Folder selection
        var folderGroup = dialog.add("panel", undefined, "Pipeline Output Folder");
        folderGroup.orientation = "column";
        folderGroup.alignChildren = "fill";
        folderGroup.margins = 10;

        var pathGroup = folderGroup.add("group");
        pathGroup.orientation = "row";
        pathGroup.alignChildren = "center";

        var folderPath = pathGroup.add("edittext", undefined, "No folder selected...");
        folderPath.enabled = false;
        folderPath.preferredSize.width = 300;

        var browseBtn = pathGroup.add("button", undefined, "Browse");
        browseBtn.preferredSize.width = 80;

        // File preview
        var previewGroup = dialog.add("panel", undefined, "Files Found");
        previewGroup.orientation = "column";
        previewGroup.alignChildren = "fill";
        previewGroup.margins = 10;
        previewGroup.preferredSize.height = 120;

        var fileList = previewGroup.add("edittext", undefined, "Select a folder to scan for files...", {multiline: true, readonly: true});
        fileList.preferredSize.height = 100;

        // Import options
        var optionsGroup = dialog.add("panel", undefined, "Import Options");
        optionsGroup.orientation = "column";
        optionsGroup.alignChildren = "left";
        optionsGroup.margins = 10;

        var importSVG = optionsGroup.add("checkbox", undefined, "Import SVG files (symbolic elements)");
        importSVG.value = true;

        var importAudio = optionsGroup.add("checkbox", undefined, "Import Audio files (.wav, .mp3, .aiff)");
        importAudio.value = true;

        var importJSON = optionsGroup.add("checkbox", undefined, "Process JSON files (keyframes)");
        importJSON.value = true;

        var createComp = optionsGroup.add("checkbox", undefined, "Create new composition");
        createComp.value = true;

        // Progress
        var progressGroup = dialog.add("group");
        progressGroup.orientation = "column";
        progressGroup.alignChildren = "fill";

        var progressText = progressGroup.add("statictext", undefined, "Ready to import...");
        var progressBar = progressGroup.add("progressbar", undefined, 0, 100);
        progressBar.preferredSize.width = 350;

        // Buttons
        var buttonGroup = dialog.add("group");
        buttonGroup.orientation = "row";
        buttonGroup.alignment = "center";

        var importBtn = buttonGroup.add("button", undefined, "Import Files");
        importBtn.preferredSize.width = 100;
        importBtn.enabled = false;

        var closeBtn = buttonGroup.add("button", undefined, "Close");
        closeBtn.preferredSize.width = 100;

        // Event handlers
        browseBtn.onClick = function() {
            var folder = Folder.selectDialog("Select Sib2Ae Pipeline Output Folder");
            if (folder) {
                sib2ae.sourceFolder = folder;
                folderPath.text = folder.fsName;

                progressText.text = "Scanning folder...";
                dialog.update();

                scanFolder(folder);
                updateFilePreview(fileList);

                if (getTotalFileCount() > 0) {
                    importBtn.enabled = true;
                    progressText.text = "Found " + getTotalFileCount() + " files. Ready to import.";
                } else {
                    progressText.text = "No pipeline files found in selected folder.";
                }
            }
        };

        importBtn.onClick = function() {
            importFiles(progressText, progressBar, importSVG.value, importAudio.value, importJSON.value, createComp.value);
        };

        closeBtn.onClick = function() {
            dialog.close();
        };

        // Show dialog
        dialog.show();
    }

    /**
     * Scan folder for pipeline files
     */
    function scanFolder(folder) {
        sib2ae.files = {svg: [], audio: [], json: []};
        scanFolderRecursive(folder, sib2ae.files);
    }

    /**
     * Recursively scan folders
     */
    function scanFolderRecursive(folder, files) {
        var contents = folder.getFiles();

        for (var i = 0; i < contents.length; i++) {
            var item = contents[i];

            if (item instanceof Folder) {
                scanFolderRecursive(item, files);
            } else if (item instanceof File) {
                var name = item.name.toLowerCase();

                if (name.match(/\.svg$/)) {
                    files.svg.push(item);
                } else if (name.match(/\.(wav|mp3|aiff|aif)$/)) {
                    files.audio.push(item);
                } else if (name.match(/\.json$/)) {
                    files.json.push(item);
                }
            }
        }
    }

    /**
     * Update file preview display
     */
    function updateFilePreview(textElement) {
        var preview = "";

        if (sib2ae.files.svg.length > 0) {
            preview += "SVG Files (" + sib2ae.files.svg.length + "):\n";
            for (var i = 0; i < Math.min(sib2ae.files.svg.length, 5); i++) {
                preview += "  • " + sib2ae.files.svg[i].name + "\n";
            }
            if (sib2ae.files.svg.length > 5) {
                preview += "  ... and " + (sib2ae.files.svg.length - 5) + " more\n";
            }
            preview += "\n";
        }

        if (sib2ae.files.audio.length > 0) {
            preview += "Audio Files (" + sib2ae.files.audio.length + "):\n";
            for (var i = 0; i < Math.min(sib2ae.files.audio.length, 5); i++) {
                preview += "  • " + sib2ae.files.audio[i].name + "\n";
            }
            if (sib2ae.files.audio.length > 5) {
                preview += "  ... and " + (sib2ae.files.audio.length - 5) + " more\n";
            }
            preview += "\n";
        }

        if (sib2ae.files.json.length > 0) {
            preview += "JSON Files (" + sib2ae.files.json.length + "):\n";
            for (var i = 0; i < Math.min(sib2ae.files.json.length, 3); i++) {
                preview += "  • " + sib2ae.files.json[i].name + "\n";
            }
            if (sib2ae.files.json.length > 3) {
                preview += "  ... and " + (sib2ae.files.json.length - 3) + " more\n";
            }
        }

        if (preview === "") {
            preview = "No pipeline files found.\n\nExpected file types:\n• .svg (symbolic elements)\n• .wav/.mp3/.aiff (audio)\n• .json (keyframe data)";
        }

        textElement.text = preview;
    }

    /**
     * Get total file count
     */
    function getTotalFileCount() {
        return sib2ae.files.svg.length + sib2ae.files.audio.length + sib2ae.files.json.length;
    }

    /**
     * Import selected files
     */
    function importFiles(statusText, progressBar, importSVG, importAudio, importJSON, createComp) {
        try {
            app.beginUndoGroup("Sib2Ae Import");

            var totalSteps = 0;
            if (createComp) totalSteps++;
            if (importSVG && sib2ae.files.svg.length > 0) totalSteps++;
            if (importAudio && sib2ae.files.audio.length > 0) totalSteps++;
            if (importJSON && sib2ae.files.json.length > 0) totalSteps++;

            var currentStep = 0;

            // Create composition
            if (createComp) {
                statusText.text = "Creating composition...";
                progressBar.value = (currentStep / totalSteps) * 100;

                var compName = "Sib2Ae_Import_" + new Date().getTime().toString().slice(-6);
                sib2ae.composition = app.project.items.addComp(compName, 1920, 1080, 1.0, 30, 30);

                currentStep++;
            }

            // Import SVG files
            if (importSVG && sib2ae.files.svg.length > 0) {
                statusText.text = "Importing " + sib2ae.files.svg.length + " SVG files...";
                progressBar.value = (currentStep / totalSteps) * 100;

                for (var i = 0; i < sib2ae.files.svg.length; i++) {
                    try {
                        var importOptions = new ImportOptions(sib2ae.files.svg[i]);
                        var footageItem = app.project.importFile(importOptions);

                        if (footageItem && sib2ae.composition) {
                            var layer = sib2ae.composition.layers.add(footageItem);
                            layer.name = sib2ae.files.svg[i].name.replace(/\.svg$/i, "");
                        }
                    } catch (e) {
                        // Continue with next file if one fails
                    }
                }
                currentStep++;
            }

            // Import Audio files
            if (importAudio && sib2ae.files.audio.length > 0) {
                statusText.text = "Importing " + sib2ae.files.audio.length + " audio files...";
                progressBar.value = (currentStep / totalSteps) * 100;

                for (var i = 0; i < sib2ae.files.audio.length; i++) {
                    try {
                        var importOptions = new ImportOptions(sib2ae.files.audio[i]);
                        var footageItem = app.project.importFile(importOptions);

                        if (footageItem && sib2ae.composition) {
                            var layer = sib2ae.composition.layers.add(footageItem);
                            layer.name = sib2ae.files.audio[i].name.replace(/\.(wav|mp3|aiff|aif)$/i, "");
                        }
                    } catch (e) {
                        // Continue with next file if one fails
                    }
                }
                currentStep++;
            }

            // Process JSON files
            if (importJSON && sib2ae.files.json.length > 0) {
                statusText.text = "Processing " + sib2ae.files.json.length + " JSON files...";
                progressBar.value = (currentStep / totalSteps) * 100;

                // Basic JSON processing - extend this based on your keyframe data structure
                for (var i = 0; i < sib2ae.files.json.length; i++) {
                    try {
                        var jsonFile = sib2ae.files.json[i];
                        jsonFile.open("r");
                        var jsonContent = jsonFile.read();
                        jsonFile.close();

                        // Parse and apply keyframe data here
                        // var keyframeData = JSON.parse(jsonContent);
                        // Apply to composition layers as needed

                    } catch (e) {
                        // Continue with next file if one fails
                    }
                }
                currentStep++;
            }

            progressBar.value = 100;
            statusText.text = "Import completed! Imported " + getTotalFileCount() + " files.";

            // Select the created composition
            if (sib2ae.composition) {
                sib2ae.composition.selected = true;
                app.project.activeItem = sib2ae.composition;
            }

            app.endUndoGroup();

        } catch (error) {
            app.endUndoGroup();
            statusText.text = "Import failed: " + error.message;
            alert("Import Error: " + error.message);
        }
    }

})();

// Show completion message
alert("Sib2Ae Importer script loaded successfully!\n\nTo run again: File > Scripts > Run Script File > Select this .jsx file");