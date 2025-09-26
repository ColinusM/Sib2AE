// Sib2Ae Importer CEP Panel JavaScript
// Main client-side logic for the importer extension

// Initialize CSInterface
var csInterface = new CSInterface();
var selectedFolder = "";
var scannedFiles = null;

// DOM elements
var folderPathInput;
var browseFolderBtn;
var importBtn;
var clearBtn;
var filePreview;
var statusLog;
var importSymbolicCheck;
var importAudioCheck;
var importKeyframesCheck;
var createCompositionCheck;

// Initialize the extension
window.onload = function() {
    initializeUI();
    setupEventListeners();
    logStatus("Sib2Ae Importer ready.");
};

/**
 * Initialize UI elements
 */
function initializeUI() {
    folderPathInput = document.getElementById("folderPath");
    browseFolderBtn = document.getElementById("browseFolderBtn");
    importBtn = document.getElementById("importBtn");
    clearBtn = document.getElementById("clearBtn");
    filePreview = document.getElementById("filePreview");
    statusLog = document.getElementById("statusLog");
    importSymbolicCheck = document.getElementById("importSymbolic");
    importAudioCheck = document.getElementById("importAudio");
    importKeyframesCheck = document.getElementById("importKeyframes");
    createCompositionCheck = document.getElementById("createComposition");

    // Set default state
    importBtn.disabled = true;
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    browseFolderBtn.addEventListener("click", browsePipelineFolder);
    importBtn.addEventListener("click", importFiles);
    clearBtn.addEventListener("click", clearSelection);

    // Theme change listener
    csInterface.addEventListener("com.adobe.csxs.events.ThemeColorChanged", onThemeChanged);

    // Apply initial theme
    onThemeChanged();
}

/**
 * Browse for pipeline output folder
 */
function browsePipelineFolder() {
    logStatus("Browsing for pipeline folder...");

    csInterface.evalScript("browsePipelineFolder()", function(result) {
        if (result && !result.startsWith("Error")) {
            selectedFolder = result;
            folderPathInput.value = selectedFolder;
            logStatus("Selected folder: " + selectedFolder, "success");
            scanSelectedFolder();
        } else if (result) {
            logStatus(result, "error");
        } else {
            logStatus("No folder selected.");
        }
    });
}

/**
 * Scan the selected folder for files
 */
function scanSelectedFolder() {
    if (!selectedFolder) return;

    logStatus("Scanning folder for pipeline files...");

    csInterface.evalScript("scanPipelineFiles('" + selectedFolder + "')", function(result) {
        if (result && !result.startsWith("Error")) {
            try {
                scannedFiles = JSON.parse(result);
                updateFilePreview();
                importBtn.disabled = false;
                logStatus("Found files: " + getTotalFileCount() + " total", "success");
            } catch (error) {
                logStatus("Error parsing scan results: " + error.message, "error");
            }
        } else {
            logStatus(result || "Failed to scan folder", "error");
        }
    });
}

/**
 * Update the file preview display
 */
function updateFilePreview() {
    if (!scannedFiles) {
        filePreview.innerHTML = '<p class="placeholder">No files found</p>';
        return;
    }

    var html = "";

    if (scannedFiles.svg.length > 0) {
        html += "<strong>SVG Files (" + scannedFiles.svg.length + "):</strong><br>";
        for (var i = 0; i < Math.min(scannedFiles.svg.length, 5); i++) {
            html += '<div class="file-item svg">• ' + scannedFiles.svg[i].name + '</div>';
        }
        if (scannedFiles.svg.length > 5) {
            html += '<div class="file-item">... and ' + (scannedFiles.svg.length - 5) + ' more</div>';
        }
        html += "<br>";
    }

    if (scannedFiles.audio.length > 0) {
        html += "<strong>Audio Files (" + scannedFiles.audio.length + "):</strong><br>";
        for (var i = 0; i < Math.min(scannedFiles.audio.length, 5); i++) {
            html += '<div class="file-item audio">• ' + scannedFiles.audio[i].name + '</div>';
        }
        if (scannedFiles.audio.length > 5) {
            html += '<div class="file-item">... and ' + (scannedFiles.audio.length - 5) + ' more</div>';
        }
        html += "<br>";
    }

    if (scannedFiles.json.length > 0) {
        html += "<strong>JSON Files (" + scannedFiles.json.length + "):</strong><br>";
        for (var i = 0; i < Math.min(scannedFiles.json.length, 3); i++) {
            html += '<div class="file-item json">• ' + scannedFiles.json[i].name + '</div>';
        }
        if (scannedFiles.json.length > 3) {
            html += '<div class="file-item">... and ' + (scannedFiles.json.length - 3) + ' more</div>';
        }
    }

    if (html === "") {
        html = '<p class="placeholder">No pipeline files found in selected folder</p>';
    }

    filePreview.innerHTML = html;
}

/**
 * Import files based on user selection
 */
