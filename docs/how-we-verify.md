# How we verify

Every result in the EigenQ Research Series is built the same way. This page describes the method, the tools, and, just as important, what the method does not promise.

## The tools

**Lean 4 and mathlib.** Proofs are written in Lean 4, a dependently typed proof assistant, on top of mathlib, its mathematical library. A finished proof is checked by a small trusted kernel. The rest of the system, including the tactics that help write proofs, sits outside that kernel and cannot make an incorrect proof pass.

**Zero `sorry` on main.** `sorry` is Lean's placeholder for an unproved step. A continuous integration gate rejects any commit to the main branch that contains one. "Complete, zero sorry" therefore means the theorem is established end to end, with no admitted gaps, not that most of it is done.

**Python and Cython execution.** Where a result needs to run on data, the verified core is compiled and called from Python through a Cython foreign function interface. Values cross that boundary as integers in basis points, scaled by ten thousand, so that the arithmetic the proof reasons about is exactly the arithmetic the machine performs. This removes a common source of silent drift between a model on paper and the floating point that executes it.

## What a proof guarantees

A theorem with zero `sorry` rules out every counterexample to its statement, inside the model as the statement defines it. This is stronger than testing, which checks selected inputs, and stronger than type checking, which rules out a class of errors rather than establishing a positive claim. If the theorem says a quantity is always nonnegative, there is no input, however adversarial, for which it is negative.

## What a proof does not guarantee

A proof says nothing about whether the model is the right model. If a pricing theorem assumes frictionless markets, the proof holds exactly under that assumption and is silent about transaction costs. Choosing assumptions that match the world is the job of economic reasoning and empirical evidence, not of the proof assistant.

For this reason every project here states its hypotheses in plain terms and reports where a result stops applying. A formally verified result is a precise claim about a clearly defined model. It is a foundation to build empirical work on, not a substitute for it.

## How to read a project

Each project pairs a theorem with the assumptions it rests on. Read the assumptions first, then the conclusion. The READMEs in the repository give the build and test commands; the pillar pages here explain why each result matters and how the projects connect.
