import typer
from pathlib import Path
from file_processing import FileProcessor
from parser.rules_engine import RulesEngine
from parser.app_parser import ModelParser
from parser.config import ExtendReviewerConfig
from parser.config_manager import load_configuration, get_config_manager
from output.formatter import OutputFormatter, OutputFormat

app = typer.Typer()

@app.command()
def review_app(
    zip_filepath: Path = typer.Argument(..., exists=True, help="Path to the application .zip file."),
    config_file: Path = typer.Option(None, "--config", "-c", help="Path to configuration file (JSON)"),
    output_format: str = typer.Option("console", "--format", "-f", help="Output format: console, json, summary, excel"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Output file path (optional)")
):
    """
    Kicks off the analysis of a Workday Extend application archive.
    """
    typer.echo(f"Starting review for '{zip_filepath.name}'...")
    
    # Load configuration using the layered configuration system
    try:
        config = load_configuration(str(config_file) if config_file else None)
        if config_file:
            typer.echo(f"Loaded configuration: {config_file}")
        else:
            typer.echo("Using default configuration with layered loading")
    except Exception as e:
        typer.secho(f"Error loading configuration: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    # This is the entry point to our pipeline.
    processor = FileProcessor()
    source_files_map = processor.process_zip_file(zip_filepath)

    if not source_files_map:
        typer.secho("No source files found to analyze. Exiting.", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    # --- Next Step: Pass 'source_files_map' to the Parser ---
    # For example:
    # asts = parse_all_files(source_files_map)
    # ... and so on.
    
    typer.echo("\nPipeline Input:")
    for path_key, source_file in source_files_map.items():
        typer.echo(f"  - Ready to parse: {path_key}")

    # --- Parse Files into App File Models ---
    typer.echo("\nParsing files into App File models...")
    try:
        pmd_parser = ModelParser()
        context = pmd_parser.parse_files(source_files_map)
        typer.echo(f"Parsed {len(context.pmds)} PMD files, {len(context.scripts)} script files")
        
    except Exception as e:
        typer.secho(f"Error parsing files: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # --- Run Rules Analysis ---
    typer.echo("\nRunning PMD Script Analysis...")
    try:
        rules_engine = RulesEngine(config)
        findings = rules_engine.run(context)
        
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
            typer.secho(f"Invalid output format: {output_format}. Use: console, json, summary, or excel", fg=typer.colors.RED)
            raise typer.Exit(1)
        
        formatter = OutputFormatter(format_type)
        total_files = len(context.pmds) + len(context.scripts) + (1 if context.amd else 0)
        total_rules = len(rules_engine.rules)
        
        formatted_output = formatter.format_results(findings, total_files, total_rules)
        
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
        
        # Set appropriate exit code based on findings
        if findings:
            severe_count = len([f for f in findings if f.severity == "SEVERE"])
            if severe_count > 0:
                raise typer.Exit(2)  # Exit code 2 for severe issues
            else:
                raise typer.Exit(1)  # Exit code 1 for warnings/info
        else:
            raise typer.Exit(0)  # Exit code 0 for no issues
            
    except Exception as e:
        typer.secho(f"Error running analysis: {e}", fg=typer.colors.RED)
        raise typer.Exit(3)  # Exit code 3 for analysis errors


@app.command()
def generate_config(
    output_file: Path = typer.Option("extend-reviewer-config.json", "--output", "-o", help="Output file path for the configuration")
):
    """
    Generate a default configuration file with all rules enabled.
    """
    config = ExtendReviewerConfig()
    config.to_file(str(output_file))
    typer.echo(f"Generated default configuration file: {output_file}")
    typer.echo("You can now edit this file to enable/disable rules and customize settings.")


@app.command()
def list_rules():
    """
    List all available rules and their current status.
    """
    config = ExtendReviewerConfig()
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
    typer.echo("🧙‍♂️ Arcane Auditor Configuration Status\n")
    
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