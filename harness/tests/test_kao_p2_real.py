from harness.mldsa import dsa
from harness.mldsa.params import ML_DSA_44
from harness.schemes import kao_p2_real as kp


def test_signature_verifies_and_broadcast_leaks_s1():
    p = ML_DSA_44
    sch = kp.KaoP2(p, 4, 3, [7, 4, 3])
    tr = sch.sign(b"msg", [1, 2, 3])
    assert dsa.verify(tr.pk, b"msg", tr.signature, p)
    s1 = kp.attack_from_broadcast(p, tr, list(tr.broadcast.values()))
    assert s1 is not None and (s1 == sch.secret["s1"]).all()


def test_missing_broadcast_value_fails():
    p = ML_DSA_44
    sch = kp.KaoP2(p, 4, 3, [8, 4, 3])
    tr = sch.sign(b"msg", [1, 2, 3])
    s1 = kp.attack_from_broadcast(p, tr, list(tr.broadcast.values())[:-1])
    assert s1 is None or abs(s1).max() > p.eta
