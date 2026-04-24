"""
Interactive OpenWeatherMap API Setup and Live Prediction
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def get_api_key_interactive():
    """Interactively get and optionally save API key."""
    print("\n" + "=" * 70)
    print("🌤️ OpenWeatherMap API Configuration")
    print("=" * 70)
    
    print("\n📌 To use live weather predictions, you need an OpenWeatherMap API key.")
    print("\n✅ Get a FREE API key:")
    print("   1. Go to: https://openweathermap.org/api")
    print("   2. Sign up for a free account")
    print("   3. Create an API key in your account dashboard")
    print("   4. Paste the key below\n")
    
    api_key = input("Enter your OpenWeatherMap API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⚠️  No API key provided. Using default configuration.")
        return None
    
    # Validate API key format (should be 32 hex characters)
    if len(api_key) >= 30:
        print(f"✓ API key accepted: {api_key[:16]}...{api_key[-8:]}")
        
        save = input("\nSave this API key to config.py? (y/n): ").strip().lower()
        if save == 'y':
            save_api_key(api_key)
        
        return api_key
    else:
        print("❌ API key too short. Please check and try again.")
        return None


def save_api_key(api_key):
    """Save API key to config.py."""
    config_path = Path('config.py')
    
    if not config_path.exists():
        print("❌ config.py not found!")
        return False
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Replace the placeholder API key
        old_key_line = 'OPENWEATHERMAP_API_KEY = "your_api_key_here"'
        new_key_line = f'OPENWEATHERMAP_API_KEY = "{api_key}"'
        
        if old_key_line in content:
            content = content.replace(old_key_line, new_key_line)
            
            with open(config_path, 'w') as f:
                f.write(content)
            
            print("✓ API key saved to config.py")
            return True
        else:
            print("⚠️  Could not find placeholder in config.py")
            return False
    
    except Exception as e:
        print(f"❌ Error saving API key: {e}")
        return False


def run_live_prediction(api_key=None):
    """Run the live prediction."""
    print("\n" + "=" * 70)
    print("Running live weather prediction...")
    print("=" * 70 + "\n")
    
    # Import after config might be updated
    from live_prediction import predict_with_live_data, display_results, save_live_prediction
    
    result = predict_with_live_data(api_key)
    
    if result:
        display_results(result)
        save_live_prediction(result)
        print("\n✓ Prediction completed and saved!")
        return True
    else:
        print("\n❌ Prediction failed")
        return False


def show_menu():
    """Show main menu."""
    print("\n" + "=" * 70)
    print("🌤️ Live Weather Prediction System")
    print("=" * 70)
    print("\nOptions:")
    print("  1. Configure API key")
    print("  2. Run live prediction (with API key prompt)")
    print("  3. Run live prediction (with saved API key)")
    print("  4. Show current API key status")
    print("  5. Exit")
    print()
    
    choice = input("Select an option (1-5): ").strip()
    return choice


def show_api_status():
    """Show current API key status."""
    import config
    
    print("\n" + "=" * 70)
    print("🔑 API Key Status")
    print("=" * 70)
    
    api_key = config.OPENWEATHERMAP_API_KEY
    
    if api_key == "your_api_key_here":
        print("Status: ❌ NOT CONFIGURED")
        print("\nTo configure:")
        print("  • Option 1: Run 'python setup_live_api.py' and select option 1")
        print("  • Option 2: Edit config.py directly")
        print("  • Option 3: Set environment variable OPENWEATHERMAP_API_KEY")
    else:
        print("Status: ✓ CONFIGURED")
        print(f"Key: {api_key[:16]}...{api_key[-8:]}")
        print(f"\nLocation: {config.CITY}")
        print(f"Latitude: {config.LAT}")
        print(f"Longitude: {config.LON}")
    
    print("=" * 70)


def main():
    """Main interactive loop."""
    while True:
        choice = show_menu()
        
        if choice == '1':
            api_key = get_api_key_interactive()
            if api_key:
                print("\nTest API connection? (y/n): ", end="")
                if input().strip().lower() == 'y':
                    run_live_prediction(api_key)
        
        elif choice == '2':
            api_key = get_api_key_interactive()
            if api_key:
                run_live_prediction(api_key)
        
        elif choice == '3':
            import config
            if config.OPENWEATHERMAP_API_KEY != "your_api_key_here":
                print("\nUsing saved API key...")
                run_live_prediction()
            else:
                print("\n❌ No API key configured. Please use option 1 first.")
        
        elif choice == '4':
            show_api_status()
        
        elif choice == '5':
            print("\nGoodbye! 👋")
            sys.exit(0)
        
        else:
            print("❌ Invalid option. Please select 1-5.")


if __name__ == "__main__":
    # If API key passed as argument, run directly
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"Using API key from command line: {api_key[:16]}...{api_key[-8:]}\n")
        from live_prediction import predict_with_live_data, display_results, save_live_prediction
        result = predict_with_live_data(api_key)
        if result:
            display_results(result)
            save_live_prediction(result)
    else:
        # Show interactive menu
        main()
