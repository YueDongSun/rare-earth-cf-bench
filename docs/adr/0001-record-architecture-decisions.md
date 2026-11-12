# 1. Record architecture decisions

Date: 2026-11-12

## Status

Accepted

## Context

Several coding agents will change this repository in parallel. A change to the task format, the package public API, or the directory layout has to stay visible after the pull request is merged, otherwise the next agent rediscovers it from chat history or guesses.

## Decision

Architecture decisions are Markdown files in `docs/adr/`, numbered and immutable once accepted. A later decision supersedes an earlier one with a new file; it does not rewrite history.

A pull request that changes the task format, the public API of `cfbench`, or the directory layout adds a new ADR in the same pull request. Scientific definitions do not go in ADRs. Those belong in `spec/` and are written by the owner.

## Consequences

Agents can see why the layout and the task format look the way they do. An ADR is an engineering record. It does not authorise a convention, a tolerance, or a physical constant that `spec/` does not state.
