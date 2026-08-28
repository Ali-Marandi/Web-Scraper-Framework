---
name: social-card-map
description: 地图 / 行程 / 路线主导的社交卡 — 路线 + 3 个停靠点 / 邻里地图 + 推荐标签 / 一日行程 + 简化路径 / 地点卡 + 迷你地图 + 旅行笔记 / 两区两路线对比。地理必须激进简化，只标必要地点，给清晰路径层级，配 city/date/duration/walking-driving 上下文。触发："做个旅行路线卡 / 行程图卡 / 邻里地图卡 / 周末散步路线 / 城市指南"。NOT 真实地图数据虚构，NOT 地图当背景装饰。
visibility: public
mode: template
carrier: fixed-image
scenario: social-content
pattern_source: pattern.html
source_priority: skill-first
triggers:
  - "做个旅行路线卡"
  - "行程图卡"
  - "邻里地图卡"
  - "周末散步路线"
  - "城市指南卡"
  - "地图打卡卡"
related_patterns: social-card-editorial
---

# Social Card Map / Travel Template

Use when location, route, itinerary, distance, neighborhood, or place relationship is central to the card.

## Core Rule

A map card must clarify spatial relationships. Do not add a map shape only as decoration.

## Structure Options

- route map + 3 stops
- neighborhood map + recommendation labels
- day itinerary + simple path
- place card + mini map + travel note
- comparison: two areas / two routes

## Must Do

- Simplify geography aggressively.
- Label only necessary places.
- Use a clear route/path hierarchy.
- Include context: city, date, duration, walking/driving/transit if relevant.

## Avoid

- Map details too dense for phone viewing.
- Fake exact map data when none is provided.
- Decorative map backgrounds unrelated to content.

## Pattern Source Rule

Read this `SKILL.md` first. Do **not** read `pattern.html` by default.

Read `pattern.html` only when you need concrete layout rhythm, spatial relationships, or interaction/annotation behavior that this markdown cannot fully specify. When read, extract patterns only; do not copy DOM, CSS classes, exact spacing, placeholder copy, or styling wholesale.
