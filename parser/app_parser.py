"""
Parser to convert source files into PMD models for analysis.
"""
import json
from pathlib import Path
from typing import Dict, Any
from .models import ProjectContext, PMDModel, ScriptModel, AMDModel, PMDIncludes, PMDPresentation


class PMDParser:
    """Parses source files into PMD models for analysis."""
    
    def __init__(self):
        self.supported_extensions = {'.pmd', '.script', '.amd', '.pod', '.smd'}
    
    def parse_files(self, source_files_map: Dict[str, Any]) -> ProjectContext:
        """
        Parse source files into a ProjectContext with populated models.
        
        Args:
            source_files_map: Dictionary mapping file paths to SourceFile objects
            
        Returns:
            ProjectContext with all parsed models
        """
        context = ProjectContext()
        
        for file_path, source_file in source_files_map.items():
            try:
                self._parse_single_file(file_path, source_file, context)
            except Exception as e:
                print(f"⚠️ Failed to parse {file_path}: {e}")
                context.parsing_errors.append(f"{file_path}: {e}")
        
        return context
    
    def _parse_single_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a single source file based on its extension."""
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        if extension == '.pmd':
            self._parse_pmd_file(file_path, source_file, context)
        elif extension == '.script':
            self._parse_script_file(file_path, source_file, context)
        elif extension == '.amd':
            self._parse_amd_file(file_path, source_file, context)
        elif extension in {'.pod', '.smd'}:
            # TODO: Implement POD and SMD parsing
            print(f"📝 {extension} parsing not yet implemented for {file_path}")
    
    def _parse_pmd_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .pmd file into a PMDModel."""
        try:
            # Simple JSON parsing for PMD files
            content = source_file.content.strip()
            path_obj = Path(file_path)
            
            # Try to parse as JSON first
            try:
                pmd_data = json.loads(content)
                pmd_model = PMDModel(
                    pageId=pmd_data.get('pageId', 'unknown'),
                    securityDomains=pmd_data.get('securityDomains', []),
                    inboundEndpoints=pmd_data.get('inboundEndpoints', {}),
                    outboundEndpoints=pmd_data.get('outboundEndpoints', {}),
                    presentation=PMDPresentation(
                        widgets=pmd_data.get('presentation', {}).get('widgets', [])
                    ) if pmd_data.get('presentation') else None,
                    onLoad=pmd_data.get('onLoad'),
                    script=pmd_data.get('script'),
                    includes=PMDIncludes(
                        scripts=pmd_data.get('includes', {}).get('scripts', [])
                    ) if pmd_data.get('includes') else None,
                    file_path=file_path
                )
                context.pmds[pmd_model.pageId] = pmd_model
                print(f"✅ Parsed PMD: {pmd_model.pageId}")
                
            except json.JSONDecodeError:
                # Fallback: treat as plain text with basic extraction
                pmd_model = PMDModel(
                    pageId=path_obj.stem,  # Use filename as pageId
                    file_path=file_path,
                    onLoad=content if 'onLoad' in content else None,
                    script=content if 'script' in content else None
                )
                context.pmds[pmd_model.pageId] = pmd_model
                print(f"✅ Parsed PMD (fallback): {pmd_model.pageId}")
                
        except Exception as e:
            print(f"❌ Failed to parse PMD file {file_path}: {e}")
            raise
    
    def _parse_script_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .script file into a ScriptModel."""
        try:
            script_model = ScriptModel(
                source=source_file.content,
                file_path=file_path
            )
            context.scripts[Path(file_path).name] = script_model
            print(f"✅ Parsed Script: {Path(file_path).name}")
            
        except Exception as e:
            print(f"❌ Failed to parse script file {file_path}: {e}")
            raise
    
    def _parse_amd_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse an .amd file into an AMDModel."""
        try:
            content = source_file.content.strip()
            
            try:
                amd_data = json.loads(content)
                amd_model = AMDModel(
                    routes=amd_data.get('routes', {}),
                    baseUrls=amd_data.get('baseUrls', {}),
                    flows=amd_data.get('flows', {}),
                    file_path=file_path
                )
                context.amd = amd_model
                print(f"✅ Parsed AMD: {file_path}")
                
            except json.JSONDecodeError:
                # Fallback: create basic AMD model
                amd_model = AMDModel(
                    routes={},
                    file_path=file_path
                )
                context.amd = amd_model
                print(f"✅ Parsed AMD (fallback): {file_path}")
                
        except Exception as e:
            print(f"❌ Failed to parse AMD file {file_path}: {e}")
            raise
