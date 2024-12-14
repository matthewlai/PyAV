import os
import time

import av
import av.datasets


if 'TEST_FILE_PATH' in os.environ:
    test_file_path = os.environ['TEST_FILE_PATH']
else:
    test_file_path = av.datasets.curated("pexels/time-lapse-video-of-night-sky-857195.mp4")

assert av.codec.hwaccel.hwdevices_available, "No hardware-accelerated decoder available"

av.codec.hwaccel.dump_hwdevices()
av.codec.codec.dump_hwconfigs()

print("Decoding in software (auto threading)...")

container = av.open(test_file_path)

container.streams.video[0].thread_type = "AUTO"

start_time = time.time()
frame_count = 0
for packet in container.demux(video=0):
    for _ in packet.decode():
        frame_count += 1

sw_time = time.time() - start_time
sw_fps = frame_count / sw_time
assert frame_count == container.streams.video[0].frames
container.close()

print(f"Decoded with software in {sw_time:.2f}s ({sw_fps:.2f} fps).")

# Use the first available decoder on this list.
DECODER_PREFERENCES = [
    # Only choice on Macs. Access to all accelerators.
    'videotoolbox',

    # NVIDIA on Windows/Linux. Faster than d3d11va on NVIDIA cards on Windows,
    # but requires FFmpeg to be built with CUDA support.
    'cuda',

    # Widely available on Windows and allows access to all accelerators
    # (though not as fast as vendor-specific native interfaces).
    'd3d11va',

    # Now we need to deal with Intel and AMD on Linux. They should both support
    # VAAPI. NVIDIA only supports it with the unofficial nvidia-vaapi-driver, but
    # we should be using CUDA for NVIDIA on Linux anyways.
    'vaapi'
]

# Fallback... just pick the first one.
device_type = av.codec.hwaccel.hwdevices_available[0]

for candidate in DECODER_PREFERENCES:
    if candidate in av.codec.hwaccel.hwdevices_available:
        device_type = candidate
        break

print(f"Decoding with {device_type}")

hwaccel = av.codec.hwaccel.HWAccel(
    device_type=device_type,
    allow_software_fallback=False)

# Note the additional argument here.
container = av.open(test_file_path, hwaccel=hwaccel)

start_time = time.time()
frame_count = 0
for packet in container.demux(video=0):
    for _ in packet.decode():
        frame_count += 1

hw_time = time.time() - start_time
hw_fps = frame_count / hw_time
assert frame_count == container.streams.video[0].frames
container.close()

print(f"Decoded with {device_type} in {hw_time:.2f}s ({hw_fps:.2f} fps).")
