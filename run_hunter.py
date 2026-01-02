#!/usr/bin/env python3
"""
Hunter_v7 Launcher Script
Simple entry point for running Hunter_v7 with system checks
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    """Main launcher function"""
    
    # Display banner
    console.print(Panel.fit("""
🎯 Hunter_v7 - Advanced Social Media Target Acquisition Tool
═══════════════════════════════════════════════════════════
    
A sophisticated Python tool for intelligent profile discovery
Built with AI-powered filtering and advanced analysis capabilities
    """, style="bold blue"))
    
    # Check if we're in the right directory
    required_files = [
        'hunter_v7.py',
        'main_orchestrator.py', 
        'config.ini',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        console.print(f"[red]Missing required files: {', '.join(missing_files)}[/red]")
        console.print("[yellow]Please ensure all Hunter_v7 files are in the current directory.[/yellow]")
        return 1
    
    # Run system check
    console.print("[cyan]Running system compatibility check...[/cyan]")
    
    try:
        from utilities import validate_system_requirements
        if not validate_system_requirements():
            console.print("[red]System requirements not met. Please install missing components.[/red]")
            return 1
    except ImportError:
        console.print("[yellow]Could not run system check. Proceeding anyway...[/yellow]")
    
    # Check configuration
    console.print("[cyan]Checking configuration...[/cyan]")
    
    try:
        from hunter_v7 import ConfigManager
        config = ConfigManager()
        
        # Check if credentials are updated
        if config.get('CREDENTIALS', 'username') == 'your_instagram_username':
            console.print("[yellow]⚠ Instagram credentials not configured[/yellow]")
            console.print("[yellow]Please update the credentials in config.ini before running[/yellow]")
            
            proceed = input("Continue anyway? (y/N): ").lower().strip()
            if proceed != 'y':
                console.print("[yellow]Setup cancelled. Please update config.ini and try again.[/yellow]")
                return 1
    
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        return 1
    
    # Launch main orchestrator
    console.print("[bold green]🚀 Launching Hunter_v7...[/bold green]")
    console.print("Press Ctrl+C at any time to gracefully stop the session\n")
    
    try:
        from main_orchestrator import main as orchestrator_main
        return orchestrator_main()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Launch cancelled by user.[/yellow]")
        return 1
    except ImportError as e:
        console.print(f"[red]Import error: {e}[/red]")
        console.print("[yellow]Please ensure all dependencies are installed: pip install -r requirements.txt[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)