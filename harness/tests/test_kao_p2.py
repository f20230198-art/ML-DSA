"""Stage D tests: Kao P2 masking toy (fast, n=8)."""
import numpy as np

from harness.schemes import kao_p2 as K


def test_masks_cancel_and_aggregate_is_Ay():
    s = K.make_session(seed=1)
    tot = sum(s.W[i] for i in s.S) % K.Q
    assert (tot == K.mat_vec(s.A, s.y)).all()


def test_individual_mask_attack_recovers_key_when_one_honest():
    # N = T = 3, two corrupted, |S minus C| = 1 (the footnote case, T = N)
    s = K.make_session(N=3, T=3, seed=2)
    s1_h, s1 = K.attack_individual_mask(s, corrupted=[1, 2])
    assert s1_h is not None
    assert (s1_h % K.Q == K.share_of_true_key(s, 3)).all()
    assert (s1 == s.s1).all()


def test_individual_mask_attack_works_for_T_less_than_N():
    s = K.make_session(N=5, T=3, S=[2, 4, 5], seed=3)
    _, s1 = K.attack_individual_mask(s, corrupted=[2, 4])
    assert (s1 == s.s1).all()


def test_individual_mask_attack_fails_with_two_honest():
    # control: |S minus C| = 2 -> honest-honest seed unknown, recovered y_h is wrong
    s = K.make_session(N=4, T=3, seed=4)
    _, s1 = K.attack_individual_mask(s, corrupted=[1])
    assert s1 is None or not (s1 == s.s1).all()


def test_aggregate_attack_recovers_key_for_any_honest_count():
    for seed, (N, T) in enumerate([(3, 3), (4, 3), (5, 4)]):
        s = K.make_session(N=N, T=T, seed=10 + seed)
        assert (K.attack_aggregate(s) == s.s1).all()
