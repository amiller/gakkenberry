#!/usr/bin/env python3
import math, random, time, sys
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, FULLSCREEN
from OpenGL import GL as gl

W, H = 1280, 720

VERT_SRC = r"""
#version 100
precision mediump float;
attribute vec2 a_pos;
void main() {
  gl_Position = vec4(a_pos, 0.0, 1.0);
}
"""

FRAG_SRC = r"""
#version 100
precision mediump float;

/* Uniforms */
uniform vec2  u_res;          // screen resolution
uniform float u_time;         // seconds
uniform vec2  u_eye;          // eye center in [-1,1] coords
uniform vec2  u_iris_r;       // iris radii in normalized coords
uniform vec2  u_pupil_r;      // pupil radii in normalized coords (base)
uniform float u_pupil_scale;  // pupil scale
uniform float u_blink;        // 0..1
uniform vec3  u_sclera;       // 248,248,255
uniform vec3  u_iris_base;    // e.g., 34,139,34
uniform vec3  u_iris_dark;    // e.g., 0,100,0
uniform vec3  u_lid;          // eyelid colour

/* Helpers */
float sdEllipse(vec2 p, vec2 r) {
  // Cheap inside-test: (p.x/r.x)^2 + (p.y/r.y)^2 - 1
  vec2 q = p / r;
  return dot(q,q) - 1.0;
}

void main() {
  // Normalized pixel coords in [-1,1]
  vec2 uv = (gl_FragCoord.xy / u_res) * 2.0 - 1.0;

  // Sclera gradient (radial falloff from screen center, NOT eyeball center)
  float d = length(uv);
  float bright = 1.0 - 0.1 * clamp(d, 0.0, 1.0);
  vec3 color = u_sclera * bright;

  // Eyelids (fast path): close from top+bottom
  // Threshold is symmetric in normalized Y; higher u_blink -> more closed
  float thr = 0.6 * (1.0 - u_blink);
  if (u_blink > 0.0 && (uv.y >  thr || uv.y < -thr)) {
    gl_FragColor = vec4(u_lid/255.0, 1.0);
    return;
  }

  // Eye-relative coordinates
  vec2 p   = uv - u_eye;

  // IRIS
  // Elliptical normalized coordinates
  vec2 pe  = p / u_iris_r;
  float r2 = dot(pe, pe);
  if (r2 <= 1.0) {
    float r  = sqrt(max(r2, 1e-6));
    // Radial texture: sin(8*pi*r)
    float radial = sin(8.0 * 3.14159265 * r) * 0.3 + 0.7;

    // Angular texture: sin(12 * theta)
    // GPU trigs are fine; atan(y,x) is available in ES 2.0
    float theta = atan(pe.y, pe.x);
    float angular = sin(12.0 * theta) * 0.2 + 0.8;

    float pat = radial * angular;

    vec3 base = u_iris_base / 255.0;
    vec3 dark = u_iris_dark / 255.0;
    color = mix(dark, base, pat);
  }

  // PUPIL (overrides iris)
  vec2 pr = u_pupil_r * u_pupil_scale;
  float pupil_d = sdEllipse(p, pr);
  if (pupil_d <= 0.0) {
    color = vec3(0.0);
  }

  gl_FragColor = vec4(color, 1.0);
}
"""

