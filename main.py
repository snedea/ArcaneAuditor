import typer
import time
from pathlib import Path
from file_processing import FileProcessor
from parser.rules_engine import RulesEngine
from parser.app_parser import ModelParser
from parser.config import ArcaneAuditorConfig
from parser.config_manager import load_configuration, get_config_manager
from output.formatter import OutputFormatter, OutputFormat

app = typer.Typer()

@app.command()
def review_app(
    zip_filepath: Path = typer.Argument(..., exists=True, help="Path to the application .zip file."),
    config_file: Path = typer.Option(None, "--config", "-c", help="Path to configuration file (JSON)"),
    output_format: str = typer.Option("console", "--format", "-f", help="Output format: console, json, summary, excel"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Output file path (optional)"),
    show_timing: bool = typer.Option(False, "--timing", "-t", help="Show detailed timing information")
):
    """
    Kicks off the analysis of a Workday Extend application archive.
    """
    # Start overall timing
    overall_start_time = time.time()
    
    typer.echo(f"Starting review for '{zip_filepath.name}'...")
    
    # Load configuration using the layered configuration system
    config_start_time = time.time()
    try:
        config = load_configuration(str(config_file) if config_file else None)
        if config_file:
            typer.echo(f"📋 Loaded configuration: {config_file}")
        else:
            typer.echo("📋 Using default configuration with layered loading")
    except Exception as e:
        typer.secho(f"❌ Configuration Error: {e}", fg=typer.colors.RED)
        typer.echo("💡 Try using --config with a valid configuration file, or run without --config for defaults")
        raise typer.Exit(1)
    
    config_time = time.time() - config_start_time
    if show_timing:
        typer.echo(f"⏱️  Configuration loading: {config_time:.2f}s")
    
    # This is the entry point to our pipeline.
    typer.echo("📁 Extracting and processing files...")
    file_processing_start_time = time.time()
    processor = FileProcessor()
    source_files_map = processor.process_zip_file(zip_filepath)
    file_processing_time = time.time() - file_processing_start_time
    typer.echo(f"✅ Found {len(source_files_map)} relevant files to analyze")
    if show_timing:
        typer.echo(f"⏱️  File processing: {file_processing_time:.2f}s")

    if not source_files_map:
        typer.secho("❌ No source files found to analyze.", fg=typer.colors.RED)
        typer.echo("💡 Make sure your ZIP contains .pmd, .pod, .script, .amd, or .smd files")
        raise typer.Exit(1)
        
    # --- Next Step: Pass 'source_files_map' to the Parser ---
    # For example:
    # asts = parse_all_files(source_files_map)
    # ... and so on.
    
    typer.echo("\nPipeline Input:")
    for path_key, source_file in source_files_map.items():
        typer.echo(f"  - Ready to parse: {path_key}")

    # --- Parse Files into App File Models ---
    typer.echo("🔍 Parsing files into App File models...")
    parsing_start_time = time.time()
    try:
        pmd_parser = ModelParser()
        context = pmd_parser.parse_files(source_files_map)
        parsing_time = time.time() - parsing_start_time
        
        # Better summary of what was parsed
        parsed_summary = []
        if context.pmds: parsed_summary.append(f"{len(context.pmds)} PMD files")
        if context.scripts: parsed_summary.append(f"{len(context.scripts)} script files")
        if context.pods: parsed_summary.append(f"{len(context.pods)} Pod files")
        if context.smds: parsed_summary.append(f"{len(context.smds)} SMD file")
        if context.amd: parsed_summary.append("AMD file")
        
        if parsed_summary:
            typer.echo(f"✅ Parsed: {', '.join(parsed_summary)}")
        else:
            typer.echo("⚠️ No files were successfully parsed")
        
        if show_timing:
            typer.echo(f"⏱️  File parsing: {parsing_time:.2f}s")
        
    except Exception as e:
        typer.secho(f"❌ Parsing Error: {e}", fg=typer.colors.RED)
        typer.echo("💡 Check that your files are valid Workday Extend format")
        raise typer.Exit(1)

    # --- Run Rules Analysis ---
    typer.echo("🔮 Initializing rules engine...")
    findings = []  # Initialize findings before try block
    try:
        rules_init_start_time = time.time()
        rules_engine = RulesEngine(config)
        rules_init_time = time.time() - rules_init_start_time
        typer.echo(f"✅ Loaded {len(rules_engine.rules)} validation rules")
        if show_timing:
            typer.echo(f"⏱️  Rules engine initialization: {rules_init_time:.2f}s")
        
        typer.echo("🔮 Invoking analysis...")
        analysis_start_time = time.time()
        findings = rules_engine.run(context)
        analysis_time = time.time() - analysis_start_time
        
        if findings:
            typer.echo(f"✅ Analysis complete. Found {len(findings)} issue(s).")
        else:
            typer.echo("✅ Analysis complete. No issues found! 🎉")
        
        if show_timing:
            typer.echo(f"⏱️  Analysis execution: {analysis_time:.2f}s")
        
        # Auto-detect format based on output file extension if not explicitly specified
        if output_file and output_format == "console":  # Default format
            file_ext = output_file.suffix.lower()
            if file_ext == '.xlsx':
                output_format = "excel"
                typer.echo("Auto-detected Excel format based on .xlsx extension")
            elif file_ext == '.json':
                output_format = "json" 
                typer.echo("Auto-detected JSON format based on .json extension")
        
        # Format output based on selected format
        try:
            format_type = OutputFormat(output_format.lower())
        except ValueError:
            typer.secho(f"❌ Invalid output format: {output_format}", fg=typer.colors.RED)
            typer.echo("💡 Valid formats: console, json, summary, excel")
            raise typer.Exit(1)
        
        formatting_start_time = time.time()
        formatter = OutputFormatter(format_type)
        total_files = len(context.pmds) + len(context.scripts) + (1 if context.amd else 0)
        total_rules = len(rules_engine.rules)
        
        formatted_output = formatter.format_results(findings, total_files, total_rules)
        formatting_time = time.time() - formatting_start_time
        
        if show_timing:
            typer.echo(f"⏱️  Output formatting: {formatting_time:.2f}s")
        
        # Output to file or console
        if output_file:
            if format_type == OutputFormat.EXCEL:
                # For Excel, the formatter returns the file path
                import shutil
                try:
                    shutil.move(formatted_output, str(output_file))
                    typer.echo(f"Excel file written to: {output_file}")
                except Exception as e:
                    typer.secho(f"Error moving Excel file: {e}", fg=typer.colors.RED)
                    typer.echo(f"Excel file created at: {formatted_output}")
            else:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(formatted_output)
                typer.echo(f"Results written to: {output_file}")
        else:
            if format_type == OutputFormat.EXCEL:
                typer.echo(f"Excel file created at: {formatted_output}")
            else:
                typer.echo(formatted_output)
                
    except Exception as e:
        typer.secho(f"❌ Analysis Error: {e}", fg=typer.colors.RED)
        typer.echo("💡 This might be due to unsupported syntax or corrupted files")
        raise typer.Exit(3)  # Exit code 3 for analysis errors
    
    # Calculate total time and show timing summary
    total_time = time.time() - overall_start_time
    
    if show_timing:
        typer.echo("\n" + "="*60)
        typer.echo("📊 TIMING SUMMARY")
        typer.echo("="*60)
        
        # Calculate percentages
        config_pct = (config_time / total_time) * 100 if total_time > 0 else 0
        file_proc_pct = (file_processing_time / total_time) * 100 if total_time > 0 else 0
        parsing_pct = (parsing_time / total_time) * 100 if total_time > 0 else 0
        rules_init_pct = (rules_init_time / total_time) * 100 if total_time > 0 else 0
        analysis_pct = (analysis_time / total_time) * 100 if total_time > 0 else 0
        formatting_pct = (formatting_time / total_time) * 100 if total_time > 0 else 0
        
        typer.echo(f"🕐 Total Analysis Time: {total_time:.2f}s")
        typer.echo()
        typer.echo("📈 Stage Breakdown:")
        typer.echo(f"  Analysis Execution: {analysis_time:.2f}s ({analysis_pct:.1f}%)")
        typer.echo(f"  File Parsing: {parsing_time:.2f}s ({parsing_pct:.1f}%)")
        typer.echo(f"  File Processing: {file_processing_time:.2f}s ({file_proc_pct:.1f}%)")
        typer.echo(f"  Output Formatting: {formatting_time:.2f}s ({formatting_pct:.1f}%)")
        typer.echo(f"  Rules Engine Init: {rules_init_time:.2f}s ({rules_init_pct:.1f}%)")
        typer.echo(f"  Configuration Loading: {config_time:.2f}s ({config_pct:.1f}%)")
        
        # Performance assessment
        typer.echo()
        typer.echo("🎯 Performance Assessment:")
        if total_time < 30:
            typer.echo("  ✅ Excellent performance (<30s)")
        elif total_time < 60:
            typer.echo("  ✅ Good performance (<60s)")
        elif total_time < 120:
            typer.echo("  ⚠️  Moderate performance (<2min)")
        else:
            typer.echo("  ❌ Slow performance (>2min)")
            typer.echo("  💡 Consider using --timing to identify bottlenecks")
        
        # Bottleneck identification
        if analysis_pct > 70:
            typer.echo("  🔍 Analysis execution is the primary bottleneck")
            typer.echo("  💡 Consider disabling CPU-intensive rules for faster analysis")
        elif parsing_pct > 30:
            typer.echo("  🔍 File parsing is a significant bottleneck")
            typer.echo("  💡 Consider reducing parallel workers or file size limits")
        
        typer.echo("="*60)
    else:
        typer.echo(f"\n⏱️  Total analysis time: {total_time:.2f}s")
        typer.echo("💡 Use --timing flag for detailed performance breakdown")
    
    # Set appropriate exit code based on findings (outside try block)
    if findings:
        severe_count = len([f for f in findings if f.severity == "SEVERE"])
        if severe_count > 0:
            typer.echo(f"🚨 Analysis completed with {severe_count} severe issue(s)")
            raise typer.Exit(2)  # Exit code 2 for severe issues
        else:
            typer.echo("⚠️ Analysis completed with warnings/info issues")
            raise typer.Exit(1)  # Exit code 1 for warnings/info
    else:
        typer.echo("✅ Analysis completed successfully - no issues found!")
        raise typer.Exit(0)  # Exit code 0 for no issues


@app.command()
def generate_config(
    output_file: Path = typer.Option("arcane-auditor-config.json", "--output", "-o", help="Output file path for the configuration")
):
    """
    Generate a default configuration file with all rules enabled.
    """
    config = ArcaneAuditorConfig()
    config.to_file(str(output_file))
    typer.echo(f"Generated default configuration file: {output_file}")
    typer.echo("You can now edit this file to enable/disable rules and customize settings.")


@app.command()
def list_rules():
    """
    List all available rules and their current status.
    """
    config = ArcaneAuditorConfig()
    typer.echo("Available rules:")
    typer.echo("=" * 80)
    
    # Use the rules engine to discover all available rules dynamically
    rules_engine = RulesEngine(config)
    
    # Get all discovered rules
    discovered_rules = rules_engine.rules
    
    if not discovered_rules:
        typer.echo("No rules discovered.")
        return
    
    # Group rules by category for better organization
    script_rules = []
    structure_rules = []
    other_rules = []
    
    for rule in discovered_rules:
        rule_name = rule.__class__.__name__
        if rule_name.startswith("Script"):
            script_rules.append(rule)
        elif rule_name.startswith(("Widget", "Endpoint", "Footer", "String")):
            structure_rules.append(rule)
        else:
            other_rules.append(rule)
    
    # Display script rules
    if script_rules:
        typer.echo("SCRIPT RULES:")
        typer.echo("-" * 40)
        for rule in sorted(script_rules, key=lambda r: r.__class__.__name__):
            rule_name = rule.__class__.__name__
            status = "ENABLED" if config.is_rule_enabled(rule_name) else "DISABLED"
            severity = config.get_rule_severity(rule_name, rule.SEVERITY)
            description = getattr(rule, 'DESCRIPTION', 'No description available')
            
            typer.echo(f"{rule_name}: {status} (severity: {severity})")
            typer.echo(f"  {description}")
            typer.echo()
    
    # Display structure rules
    if structure_rules:
        typer.echo("STRUCTURE RULES:")
        typer.echo("-" * 40)
        for rule in sorted(structure_rules, key=lambda r: r.__class__.__name__):
            rule_name = rule.__class__.__name__
            status = "ENABLED" if config.is_rule_enabled(rule_name) else "DISABLED"
            severity = config.get_rule_severity(rule_name, rule.SEVERITY)
            description = getattr(rule, 'DESCRIPTION', 'No description available')
            
            typer.echo(f"{rule_name}: {status} (severity: {severity})")
            typer.echo(f"  {description}")
            typer.echo()
    
    # Display other rules
    if other_rules:
        typer.echo("OTHER RULES:")
        typer.echo("-" * 40)
        for rule in sorted(other_rules, key=lambda r: r.__class__.__name__):
            rule_name = rule.__class__.__name__
            status = "ENABLED" if config.is_rule_enabled(rule_name) else "DISABLED"
            severity = config.get_rule_severity(rule_name, rule.SEVERITY)
            description = getattr(rule, 'DESCRIPTION', 'No description available')
            
            typer.echo(f"{rule_name}: {status} (severity: {severity})")
            typer.echo(f"  {description}")
            typer.echo()
    
    typer.echo(f"Total: {len(discovered_rules)} rules discovered")


@app.command()
def list_configs():
    """List all available configurations and their safety status."""
    typer.echo("🔮 Arcane Auditor Configuration Status\n")
    
    config_manager = get_config_manager()
    
    # List available configurations
    available_configs = config_manager.list_available_configs()
    
    if not available_configs:
        typer.echo("No configurations found.")
        return
    
    typer.echo("📁 Available Configurations:")
    for directory, configs in available_configs.items():
        if directory == "local_configs":
            icon = "🏠"
            desc = "Personal overrides (highest priority)"
        elif directory == "user_configs":
            icon = "🛡️"
            desc = "Team/project configs (update-safe)"
        else:
            icon = "🔒"
            desc = "App defaults (may be updated)"
        
        typer.echo(f"\n{icon} {directory}/ - {desc}")
        for config in configs:
            typer.echo(f"  - {config}")
    
    # Check safety status
    typer.echo("\n🛡️ Configuration Safety Status:")
    safety_status = config_manager.validate_config_safety()
    
    for directory, status in safety_status.items():
        if "Protected" in status:
            color = typer.colors.GREEN
            icon = "✅"
        elif "Warning" in status:
            color = typer.colors.YELLOW
            icon = "⚠️"
        elif "App-managed" in status:
            color = typer.colors.BLUE
            icon = "🔒"
        else:
            color = typer.colors.RED
            icon = "❌"
        
        typer.secho(f"{icon} {directory}/: {status}", fg=color)
    
    typer.echo("\n💡 Usage Examples:")
    typer.echo("  uv run main.py review-app myapp.zip --config team-standard")
    typer.echo("  uv run main.py review-app myapp.zip --config user_configs/my-config.json")
    typer.echo("  uv run main.py list-configs  # Show this information")


if __name__ == "__main__":
    app()