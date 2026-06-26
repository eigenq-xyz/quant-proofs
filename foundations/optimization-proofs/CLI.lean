import OptimizationProofs.PGDFlat
/-!
# PGD stdin/stdout CLI — direct invocation by Python (no FFI, no Cython)

Protocol (single-shot, one problem per invocation):

  stdin:   one line, space-separated tokens:
           N  sigma_00 sigma_01 … sigma_{N-1,N-1}  mu_0 … mu_{N-1}  lambda_max  leverage_cap

  All float tokens are Python repr() strings, e.g. "1.5", "-0.25", "1.234e-05".

  stdout:  space-separated float64 weights on a single line:
           w_0 w_1 … w_{N-1}

Python calls this as:
    result = subprocess.run([binary], input=line, capture_output=True, text=True)
    weights = [float(x) for x in result.stdout.split()]

No Cython, no FFI layer, no Lean runtime embedded in the Python process.

NOTE on Lean v4.30.0-rc2 API:
  String.drop / dropEnd / trim now return String.Slice.
  All such calls are followed by .toString to recover String.
-/

open OptimizationProofs

-- ── Helpers that re-materialize Slices as Strings ────────────────────────────

/-- Drop the leading char if present, returning String (not Slice). -/
private def dropLeading (s : String) : String := (s.drop 1).toString

/-- Drop the last n chars, returning String (not Slice). -/
private def dropTrailing (s : String) (n : Nat) : String :=
  (s.dropEnd n).toString

-- ── Float parser (String.toFloat? absent in Lean v4.30.0-rc2) ────────────────

/-- Accumulate ASCII digit characters into a Float. -/
private def parseDigits (s : String) : Float :=
  s.foldl (fun acc c => acc * 10.0 + (c.toNat - '0'.toNat).toFloat) 0.0

/-- Parse a Float from Python repr: "42", "1.5", "-0.25", "1.234e-05", "3e+02". -/
private def parseFloat (s : String) : Float :=
  let negMant : Bool := s.startsWith "-"
  let s2 : String :=
    if negMant || s.startsWith "+" then dropLeading s else s
  -- Split on exponent marker
  let (mantPart, expPart) : String × Option String :=
    match s2.splitOn "e" with
    | [m, e] => (m, some e)
    | _ => match s2.splitOn "E" with
             | [m, e] => (m, some e)
             | _      => (s2, none)
  -- Integer and fractional parts of mantissa
  let (intStr, fracStr) : String × String :=
    match mantPart.splitOn "." with
    | [i, f] => (i, f)
    | [i]    => (i, "")
    | _      => ("0", "")
  let intVal  : Float := parseDigits intStr
  let fracVal : Float :=
    if fracStr.isEmpty then 0.0
    else parseDigits fracStr / Float.pow 10.0 fracStr.length.toFloat
  let mant : Float := if negMant then -(intVal + fracVal) else intVal + fracVal
  -- Optional exponent
  match expPart with
  | none => mant
  | some e =>
    let negExp : Bool := e.startsWith "-"
    let eStr : String :=
      if negExp || e.startsWith "+" then dropLeading e else e
    let scale : Float := Float.pow 10.0 (parseDigits eStr)
    if negExp then mant / scale else mant * scale

-- ── Entry point ──────────────────────────────────────────────────────────────

-- Solve one problem described by `toks` (already parsed), print weights to stdout.
private def solveTokens (toks : Array String) : IO Unit := do
  let n : Nat := match toks[0]!.toNat? with
    | some v => v
    | none   => (parseFloat toks[0]!).toUInt64.toNat

  let expected : Nat := 1 + n * n + n + 2
  if n = 0 || toks.size < expected then
    IO.eprintln s!"pgd_solve: need {expected} tokens for N={n}, got {toks.size}"
    return

  let sigmaFlat : FloatArray :=
    (List.range (n * n)).foldl (fun fa i =>
      fa.push (parseFloat toks[1 + i]!)) FloatArray.empty

  let muArr : FloatArray :=
    (List.range n).foldl (fun fa i =>
      fa.push (parseFloat toks[1 + n * n + i]!)) FloatArray.empty

  let lambdaMax   : Float := parseFloat toks[1 + n * n + n]!
  let leverageCap : Float := parseFloat toks[1 + n * n + n + 1]!

  let (wStar, _) := pgdFlat sigmaFlat muArr lambdaMax leverageCap

  IO.println (String.intercalate " "
    ((List.range n).map fun i => toString (wStar.get! i)))

-- Strip a trailing newline from a line returned by getLine.
private def stripNl (s : String) : String :=
  if s.endsWith "\r\n" then dropTrailing s 2
  else if s.endsWith "\n" then dropTrailing s 1
  else s

/-- Read and solve one problem per line from stdin until EOF.
    Defined as `partial` because the loop has no well-founded decreasing measure. -/
partial def serveLoop (stdin stdout : IO.FS.Stream) : IO Unit := do
  let raw  ← stdin.getLine
  let line := stripNl raw
  if line.isEmpty then return  -- EOF
  let toks : Array String := line.splitOn " " |>.filter (· ≠ "") |>.toArray
  unless toks.isEmpty do
    solveTokens toks
    stdout.flush
  serveLoop stdin stdout

/-- Main entry point.  Processes problems one per line until EOF.
    A persistent Python subprocess amortises the process-spawn cost across
    many solves; a single-shot call closes stdin after one line. -/
def main : IO Unit := do
  let stdin  ← IO.getStdin
  let stdout ← IO.getStdout
  serveLoop stdin stdout