function importFiles() {
    if (!scannedFiles) {
        logStatus("No files to import", "error");
        return;
    }

    logStatus("Starting import process...");
    importBtn.disabled = true;

    var importTasks = [];

    // Create composition if requested
    if (createCompositionCheck.checked) {
        importTasks.push(function(callback) {
            var compName = "Sib2Ae_" + new Date().toISOString().slice(0, 19).replace(/[:-]/g, "");
            csInterface.evalScript("createSib2aeComposition('" + compName + "')", function(result) {
                logStatus(result);
                callback();
            });
        });
    }

    // Import SVG files
    if (importSymbolicCheck.checked && scannedFiles.svg.length > 0) {
        importTasks.push(function(callback) {
            logStatus("Importing " + scannedFiles.svg.length + " SVG files...");
            var svgFilesJson = JSON.stringify(scannedFiles.svg);
            csInterface.evalScript("importSVGFiles(" + svgFilesJson + ")", function(result) {
                try {
                    var importResult = JSON.parse(result);
                    logStatus("SVG import: " + importResult.imported + " files imported", "success");
                    if (importResult.errors.length > 0) {
                        for (var i = 0; i < importResult.errors.length; i++) {
                            logStatus(importResult.errors[i], "warning");
                        }
                    }
                } catch (error) {
                    logStatus("SVG import result: " + result);
                }
                callback();
            });
        });
    }

    // Import audio files
    if (importAudioCheck.checked && scannedFiles.audio.length > 0) {
        importTasks.push(function(callback) {
            logStatus("Importing " + scannedFiles.audio.length + " audio files...");
            var audioFilesJson = JSON.stringify(scannedFiles.audio);
            csInterface.evalScript("importAudioFiles(" + audioFilesJson + ")", function(result) {
                try {
                    var importResult = JSON.parse(result);
                    logStatus("Audio import: " + importResult.imported + " files imported", "success");
                    if (importResult.errors.length > 0) {
                        for (var i = 0; i < importResult.errors.length; i++) {
                            logStatus(importResult.errors[i], "warning");
                        }
                    }
                } catch (error) {
                    logStatus("Audio import result: " + result);
                }
                callback();
            });
        });
    }

    // Apply keyframe data
    if (importKeyframesCheck.checked && scannedFiles.json.length > 0) {
        importTasks.push(function(callback) {
            logStatus("Processing " + scannedFiles.json.length + " JSON keyframe files...");
            var jsonFilesJson = JSON.stringify(scannedFiles.json);
            csInterface.evalScript("applyKeyframeData(" + jsonFilesJson + ")", function(result) {
                try {
                    var applyResult = JSON.parse(result);
                    logStatus("Keyframes: " + applyResult.applied + " files processed", "success");
                    if (applyResult.errors.length > 0) {
                        for (var i = 0; i < applyResult.errors.length; i++) {
                            logStatus(applyResult.errors[i], "warning");
                        }
                    }
                } catch (error) {
                    logStatus("Keyframe processing result: " + result);
                }
                callback();
            });
        });
    }

    // Execute import tasks sequentially
    executeTasksSequentially(importTasks, function() {
        logStatus("Import process completed!", "success");
        importBtn.disabled = false;
    });
}

/**
 * Execute tasks sequentially
 */
function executeTasksSequentially(tasks, callback) {
    if (tasks.length === 0) {
        callback();
        return;
    }

    var task = tasks.shift();
    task(function() {
        executeTasksSequentially(tasks, callback);
    });
}

/**
 * Clear selection and reset UI
 */
function clearSelection() {
    selectedFolder = "";
    scannedFiles = null;
    folderPathInput.value = "";
    filePreview.innerHTML = '<p class="placeholder">Select a folder to preview files...</p>';
    importBtn.disabled = true;

    csInterface.evalScript("clearImportedItems()", function(result) {
        logStatus("Cleared: " + result);
    });
}

/**
 * Get total file count
 */
function getTotalFileCount() {
    if (!scannedFiles) return 0;
    return scannedFiles.svg.length + scannedFiles.audio.length + scannedFiles.json.length;
}

/**
 * Log status message
 */
function logStatus(message, type) {
    var timestamp = new Date().toLocaleTimeString();
    var logEntry = document.createElement("p");
    logEntry.textContent = "[" + timestamp + "] " + message;

    if (type) {
        logEntry.className = type;
    }

    statusLog.appendChild(logEntry);
    statusLog.scrollTop = statusLog.scrollHeight;

    // Keep only last 20 log entries
    while (statusLog.children.length > 20) {
        statusLog.removeChild(statusLog.firstChild);
    }
}

/**
 * Handle theme changes
 */
function onThemeChanged() {
    var hostEnv = csInterface.getHostEnvironment();
    if (hostEnv && hostEnv.appSkinInfo) {
        var bgColor = hostEnv.appSkinInfo.appBarBackgroundColor;
        if (bgColor) {
            var red = Math.round(bgColor.color.red);
            var green = Math.round(bgColor.color.green);
            var blue = Math.round(bgColor.color.blue);

            // Adjust theme based on host application
            if (red + green + blue < 384) {
                // Dark theme
                document.body.style.backgroundColor = "#2e2e2e";
                document.body.style.color = "#e0e0e0";
            } else {
                // Light theme
                document.body.style.backgroundColor = "#f0f0f0";
                document.body.style.color = "#333333";
            }
        }
    }
}