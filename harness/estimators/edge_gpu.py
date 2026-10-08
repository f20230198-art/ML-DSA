"""GPU (PyTorch/CUDA) versions of the heavy steps of the edge-aware estimator.

The CPU profile at n = 256 shows about 90% of the edge estimator's time is the ring products in
the residual check, which are batched FFTs. Here those run on the GPU in float64 (so results match
the CPU code to rounding); the small LP still runs on the CPU with HiGHS. Same algorithm and
interface as `edge.chebyshev_cutting_plane`, so results are comparable.
"""
import numpy as np
import torch
from .edge import solve_lp

from ..mldsa.ringn import constraint_rows, get_ring


def available():
    return torch.cuda.is_available()


class GpuObs:
    """Observations (c, b) held on the GPU, with ring products against a fixed vector x."""

    def __init__(self, c, b, device="cuda", chunk=8192, cache_limit_bytes=3_000_000_000):
        self.n = c.shape[1]
        self.count = len(c)
        self.dev = torch.device(device)
        self.chunk = chunk
        psi = get_ring(self.n)._psi
        self.psi = torch.tensor(psi, dtype=torch.complex128, device=self.dev)
        self.psi_inv = self.psi.conj()
        self.c = torch.as_tensor(c, device=self.dev)
        self.b = torch.as_tensor(b, device=self.dev)
        cache = self.count * self.n * 16 <= cache_limit_bytes
        self.chat = [self._chat(s) for s in range(0, self.count, chunk)] if cache else None

    def _chat(self, start):
        return torch.fft.fft(self.c[start:start + self.chunk].to(torch.float64) * self.psi, dim=-1)

    def residual_blocks(self, x):
        """Yield (start, r) with r = b + c*x as float64 GPU tensors."""
        xh = torch.fft.fft(torch.as_tensor(x, dtype=torch.float64, device=self.dev) * self.psi)
        for k, start in enumerate(range(0, self.count, self.chunk)):
            ch = self.chat[k] if self.chat is not None else self._chat(start)
            prod = (torch.fft.ifft(ch * xh, dim=-1) * self.psi_inv).real
            yield start, self.b[start:start + self.chunk].to(torch.float64) + prod

    def max_abs_residual(self, x):
        return max(float(r.abs().max()) for _, r in self.residual_blocks(x))

    def least_squares(self):
        n = self.n
        m = torch.zeros(n, dtype=torch.float64, device=self.dev)
        r = torch.zeros(n, dtype=torch.complex128, device=self.dev)
        for k, start in enumerate(range(0, self.count, self.chunk)):
            ch = self.chat[k] if self.chat is not None else self._chat(start)
            bh = torch.fft.fft(self.b[start:start + self.chunk].to(torch.float64) * self.psi, dim=-1)
            m += (ch.real ** 2 + ch.imag ** 2).sum(dim=0)
            r += (ch.conj() * bh).sum(dim=0)
        x = (torch.fft.ifft(-r / m) * self.psi_inv).real
        return x.cpu().numpy()


def chebyshev_cutting_plane_gpu(c, b, box, rng, obs=None, init_rows=None, add=None, max_iter=80,
                                tol=1e-6):
    """GPU twin of edge.chebyshev_cutting_plane. Pass `obs` to reuse GPU-resident data."""
    count, n = c.shape
    obs = obs or GpuObs(c, b)
    init_rows = init_rows or 8 * n
    add = add or 2 * n
    seen = set()

    def new_rows(i, j):
        keep = [(a, b_) for a, b_ in zip(i.tolist(), j.tolist()) if (a, b_) not in seen]
        seen.update(keep)
        if not keep:
            return None, None
        ii = np.array([a for a, _ in keep])
        jj = np.array([b_ for _, b_ in keep])
        return constraint_rows(c, ii, jj), b[ii, jj].astype(float)

    rows, rhs = new_rows(rng.integers(0, count, size=init_rows), rng.integers(0, n, size=init_rows))
    x = np.zeros(n)
    t = 0.0
    for it in range(1, max_iter + 1):
        m = len(rows)
        ones = np.ones((m, 1))
        a_ub = np.vstack([np.hstack([rows, -ones]), np.hstack([-rows, -ones])])
        b_ub = np.concatenate([-rhs, rhs])
        cost = np.zeros(n + 1)
        cost[-1] = 1.0
        res = solve_lp(cost, a_ub, b_ub, [(-box, box)] * n + [(0, None)])
        x, t = res.x[:n], res.x[-1]

        top = 0.0
        cand_val, cand_i, cand_j = [], [], []
        for start, r in obs.residual_blocks(x):
            a = r.abs().reshape(-1)
            top = max(top, float(a.max()))
            k = min(add, a.numel())
            v, idx = torch.topk(a, k)
            cand_val.append(v.cpu().numpy())
            idx = idx.cpu().numpy()
            cand_i.append(start + idx // n)
            cand_j.append(idx % n)
        if top <= t + tol:
            return x, t, dict(iters=it, converged=True, rows=len(rows), max_residual=top)
        order = np.argsort(np.concatenate(cand_val))[-add:]
        new_r, new_h = new_rows(np.concatenate(cand_i)[order], np.concatenate(cand_j)[order])
        if new_r is None:
            return x, t, dict(iters=it, converged=True, rows=len(rows), max_residual=top)
        rows = np.vstack([rows, new_r])
        rhs = np.concatenate([rhs, new_h])
    return x, t, dict(iters=max_iter, converged=False, rows=len(rows), max_residual=top)
