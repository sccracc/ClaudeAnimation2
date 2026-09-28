"""Render the film to H.264 using parallel workers (each encodes one contiguous chunk), then concatenate."""
import os, sys, time, subprocess, argparse, multiprocessing as mp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

def worker(args):
    idx, f0, f1, out, crf = args
    import engine, film
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{engine.W}x{engine.H}', '-r', str(engine.FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-profile:v', 'high',
           '-g', '48', '-bf', '2', '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    s = engine.new_surface()
    t0 = time.time()
    for f in range(f0, f1):
        c = s.getCanvas(); c.save()
        c.clear(engine.skia.ColorBLACK)
        film.draw_frame(c, f / engine.FPS, f)
        c.restore()
        arr = s.makeImageSnapshot().toarray()
        p.stdin.write(arr.tobytes())
        if (f - f0) % 24 == 0:
            el = time.time() - t0
            print(f'[w{idx}] frame {f} ({f - f0 + 1}/{f1 - f0}) {el:.0f}s', flush=True)
    p.stdin.close(); p.wait()
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'build', 'video_only.mp4'))
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--start', type=float, default=0.0)
    ap.add_argument('--end', type=float, default=None)
    ap.add_argument('--crf', type=int, default=15)
    a = ap.parse_args()
    import engine, film
    end = a.end if a.end is not None else film.DURATION
    F0, F1 = int(round(a.start * engine.FPS)), int(round(end * engine.FPS))
    n = F1 - F0
    k = a.workers
    bounds = [F0 + (n * i) // k for i in range(k + 1)]
    os.makedirs(os.path.join(ROOT, 'build', 'chunks'), exist_ok=True)
    jobs = [(i, bounds[i], bounds[i + 1], os.path.join(ROOT, 'build', 'chunks', f'chunk_{i:02d}.mp4'), a.crf) for i in range(k)]
    t0 = time.time()
    with mp.get_context('fork').Pool(k) as pool:
        outs = pool.map(worker, jobs)
    lst = os.path.join(ROOT, 'build', 'chunks', 'list.txt')
    with open(lst, 'w') as fh:
        for o in outs: fh.write(f"file '{o}'\n")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', a.out], check=True)
    print(f'done: {a.out}  frames {n}  in {time.time() - t0:.0f}s')

if __name__ == '__main__':
    main()
