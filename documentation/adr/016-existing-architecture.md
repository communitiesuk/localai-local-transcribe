# ADR-016: Existing Minute Architecture Choices

## Status

Accepted

Date of decision: 2026-02-06

## Context and Problem Statement

Ideally, each architectural decision would be captured in an ADR as the system is designed. In our case, we are inheriting Minute as essentially a fully formed system. This system has been deployed and trialled with 22 councils, so we can trust it is fit for that purpose, at least.

How much re-examination, retrospective documentation, and rebuilding should be aiming for?

## Considered Options

* Start from scratch
* Exhaustively document
* Ad hoc deviations from baseline

## Decision Outcome

Ad-hoc deviation from baseline, as it avoids low-value rework while retaining flexibility

## Pros and Cons of the Options

### Start from scratch

Assume we're starting from zero, and build up a new Minute solution design making fresh decisions at each step.

* Good, because it gives the best chance of the architecture fitting our particular needs.
* Good, because it provides good coverage of decisions.
* Bad, because it involves a great deal of rework.

### Exhaustively document

Attempt to document all the decisions that lead to the existing architecture

* Good, because it essentially forces a comprehensive review and an opportunity to rationalise, leaving us with good coverage of decisions.
* Bad, because it requires us to artificially create ADRs retrospectively (and our reasoning may not be the reasoning of the time).
* Bad, because it requires us to write quite a lot of ADRs up front (though less work than potentially changing all those decisions).

### Ad hoc deviations from baseline

Accept the current architicture as a baseline (via this ADR), then make ADRs where we spot areas where we'd like to deviate from that baseline.

* Good, because it keeps the amount of (re)work low.
* Good, beause we can still make the changes we think are necessary.
* Bad, because we won't have explicitly documented decisions for choices we're happy with.