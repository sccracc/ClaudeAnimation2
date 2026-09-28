import numpy as np, wave, sys
def load(p):
    w=wave.open(p); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
    return x,sr
def segments(x,sr,thr_db=-42,min_gap=0.22):
    hop=int(0.01*sr)
    n=len(x)//hop
    rms=np.sqrt(np.array([np.mean(x[i*hop:(i+1)*hop]**2) for i in range(n)])+1e-12)
    db=20*np.log10(rms)
    act=db>thr_db
    segs=[];inside=False
    for i,a in enumerate(act):
        if a and not inside: st=i; inside=True
        if not a and inside: segs.append([st,i]); inside=False
    if inside: segs.append([st,n])
    # merge gaps shorter than min_gap
    out=[]
    for s in segs:
        if out and (s[0]-out[-1][1])*0.01<min_gap: out[-1][1]=s[1]
        else: out.append(s)
    return [(a*0.01,b*0.01) for a,b in out if (b-a)*0.01>0.08]
if __name__=='__main__':
    x,sr=load(sys.argv[1]); print('dur',len(x)/sr,'peak',np.abs(x).max())
    segs=segments(x,sr,min_gap=float(sys.argv[2]) if len(sys.argv)>2 else 0.22)
    prev=0
    for a,b in segs:
        print(f'{a:6.2f}-{b:6.2f} ({b-a:5.2f})  gap before {a-prev:4.2f}'); prev=b
