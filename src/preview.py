import sys, time, os
from engine import *
import film
def main():
    times=[float(x) for x in sys.argv[1:]]
    os.makedirs('build/preview',exist_ok=True)
    for t in times:
        f=int(round(t*FPS)); t0=time.time()
        s=new_surface(); c=s.getCanvas(); film.draw_frame(c,f/FPS,f)
        s.makeImageSnapshot().save(f'build/preview/f_{t:06.2f}.png')
        print(f't={t:.2f} {time.time()-t0:.2f}s')
main()
