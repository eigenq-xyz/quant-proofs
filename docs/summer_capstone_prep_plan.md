# Summer 2026: Capstone Outcome & QR Interview Prep Plan

This document establishes a **high-impact, premium capstone outcome** for your summer work and integrates it with a rigorous **QR Interview Prep Curriculum** (Green Book, LeetCode, QuantNet C++, and Probability/Statistics drilling) ahead of your MSCF program.

---

## 🚀 The Capstone Outcome: The "Showstopper"

To avoid looking like a mediocre or "toy" project, your summer work must deliver a highly novel, production-ready system accompanied by academic-grade documentation.

### The Deliverable:
**"A Formally Verified Options Backtester with Compiler-Enforced Look-Ahead Bias Guarantees"**

This consists of:
1. **The Codebase**: An event-driven backtesting engine where the core accounting, settlement, and signal-generation rules are written in **Lean 4**, compiled to C, and bound to **Python/Cython** via high-performance FFI.
2. **The Invariant**: A mathematical proof, checked by the compiler, that trading signals generated at time $t$ can *only* access information in the filtration $\mathcal{F}_{t-1}$. This **physically and mathematically eradicates look-ahead bias** in your backtester.
3. **The Preprint**: An SSRN-style research paper (8–10 pages) titled:
   > *"Formally Verified Financial Backtesting: Eradicating Look-Ahead Bias via Compiler-Enforced Information Filtrations."*

*Why this works in interviews*: Look-ahead bias is one of the most common, expensive, and embarrassing errors in quantitative research. When you tell a Head of QR that you solved this not by writing unit tests, but by **proving its physical impossibility via a compiled mathematical type system**, they will immediately recognize the novelty and depth of your engineering skills.

---

## 📚 Parallel QR Prep Curriculum

To excel in MSCF and Summer 2027 QR recruiting, your practical coding must run in parallel with rigorous technical drilling.

```
        ┌────────────────────────────────────────────────────────┐
        │             DAILY QUANT PREP WORKFLOW                  │
        └──────────────────────────┬─────────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
  ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
  │ PROB & STATS  │        │   ALGORITHMS  │        │  QUANT THEORY │
  │  Green Book   │        │   LeetCode    │        │  QuantNet C++ │
  │  Zhou / Heard │        │  Tree/DP/Graph│        │ Options Models│
  └───────┬───────┘        └───────┬───────┘        └───────┬───────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                                   ▼
        ┌────────────────────────────────────────────────────────┐
        │   `quant-proofs` IMPLEMENTATION & FORMAL THEOREMS      │
        └────────────────────────────────────────────────────────┘
```

### 1. Probability & Statistics (The "Green Book" & Zhou)
* **Resource**: *A Practical Guide to Quantitative Finance Interviews* (Xinfeng Zhou) + *Heard on the Street* (Timothy Falcon Crack).
* **Focus**: Martingales, Markov chains, conditional expectation, and random walks.
* **Direct Tie-in to Project**: The formalization of equivalent martingale measures in **Phase 1 (FTAP)** acts as the ultimate conceptual playground. Proving radon-nikodym derivatives or conditional expectations in Lean 4 forces you to understand these concepts at a deeper level than 99% of your peers.

### 2. High-Performance Options Programming (QuantNet C++ / Options)
* **Resource**: QuantNet C++ Programming for Financial Engineering (Baruch MFE course).
* **Focus**: Binomial lattice implementations, Black-Scholes pricing, finite differences, and C++ memory management.
* **Direct Tie-in to Project**: Translate the CRR Binomial lattice and Black-Scholes solvers studied in your course directly into the high-performance Python/Cython execution layer of `backtest-proofs`.

### 3. Algorithms & Data Structures (LeetCode)
* **Resource**: LeetCode (Focus: Medium/Hard levels).
* **Focus**: Dynamic Programming (DP), Tree Traversals (DFS/BFS), and Graphs.
* **Direct Tie-in to Project**: Implementing a binomial pricing lattice is fundamentally a dynamic programming problem on a directed acyclic graph (DAG). Proving its properties trains the exact structural logic needed to solve complex DP and graph-based LeetCode problems.

---

## 📅 Integrated Weekly Schedule (May 25 – July 24)

| Week | Project Milestone | Quant Prep Focus | LeetCode / Coding Drill |
| :--- | :--- | :--- | :--- |
| **Week 1** | Define `NoArbitrage` & $K$ subspace geometry. | **Zhou Ch. 4**: Probability drilling (Combinatorics, Bayes, PDF/CDF). | 5 Mediums: Arrays & Hashing, Two Pointers. |
| **Week 2** | Define EMM & Martingale processes in Lean. | **Zhou Ch. 4 (Cont.)**: Expected value, variance, conditional expectation. | 5 Mediums: Binary Search, Sliding Window. |
| **Week 3** | Complete FTAP proof (separating hyperplane / Farkas). | **Zhou Ch. 5**: Stochastic Processes (Martingales, Random Walks). | 3 Mediums, 1 Hard: Stacks & Trees. |
| **Week 4** | Build CRR tree in Lean; step probability $q$. | **QuantNet Ch 1–3**: C++ OOP, financial data structures. | 5 Mediums: Backtracking, DFS/BFS. |
| **Week 5** | Complete Put-Call Parity proof in Lean. | **QuantNet Ch 4–6**: Binomial lattice algorithms, option payoffs. | 3 Mediums, 1 Hard: Dynamic Programming. |
| **Week 6** | Scaffold `backtest-proofs` & $\mathcal{F}_t$ filtration kernel. | **Zhou Ch. 6**: Quantitative Finance Theory (Black-Scholes, Greeks). | 5 Mediums: Greedy Algorithms, Interval scheduling. |
| **Week 7** | Implement Python event-driven loop & Cython FFI. | **QuantNet Ch 7–8**: High-performance optimization, memory design. | 3 Mediums, 1 Hard: Graphs, Heaps. |
| **Week 8** | Prove backtest invariants (cash preservation, zero-lookahead). | **Drill Mock Interviews**: Green Book Brainteasers (Ch. 2-3). | 5 Hards: Advanced DP, Union-Find. |
| **Week 9** | Compile full suite, run `qa_checker`, write preprint. | **Review & Prep**: Package pitch, polish resume, prep MSCF introduction. | Final review of Top 100 Interview Patterns. |

---

## 🎯 Interview Positioning Strategy

When speaking to a Head of QR or Portfolio Manager:

1. **Start with the Novelty**:
   > *"I noticed a recurring challenge in quantitative research is that backtests look stellar in research but underperform in production due to subtle look-ahead bias or implementation drift. This summer, I built a system that mathematically guarantees the absence of these errors."*
2. **Explain the Technology through Value**:
   > *"I implemented the core pricing and signal-generation logic in Lean 4, a formal proof assistant. The compiler mathematically verifies that my trading signals only reference past information ($\mathcal{F}_{t-1}$) relative to the price filtration. This means look-ahead bias is physically impossible under the type system."*
3. **Show high-performance capability**:
   > *"To keep execution fast, I compiled the verified kernel to C and built high-performance Python/Cython FFI bindings, letting me run event-driven simulations over large option data sets without sacrificing safety or performance."*
