# After Effects Plugin & Extension Development Reference 2025

## Terminology Clarification

**Plugin vs Extension:**
- **Plugin**: Native C++ compiled code (.dll/.dylib) that adds effects, filters, or deep system integration
- **Extension**: Web-based panels (.zxp/.ccx) using HTML/CSS/JavaScript that add UI and workflow tools
- **Format**: Extensions use .zxp (CEP) or .ccx (UXP) packages; Plugins use platform-specific installers

## AI Documentation Reference Links

For future AI assistance and up-to-date information, reference these canonical documentation sources:

### Primary Documentation URLs
- **CEP Extensions**: https://github.com/Adobe-CEP/Getting-Started-guides
- **CEP Samples**: https://github.com/Adobe-CEP/Samples
- **Native C++ SDK**: https://ae-plugins.docsforadobe.dev/
- **ExtendScript API**: https://ae-scripting.docsforadobe.dev/
- **Adobe Developer Portal**: https://developer.adobe.com/after-effects/
- **UXP Documentation**: https://developer.adobe.com/photoshop/uxp/2022/ (reference for future AE UXP)

### Community Resources
- **Adobe Forums**: https://community.adobe.com/t5/after-effects/ct-p/ct-after-effects
- **GitHub Topics**: https://github.com/topics/aftereffects
- **aescripts.com**: https://aescripts.com/ (marketplace and resources)

## Overview

Comprehensive reference document for developing Adobe After Effects plugins and extensions in 2025. This PRP documents all major development paths, tools, frameworks, and distribution methods.

## Development Paths

### 1. CEP Extensions (HTML/CSS/JavaScript)
**Current Status**: Primary extension development method for After Effects 2025
- CEP 12 shipped with After Effects 25.0
- CEP 12 is the final major CEP update (security fixes only)
- UXP transition planned but not yet available for After Effects

### 2. Native Plugins (C++ SDK)
**Current Status**: Fully supported and actively maintained
- Latest SDK available at: https://www.adobe.io/after-effects/
- Apple Silicon native support added
- Multi-Frame Rendering (MFR) optimization available

### 3. UXP Extensions (Future)
**Current Status**: Not yet available for After Effects
- Available in Photoshop 2025 and InDesign v20.0
- Premiere Pro UXP in private beta (public beta expected early 2025)
- After Effects UXP APIs expected "as early as next year" (2025-2026)

## CEP Extension Development

### Core Technologies
- **Languages**: HTML, CSS, JavaScript, ExtendScript
- **Communication**: CSInterface.js for app integration
- **Frameworks**: Support for React, Vue, Angular

### Modern Development Stack (2025)
```bash
# Recommended: Vite + React + TypeScript + Sass
# Alternative: Webpack + React + TypeScript
```

### Project Structure
```
extension/
├── CSXS/
│   └── manifest.xml          # Extension configuration
├── client/                   # Frontend (HTML/CSS/JS)
│   ├── index.html
│   ├── CSInterface.js        # Adobe communication layer
│   └── main.js
└── host/                     # ExtendScript (Adobe app integration)
    └── index.jsx
```

### Key Resources
- **Documentation**: https://github.com/Adobe-CEP/Getting-Started-guides
- **Samples**: https://github.com/Adobe-CEP/Samples
- **Boilerplate**: Bolt CEP (Vite-based, modern tooling)
- **TypeScript Support**: Types for Adobe (community project)

### CEP Development Tools
- **Primary IDE**: Visual Studio Code with ExtendScript extension
- **Alternative**: ExtendScript Toolkit (legacy, use VS Code recommended)
- **Build Tools**: Vite (recommended), Webpack (established)
- **Package Tool**: ZXPSignCmd for .zxp packaging

## Native Plugin Development (C++ SDK)

### SDK Capabilities
- **Effect Types**: Visual effects, audio effects, transitions
- **Plugin Types**: Effects, AEGPs (General Plugins), AEIOs (Input/Output), Artisans
- **Color Depths**: 8-bit, 16-bit, 32-bit floating point
- **Color Spaces**: RGB, YUV
- **GPU Support**: CUDA, OpenCL

### Development Environment
- **Platform**: Windows (Visual Studio 2019+), macOS (Xcode)
- **Build System**: CMake (recommended), Visual Studio projects
- **SDK Location**: Download from https://www.adobe.io/after-effects/

