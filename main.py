import typer
from pathlib import Path
from file_processing import FileProcessor
from parser.rules_engine import RulesEngine
from parser.app_parser import ModelParser
from parser.config import ExtendReviewerConfig

app = typer.Typer()

@app.command()
def review_app(
    zip_filepath: Path = typer.Argument(..., exists=True, help="Path to the application .zip file."),
    config_file: Path = typer.Option(None, "--config", "-c", help="Path to configuration file (JSON)")
):
    """
    Kicks off the analysis of a Workday Extend application archive.
    """
    typer.echo(f"Starting review for '{zip_filepath.name}'...")
    
    # Load configuration if provided
    config = None
    if config_file:
        if not config_file.exists():
            typer.secho(f"❌ Configuration file not found: {config_file}", fg=typer.colors.RED)
            raise typer.Exit(1)
        try:
            config = ExtendReviewerConfig.from_file(str(config_file))
            typer.echo(f"✅ Loaded configuration from {config_file}")
        except Exception as e:
            typer.secho(f"❌ Error loading configuration: {e}", fg=typer.colors.RED)
            raise typer.Exit(1)
    else:
        config = ExtendReviewerConfig()  # Use default configuration
        typer.echo("ℹ️  Using default configuration (no config file specified)")
    
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
    typer.echo("\n🔍 Parsing files into App File models...")
    try:
        pmd_parser = ModelParser()
        context = pmd_parser.parse_files(source_files_map)
        typer.echo(f"✅ Parsed {len(context.pmds)} PMD files, {len(context.scripts)} script files")
        
    except Exception as e:
        typer.secho(f"❌ Error parsing files: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # --- Run Rules Analysis ---
    typer.echo("\n🔍 Running PMD Script Analysis...")
    try:
        rules_engine = RulesEngine(config)
        findings = rules_engine.run(context)
        
        if findings:
            typer.echo(f"\n📋 Found {len(findings)} issue(s):")
            for finding in findings:
                typer.echo(f"  {finding}")
        else:
            typer.echo("✅ No issues found!")
            
    except Exception as e:
        typer.secho(f"❌ Error running analysis: {e}", fg=typer.colors.RED)


@app.command()
def generate_config(
    output_file: Path = typer.Option("extend-reviewer-config.json", "--output", "-o", help="Output file path for the configuration")
):
    """
    Generate a default configuration file with all rules enabled.
    """
    config = ExtendReviewerConfig()
    config.to_file(str(output_file))
    typer.echo(f"✅ Generated default configuration file: {output_file}")
    typer.echo("You can now edit this file to enable/disable rules and customize settings.")


@app.command()
def list_rules():
    """
    List all available rules and their current status.
    """
    config = ExtendReviewerConfig()
    typer.echo("Available rules:")
    typer.echo("=" * 50)
    
    # Get all rule configurations
    rule_configs = config.rules.model_dump()
    
    for rule_id, rule_config in rule_configs.items():
        status = "✅ ENABLED" if rule_config["enabled"] else "❌ DISABLED"
        severity = rule_config.get("severity_override") or "default"
        typer.echo(f"{rule_id}: {status} (severity: {severity})")


if __name__ == "__main__":
    app()