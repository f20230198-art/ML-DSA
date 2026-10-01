# ML-DSA Overview

ML-DSA is a lattice-based signature scheme standardized in FIPS 204. Security rests on the hardness of Module-LWE and Module-SIS problems.

## Parameter sets

| Set | Security category | (k, l) | eta | tau | gamma1 | gamma2 |
|-----|-------------------|--------|-----|-----|--------|--------|
| ML-DSA-44 | 2 | (4, 4) | 2 | 39 | 2^17 | (q-1)/88 |
| ML-DSA-65 | 3 | (6, 5) | 4 | 49 | 2^19 | (q-1)/32 |
| ML-DSA-87 | 5 | (8, 7) | 2 | 60 | 2^19 | (q-1)/32 |

Common: q = 8380417, n = 256, d = 13.

## Core algorithms

- KeyGen
- Sign (Fiat-Shamir with aborts)
- Verify

## Building blocks

- NTT over Z_q[X]/(X^256 + 1)
- SHAKE128 / SHAKE256 for expansion and hashing
- Rounding: Power2Round, Decompose, HighBits, LowBits, MakeHint, UseHint
- Bit packing / unpacking of keys and signatures