### Key SDK Features (2024-2025)
- Apple Silicon native compilation support
- Multi-Frame Rendering (MFR) optimization
- Premiere Pro compatibility for effects
- Enhanced performance with modern hardware

### Project Setup
```cpp
// Environment variable for VS development
AE_PLUGIN_BUILD_DIR = [path_to_ae_plugins_directory]

// Plugin installation paths:
// macOS: /Library/Application Support/Adobe/Common/Plug-ins/[version]/MediaCore/
// Windows: [Program Files]\Adobe\Common\Plug-ins\[version]\MediaCore\
```

### SDK Documentation
- **Primary Resource**: https://ae-plugins.docsforadobe.dev/
- **GitHub**: https://github.com/docsforadobe/after-effects-plugin-guide
- **Coding Conventions**: Pseudo-Hungarian notation
- **Support**: Adobe Developer Community forums

## ExtendScript Development

### Language Specifications
- **Base**: Extended JavaScript (ECMA-262 3rd Edition)
- **Extensions**: Adobe-specific objects and methods
- **Engine**: Legacy ExtendScript (expressions use ES2018 since AE 16.0)

### Development Resources
- **Documentation**: https://ae-scripting.docsforadobe.dev/ (community-maintained)
- **Official Guide**: Adobe ExtendScript CS6 reference (updated)
- **IDE**: Visual Studio Code with ExtendScript Debugger
- **Legacy IDE**: ExtendScript Toolkit (obsolete)

### Object Model
```javascript
app                          // Application object
  └── project                // Current project
      ├── items[]            // Project items (comps, footage)
      ├── renderQueue        // Render queue
      └── selection[]        // Selected items
```

## Modern Development Frameworks

### React + TypeScript Setup
```json
// package.json dependencies
{
  "react": "^18.x",
  "typescript": "^5.x",
  "@types/react": "^18.x"
}

// TypeScript config for CEP
{
  "compilerOptions": {
    "jsx": "react",
    "module": "es6",
    "moduleResolution": "node",
    "target": "es5"
  }
}
```

### Vite Configuration (Recommended 2025)
```javascript
// vite.config.js for CEP
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    target: 'es5',
    outDir: 'dist'
  }
})
```

### Webpack Alternative
```javascript
// webpack.config.js
module.exports = {
  entry: './src/index.tsx',
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/
      }
    ]
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js']
  }
}
```

## Testing & Quality Assurance

### CEP Extension Testing
- **Development**: Live reload with Vite/Webpack dev server
- **Manual Testing**: Install as .zxp in After Effects
- **Debugging**: Chrome DevTools for UI, ExtendScript Debugger for host scripts

### Native Plugin Testing
- **Environment**: Visual Studio debugger attached to After Effects
- **Automated**: SDK includes testing framework suggestions
- **Performance**: PugetBench for After Effects (benchmark tool)
- **Compatibility**: Test across AE versions, especially MFR support

### Code Quality Tools
- **Linting**: ESLint for JavaScript/TypeScript
- **Formatting**: Prettier for code formatting
- **Type Checking**: TypeScript strict mode recommended

## Distribution & Deployment

### Code Signing Requirements (2025 Update)
**New Requirement**: After Effects 25.2.0+ requires signed plugins

#### macOS Signing
- **Cost**: $99/year (Apple Developer Program)
- **Process**: Code signing + notarization required
- **Tools**: Xcode command line tools

#### Windows Signing
- **Cost**: $9.99/month (Azure Trusted Signing) - NEW 2025 option
- **Alternative**: Traditional certificates ($200-300/year)
- **Requirement**: Business 3+ years old or individual verification

### Distribution Platforms

#### Adobe Marketplace (Official)
- **Process**: Review required for all plugins
- **Requirements**: EU trader details by February 16, 2025
- **Submission**: https://developer.adobe.com/developer-distribution/creative-cloud/
- **Benefit**: Official Adobe distribution, user trust
- **Format**: .zxp (CEP extensions), .ccx (UXP extensions), installers (native plugins)

#### Third-Party Marketplaces
- **aescripts.com**: Primary third-party marketplace
- **License**: No Adobe approval needed (use SDK freely)
- **Revenue**: Developer retains more revenue vs. Adobe marketplace
- **Format**: .zxp packages for extensions, custom installers for plugins

