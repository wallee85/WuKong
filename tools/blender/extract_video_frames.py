"""Extract frames from the reference video with Blender's sequencer (no ffmpeg on PATH).

blender -b --factory-startup --python tools/blender/extract_video_frames.py -- <mp4> <outdir> <step>
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
src, outdir = argv[0], argv[1]
step = int(argv[2]) if len(argv) > 2 else 3

os.makedirs(outdir, exist_ok=True)

scene = bpy.context.scene
se = scene.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
strip = strips.new_movie("ref", src, channel=1, frame_start=1)

scene.render.fps = 10
scene.render.fps_base = 1.0
scene.frame_start = 1
scene.frame_end = strip.frame_final_duration
scene.frame_step = step
scene.render.resolution_x = strip.elements[0].orig_width
scene.render.resolution_y = strip.elements[0].orig_height
scene.render.resolution_percentage = 100
scene.render.use_sequencer = True
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(outdir, "v_")
scene.render.use_file_extension = True

print("VIDEO_ORIG", strip.elements[0].orig_width, strip.elements[0].orig_height,
      "DURATION_FRAMES", strip.frame_final_duration, "FPS_SRC", strip.fps)

bpy.ops.render.render(animation=True)
print("EXTRACT_DONE", outdir)
