/-!
# No label leakage across an out-of-sample split

The out-of-sample evaluation uses an expanding walk-forward with an **embargo** (purge) gap
between the end of the training window and the start of the test window. A label looks
`horizon` steps into the future (the realised forward return), so leakage would occur if the
forward-return window of a training observation extended into the test window.

This module proves the discrete condition under which that cannot happen: if the embargo is
at least the label horizon, the forward window of the *last* training observation ends
strictly before the *first* test index, so no training label can bleed across the split.
This is the formal contract behind `oos.walk_forward_splits` and the runtime `leakage_gap`
witness. Dependency-free and fully proved (no proof gaps).
-/

namespace ResearchPipeline

/-- An expanding walk-forward split with an embargo gap. Training indices are `[0, trainEnd)`;
the test window starts `embargo` steps after the training window ends. -/
structure WalkForwardSplit where
  /-- One past the last training index (size of the expanding training window). -/
  trainEnd : Nat
  /-- Purge gap inserted between training end and test start. -/
  embargo : Nat
  deriving Repr

namespace WalkForwardSplit

/-- First index of the test window. -/
def testStart (s : WalkForwardSplit) : Nat := s.trainEnd + s.embargo

/-- Last index of the (non-empty) training window. -/
def lastTrain (s : WalkForwardSplit) : Nat := s.trainEnd - 1

end WalkForwardSplit

/-- The forward-return label at index `i`, looking `horizon` steps ahead, reads data up to
and including index `i + horizon`. -/
def labelEnd (i horizon : Nat) : Nat := i + horizon

/-- **No label leakage.** If the embargo is at least the label horizon and the training set
is non-empty, the forward-return label of the last training observation ends strictly before
the first test index: no training label can bleed into the test window. -/
theorem embargo_blocks_label_leakage
    (s : WalkForwardSplit) (horizon : Nat)
    (h_train : 0 < s.trainEnd) (h_emb : horizon ≤ s.embargo) :
    labelEnd s.lastTrain horizon < s.testStart := by
  unfold labelEnd WalkForwardSplit.lastTrain WalkForwardSplit.testStart
  omega

/-- Contrapositive framing: a sufficient embargo is exactly `horizon`. With `embargo < horizon`
the inequality can fail (e.g. `trainEnd = 1`), so the hypothesis `horizon ≤ embargo` is tight. -/
theorem leakage_possible_without_embargo :
    ∃ (s : WalkForwardSplit) (horizon : Nat),
      0 < s.trainEnd ∧ s.embargo < horizon ∧ s.testStart ≤ labelEnd s.lastTrain horizon := by
  refine ⟨⟨1, 0⟩, 1, ?_, ?_, ?_⟩ <;> simp [WalkForwardSplit.testStart, WalkForwardSplit.lastTrain, labelEnd]

end ResearchPipeline