#### Direct Distribution
- **Extensions**: .zxp files (CEP) or .ccx files (UXP future)
- **Plugins**: Platform-specific installers (.exe/.pkg/.dmg)
- **Requirements**: Code signing mandatory for AE 25.2+
- **Packaging**: ZXPSignCmd for CEP extensions, UXP Developer Tool for UXP

## Performance Optimization

### CEP Extensions
- **Bundle Size**: Minimize JavaScript bundle size
- **Loading**: Lazy load components when possible
- **Communication**: Batch ExtendScript calls to reduce overhead
- **UI**: Use CSS transforms for smooth animations

### Native Plugins
- **MFR Support**: Implement Multi-Frame Rendering for 2024+ performance
- **Memory**: Efficient memory management for large projects
- **GPU**: Utilize CUDA/OpenCL for compute-intensive operations
- **Threading**: Support multi-threaded processing where applicable

## Security Best Practices

### Code Security
- **Secrets**: Never embed API keys or sensitive data
- **Validation**: Validate all user inputs
- **Sandboxing**: CEP extensions run in sandboxed environment
- **Permissions**: Request minimal necessary permissions

### Distribution Security
- **Signing**: Required for production distribution
- **Updates**: Implement secure update mechanisms
- **Dependencies**: Audit third-party dependencies regularly

## Future Considerations

### Transition Timeline
- **2025**: CEP remains primary, UXP development for AE begins
- **2026-2027**: UXP likely becomes available for After Effects
- **2028+**: CEP deprecation timeline (estimated)

### Preparation Strategies
- **Architecture**: Design CEP extensions with UXP migration in mind
- **Skills**: Learn UXP development through Photoshop/Premiere
- **Framework**: Choose frameworks that will work with both CEP and UXP

## Learning Resources

### Official Documentation
- **CEP**: https://github.com/Adobe-CEP/Getting-Started-guides
- **SDK**: https://ae-plugins.docsforadobe.dev/
- **ExtendScript**: https://ae-scripting.docsforadobe.dev/

### Community Resources
- **Forums**: Adobe Developer Community
- **Discord**: AE Scripting Discord
- **GitHub**: Search for 'after-effects-extension' and 'cep-extension'

### Educational Courses
- **fxphd**: Plugin Development for Adobe Premiere and After Effects
- **YouTube**: Various CEP and ExtendScript tutorials
- **Udemy**: Extension development courses

## Quick Start Templates

### CEP Extension (Vite + React + TypeScript)
```bash
# Clone modern boilerplate
git clone [bolt-cep-template]
cd bolt-cep-extension
npm install
npm run dev
```

### Native Plugin (C++ SDK)
```bash
# Download SDK from Adobe
# Extract to development directory
# Open sample project in Visual Studio
# Configure AE_PLUGIN_BUILD_DIR environment variable
# Build and test
```

### ExtendScript Panel
```bash
# Create basic ScriptUI panel
# Place in AE Scripts folder
# Access via File > Scripts menu
```

## Common Issues & Solutions

### CEP Development
- **CORS Issues**: Configure manifest.xml for external resources
- **ExtendScript Errors**: Use try-catch and proper error handling
- **Packaging**: Ensure proper .zxp structure and signing

### Native Plugin Development
- **Build Errors**: Verify SDK version matches AE version
- **Performance**: Implement MFR for modern AE versions
- **Compatibility**: Test across different AE versions

### Distribution
- **Signing Failures**: Verify certificate validity and process
- **User Installation**: Provide clear installation instructions
- **Updates**: Plan for version management and user migration

---

## Summary

After Effects plugin/extension development in 2025 offers multiple robust paths:

1. **CEP Extensions**: Primary choice for UI-heavy tools, modern web frameworks supported
2. **Native Plugins**: Best for performance-critical effects and deep AE integration
3. **ExtendScript**: Essential for both CEP and native plugin host communication

Key 2025 updates include mandatory code signing for AE 25.2+, improved Azure signing options for Windows, and the continued transition toward UXP while CEP remains fully supported.

Choose your development path based on:
- **UI Complexity**: CEP for rich interfaces
- **Performance Needs**: Native SDK for compute-intensive tasks
- **Timeline**: CEP for immediate deployment, plan for UXP transition
- **Target Audience**: Consider distribution platform and signing requirements

This reference document provides the foundation for successful After Effects plugin development in 2025 and beyond.