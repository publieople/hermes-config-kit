#!/usr/bin/env python3
"""
FLF2V/ComfyUI async job submitter + deferred poller.
Fire-and-forget pattern: submit returns immediately, poll checks later.

Usage:
  python3 flf2v_runner.py submit <prefix> <start_img> <end_img> "<prompt_text>"
  python3 flf2v_runner.py poll    # checks all pending jobs

The poll mode scans output/ and output/video/ for files by prefix,
  and removes the job marker when found.
"""

import requests, time, sys, json, os, glob

API = "http://localhost:8188"
OUTPUT = "/data/comfy/ComfyUI/output"
JOBDIR = "/tmp/flf2v_jobs"
DEFAULT_PROMPT = (
    "Slow cinematic push-in from wide bird's-eye view of the ancient temple "
    "to a medium shot of the main hall entrance at eye level. "
    "Camera smoothly moves forward through the moonlit courtyard. "
    "Fireflies gently float upward and gradually increase in number. "
    "Moonlight reveals more architectural details on the temple facade. "
    "Mysterious, serene atmosphere. No sudden movements, no cuts, no camera shake."
)
NEGATIVE_PROMPT = "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走"

os.makedirs(JOBDIR, exist_ok=True)


def build_workflow(start_img, end_img, prompt_text, prefix):
    """FLF2V Default 20-step workflow (640x640, 81帧)."""
    return {
        "72": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "76": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "77": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "73": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["76", 0], "shift": 8.0}},
        "74": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["77", 0], "shift": 8.0}},
        "79": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
        "80": {"class_type": "LoadImage", "inputs": {"image": start_img, "upload": "image"}},
        "89": {"class_type": "LoadImage", "inputs": {"image": end_img, "upload": "image"}},
        "90": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["72", 0], "text": prompt_text}},
        "78": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["72", 0], "text": NEGATIVE_PROMPT}},
        "81": {"class_type": "WanFirstLastFrameToVideo", "inputs": {
            "positive": ["90", 0], "negative": ["78", 0], "vae": ["79", 0],
            "start_image": ["80", 0], "end_image": ["89", 0],
            "width": 640, "height": 640, "length": 81, "batch_size": 1}},
        "84": {"class_type": "KSamplerAdvanced", "inputs": {
            "model": ["73", 0], "add_noise": "enable", "noise_seed": 42, "steps": 20, "cfg": 4.0,
            "sampler_name": "euler", "scheduler": "simple",
            "positive": ["81", 0], "negative": ["81", 1], "latent_image": ["81", 2],
            "start_at_step": 0, "end_at_step": 10, "return_with_leftover_noise": "enable"}},
        "87": {"class_type": "KSamplerAdvanced", "inputs": {
            "model": ["74", 0], "add_noise": "disable", "noise_seed": 0, "steps": 20, "cfg": 4.0,
            "sampler_name": "euler", "scheduler": "simple",
            "positive": ["81", 0], "negative": ["81", 1], "latent_image": ["84", 0],
            "start_at_step": 10, "end_at_step": 10000, "return_with_leftover_noise": "disable"}},
        "85": {"class_type": "VAEDecode", "inputs": {"samples": ["87", 0], "vae": ["79", 0]}},
        "86": {"class_type": "CreateVideo", "inputs": {"images": ["85", 0], "fps": 16}},
        "83": {"class_type": "SaveVideo", "inputs": {"video": ["86", 0], "filename_prefix": prefix, "format": "auto", "codec": "auto"}},
    }


def submit(start_img, end_img, prompt_text, prefix):
    """Submit job. Returns prompt_id on success, None on error."""
    wf = build_workflow(start_img, end_img, prompt_text, prefix)
    resp = requests.post(f"{API}/prompt", json={"prompt": wf}, timeout=30)

    if resp.status_code != 200:
        print(f"ERROR:{resp.status_code}:{resp.text[:300]}")
        return None

    pid = resp.json()["prompt_id"]

    # Write job marker
    job = {"prompt_id": pid, "prefix": prefix,
           "start_img": start_img, "end_img": end_img,
           "submitted_at": time.time()}
    with open(f"{JOBDIR}/{pid[:12]}.json", "w") as f:
        json.dump(job, f)

    # Verify queue
    time.sleep(3)
    q = requests.get(f"{API}/queue", timeout=10).json()
    running = len(q.get("queue_running", []))
    pending = len(q.get("queue_pending", []))
    print(f"SUBMITTED:{pid}")
    print(f"QUEUE:{running}r+{pending}p")
    return pid


def poll():
    """Check all pending jobs. Print DONE with path if any completed."""
    job_files = sorted(glob.glob(f"{JOBDIR}/*.json"))
    if not job_files:
        print("NO_JOBS")
        return

    for jf in job_files:
        with open(jf) as f:
            job = json.load(f)

        pid = job["prompt_id"]
        prefix = job["prefix"]
        search_prefix = os.path.basename(prefix)

        # Check history for completion
        resp = requests.get(f"{API}/history/{pid}", timeout=10)
        completed = False
        if resp.status_code == 200 and pid in resp.json():
            completed = resp.json()[pid].get("status", {}).get("completed", False)

        # Check queue
        q = requests.get(f"{API}/queue", timeout=10).json()
        running_ids = [i[1] for i in q.get("queue_running", [])]
        pending_ids = [i[1] for i in q.get("queue_pending", [])]
        in_queue = pid in running_ids or pid in pending_ids

        if completed or not in_queue:
            # Scan output dirs for the file (more reliable than API history outputs)
            found = []
            for d in [OUTPUT, f"{OUTPUT}/video"]:
                if not os.path.isdir(d): continue
                for fname in os.listdir(d):
                    if fname.startswith(search_prefix) and fname.endswith(".mp4"):
                        found.append(os.path.join(d, fname))
            found.sort()

            if found:
                fpath = found[-1]
                size = os.path.getsize(fpath)
                print(f"DONE:{pid[:12]}:{fpath}:{size}")
                os.remove(jf)
                return
            else:
                print(f"STALE:{pid[:12]} (no output file found)")
                os.remove(jf)
                return
        else:
            print(f"RUNNING:{pid[:12]}")
            return


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "submit"

    if mode == "submit":
        prefix = sys.argv[2] if len(sys.argv) > 2 else "video/flf2v_job"
        start_img = sys.argv[3] if len(sys.argv) > 3 else "Flux2-Klein_00003_.png"
        end_img = sys.argv[4] if len(sys.argv) > 4 else "Flux2-Klein_00004_.png"
        prompt_text = sys.argv[5] if len(sys.argv) > 5 else DEFAULT_PROMPT
        pid = submit(start_img, end_img, prompt_text, prefix)
        sys.exit(0 if pid else 1)

    elif mode == "poll":
        poll()
        sys.exit(0)

    else:
        print(f"Unknown mode: {mode}")
        print("Usage: flf2v_runner.py submit|poll [...]")
        sys.exit(1)
