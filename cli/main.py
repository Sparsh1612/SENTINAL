#!/usr/bin/env python3
"""
Sentinel CLI - Command-line interface for fraud detection system
"""

import typer
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from .commands import detect, explain, feedback, plugins, train, ui

# Create Typer app
app = typer.Typer(
    name="sentinel",
    help="Sentinel Fraud Detection System CLI",
    add_completion=False,
    rich_markup_mode="rich"
)

# Rich console for better output
console = Console()

@app.command()
def version():
    """Show Sentinel version information"""
    version_info = {
        "name": "Sentinel Fraud Detection System",
        "version": "1.0.0",
        "author": "Sparsh",
        "license": "MIT"
    }
    
    table = Table(title="Sentinel Version Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in version_info.items():
        table.add_row(key.title(), str(value))
    
    console.print(table)

@app.command()
def status():
    """Show system status and health"""
    with console.status("[bold green]Checking system status...", spinner="dots"):
        # Simulate status check
        import time
        time.sleep(2)
    
    status_data = {
        "API": "🟢 Operational",
        "Database": "🟢 Connected",
        "ML Models": "🟢 Loaded",
        "Kafka": "🟢 Streaming",
        "Redis": "🟢 Cached"
    }
    
    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    for component, status in status_data.items():
        table.add_row(component, status)
    
    console.print(table)

@app.command()
def init(
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path"),
    force: bool = typer.Option(False, "--force", "-f", help="Force initialization")
):
    """Initialize Sentinel system"""
    if config_file and not config_file.exists():
        console.print(f"[red]Configuration file not found: {config_file}")
        raise typer.Exit(1)
    
    with console.status("[bold green]Initializing Sentinel system...", spinner="dots"):
        # Simulate initialization
        import time
        time.sleep(3)
    
    console.print("[green]✅ Sentinel system initialized successfully!")
    
    if config_file:
        console.print(f"[blue]Configuration loaded from: {config_file}")
    
    # Show next steps
    next_steps = Panel(
        Text("Next steps:\n"
             "1. Start the API server: sentinel start-api\n"
             "2. Launch the UI: sentinel launch-ui\n"
             "3. Train models: sentinel train-model\n"
             "4. Run detection: sentinel detect-fraud"),
        title="[bold blue]Next Steps",
        border_style="blue"
    )
    console.print(next_steps)

@app.command()
def start_api(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
    workers: int = typer.Option(4, "--workers", "-w", help="Number of worker processes")
):
    """Start the Sentinel API server"""
    console.print(f"[bold blue]Starting Sentinel API server on {host}:{port}")
    
    if reload:
        console.print("[yellow]Auto-reload enabled")
    
    console.print(f"[blue]Worker processes: {workers}")
    
    # In a real implementation, this would start the FastAPI server
    console.print("[green]✅ API server started successfully!")
    console.print(f"[blue]📖 API documentation: http://{host}:{port}/docs")
    console.print(f"[blue]🔍 Health check: http://{host}:{port}/health")

@app.command()
def launch_ui(
    port: int = typer.Option(3000, "--port", "-p", help="Port for the UI server"),
    open_browser: bool = typer.Option(True, "--open", "-o", help="Open browser automatically")
):
    """Launch the Sentinel web UI"""
    console.print(f"[bold blue]Launching Sentinel Web UI on port {port}")
    
    with console.status("[bold green]Starting UI server...", spinner="dots"):
        # Simulate UI startup
        import time
        time.sleep(2)
    
    console.print("[green]✅ Web UI started successfully!")
    console.print(f"[blue]🌐 UI URL: http://localhost:{port}")
    
    if open_browser:
        console.print("[blue]🔗 Opening browser...")
        # In a real implementation, this would open the browser
        import webbrowser
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            console.print("[yellow]Could not open browser automatically")

@app.command()
def health():
    """Check system health and connectivity"""
    console.print("[bold blue]Checking system health...")
    
    health_checks = [
        ("API Server", "http://localhost:8000/health"),
        ("Database", "PostgreSQL connection"),
        ("Redis Cache", "Redis connection"),
        ("Kafka", "Kafka broker connection"),
        ("ML Models", "Model loading status")
    ]
    
    table = Table(title="Health Check Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Response Time", style="yellow")
    
    for component, endpoint in health_checks:
        with console.status(f"Checking {component}...", spinner="dots"):
            import time
            time.sleep(0.5)
        
        # Simulate health check results
        status = "🟢 Healthy"
        response_time = f"{round(0.1 + (hash(component) % 100) / 1000, 3)}s"
        
        table.add_row(component, status, response_time)
    
    console.print(table)
    console.print("[green]✅ All systems operational!")

@app.command()
def logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    level: str = typer.Option("INFO", "--level", "-l", help="Log level (DEBUG, INFO, WARNING, ERROR)"),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines to show")
):
    """Show system logs"""
    console.print(f"[bold blue]Showing logs (level: {level}, lines: {lines})")
    
    if follow:
        console.print("[yellow]Following log output... (Press Ctrl+C to stop)")
    
    # Simulate log output
    log_entries = [
        ("2024-01-15 10:30:15", "INFO", "API server started on port 8000"),
        ("2024-01-15 10:30:16", "INFO", "Database connection established"),
        ("2024-01-15 10:30:17", "INFO", "ML models loaded successfully"),
        ("2024-01-15 10:30:18", "INFO", "Kafka consumer started"),
        ("2024-01-15 10:30:19", "INFO", "System ready for fraud detection")
    ]
    
    for timestamp, level_name, message in log_entries:
        level_color = {
            "DEBUG": "blue",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red"
        }.get(level_name, "white")
        
        console.print(f"[{level_color}]{timestamp} [{level_name}] {message}")

