import os
import sys
import socket
import subprocess
import time
import urllib.request

# Define paths relative to this script's location
current_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(current_dir, '.venv', 'Scripts', 'python.exe')
manage_py = os.path.join(current_dir, 'manage.py')

# 1. Self-re-execute inside virtual environment if not already running there.
# This prevents ModuleNotFoundError if the user or IDE runs this script using system python.
if os.path.exists(venv_python) and os.path.abspath(sys.executable) != os.path.abspath(venv_python):
    print(f"Switching Python interpreter to virtual environment: {venv_python}")
    # Execute the current script with the virtual environment Python interpreter
    result = subprocess.run([venv_python] + sys.argv, cwd=current_dir)
    sys.exit(result.returncode)

# 2. Once in virtual environment, import pywebview (which is installed in .venv)
import webview

def get_free_port():
    """Finds an available TCP port on localhost."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def main():
    # Dynamically select an available port
    port = get_free_port()
    url = f"http://127.0.0.1:{port}"
    
    print(f"Starting Django server on port {port}...")
    
    # Start the Django server in the background
    creation_flags = 0
    if os.name == 'nt':
        # 0x08000000 is the flag for CREATE_NO_WINDOW
        creation_flags = 0x08000000

    django_proc = subprocess.Popen(
        [venv_python, manage_py, 'runserver', f'127.0.0.1:{port}', '--noreload'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
        cwd=current_dir
    )
    
    def shutdown_backend():
        print("Stopping Django server...")
        try:
            django_proc.terminate()
            django_proc.wait(timeout=2)
        except Exception:
            try:
                django_proc.kill()
            except Exception:
                pass

    # Wait until the Django server is responsive
    print("Waiting for server to be responsive...")
    server_ready = False
    for _ in range(50):  # Try for up to 5 seconds
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    server_ready = True
                    break
        except Exception:
            pass
        time.sleep(0.1)

    if not server_ready:
        print("Error: Django server failed to start in time.")
        shutdown_backend()
        sys.exit(1)
        
    print("Server ready! Starting desktop webview...")

    # Configure and launch the native GUI window
    window = webview.create_window(
        title='MediPOS Karachi',
        url=url + "/dashboard/",
        width=1280,
        height=800,
        min_size=(1024, 768),
        text_select=True,
        confirm_close=True
    )
    
    window.events.closed += shutdown_backend
    webview.start()
    shutdown_backend()

if __name__ == '__main__':
    main()
