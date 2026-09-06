"""
Windows Automation Controller
Unified interface for natural language Windows automation using SmolLM2 via Ollama.

Usage:
    from windows_automation import WindowsAutomation
    
    auto = WindowsAutomation()
    auto.run("open chrome")
    auto.run("search for pdf files")
    auto.run("take a screenshot")
"""

import json
from typing import Optional, Dict, Any, Tuple

from windows_command_generator import WindowsCommandGenerator
from command_executor import CommandExecutor


class WindowsAutomation:
    """
    Main interface for Windows automation using natural language.
    Uses SmolLM2 via Ollama to interpret commands and execute them.
    """
    
    def __init__(self, model_name: str = "smollm2", ollama_url: str = None):
        """
        Initialize the Windows Automation system.
        
        Args:
            model_name: Ollama model name (default: smollm2)
            ollama_url: Ollama API URL (default: http://localhost:11434/api/generate)
        """
        self.generator = WindowsCommandGenerator(model_name=model_name, ollama_url=ollama_url)
        self.executor = CommandExecutor()
        self.last_command = None
        self.last_result = None
        
    def check_status(self) -> bool:
        """
        Check if the automation system is ready.
        
        Returns:
            True if Ollama is running with the required model
        """
        return self.generator.check_ollama_status()
    
    def generate(self, natural_language: str) -> Optional[Dict[str, Any]]:
        """
        Generate a command from natural language without executing it.
        
        Args:
            natural_language: The user's command in plain English
            
        Returns:
            The structured command dict
        """
        self.last_command = self.generator.generate_command(natural_language)
        return self.last_command
    
    def execute(self, command: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Execute a structured command.
        
        Args:
            command: The structured command dict
            
        Returns:
            Tuple of (success, message)
        """
        self.last_result = self.executor.execute(command)
        return self.last_result
    
    def run(self, natural_language: str) -> Tuple[bool, str]:
        """
        Generate and execute a command from natural language.
        
        Args:
            natural_language: The user's command in plain English
            
        Returns:
            Tuple of (success, message)
        """
        # Generate the command
        command = self.generate(natural_language)
        
        if not command:
            return False, "Failed to generate command"
        
        # Execute the command
        return self.execute(command)
    
    def get_last_command(self) -> Optional[Dict[str, Any]]:
        """Get the last generated command."""
        return self.last_command
    
    def get_last_result(self) -> Optional[Tuple[bool, str]]:
        """Get the result of the last execution."""
        return self.last_result


def main():
    """Interactive command line interface."""
    print("=" * 60)
    print("   Windows Automation with SmolLM2")
    print("   Natural Language → Windows Commands")
    print("=" * 60)
    print()
    
    auto = WindowsAutomation()
    
    # Check system status
    print("Checking system status...")
    if not auto.check_status():
        print("\n⚠️  System not ready. Please ensure Ollama is running with SmolLM2.")
        print("\nSetup instructions:")
        print("  1. Install Ollama: https://ollama.ai")
        print("  2. Start Ollama: ollama serve")
        print("  3. Pull SmolLM2: ollama pull smollm2")
        print("\nPress Enter to continue anyway or Ctrl+C to exit...")
        try:
            input()
        except KeyboardInterrupt:
            return
    
    print("\n" + "-" * 60)
    print("Ready! Type your commands in natural language.")
    print("Examples:")
    print("  - 'open chrome'")
    print("  - 'search for pdf files'")
    print("  - 'take a screenshot'")
    print("  - 'create a folder called Projects on desktop'")
    print("  - 'open task manager'")
    print("Type 'quit' or 'exit' to stop.")
    print("-" * 60 + "\n")
    
    while True:
        try:
            user_input = input("🎤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "bye", "stop"]:
                print("👋 Goodbye!")
                break
            
            # Special commands
            if user_input.lower() == "last":
                if auto.last_command:
                    print(f"Last command: {json.dumps(auto.last_command, indent=2)}")
                else:
                    print("No previous command.")
                continue
            
            if user_input.lower() == "status":
                auto.check_status()
                continue
            
            # Run the command
            success, message = auto.run(user_input)
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {message}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    main()
