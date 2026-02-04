
import os
import argparse
import subprocess
import time

def run_adb(cmd, device_id=None):
    adb_cmd = ["adb"]
    if device_id:
        adb_cmd.extend(["-s", device_id])
    adb_cmd.extend(cmd)
    print(f"Running: {' '.join(adb_cmd)}")
    result = subprocess.run(adb_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description="Deploy and Run on Luckfox Pico")
    parser.add_argument("--device", default="1f931ede301b76e0", help="ADB Device ID")
    parser.add_argument("--exe", required=True, help="Path to compiled executable")
    parser.add_argument("--model", required=True, help="Path to RKNN model")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--remote_dir", default="/root/rknn_demo", help="Remote directory on board")
    
    args = parser.parse_args()
    
    exe_name = os.path.basename(args.exe)
    model_name = os.path.basename(args.model)
    image_name = os.path.basename(args.image)
    
    print(f"Device ID: {args.device}")
    
    # Check local files existence
    if not os.path.exists(args.exe):
        print(f"Error: Executable not found at {args.exe}")
        return
    if not os.path.exists(args.model):
        print(f"Error: Model file not found at {args.model}")
        return
    if not os.path.exists(args.image):
        print(f"Error: Image file not found at {args.image}")
        return

    # Check device connection
    devices = run_adb(["devices"])
    if args.device not in devices:
        print(f"Device {args.device} not found!")
        return

    # Check Disk Space
    print("Checking disk space...")
    output = run_adb(["shell", "df -h"], args.device)
    print(output)

    # Clean remote directory
    print(f"Cleaning {args.remote_dir}...")
    run_adb(["shell", f"rm -rf {args.remote_dir}"], args.device)

    # Create remote directory
    run_adb(["shell", f"mkdir -p {args.remote_dir}"], args.device)
    
    # KILL rkipc
    print("Killing rkipc to free NPU...")
    run_adb(["shell", "killall rkipc"], args.device)
    time.sleep(1) # Wait for it to die
    
    # Push files
    print("Pushing files...")
    
    res = run_adb(["push", args.exe, f"{args.remote_dir}/{exe_name}"], args.device)
    
    res = run_adb(["push", args.model, f"{args.remote_dir}/{model_name}"], args.device)
    
    res = run_adb(["push", args.image, f"{args.remote_dir}/{image_name}"], args.device)

    # Push lib
    lib_path = os.path.join(os.path.dirname(args.exe), "lib", "librknnmrt.so")
    if os.path.exists(lib_path):
        print(f"Pushing library from {lib_path}...")
        run_adb(["shell", f"mkdir -p {args.remote_dir}/lib"], args.device)
        run_adb(["push", lib_path, f"{args.remote_dir}/lib/librknnmrt.so"], args.device)
        ld_preload = f"export LD_LIBRARY_PATH={args.remote_dir}/lib:$LD_LIBRARY_PATH &&"
    else:
        print("Warning: local librknnmrt.so not found, using system default.")
        ld_preload = ""
    
    # chmod
    run_adb(["shell", f"chmod +x {args.remote_dir}/{exe_name}"], args.device)
    
    # Run
    print("Running inference...")
    cmd = f"cd {args.remote_dir} && {ld_preload} ./{exe_name} ./{model_name} ./{image_name}"
    output = run_adb(["shell", cmd], args.device)
    print("Output:")
    print(output)
    
    # Pull result
    print("Pulling result...")
    run_adb(["pull", f"{args.remote_dir}/out.jpg", "./out.jpg"], args.device)
    
    if os.path.exists("./out.jpg"):
        print("Success! Result saved to ./out.jpg")
    else:
        print("Failed to pull out.jpg")

if __name__ == "__main__":
    main()
