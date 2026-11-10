"""Throughput of toy_exo30 with a pool of all allocated CPUs, and the change of the benchmark spectrum vs the
fine grid (TOY30_NLAYER, TOY30_NWL set by the caller). Writes the clean benchmark to $BENCH_OUT."""
import os, sys, time
import numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(__file__))
import toy_exo30 as T
S = T.Simulator(noisy=False)
def f(th): return S.clean(th)
th = T.Simulator(seed=0).sample_prior(4000)
t = time.time()
with Pool(len(os.sched_getaffinity(0))) as p: p.map(f, list(th), chunksize=50)
dt = time.time() - t
n = len(os.sched_getaffinity(0))
print(f"layers {len(T.P)} wl {len(T.WL)}: {4000/dt:.0f} sims/s on {n} CPUs, {n*dt/4000*1e3:.0f} ms per sim per CPU, sigma {T.SIGMA_NOISE:.3e}", flush=True)
np.save(os.environ["BENCH_OUT"], S.clean(T.THETA_STAR))
