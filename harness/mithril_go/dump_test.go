// Transcript dumper for the Mithril reference code (GuilhemN/threshold-ml-dsa, commit 66e269e).
// Copy into implementation/sign/thmldsa/thmldsa44/internal/ and run
//   MITHRIL_OUT=<file> MITHRIL_SLOTS=<count> MITHRIL_T=2 MITHRIL_N=3 go test -run TestDumpTranscripts -timeout 0
// It lives in package internal so it can read the secret shares as ground truth.
//
// Output (little-endian int32): header [T, N, K, slots, seed], rho (32 bytes), then t (K*256), s1 (L*256), s2 (K*256)
// of the full secret, then per slot: rejmask, c (256), w (K*256), z (L*256).
// rejmask bit j is set when signer j's hyperball check failed (it sends an all-zero z for the slot).
// w is the aggregated commitment, z the aggregated response, c the challenge, all in [0, q).
// Signing randomness rhop is fresh from crypto/rand per attempt, as in the public Round1.
package internal

import (
	cryptoRand "crypto/rand"
	"encoding/binary"
	"io"
	"os"
	"strconv"
	"testing"

	common "github.com/cloudflare/circl/sign/internal/dilithium"
	"github.com/cloudflare/circl/internal/sha3"
)

func envInt(name string, def int) int {
	if v, err := strconv.Atoi(os.Getenv(name)); err == nil {
		return v
	}
	return def
}

func TestDumpTranscripts(t *testing.T) {
	out := os.Getenv("MITHRIL_OUT")
	if out == "" {
		t.Skip("MITHRIL_OUT not set")
	}
	T, N := uint8(envInt("MITHRIL_T", 2)), uint8(envInt("MITHRIL_N", 3))
	slots := envInt("MITHRIL_SLOTS", 1000)
	seedVal := envInt("MITHRIL_SEED", 1)

	params, err := GetThresholdParams(T, N)
	if err != nil {
		t.Fatal(err)
	}
	var seed [common.SeedSize]byte
	binary.LittleEndian.PutUint64(seed[:], uint64(seedVal))
	pk, sks := NewThresholdKeysFromSeed(&seed, params)

	// Full secret: sum of all shares (each share is held by several parties, count it once).
	var s1 VecL
	var s2k VecK
	seen := map[uint8]bool{}
	for i := range sks {
		for u, sh := range sks[i].shares {
			if !seen[u] {
				seen[u] = true
				s1.Add(&s1, &sh.s1)
				s2k.Add(&s2k, &sh.s2)
			}
		}
	}
	s1.Normalize()
	s2k.Normalize()

	// t = A s1 + s2
	var tv VecK
	s1h := s1
	s1h.NTT()
	for j := 0; j < K; j++ {
		PolyDotHat(&tv[j], &pk.A[j], &s1h)
		tv[j].ReduceLe2Q()
		tv[j].InvNTT()
	}
	tv.Add(&tv, &s2k)
	tv.Normalize()

	f, err := os.Create(out)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	put := func(v uint32) { _ = binary.Write(f, binary.LittleEndian, v) }
	putPoly := func(p *common.Poly) {
		for _, x := range p {
			put(x)
		}
	}
	put(uint32(T))
	put(uint32(N))
	put(uint32(params.K))
	put(uint32(slots))
	put(uint32(seedVal))
	_, _ = f.Write(pk.rho[:])
	for j := 0; j < K; j++ {
		putPoly(&tv[j])
	}
	for j := 0; j < L; j++ {
		putPoly(&s1[j])
	}
	for j := 0; j < K; j++ {
		putPoly(&s2k[j])
	}

	act := uint8(0)
	for j := uint8(0); j < T; j++ {
		act |= 1 << j
	}
	var msg [8]byte
	written := 0
	for attempt := 0; written < slots; attempt++ {
		binary.LittleEndian.PutUint64(msg[:], uint64(attempt))
		msgWriter := func(w io.Writer) { _, _ = w.Write(msg[:]) }
		mu := ComputeMu(&sks[0], msgWriter)

		var wsum []VecK
		sts := make([][]FVec, T)
		for j := uint8(0); j < T; j++ {
			var rhop [64]byte
			if _, err := cryptoRand.Read(rhop[:]); err != nil {
				t.Fatal(err)
			}
			wj, st := GenThCommitment(&sks[j], rhop, 0, params)
			sts[j] = st
			if wsum == nil {
				wsum = wj
			} else {
				AggregateCommitments(wsum, wj)
			}
		}
		zsum := make([]VecL, params.K)
		rej := make([]uint32, params.K)
		for j := uint8(0); j < T; j++ {
			zj := ComputeResponses(&sks[j], act, mu, wsum, sts[j], params)
			for i := range zj {
				var zero VecL
				if zj[i] == zero {
					rej[i] |= 1 << j
				}
			}
			AggregateResponses(zsum, zj)
		}
		for i := uint16(0); i < params.K && written < slots; i++ {
			var w0, w1 VecK
			var w1Packed [PolyW1Size * K]byte
			var ctilde [CTildeSize]byte
			var ch common.Poly
			wsum[i].Decompose(&w0, &w1)
			w1.PackW1(w1Packed[:])
			h := sha3.NewShake256()
			_, _ = h.Write(mu[:])
			_, _ = h.Write(w1Packed[:])
			_, _ = h.Read(ctilde[:])
			PolyDeriveUniformBall(&ch, ctilde[:])

			put(rej[i])
			putPoly(&ch)
			for j := 0; j < K; j++ {
				putPoly(&wsum[i][j])
			}
			for j := 0; j < L; j++ {
				putPoly(&zsum[i][j])
			}
			written++
		}
	}
}
