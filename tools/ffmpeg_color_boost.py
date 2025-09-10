import os, subprocess, sys
import imageio_ffmpeg

# Elegimos el mejor origen disponible (fullres > orig > actual)
candidates = [
    os.path.join('static','abstract_background.fullres.backup.mp4'),
    os.path.join('static','abstract_background.orig.mp4'),
    os.path.join('static','abstract_background.mp4'),
]
src = next((p for p in candidates if os.path.exists(p)), None)
if not src:
    print('SRC_NOT_FOUND')
    sys.exit(2)

out = os.path.join('static','abstract_background.color.mp4')
ff = imageio_ffmpeg.get_ffmpeg_exe()

# Filtros: escalar, aumentar saturación/contraste/leve brillo y aplicar blur suave
vf = 'scale=854:-2:flags=lanczos,eq=saturation=1.5:contrast=1.06:brightness=0.03,gblur=sigma=14,fps=20'

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
