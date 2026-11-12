#!/usr/bin/env python3
"""Generate the authoritative Lorenz x-z data offline; --check detects drift.

RK4, initial (1,1,1), sigma=10, rho=28, beta=8/3; dt=0.005.
Integrate 35 time units; discard the first 10; retain every second step
(including both endpoints): 2501 points over 25 time units. No TeX integration.
"""
from pathlib import Path
import argparse, math
ROOT = Path(__file__).resolve().parents[1]

def trajectory():
    def f(v):
        x,y,z=v
        return (10*(y-x), x*(28-z)-y, x*y-(8/3)*z)
    def add(v,k,h):
        return tuple(a+h*b for a,b in zip(v,k))
    v=(1.,1.,1.); points=[]; h=0.005
    for step in range(7001):
        if step>=2000 and step%2==0:
            assert all(math.isfinite(a) for a in v)
            points.append((v[0],v[2]))
        if step==7000: break
        a=f(v); b=f(add(v,a,h/2)); c=f(add(v,b,h/2)); d=f(add(v,c,h))
        v=tuple(q+h*(aa+2*bb+2*cc+dd)/6 for q,aa,bb,cc,dd in zip(v,a,b,c,d))
    assert len(points)==2501
    assert -25<min(x for x,z in points)<-10 and 10<max(x for x,z in points)<25
    assert 0<min(z for x,z in points)<15 and 35<max(z for x,z in points)<55
    return ''.join(f'{x:.6f} {z:.6f}\n' for x,z in points)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true'); args=ap.parse_args()
    path=ROOT/'shared/lorenz-xz.dat'; data=trajectory()
    if args.check:
        if not path.is_file() or path.read_text()!=data: raise SystemExit('Lorenz data drift: regenerate with tools/make-lorenz.py')
    else: path.write_text(data)
    print('Lorenz data verified.' if args.check else 'Lorenz data generated.')
if __name__=='__main__': main()
