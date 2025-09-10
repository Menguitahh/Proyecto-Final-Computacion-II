import os, subprocess, sys
import imageio_ffmpeg

cand = [
    os.path.join('static','abstract_background.fullres.backup.mp4'),
    os.path.join('static','abstract_background.orig.mp4'),
    os.path.join('static','abstract_background.mp4'),
]
src = next((p for p in cand if os.path.exists(p)), None)
if not src:
    print('SRC_NOT_FOUND')
    sys.exit(2)
out = os.path.join('static','abstract_background.opt2.mp4')

ff = imageio_ffmpeg.get_ffmpeg_exe()
# Baseline profile, no bframes, no cabac, ref=1, 20fps, 854px width, pre-blur
vf = 'scale=854:-2,fps=20,gblur=sigma=16'
cmd = [
    ff,
    '-y','-i', src,
    '-vf', vf,
    '-c:v','libx264','-preset','veryfast','-crf','29',
    '-profile:v','baseline','-level','3.0',
    '-x264-params','cabac=0:ref=1:bframes=0:weightp=0:8x8dct=0:scenecut=0:vbv-maxrate=1200:vbv-bufsize=1200',
    '-pix_fmt','yuv420p','-movflags','+faststart',
    '-an', out
]
print('CMD', ' '.join(cmd))
subprocess.check_call(cmd)
print('OK', out)
