import subprocess
import json
import sys

def main():
    print("Fetching outdated packages...")
    result = subprocess.run([sys.executable, "-m", "pip", "list", "--outdated", "--format=json"], capture_output=True, text=True)
    try:
        packages = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Failed to decode JSON. Stdout:")
        print(result.stdout)
        return

    if not packages:
        print("No packages to upgrade.")
        return

    to_upgrade = [pkg['name'] for pkg in packages]
    print(f"Packages to upgrade: {', '.join(to_upgrade)}")
    
    # Run pip install --upgrade for all packages
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + to_upgrade
    print("Running:", " ".join(cmd))
    subprocess.run(cmd)

    print("Freezing new requirements...")
    freeze_result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(freeze_result.stdout)
    print("Done!")

if __name__ == "__main__":
    main()
