import subprocess
import shutil
import os
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
print("Using ffmpeg:", ffmpeg_exe)

src_mp4 = "output/20261007_morluto_rea_viral_reel.mp4"
if not os.path.exists(src_mp4):
    files = [f for f in os.listdir("output") if f.endswith(".mp4")]
    src_mp4 = os.path.join("output", files[-1])

print(f"Source video: {src_mp4}")

# 1. Copy sample MP4 to assets
shutil.copyfile(src_mp4, "assets/sample_reel.mp4")
print("Copied to assets/sample_reel.mp4")

# 2. Generate crisp animated GIF preview
gif_out = "assets/reel_demo.gif"
cmd = [
    ffmpeg_exe,
    "-y",
    "-ss", "2.5",
    "-t", "7",
    "-i", src_mp4,
    "-vf", "fps=14,scale=360:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
    "-loop", "0",
    gif_out
]

print("Rendering demo GIF...")
subprocess.run(cmd, check=True)
print(f"Demo GIF created successfully at {gif_out} (Size: {os.path.getsize(gif_out)} bytes)")
