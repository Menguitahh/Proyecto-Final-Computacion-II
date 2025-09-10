import os, subprocess, sys
import imageio_ffmpeg

src = os.path.join('static','abstract_background.mp4')
out = os.path.join('static','abstract_background.opt.mp4')

ff = imageio_ffmpeg.get_ffmpeg_exe()
if not os.path.exists(src):
    print('SRC_NOT_FOUND')
    sys.exit(2)

cmd = [
    ff,
    '-y', '-i', src,
    '-vf', 'scale=1280:-2,fps=24',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '28',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    '-an',
    out
]
print('CMD', ' '.join(cmd))
subprocess.check_call(cmd)
print('OK')
