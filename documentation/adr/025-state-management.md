# ADR-025: State management

## Status

Approved

Date of decision: 2026-06-26

## Context and Problem Statement

Many user journeys require data from one page to be available on subsequente pages. We currently don't have an agreed
approach for supporting this pattern. What default approach should we adopt?

## Considered Options

* Local Storage 
* Session Storage 
* Zustand
* React Context API
* URL Params
* Redux
* Server-side state

## Decision Outcome

Zustand, because it is simple, lightweight, performant, integrates well with React, and
offers optional persistance.

## Pros and Cons of the Options

### Local Storage

A brower based storage option that allows for the storage of data as key-value pairs on a
user's device. The stored data doesn't expire and persists even after users close & reopen
the browser.

* Good, because it requires no additional dependencies
* Good, because it's simple to use
* Good, because it's extensible beyond React
* Neutral, because it persists across sessions (which is sometimes useful, or sometimes unexpected)
* Neutral, because some data structures require careful marshalling
* Bad, because the data can be mutated indirectly 
* Bad, because local storage can be vulnerable to XSS attacks
* Bad, because as it's a client-side API, inconsistencies may arise during SSR
 
# Session Storage

Near identical to local storage with the exception that stored data doesn't persist when a 
user closes their tab, browser or window.

* Good, because it requires no additional dependencies
* Good, because it's simple to use
* Good, because it's extensible beyond React
* Good, because data is automatically cleared on tab/window close, reducing data exposure
* Good, because data is scoped to a single tab, preventing unintended cross-tab data sharing
* Neutral, because some data structures require careful / marshalling
* Neutral, because tab-scoped isolation may be a limitation for workflows spanning multiple   
sessions where continuity is expected
* Bad, because the data can be mutated indirectly
* Bad, because session storage can be vulnerable to XSS attacks
* Bad, because as it's a client-side API, inconsistencies may arise during SSR

### Zustand

A lightweight state management library best suited for managing small to medium state complexity. It provides intuitive hooks that allow components to consume and update state as needed.

* Good, because it provides simple global state management with minimal boilerplate
* Good, because it allows state to be shared across pages and components
* Good, because it has a small bundle size and simple API
* Good, because state updates only re-render subscribed components
* Good, because persistence can be added through middleware if required
* Bad, because state is stored in memory by default and is lost on page refresh (can be mitigated using middleware)
* Bad, because it introduces an additional dependency to the application
* Bad, because application state can become difficult to reason about if stores grow without clear ownership boundaries

### React Context API

A native React API that enables data sharing across components without prop drilling. 
State is stored in a context object whose values are accessible to any wrapped component 
via the `useContext` hook.

* Good, because it is built into React and requires no additional dependencies
* Good, because it allows state to be shared across pages and components
* Good, because it integrates naturally with existing React patterns
* Good, because it is suitable for relatively simple and low-frequency state updates
* Bad, because context updates can trigger unnecessary re-renders if not carefully designed
* Bad, because managing complex application state can become cumbersome
* Bad, because it requires additional provider setup and wiring
* Bad, because state is stored in memory and is lost on page refresh

### URL Parameters

A means of encoding parts of an application's state directly in the URL through query parameters. 

* Good, because state is preserved across page refreshes and browser navigation
* Good, because it requires no additional dependencies
* Good, because it aligns with web navigation conventions
* Neutral, because state can be bookmarked, shared, and deep-linked
* Bad, because only small amounts of serializable data can be reasonably stored in URLs
* Bad, because URLs can become difficult to read and maintain as state grows
* Bad, because sensitive information should not be exposed in URLs
* Bad, because additional parsing, validation, and encoding logic is required

### Redux

A state management library designed to handle complex application state predictably 
through a unidirectional data flow and a centralised store.

* Good, because it provides a well-established and widely adopted state management pattern
* Good, because it centralises application state in a predictable manner
* Good, because it offers strong debugging and developer tooling
* Good, because it scales well for large and complex applications
* Bad, because it introduces additional dependencies and concepts to learn
* Bad, because it requires more boilerplate than the alternative options
* Bad, because it may be overly complex for simple cross-page state requirements
* Bad, because state is stored in memory by default and is lost on page refresh unless persistence is added

### Server-side state

A means of managing application state on the server rather than the client, with state 
changes triggered via server requests and reflected through updated responses - either on a
per-session basis (e.g. Redis + session ID in cookie) or persisted (e.g. to a database).

* Good, because it aligns with GDS recommendations to avoid SPAs and not require 
  JavaScript for core functionality
* Good, because potentially sensitive state is not held long-term on the client-side
* Good, because state is consistently reflected across all tabs, devices and sessions 
  without any additional synchronisation logic
* Good, because it leverages existing server infrastructure (e.g. PostgreSQL) without 
  requiring additional client-side state management dependencies
* Neutral, because server-side rendering moves complexity from the client to the server, 
  which may require architectural changes
* Bad, because fetching and reflecting server-side state during SPA-style client 
  navigation isn't an optimal fit — each state change requires a round trip to the server, 
  introducing latency and diverging from the expected SPA behaviour & dynamism
* Bad, because it is a poor fit for highly interactive UI (e.g. real-time updates) where immediate client-side feedback is expected before server confirmation
* Bad, because it increases server load and costs proportionally to the frequency of state 
  changes, which may require additional infrastructure consideration at scale


