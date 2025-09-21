"""
Parser to convert source files into PMD models for analysis.
"""
import json
from pathlib import Path
from typing import Dict, Any
from .models import ProjectContext, PMDModel, ScriptModel, AMDModel, PMDIncludes, PMDPresentation, PODModel, PODSeed, SMDModel
from .pmd_preprocessor import preprocess_pmd_content


class ModelParser:
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
                print(f"Failed to parse {file_path}: {e}")
                context.parsing_errors.append(f"{file_path}: {e}")
        
        return context
    
    def _parse_single_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a single source file based on its extension."""
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        if extension == '.pmd':
            self._parse_pmd_file(file_path, source_file, context)
        elif extension == '.amd':
            self._parse_amd_file(file_path, source_file, context)
        elif extension == '.smd':
            self._parse_smd_file(file_path, source_file, context)
        elif extension == '.pod':
            self._parse_pod_file(file_path, source_file, context)
        elif extension == '.script':
            self._parse_script_file(file_path, source_file, context)
    
    def _parse_pmd_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .pmd file into a PMDModel."""
        try:
            # Preprocess the content to handle multi-line script sections
            content = source_file.content.strip()
            path_obj = Path(file_path)
            
            # Preprocess the PMD content
            processed_content, line_mappings = preprocess_pmd_content(content)
            
            # Try to parse as JSON
            try:
                pmd_data = json.loads(processed_content)

                # Extract presentation data - handle the nested structure properly
                presentation_data = pmd_data.get('presentation', {})

                # Handle includes - convert to PMDIncludes format
                includes_data = pmd_data.get('include', [])
                if isinstance(includes_data, list):
                    includes = PMDIncludes(scripts=includes_data)
                else:
                    includes = None
                
                pmd_model = PMDModel(
                    pageId=pmd_data.get('id', path_obj.stem),  # Use 'id' field or fallback to filename
                    securityDomains=pmd_data.get('securityDomains', []),
                    inboundEndpoints=pmd_data.get('endPoints', []), 
                    outboundEndpoints=pmd_data.get('outboundData', {}).get('outboundEndPoints', []),  # Handle nested structure
                    presentation=PMDPresentation(attributes={}, title=presentation_data.get("title", {}), body=presentation_data.get("body", []), footer=presentation_data.get("footer", {})) if presentation_data else None,
                    onLoad=pmd_data.get('onLoad'),
                    script=pmd_data.get('script'),
                    includes=includes,
                    file_path=file_path,
                    source_content=content  # Store the original content for line offset calculation
                )
                
                # Set line mappings for proper error reporting
                pmd_model.set_line_mappings(line_mappings)
                
                context.pmds[pmd_model.pageId] = pmd_model
                print(f"Parsed PMD: {pmd_model.pageId}")
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed for {file_path}: {e}")
                # Fallback: treat as plain text with basic extraction
                pmd_model = PMDModel(
                    pageId=path_obj.stem,  # Use filename as pageId
                    file_path=file_path,
                    onLoad=content if 'onLoad' in content else None,
                    script=content if 'script' in content else None
                )
                context.pmds[pmd_model.pageId] = pmd_model
                print(f"Parsed PMD (fallback): {pmd_model.pageId}")
                
        except Exception as e:
            print(f"Failed to parse PMD file {file_path}: {e}")
            raise
    
    def _parse_script_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .script file into a ScriptModel."""
        try:
            script_model = ScriptModel(
                source=source_file.content,
                file_path=file_path
            )
            # Use the full filename (including extension) as the key since that's how it's referenced in PMD files
            context.scripts[Path(file_path).name] = script_model
            print(f"Parsed Script: {Path(file_path).name}")
            
        except Exception as e:
            print(f"Failed to parse script file {file_path}: {e}")
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
                print(f"Parsed AMD: {file_path}")
                
            except json.JSONDecodeError:
                # Fallback: create basic AMD model
                amd_model = AMDModel(
                    routes={},
                    file_path=file_path
                )
                context.amd = amd_model
                print(f"Parsed AMD (fallback): {file_path}")
                
        except Exception as e:
            print(f"Failed to parse AMD file {file_path}: {e}")
            raise
    
    def _parse_pod_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .pod file into a PODModel."""
        try:
            content = source_file.content.strip()
            
            try:
                pod_data = json.loads(content)
                
                # Extract seed data
                seed_data = pod_data.get('seed', {})
                seed = PODSeed(
                    parameters=seed_data.get('parameters', []),
                    endPoints=seed_data.get('endPoints', []),
                    template=seed_data.get('template', {})
                )
                
                pod_model = PODModel(
                    podId=pod_data.get('podId', Path(file_path).stem),
                    seed=seed,
                    file_path=file_path,
                    source_content=content
                )
                
                context.pods[pod_model.podId] = pod_model
                print(f"Parsed POD: {pod_model.podId}")
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error in POD file {file_path}: {e}")
                # Create a basic POD model as fallback
                pod_model = PODModel(
                    podId=Path(file_path).stem,
                    seed=PODSeed(),
                    file_path=file_path,
                    source_content=content
                )
                context.pods[pod_model.podId] = pod_model
                print(f"Parsed POD (fallback): {pod_model.podId}")
                
        except Exception as e:
            print(f"Failed to parse POD file {file_path}: {e}")
            raise

    def _parse_smd_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .smd file into an SMDModel."""
        try:
            content = source_file.content.strip()
            path_obj = Path(file_path)
            
            # Parse JSON content
            smd_data = json.loads(content)
            
            # Create SMD model
            smd_model = SMDModel(
                id=smd_data.get('id', path_obj.stem),
                applicationId=smd_data.get('applicationId', ''),
                siteId=smd_data.get('siteId', ''),
                languages=smd_data.get('languages', []),
                siteAuth=smd_data.get('siteAuth'),
                errorPageConfigurations=smd_data.get('errorPageConfigurations', []),
                file_path=file_path,
                source_content=content
            )
            
            # Add to context
            context.smds[smd_model.id] = smd_model
            print(f"Parsed SMD: {smd_model.id}")
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in SMD file {file_path}: {e}")
            # Create a basic SMD model as fallback
            smd_model = SMDModel(
                id=Path(file_path).stem,
                applicationId='',
                siteId='',
                file_path=file_path,
                source_content=content
            )
            context.smds[smd_model.id] = smd_model
            print(f"Parsed SMD (fallback): {smd_model.id}")
            
        except Exception as e:
            print(f"Failed to parse SMD file {file_path}: {e}")
            raise
