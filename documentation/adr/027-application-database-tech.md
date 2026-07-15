
# ADR-027: Application Database Technology

## Status

Accepted

Date of decision: 2026-07-14

## Context and Problem Statement

Local Transcribe needs a database to persist its application data. The i.AI Minute implementation relied
on Aurora, following i.AI's common platform pattern. What database should Local Transcribe use?

## Considered Options

* AWS Aurora Serverless v2
* AWS RDS for PostgreSQL

## Decision Outcome

AWS RDS for PostgreSQL, because it is cheaper than Aurora (especially at small scale), sufficient for our
capacity needs, and fully compatible with existing code.

## Pros and Cons of the Options

### AWS Aurora Serverless v2

Use Aurora Serverless v2 with PostgreSQL compatibility.

* Good, because its use with i.AI's Minute gives us confidence it will meet our needs
* Good, because it offers strong managed database capabilities and high availability options
* Neutral, because it can scale capacity more dynamically for sharp or unpredictable demand spikes, but
  we don't anticipate such spikes
* Bad, because it has higher baseline and operational cost for our expected workload profile
* Bad, because we do not currently need the additional elasticity that drives Aurora's cost premium

### AWS RDS for PostgreSQL

Use standard managed PostgreSQL on AWS RDS.

* Good, because it is lower cost for low to moderate, predictable workload levels
* Good, because it preserves PostgreSQL compatibility with minimal application-level change
* Good, because it is operationally simpler for current needs while still providing managed backups,
  patching, and high availability configurations
* Good, because it provides sufficient performance and reliability for foreseeable demand
* Bad, because it has less automatic elasticity than Aurora if demand becomes highly spiky
* Bad, because a future step-change in traffic may require re-evaluation and potential migration

## More Information

This decision is based on current and expected Local Transcribe usage patterns. If traffic volatility,
scale, or availability requirements materially change, this ADR should be revisited.