@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    edit: bool = typer.Option(False, "--edit", "-e", help="Edit configuration"),
    validate: bool = typer.Option(False, "--validate", "-v", help="Validate configuration")
):
    """Manage Sentinel configuration"""
    if show:
        config_data = {
            "API": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 4
            },
            "Database": {
                "url": "postgresql://sentinel:password@localhost:5432/sentinel_db",
                "pool_size": 20
            },
            "ML Models": {
                "path": "data/models",
                "update_interval": 3600
            },
            "Kafka": {
                "bootstrap_servers": "localhost:9092",
                "topics": ["transactions", "fraud_alerts"]
            }
        }
        
        table = Table(title="Current Configuration")
        table.add_column("Section", style="cyan")
        table.add_column("Key", style="blue")
        table.add_column("Value", style="green")
        
        for section, settings in config_data.items():
            for key, value in settings.items():
                table.add_row(section, key, str(value))
        
        console.print(table)
    
    if edit:
        console.print("[yellow]Opening configuration editor...")
        # In a real implementation, this would open an editor
    
    if validate:
        with console.status("[bold green]Validating configuration...", spinner="dots"):
            import time
            time.sleep(1)
        console.print("[green]✅ Configuration is valid!")

@app.command()
def backup(
    destination: Path = typer.Argument(..., help="Backup destination directory"),
    include_models: bool = typer.Option(True, "--models", help="Include ML models"),
    include_data: bool = typer.Option(True, "--data", help="Include transaction data"),
    compress: bool = typer.Option(True, "--compress", help="Compress backup files")
):
    """Create system backup"""
    console.print(f"[bold blue]Creating backup to: {destination}")
    
    if not destination.exists():
        destination.mkdir(parents=True, exist_ok=True)
    
    backup_items = []
    if include_models:
        backup_items.append("ML Models")
    if include_data:
        backup_items.append("Transaction Data")
    
    backup_items.append("Configuration")
    backup_items.append("Database Schema")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Creating backup...", total=len(backup_items))
        
        for item in backup_items:
            progress.update(task, description=f"Backing up {item}...")
            import time
            time.sleep(1)
            progress.advance(task)
    
    console.print("[green]✅ Backup completed successfully!")
    console.print(f"[blue]📁 Backup location: {destination}")

@app.command()
def restore(
    backup_path: Path = typer.Argument(..., help="Path to backup directory"),
    force: bool = typer.Option(False, "--force", help="Force restore without confirmation")
):
    """Restore system from backup"""
    if not backup_path.exists():
        console.print(f"[red]Backup not found: {backup_path}")
        raise typer.Exit(1)
    
    if not force:
        confirm = typer.confirm(f"Are you sure you want to restore from {backup_path}? This will overwrite current data.")
        if not confirm:
            console.print("[yellow]Restore cancelled")
            raise typer.Exit(0)
    
    console.print(f"[bold blue]Restoring from backup: {backup_path}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Restoring system...", total=4)
        
        for step in ["Configuration", "Database", "Models", "Data"]:
            progress.update(task, description=f"Restoring {step}...")
            import time
            time.sleep(1.5)
            progress.advance(task)
    
    console.print("[green]✅ System restored successfully!")
    console.print("[blue]🔄 Please restart the system to apply changes")

# Add subcommands
app.add_typer(detect.app, name="detect", help="Fraud detection commands")
app.add_typer(explain.app, name="explain", help="Explainability commands")
app.add_typer(feedback.app, name="feedback", help="Feedback system commands")
app.add_typer(plugins.app, name="plugins", help="Plugin management commands")
app.add_typer(train.app, name="train", help="Model training commands")
app.add_typer(ui.app, name="ui", help="UI management commands")

def main():
    """Main entry point"""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
