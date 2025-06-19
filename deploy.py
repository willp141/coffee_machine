import subprocess
import os

# Verify connection first
print("Checking ESP32 connection...")
result = subprocess.run(['mpremote', 'connect', 'COM4', 'exec', 'print("CONNECTED")'], capture_output=True, text=True)

if result.returncode != 0 or "CONNECTED" not in result.stdout:
    print("❌ ERROR: Unable to connect to ESP32 on COM4.")
    print(result.stderr)
    exit(1)
else:
    print("✅ Connected successfully!\n")

print("Starting deployment script...")

# Files/folders to exclude
EXCLUDE = [
    'images',
    'PCB_design',
    'Outdated Code',
    'mechanical_housing',
    '.git',
    '__pycache__',
    '.DS_Store',
    '*.kicad_pcb',
    '*.kicad_sch',
    '*.md',
    'deploy.py',
    '.vscode',
]

# File types to include
INCLUDE_EXTENSIONS = ['.py', '.html', '.js', '.json', '.txt']

def should_include(filepath):
    for ex in EXCLUDE:
        if ex in filepath:
            return False
    ext = os.path.splitext(filepath)[1]
    return ext in INCLUDE_EXTENSIONS

# Build upload list
upload_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        rel_path = os.path.join(root, file).replace('./', '').replace('\\', '/')
        if should_include(rel_path):
            upload_files.append(rel_path)

if not upload_files:
    print("Nothing to upload! Check your filter rules.")
    exit(0)

print(f"Starting upload of {len(upload_files)} files...")

# Upload loop
for f in upload_files:
    print(f"Uploading: {f} ...", end=' ')
    #result = subprocess.run(['mpremote', 'connect', 'COM4', 'fs', 'cp', f, f], capture_output=True, text=True)
    result = subprocess.run(['mpremote', 'connect', 'COM4', 'fs', 'cp', f, f':{f}'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Success")
    else:
        print("❌ Failed")
        print(result.stderr)

print("\n🚀 Upload complete!")


# Simple serial monitor after deploy
print("Starting Serial Monitor... (Ctrl+C to exit)")
subprocess.run(['mpremote', 'connect', 'COM4'])