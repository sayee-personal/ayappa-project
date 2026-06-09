from Flask import Flask, redirect
import subprocess
import time
import os

app = Flask(__name__, static_url_path='', static_folder='.')

# Dictionaries to keep track of running Streamlit processes
processes = {}

def start_streamlit(script_name, port):
    """Starts a Streamlit app on a specific port if it isn't already running."""
    if script_name not in processes or processes[script_name].poll() is not None:
        print(f"Starting {script_name} on port {port}...")
        
        # Use python -m streamlit run to ensure it runs in the current environment
        proc = subprocess.Popen([
            'python', '-m', 'streamlit', 'run', script_name,
            '--server.port', str(port),
            '--server.headless', 'true'
        ])
        processes[script_name] = proc
        # Wait a moment for the server to spin up
        time.sleep(2)

@app.route('/')
def index():
    """Serve the static landing page (index.html)."""
    return app.send_static_file('index.html')

@app.route('/run-screener')
def run_screener():
    """Endpoint for the 'Institutional Credit Intelligence' button."""
    script = 'website_with_screener_&_dashboard_corporate.py'
    port = 8501
    start_streamlit(script, port)
    return redirect(f"https://axiom-screener-1058901886653.us-central1.run.app")

@app.route('/run-strategies')
def run_strategies():
    """Endpoint for the 'Algorithmic Alpha Engine' button."""
    script = 'strategies_for_trading.py'
    port = 8502
    start_streamlit(script, port)
    return redirect(f"https://axiom-strategies-1058901886653.us-central1.run.app")

if __name__ == '__main__':
    print("========================================")
    print("🚀 Axiom Core Master Server is running!")
    print("👉 Go to: http://localhost:5000")
    print("========================================")
    
    # Run the Flask server
    app.run(port=5000, debug=False)
