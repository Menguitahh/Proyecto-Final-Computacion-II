import cv2
import os
import sys

src = os.path.join('static','abstract_background.mp4')
out = os.path.join('static','abstract_background.opt.mp4')

if not os.path.exists(src):
    print('SRC_NOT_FOUND')
    sys.exit(2)

cap = cv2.VideoCapture(src)
if not cap.isOpened():
    print('CAP_OPEN_FAIL')
    sys.exit(3)

# input properties
in_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# target
target_fps = 24.0
scale_w = 960  # 540p-ish with aspect preserved
scale_h = int(height * (scale_w / max(1,width)))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
writer = cv2.VideoWriter(out, fourcc, target_fps, (scale_w, scale_h))
if not writer.isOpened():
    print('WRITER_OPEN_FAIL')
    sys.exit(4)

# frame skipping factor
step = max(1, int(round(in_fps / target_fps)))

idx = 0
written = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    if idx % step == 0:
        resized = cv2.resize(frame, (scale_w, scale_h), interpolation=cv2.INTER_AREA)
        writer.write(resized)
        written += 1
    idx += 1

cap.release()
writer.release()

print('OK', frame_count, in_fps, '->', written, target_fps)
