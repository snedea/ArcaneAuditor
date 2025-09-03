import typer
from pathlib import Path
from file_processing import FileProcessor
from parser.rules_engine import RulesEngine
from parser.app_parser import ModelParser

app = typer.Typer()

@app.command()
def review_app(
    zip_filepath: Path = typer.Argument(..., exists=True, help="Path to the application .zip file.")
):
    """
    Kicks off the analysis of a Workday Extend application archive.
    """
    typer.echo(f"Starting review for '{zip_filepath.name}'...")
    
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
        rules_engine = RulesEngine()
        findings = rules_engine.run(context)
        
        if findings:
            typer.echo(f"\n📋 Found {len(findings)} issue(s):")
            for finding in findings:
                typer.echo(f"  {finding}")
        else:
            typer.echo("✅ No issues found!")
            
    except Exception as e:
        typer.secho(f"❌ Error running analysis: {e}", fg=typer.colors.RED)


if __name__ == "__main__":
    app()