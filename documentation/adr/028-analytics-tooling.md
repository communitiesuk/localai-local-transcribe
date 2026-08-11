# ADR-028: Analytics Tooling

## Status

Proposed

Date of decision: {yyyy-MM-dd}

## Context and Problem Statement

We want to gain insights into how people use Local Transcribe, so we can understand how to make (particularly incremental)
improvements. We _also_ want to understand how Local Transcribe impacts real world outcomes. To support both of these goals,
we need to record and review analytics data. What tool(s) should we use to do so?

## Considered Options

* PostHog
* Google Analytics
* Plausible
* First-party database
* Plausible + first-party database

## Decision Outcome

Plausible + first-party database, because it leverages off-the-shelf software where possible whilst also avoiding cookie banners
(which would significantly reduce the amount of data gathered).

## Pros and Cons of the Options

### PostHog

The inherited Minute codebase used PostHog, so this is still present (dormant) in the Local Transcribe codebase. PostHog provides
basic web analytics, custom events, and user-level insights.

* Bad, because it is not Cyber assured
* Bad, because it requires a 'cookie banner' to gather consent from the user for it to be used
* Good, because we could reuse existing code

### Google Analytics

Google Analytics is a mature, widely used web analytics platform.

* Good, because it is commonly used across HMG and MHCLG
* Bad, because it requires a 'cookie banner' to gather consent from the user for it to be used.
* Bad, because it does not sit well with the technology code of practice requirement to respect user's privacy
* Good, because it is available for free

### Plausible

Plausble is an alternative to Google Analytics that is privacy-focused, EU hosted, but less feature rich.

* Neutral, because it is used elsewhere in MHCLG, but not widely (yet!)
* Good, because it preserves user's privacy
* Good, because it doesn't require a 'cookie banner'
* Bad, because to preserve privacy and avoid a cookie banner, we couldn't gather per-user data: Plausible is designed
  around recording and providing only aggregated, non-identifiable data.
* Bad, because it has a financial cost

### First-party database

Instead of using an off-the-shelf solution, we could build some basic analytics event storage in Local Transcribe's
infrastructure.

* Bad, because it requires developer effort, even for the basics
* Bad, because it will be less feature-rich than an off-the-shelf product
* Good, because it doesn't require a 'cookie banner', even for per-user data (confirmed with data governance colleagues)
* Good, because we have total control over how we aggregate / analyse the data

### Plausible + first-party database

Use Plausible for aggregate-level data (for understanding how people use Local Transcribe in general) and first-party
database recording for user-level data (for understanding real world impact).

* Good, because it preserves user's privacy to the degree possible
* Good, because it doesn't require a 'cookie banner'
* Good, because it provides a useful UI (Plausible) for web analytics
* Bad, because it requires all the dev work associated with the first-party database option
* Bad, because it increases architectural complexity