def compile_shader(src, typ):
    sid = gl.glCreateShader(typ)
    gl.glShaderSource(sid, src)
    gl.glCompileShader(sid)
    if gl.glGetShaderiv(sid, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
        raise RuntimeError(gl.glGetShaderInfoLog(sid).decode())
    return sid

def make_program(vsrc, fsrc):
    vs = compile_shader(vsrc, gl.GL_VERTEX_SHADER)
    fs = compile_shader(fsrc, gl.GL_FRAGMENT_SHADER)
    prog = gl.glCreateProgram()
    gl.glAttachShader(prog, vs)
    gl.glAttachShader(prog, fs)
    gl.glLinkProgram(prog)
    if gl.glGetProgramiv(prog, gl.GL_LINK_STATUS) != gl.GL_TRUE:
        raise RuntimeError(gl.glGetProgramInfoLog(prog).decode())
    gl.glDeleteShader(vs); gl.glDeleteShader(fs)
    return prog

def main():
    fullscreen = "--windowed" not in sys.argv
    pygame.init()
    flags = DOUBLEBUF | OPENGL | (FULLSCREEN if fullscreen else 0)
    pygame.display.set_mode((W, H), flags)
    pygame.display.set_caption("GPU Eyeball (GLES fragment shader)")

    prog = make_program(VERT_SRC, FRAG_SRC)
    gl.glUseProgram(prog)

    # Full-screen triangle (covers NDC)
    # Using a big triangle avoids precision seams vs quad
    verts = (-1.0, -1.0, 3.0, -1.0, -1.0, 3.0)
    vbo = gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
    import array
    gl.glBufferData(gl.GL_ARRAY_BUFFER, array.array('f', verts).tobytes(), gl.GL_STATIC_DRAW)

    loc_pos = gl.glGetAttribLocation(prog, "a_pos")
    gl.glEnableVertexAttribArray(loc_pos)
    gl.glVertexAttribPointer(loc_pos, 2, gl.GL_FLOAT, False, 0, None)

    # Uniform locations
    u_res          = gl.glGetUniformLocation(prog, "u_res")
    u_time         = gl.glGetUniformLocation(prog, "u_time")
    u_eye          = gl.glGetUniformLocation(prog, "u_eye")
    u_iris_r       = gl.glGetUniformLocation(prog, "u_iris_r")
    u_pupil_r      = gl.glGetUniformLocation(prog, "u_pupil_r")
    u_pupil_scale  = gl.glGetUniformLocation(prog, "u_pupil_scale")
    u_blink        = gl.glGetUniformLocation(prog, "u_blink")
    u_sclera       = gl.glGetUniformLocation(prog, "u_sclera")
    u_iris_base    = gl.glGetUniformLocation(prog, "u_iris_base")
    u_iris_dark    = gl.glGetUniformLocation(prog, "u_iris_dark")
    u_lid          = gl.glGetUniformLocation(prog, "u_lid")

    # Static uniforms
    gl.glUniform2f(u_res, float(W), float(H))
    gl.glUniform3f(u_sclera, 248.0/255.0, 248.0/255.0, 255.0/255.0)

    # Default colours (tweakable)
    eye_colors = {
        'green': ((34,139,34), (0,100,0)),
        'blue' : ((70,130,180), (25,25,112)),
        'brown': ((139,69,19), (101,67,33)),
        'hazel': ((154,205,50), (107,142,35)),
        'gray' : ((105,105,105), (64,64,64)),
    }
    chosen = 'green'
    for arg in sys.argv[1:]:
        if arg.startswith("color="):
            c = arg.split("=",1)[1]
            if c in eye_colors: chosen = c

    base, dark = eye_colors[chosen]
    gl.glUniform3f(u_iris_base, base[0], base[1], base[2])
    gl.glUniform3f(u_iris_dark, dark[0], dark[1], dark[2])
    gl.glUniform3f(u_lid, 205.0, 133.0, 63.0)

    # Eye geometry (match your CPU version)
    # CPU version: iris_radius_x = 0.3, iris_radius_y = 0.4
    # Let's try matching these directly first
    iris_rx, iris_ry = 0.30, 0.40
    pupil_rx, pupil_ry = 0.08, 0.11
    pupil_scale = 1.0

    # Motion state
    eye_x = 0.0; eye_y = 0.0
    target_x = 0.0; target_y = 0.0
    max_mv = 0.30
    mv_speed = 0.05
    blink = 0.0
    blink_speed = 0.20
    next_blink = 0.5   # first blink at 0.5s
    blink_closing = False

    clock = pygame.time.Clock()
    t0 = time.perf_counter()
    running = True
    fps_acc = 0; fps_time = 0.0

    while running:
        now = time.perf_counter()
        t = now - t0

        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q): running = False
                elif e.key == pygame.K_SPACE: next_blink = t
                elif e.key == pygame.K_EQUALS or e.key == pygame.K_PLUS:
                    pupil_scale = min(1.4, pupil_scale + 0.1)
                elif e.key == pygame.K_MINUS:
                    pupil_scale = max(0.6, pupil_scale - 0.1)
                elif e.key == pygame.K_r:
                    eye_x = eye_y = target_x = target_y = 0.0

        # Saccade scheduling
        # Pick a new target every 2–5 s
        # (Do it time-based not frame-based)
        if not hasattr(main, "_last_move") or (t - main._last_move) > getattr(main, "_move_ivl", 0):
            target_x = random.uniform(-max_mv, max_mv)
            target_y = random.uniform(-max_mv, max_mv)
            main._last_move = t
            main._move_ivl = random.uniform(2.0, 5.0)

        # Ease to target
        eye_x += (target_x - eye_x) * mv_speed
        eye_y += (target_y - eye_y) * mv_speed

        # Blink state machine
        if t >= next_blink and blink == 0.0:
            blink = 0.01; blink_closing = True
        if blink_closing:
            blink = min(1.0, blink + blink_speed)
            if blink >= 1.0: blink_closing = False
        elif blink > 0.0:
            blink = max(0.0, blink - blink_speed)
            if blink <= 0.0:
                next_blink = t + random.uniform(3.0, 6.0)

        # Upload uniforms
        gl.glUniform1f(u_time, float(t))
        gl.glUniform2f(u_eye, float(eye_x), float(eye_y))
        gl.glUniform2f(u_iris_r, float(iris_rx), float(iris_ry))
        gl.glUniform2f(u_pupil_r, float(pupil_rx), float(pupil_ry))
        gl.glUniform1f(u_pupil_scale, float(pupil_scale))
        gl.glUniform1f(u_blink, float(blink))

        # Draw
        gl.glViewport(0, 0, W, H)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)
        pygame.display.flip()

        dt = clock.tick(60) / 1000.0
        fps_acc += 1; fps_time += dt
        if fps_acc == 60:
            # print rough FPS every ~60 frames without spamming
            # print(f"FPS ~ {fps_acc/fps_time:.1f}")
            fps_acc = 0; fps_time = 0.0

    pygame.quit()

if __name__ == "__main__":
    main()