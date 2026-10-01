"""ML-DSA parameter sets (FIPS 204, Table 1)."""
from dataclasses import dataclass

Q = 8380417
N = 256
D = 13


@dataclass(frozen=True)
class Params:
    name: str
    k: int
    l: int
    eta: int
    tau: int
    gamma1: int
    gamma2: int
    beta: int
    omega: int


ML_DSA_44 = Params("ML-DSA-44", 4, 4, 2, 39, 1 << 17, (Q - 1) // 88, 78, 80)
ML_DSA_65 = Params("ML-DSA-65", 6, 5, 4, 49, 1 << 19, (Q - 1) // 32, 196, 55)
ML_DSA_87 = Params("ML-DSA-87", 8, 7, 2, 60, 1 << 19, (Q - 1) // 32, 120, 75)

ALL = {p.name: p for p in (ML_DSA_44, ML_DSA_65, ML_DSA_87)}
