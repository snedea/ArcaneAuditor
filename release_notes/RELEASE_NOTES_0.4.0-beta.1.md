# Arcane Auditor v0.4.0-beta.1 Release Notes

## 🎉 Major Release: Context Awareness & Enhanced Analysis Modes

**Release Date:** December 2024
**Version:** 0.4.0-beta.1
**Type:** Beta Release

---

## 🚀 What's New

### 🧠 **Context Awareness (NEW!)**

#### **Intelligent Analysis Detection**

- **Complete vs Partial Analysis**: Automatically detects when all required files are present vs when analysis is incomplete
- **Missing File Identification**: Shows which AMD/SMD files are needed for complete validation
- **Rule Execution Transparency**: Lists which rules couldn't run due to missing context
- **Cross-Platform Support**: Context awareness available in CLI, Web UI, JSON, and Excel outputs

#### **Multiple Analysis Modes**

- **ZIP File Analysis**: Complete application archive analysis (existing functionality)
- **Individual File Analysis**: Analyze single files or multiple files together
- **Directory Scanning**: Recursively scan directories for relevant files
- **Flexible Input**: Support for any combination of PMD, POD, AMD, SMD, and SCRIPT files

#### **Context Information Display**

- **Files Processed**: Shows which files were successfully analyzed with file type icons
- **Files Needed**: Indicates missing AMD/SMD files for complete validation (red styling for required files)
- **Checks Skipped**: Lists rules that couldn't run due to missing context with conversational messaging
- **Actionable Tips**: Provides specific guidance on what to add for complete validation

#### **Example Context Panel**

```
📊 Analysis Summary                    [⚠️ Partial]
▼
  ✅ Files Processed (1)
     📄 page.pmd
  
  ⚠️ Files Needed for Full Validation
     [ AMD ] [ SMD ]
  
  🚫 Checks Skipped
     Some rules could not be evaluated due to missing file types.
     • AMDDataprov…Rule — Skipped — missing required AMD file.
  
  💡 Tip: Add AMD and SMD files for complete application validation.
```

### 🌐 **Web Interface Enhancements**

#### **Multiple File Upload Support**

- **Individual File Upload**: Support for .pmd, .pod, .amd, .smd, and .script files
- **Drag & Drop**: Enhanced drag-and-drop support for both ZIP files and individual files
- **File Management**: Visual file list with remove functionality for selected files
- **Smart Detection**: Automatic detection of ZIP vs individual file uploads

#### **Context Awareness Panel**

- **Real-Time Display**: Shows analysis completeness and missing dependencies
- **Collapsible Design**: Starts collapsed with status badge always visible
- **Visual Hierarchy**: Clear distinction between required and optional files
- **Professional Styling**: Warm gradient badges and improved spacing

#### **Enhanced User Experience**

- **Improved Layout**: File upload moved to top, configuration selection below for better workflow
- **Scroll Jiggle Fix**: Definitive solution eliminating layout shifts and scroll bar jumping
- **Dark Mode Hover Fix**: Resolved text readability issues in dark mode hover states
- **Responsive Design**: Optimized spacing and layout for all screen sizes
- **Summary Block Refinement**: Merged redundant summary information with inline icons and theme-aware accent colors
- **Excel Context Tab Fix**: Web interface now properly includes context tab in Excel exports (matching CLI behavior)

### 🖥️ **CLI Enhancements**

#### **Individual File Support**

- **Single File Analysis**: `uv run main.py review-app page.pmd`
- **Multiple File Analysis**: `uv run main.py review-app page.pmd app.smd app.amd`
- **Directory Scanning**: `uv run main.py review-app presentation/`
- **Automatic Detection**: Smart detection of input type (ZIP, file, directory)

#### **Context Awareness Output**

- **Console Context Panel**: Always-on context information in CLI output
- **Clean Filenames**: Removes UUID prefixes from display (backend collision prevention preserved)
- **Status Indicators**: Clear visual indicators for complete vs partial analysis
- **Actionable Guidance**: Specific recommendations for complete validation

### 📊 **Output Format Enhancements**

#### **Excel Export**

- **Context Sheet**: Dedicated sheet showing analysis completeness and missing files
- **Clean Filenames**: Removes UUID prefixes for professional presentation
- **Status Indicators**: Color-coded status for complete vs partial analysis

#### **JSON Export**

- **Context Object**: Root-level context information in JSON responses
- **Analysis Metadata**: Complete information about files analyzed and missing dependencies
- **API Integration**: Enhanced API responses with context awareness data

---

## 🔧 **Technical Improvements**

### **Performance Enhancements**

- **Efficient File Processing**: Optimized handling of individual files and directories
- **Memory Management**: Improved resource usage for multiple file analysis
- **Parallel Processing**: Enhanced multi-threaded analysis capabilities

### **Code Quality**

- **Context Tracking**: New `AnalysisContext` and `SkippedCheck` data structures
- **Rule Integration**: Enhanced rules to report missing context gracefully
- **Comprehensive Testing**: 35+ unit tests covering context awareness functionality
- **DRY Principles**: Reusable context formatting across all output types

### **Bug Fixes**

