---
name: audio-jingle
description: Single-track / single-episode music-player mockup template — glassmorphic iOS-Music style player card with ambient album-art wash, for showcasing one song, one podcast episode, or one audio jingle as a shareable interactive surface.
visibility: public
mode: template
carrier: web-page
scenario: audio-showcase
pattern_source: music-player.html
source_priority: skill-first
triggers:
  - "做个音乐播放器 mockup"
  - "单曲展示页"
  - "播客单期封面"
  - "iOS Music 风播放器卡"
  - "玻璃感播放器"
---

# Audio Jingle Template

Use this template when the artifact is a small, focused player UI around a single piece of audio — a song drop, a podcast episode, a brand jingle demo, an artist spotlight.

## Use When

- The user wants to show off **one** track / episode / jingle (not a full library).
- The output is a sharable mini-player page or an in-line embed mockup (artist landing, EPK, "listen now" card).
- The desired look is calm, premium, Apple-Music-leaning glassmorphism over an ambient album-art wash.
- The user is pitching a music release, a podcast hook, or a sonic-branding deliverable.

## Avoid When

- The content is a long playlist, browsable library, or full music-app product (this template's queue strip is decorative, not browsable).
- The audio needs lyrics scrolling, waveform editing, or audiogram-style captioning.
- The user actually wants a video player, social card, or marketing landing.
- The release is loud / cyberpunk / underground — the template's mood is restrained and premium; replace, don't fight it.

## Required Reading

Read this `SKILL.md` first. Do **not** read `music-player.html` by default.

Read `music-player.html` only when you need concrete layout rhythm of the player card, scrubber/control geometry, or the active-track equalizer animation. Extract patterns; do not copy DOM, CSS classes, color tokens, or the placeholder track metadata wholesale.

## Design Strategy

Decide the surface role first:

- single-track release card (artist + title + art + play)
- podcast episode hero (episode title + show + duration)
- jingle showcase (brand mark + track + small "use cases" caption)
- artist spotlight (avatar + bio sliver + featured track)

Then pin the dominant color to the album/episode artwork — let the ambient wash do the color-bearing.

## Layout Bias

Prefer:

- one square hero artwork, perceptibly large
- the player card centered with breathing room, not stretched edge-to-edge
- ambient blurred backdrop sampled from the artwork (not arbitrary gradient)
- monospaced or tabular numerals for timecodes
- a short queue strip (≤ 6 items) only if it adds context, otherwise omit

Avoid:

- decorative "vinyl spin" or 3D speaker stickers (slop)
- neon EQ bars or rave gradients
- crowding the player card with social / download / share / tip / lyrics all at once
- text overlayed directly on artwork — keep type on the glass card

## Platform / Size

This is a **web-page mockup**, not a fixed-image export. Default to a mobile-first centered column (~ 390–420px content width) on a full-bleed ambient backdrop. If the user asks for an embeddable card, crop to that aspect; if they ask for a poster, switch to a social-card template instead.
