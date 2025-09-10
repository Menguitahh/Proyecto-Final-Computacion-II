import os, subprocess, sys
import imageio_ffmpeg

# Selecciona la mejor fuente disponible
candidates = [
    os.path.join('static','abstract_background.fullres.backup.mp4'),
    os.path.join('static','abstract_background.orig.mp4'),
    os.path.join('static','abstract_background.mp4'),
]
src = next((p for p in candidates if os.path.exists(p)), None)
if not src:
    print('SRC_NOT_FOUND')
    sys.exit(2)

out = os.path.join('static','abstract_background.hd.mp4')
ff = imageio_ffmpeg.get_ffmpeg_exe()

# Filtros: escalado a 1280px, color boost leve, blur moderado, gradfun para banding, 24 fps
vf = 'scale=1280:-2:flags=lanczos,eq=saturation=1.35:contrast=1.05:brightness=0.02,gblur=sigma=10,gradfun=strength=0.6,fps=24'

cmd = [
    ff,
    '-y','-i', src,
    '-vf', vf,
    '-c:v','libx264','-preset','veryfast','-crf','26',
    '-profile:v','baseline','-level','3.1',
    '-x264-params','cabac=0:ref=1:bframes=0:weightp=0:8x8dct=0:scenecut=0:vbv-maxrate=2000:vbv-bufsize=2000',
    '-pix_fmt','yuv420p','-movflags','+faststart',
    '-an', out
]
print('CMD', ' '.join(cmd))
subprocess.check_call(cmd)
print('OK', out)
