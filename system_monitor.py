import psutil
import time

# Initialize psutil CPU timings to get a baseline
psutil.cpu_percent(interval=None)

def get_system_metrics():
    """
    Returns a dictionary containing the current CPU and RAM usage percentages,
    as well as an 'emergency' flag if thresholds are exceeded.
    """
    # CPU usage since last call (non-blocking)
    cpu_percent = psutil.cpu_percent(interval=None)
    
    # RAM usage
    ram_info = psutil.virtual_memory()
    ram_percent = ram_info.percent
    
    # Check for Emergency Compute State (CPU > 85% or RAM > 80%)
    emergency_state = False
    status = "nominal"
    if cpu_percent > 85 or ram_percent > 80:
        emergency_state = True
        status = "emergency_compute_state"
        
    # GPU tracking (Basic approximation on Windows without heavy external SDKs)
    # We will pass 0 for now as a placeholder unless specific libraries are used
    gpu_percent = 0
    
    return {
        "cpu": cpu_percent,
        "ram": ram_percent,
        "gpu": gpu_percent,
        "status": status,
        "is_emergency": emergency_state
    }

if __name__ == "__main__":
    # Test the monitor locally
    print("Testing System Monitor...")
    for _ in range(3):
        metrics = get_system_metrics()
        print(metrics)
        time.sleep(1)