- **Filename Display**: Clean filenames across all outputs (Web UI, CLI, Excel)
- **API Compatibility**: Fixed parameter naming for multiple file uploads
- **Error Handling**: Improved error messages and user guidance
- **Cross-Platform**: Enhanced compatibility across Windows, macOS, and Linux
- **Regex Operations**: Fixed incorrect `str.replace(regex=True)` usage with proper `re.sub()` implementation
- **Excel Generation**: Web interface now uses shared `OutputFormatter` for consistent Excel output
- **Import Paths**: Corrected `AnalysisContext` import from `parser.models` to `file_processing.context_tracker`
- **Configuration Protection**: Proper gitignore setup for team and personal configuration directories

---

## 📊 **Rule Statistics**

- **Total Rules**: 36 (22 Script Rules, 14 Structure Rules)
- **Context-Aware Rules**: 2 (`PMDSecurityDomainRule`, `HardcodedApplicationIdRule`)
- **Cross-File Dependencies**: Enhanced detection and reporting
- **Rule Execution**: Improved transparency and user guidance

---

## 🎯 **Breaking Changes**

### **API Changes**

- **Upload Endpoint**: Changed from `file` to `files` parameter for multiple file support
- **Response Format**: Added `context` object to all analysis responses
- **File Processing**: Enhanced to support individual files and directories

### **CLI Changes**

- **Command Syntax**: Enhanced `review-app` command to support multiple input types
- **Output Format**: Added context awareness panel to console output
- **File Handling**: Automatic detection of ZIP vs individual file analysis

---

## 🚀 **Migration Guide**

### **For CLI Users**

```bash
# Old: ZIP files only
uv run main.py review-app myapp.zip

# New: Multiple input types supported
uv run main.py review-app myapp.zip                    # ZIP file
uv run main.py review-app page.pmd                     # Single file
uv run main.py review-app page.pmd app.smd app.amd     # Multiple files
uv run main.py review-app presentation/                # Directory
```

### **For Web Interface Users**

- **New Upload Options**: Choose between ZIP file or individual files
- **Context Panel**: New collapsible panel showing analysis completeness
- **File Management**: Visual file list with remove functionality

### **For API Users**

- **Parameter Change**: Use `files` instead of `file` for uploads
- **Response Enhancement**: Check for `context` object in responses
- **Multiple Files**: Support for array of files in upload requests

---

## 🎉 **What's Next**

### **Planned Features**

- **Phase 7**: Full app mode optimization (minimal output for complete ZIPs)
- **Enhanced Rules**: More context-aware validation rules
- **Integration**: Better integration with CI/CD pipelines
- **Performance**: Further optimization for large applications

### **Community Feedback**

We welcome feedback on the new context awareness features! Please report issues or suggestions through our GitHub repository.

---

## 📚 **Documentation Updates**

### **📜 Enhanced Rule Documentation**

- **RULE_BREAKDOWN.md**: Complete overhaul with professional polish
  - **Table of Contents**: Comprehensive navigation with anchor links to all 36 rules
  - **Visual Severity Indicators**: Color-coded 🔴 ACTION and 🟢 ADVICE for instant recognition
  - **Magical Summaries**: Thematic descriptions for Script Rules and Structure Rules
  - **Quick Reference Table**: Complete matrix of all rules with categories, severity, and settings
  - **Category Icons**: Visual hierarchy with 🪄 Script Rules and 🏗️ Structure Rules

### **🔮 Custom Rules Development Guide**

- **Enhanced README**: Professional developer onboarding experience
  - **Class Hierarchy Diagram**: Visual representation of RuleBase → ScriptRuleBase/StructureRuleBase
  - **"When to Use" Reference**: Clear guidance on Violation vs Finding usage patterns
  - **Optimized Flow**: Logical progression from Creating → Utilities → Best Practices → Debugging → Getting Started
  - **Immediate Debugging**: Debugging section positioned for instant feedback after rule creation
  - **Cross-References**: Links to Rules Grimoire for comprehensive coverage

### **📖 Main Documentation**

- **README.md**: Complete revamp for better navigation and user experience
  - **Table of Contents**: Comprehensive navigation with anchor links
  - **Collapsible Sections**: Context Awareness, Configuration System, and Validation Rules
  - **Visual Enhancements**: Shield.io badges, emoji icons, and improved formatting
  - **Quick Start**: Separate Web UI and CLI sections with clear dividers
  - **Screenshot Management**: Organized with collapsible "More Screenshots" section
  - **Project Structure**: Concise overview with link to detailed `docs/project-structure.md`

### **📁 Project Structure Documentation**

- **docs/project-structure.md**: Comprehensive developer guide
  - **High-Level Architecture**: Clear overview of core components and data flow
  - **Detailed Breakdown**: Complete directory structure with explanations
  - **Development Workflow**: Testing, contributing, and key files guidance
  - **Visual Flow**: Arrows and clear progression through the system

### **⚙️ Configuration Documentation**

- **config/README.md**: Professional configuration guide
  - **Decision Tables**: Quick reference for configuration types and update safety
  - **Cross-Links**: Integration with main README and rule documentation
  - **Visual Hierarchy**: Emojis, tables, and clear section organization
  - **Professional Polish**: Consistent formatting and thematic elements

### **🔒 Configuration Protection**

- **Gitignore Updates**: Proper protection for team and personal configurations
  - **Team Configurations**: Directory structure tracked, JSON files gitignored
  - **Personal Configurations**: Complete privacy with minimal structure tracking
  - **Update Safety**: Configurations protected from app updates while maintaining functionality

---

**Download**: [Arcane Auditor v0.4.0-beta.1](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases/tag/v0.4.0-beta.1)

**Full Changelog**: See [GitHub Releases](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases) for complete changelog and download links.
