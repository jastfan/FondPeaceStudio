import subprocess
import imageio_ffmpeg
import os

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
src_mp4 = "output/20261007_morluto_rea_viral_reel.mp4"
gif_out = "assets/autoplay_reel_preview.gif"

print(f"Creating autoplay GIF from {src_mp4} to {gif_out}...")

# 5 seconds duration, starting from second 2.5 (where kinetic subtitles and scroll are actively moving)
# scale width to 300px, 12 fps, high quality palette, loop 0
cmd = [
    ffmpeg_exe,
    "-y",
    "-ss", "2.5",
    "-t", "5.5",
    "-i", src_mp4,
    "-vf", "fps=12,scale=300:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
    "-loop", "0",
    gif_out
]

subprocess.run(cmd, check=True)
size = os.path.getsize(gif_out)
print(f"Success! {gif_out} created. Size: {size} bytes ({size / (1024*1024):.2f} MB)")
