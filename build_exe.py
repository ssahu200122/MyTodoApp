import PyInstaller.__main__
import customtkinter
import os
import sys
import shutil
import stat
import time

# --- CONFIGURATION ---
# Change these values to customize your build
APP_NAME = "MyModernTodo"
ICON_FILENAME = "logo.ico"  # Must be a .ico file inside the 'assets' folder!

# --- Helper to force delete locked/read-only files on Windows ---
def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree.
    If the file is read-only, try to make it writable and delete it again.
    """
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            # If we still can't delete it, raise the error so the retry loop catches it
            raise
    else:
        raise

def clean_previous_builds(base_dir):
    """Manually remove build/dist folders with robust error handling and retries"""
    for folder in ['build', 'dist']:
        folder_path = os.path.join(base_dir, folder)
        if os.path.exists(folder_path):
            print(f"Cleaning existing '{folder}' directory...")
            
            # Retry loop: Try 5 times with a small delay
            # This helps if Windows Explorer or Antivirus is momentarily holding a file lock
            success = False
            for attempt in range(5):
                try:
                    shutil.rmtree(folder_path, onerror=on_rm_error)
                    success = True
                    break
                except Exception as e:
                    print(f"  Attempt {attempt+1}/5 failed: {e}")
                    time.sleep(1) # Wait 1 second before retrying
            
            if not success:
                print(f"Error: Could not fully clean '{folder}' folder.")
                print("Tip: Close any open Explorer windows, code editors, or running instances of the app.")
                return False
            
    return True

# 1. Get the directory where this script is located
base_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Get the path to CustomTkinter
ctk_path = os.path.dirname(customtkinter.__file__)

# 3. Define the separator for the OS
separator = ';' if sys.platform.startswith('win') else ':'

# 4. Define paths
main_script = os.path.join(base_dir, 'main.py')
assets_dir = os.path.join(base_dir, 'assets')

# Verify assets exist
if not os.path.exists(assets_dir):
    print(f"Warning: Assets folder not found at {assets_dir}")

# 5. Clean up old builds BEFORE asking PyInstaller to run
if not clean_previous_builds(base_dir):
    print("Build cancelled due to cleanup failure.")
    sys.exit(1)

# 6. Define the PyInstaller command arguments
args = [
    main_script,                     
    f'--name={APP_NAME}',           
    '--noconfirm',                   
    '--windowed',                    
    '--onedir',                      
    '--clean',                       
    
    # Add CustomTkinter Data
    f'--add-data={ctk_path}{separator}customtkinter',
    
    # Add Your Local Assets
    f'--add-data={assets_dir}{separator}assets',
    
    # Hidden Imports
    '--hidden-import=plyer.platforms.win.notification',
    '--hidden-import=pystray',
    '--hidden-import=PIL',
    '--hidden-import=sqlalchemy.sql.default_comparator',
]

# 7. Add Icon if it exists
logo_icon = os.path.join(assets_dir, ICON_FILENAME)
if os.path.exists(logo_icon):
    print(f"Using icon: {logo_icon}")
    args.append(f'--icon={logo_icon}')
else:
    print(f"Warning: Icon not found at {logo_icon}. Using default PyInstaller icon.")

# 8. Run the build
print(f"Starting Build Process in {base_dir}...")
try:
    PyInstaller.__main__.run(args)
    
    # 9. Manually Copy Assets to Root of Dist
    # PyInstaller puts data in _internal, but app looks in root. This fixes it.
    dist_folder = os.path.join(base_dir, 'dist', APP_NAME)
    dest_assets = os.path.join(dist_folder, 'assets')
    
    if os.path.exists(dist_folder) and os.path.exists(assets_dir):
        print("Performing post-build asset copy...")
        # If assets folder already exists in dist (from --add-data), remove it to be clean
        if os.path.exists(dest_assets):
            shutil.rmtree(dest_assets, onerror=on_rm_error)
        
        # Copy assets folder to root of EXE directory
        shutil.copytree(assets_dir, dest_assets)
        print(f"Assets manually copied to: {dest_assets}")

    print(f"Build Complete! Check the 'dist/{APP_NAME}' folder.")
except Exception as e:
    print(f"Build failed: {e}")