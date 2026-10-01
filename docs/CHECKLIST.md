# Attack Checklist (from dossier)

1. Published A·x of a secret or nonce? A is left-invertible, so x = A⁺(A·x).
2. Any nonce leak? Then s1 = c⁻¹(z − y).
3. Rejection checks removed, moved or altered? Regress released values against c·s1, c·s2 (ILWE, least squares, bounded-noise, ILP).
4. Non-uniform accepted-z distribution? Fisher information about s1 per signature; wall ≈ 4/(I·τ) signatures.
5. Rejected-attempt transcripts: what is revealed, does the simulator cover it, does the implementation leak which check failed?
6. Malicious nonce contributions (e.g. y_i = 0) biasing the aggregate?
7. Quorum and session binding: nonce reuse, unique session IDs, erasure.
8. Corruption-model gaps: static-only proofs, N = 2T−1 boundaries, footnote conditions like |S∖C| ≥ 2.
9. A posteriori key sharing and hints: quantify hardness loss with the shares actually held.
10. Implementation: floating-point samplers, timing, test vectors, reference code vs spec.
