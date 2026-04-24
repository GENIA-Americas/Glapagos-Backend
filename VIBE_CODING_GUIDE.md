# Vibe Coding: A Collaboration Guide

This guide explains how we work together on Glapagos-Backend using vibe coding principles. It's not a rulebook—it's a shared understanding of what makes collaboration good.

## Core Principles

### 1. Clarity Over Cleverness

Code should be easy to read and understand. A straightforward solution that anyone can follow beats a clever solution that only the author understands. We optimize for the next person reading the code, not for how smart it makes us look.

### 2. Readability Is a Feature

How code reads directly affects developer experience. We care about:
- Variable names that explain intent
- Functions that do one thing well
- Comments that explain why, not what
- Structure that makes sense at a glance

### 3. Shared Ownership

No one person owns a piece of code. We all own it together. This means:
- Code review is collaborative, not gatekeeping
- Questions are invitations to explain, not challenges to defend
- We help each other improve incrementally

### 4. Async-First Mentality

Not everyone is available at the same time. Work should be documented so:
- Teammates in different timezones can pick up where you left off
- Decisions are explained in writing, not just in Slack
- Pairing sessions accelerate work, but don't block it

### 5. Improvement Over Perfection

We ship incrementally. A good solution shipped today beats a perfect solution that never ships. We iterate based on real usage, not hypotheticals.

## Workflow: How We Build

### Phase 1: Planning (30 minutes to 1 hour)

Before writing code:
1. Read the issue completely
2. Identify what's unclear
3. Ask questions in a comment (tag the team)
4. Wait for answers before starting
5. If it's your first time with this code, pair for the planning phase

What this produces:
- A clear understanding of what "done" looks like
- Knowledge of where the code lives
- Agreement on the approach

### Phase 2: Development (varies)

Choose your approach:

Option A: Solo + Async Checkpoints
- Work on your branch
- Push commits with clear messages
- Post a draft PR with notes on progress
- Ask for feedback at key points
- Team responds within 24 hours

Option B: Pairing Session
- Schedule a sync session (1-3 hours)
- Work through the problem together
- Take turns driving and navigating
- Commit as you go

Option C: Hybrid
- Pair for the tricky parts
- Solo for the straightforward parts
- Async check-ins in between

### Phase 3: Review (1-2 hours typically)

Code review is collaborative:

1. Open a PR with a clear description
2. Link to the issue it solves
3. Note any decisions or tradeoffs
4. Tag reviewers
5. Reviewers ask questions, suggest improvements (always kindly)
6. Author responds to feedback
7. Iterate until everyone is happy
8. Merge

No "request changes" blocking—only "let's discuss this together."

### Phase 4: Merge & Learn

1. Merge to main
2. Deploy (if applicable)
3. Post a summary in Slack: what worked, what surprised us, what we'd do differently
4. Celebrate

## Feedback Philosophy

How we give and receive feedback matters as much as the feedback itself.

### Giving Feedback

Assume good intent. The person who wrote this code was doing their best with the information they had.

Good feedback:
- Asks questions instead of commands: "What if we..." instead of "You should..."
- Explains the reasoning: "This is because..." not just "No"
- Acknowledges tradeoffs: "This is clearer but slightly slower—is that OK?"
- Celebrates good work: "I like how you handled this edge case"

Bad feedback:
- "This is wrong" (wrong for whom? why?)
- "That's not how we do it" (without explaining why you do it that way)
- Nitpicking style while ignoring substance
- Sarcasm or impatience

### Receiving Feedback

Remember: feedback is about the code, not you.

- Read it fully before responding
- Ask clarifying questions if you don't understand
- Explain your reasoning—help reviewers understand your intent
- Change your mind when you see a good point
- It's OK to disagree; we discuss

## Pairing Sessions

Pairing accelerates learning and solves hard problems faster.

### When to Pair

- First time with a new codebase
- Stuck on something for 30+ minutes
- Complex logic that needs discussion
- Mentoring a new contributor
- High-risk changes that benefit from two brains

### How to Pair

1. Schedule 60-90 minutes
2. One person drives (writes code), one navigates (thinks ahead)
3. Switch every 15-20 minutes
4. Talk out loud—explain what you're doing and why
5. Take notes on decisions
6. Commit together with a message noting it was a pairing session

### After the Session

- Write a summary in the PR: what you learned, what you decided
- Share notes with the team (async folks benefit from knowing what happened)
- Continue work async if needed

## Code Standards: The Vibe

We follow Python/Django best practices, but we apply them with pragmatism.

### What We Care About

- Code passes linting (we use standard Django/Python tools)
- Tests exist and pass for core logic
- Functions are reasonably sized (you should understand them in one read)
- Variable names are clear
- Comments explain the why, not the what
- Documentation exists for public APIs

### What We Don't Care About

- Perfect test coverage (aim for meaningful coverage, not 100%)
- Clever one-liners if they sacrifice readability
- Following a rule if it makes code worse
- Matching a style guide at the expense of clarity

In conflicts between the rulebook and clarity, clarity wins.

### Code Review Checklist

When reviewing code, ask:

- Is this clear? Could I explain it to someone else?
- Does it do what the issue asks?
- Are there obvious bugs or edge cases?
- Does it fit the existing code style?
- Are there tests for the new behavior?
- Is it documented (comments, docstrings, README)?

That's it. You don't need to be perfect.

## Common Workflows

### Bug Fixes

1. Reproduce the bug locally
2. Write a test that fails
3. Fix the bug
4. Watch the test pass
5. PR with a link to the issue
6. Done in usually 1-2 hours

### Refactoring

1. Make sure tests pass before you start
2. Make small changes—don't rewrite everything at once
3. Run tests after each change
4. Commit frequently so history is clear
5. PR explaining what changed and why
6. Reviewers: check that tests still pass and logic is preserved

### Getting Unstuck

If you're stuck:
1. Try for 30 minutes on your own
2. Write down exactly where you're stuck
3. Post in Slack or GitHub with:
   - What you tried
   - What you expected
   - What happened instead
   - Relevant code links
4. A teammate will pair with you or suggest a direction
5. You're usually unblocked within an hour

### Disagreements

Sometimes we disagree on the best approach.

1. Both people explain their reasoning clearly
2. We discuss tradeoffs
3. If it's not a safety issue, we try the first approach
4. If it doesn't work out, we iterate
5. We learn together

There's rarely one perfect answer. We move forward and adjust.

## Learning Culture

This project is a learning space. You don't need to know everything.

- Questions are celebrated, not penalized
- "I don't know" is a complete sentence
- Mistakes teach us more than successes
- Teaching each other is part of the work
- It's OK to be wrong in a PR—that's what pairing and review are for

We move fast, but we move kindly.

## Async Communication

Working async requires being explicit.

### In GitHub Issues

- Describe the problem clearly
- Provide context and links
- If you're stuck, explain where
- Assume people will read this later with fresh eyes

### In PRs

- Explain what changed and why
- Link to the issue
- Note any decisions or tradeoffs
- If something is experimental, say so
- Ask specific questions instead of generic "thoughts?"

### In Slack

- Use threads so conversations don't get lost
- Share links to relevant code/PRs
- If something is important, also open an issue or PR
- Slack is transient; decisions go in GitHub

## Getting Help

You never work alone on vibe coding.

- Stuck? Post in Slack with your setup + what you've tried
- Need a pairing session? Ask in the issue
- Not sure if your approach is right? Open a draft PR and ask
- Want feedback on design? We discuss before you code

Everyone in this project wants you to succeed. Asking for help is how you move faster.
