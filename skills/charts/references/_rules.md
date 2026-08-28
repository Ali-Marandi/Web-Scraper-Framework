# ⚠️ STRUCTURAL DIAGRAM IRON LAWS

These rules apply to Playwright+CSS structural diagrams (flowcharts, mind maps, radial grids, org charts). They are enforced by the template files. Violating any = task failure.

## 1. ZERO OVERLAP
No element may overlap another:
- Arrows/connectors must not cross over text boxes
- Connectors must not pass through node bodies
- Text boxes / nodes must not overlap each other
- Labels must not obscure any graphic element

**Post-generation**: verify every element has clear separation. If overlap exists, fix before delivery — enlarge canvas, increase spacing, or reduce content.

## 2. LAYOUT MUST HAVE HIERARCHY
Forbidden: all nodes same size, same level, mechanically tiled in a flat grid.

Required:
- Primary nodes visually larger/bolder than secondary nodes
- Annotation nodes clearly subordinate (smaller, muted color)
- Spacing between groups > spacing within groups
- Clear reading path (top→bottom, left→right, or center→outward)

**Squint test**: if every box looks identical, the layout has failed.

## 3. NODE BACKGROUND COLORS

**🚫 Forbidden as background (too saturated for large fills):**

| Color | Forbidden Hex |
|-------|--------------|
| Pure blue | `#3B82F6`, `#2563EB`, `#1D4ED8` |
| Pure green | `#10B981`, `#059669`, `#22C55E` |
| Pure red | `#EF4444`, `#DC2626`, `#F87171` |
| Pure purple | `#8B5CF6`, `#7C3AED`, `#A855F7` |
| Pure amber | `#F59E0B`, `#D97706`, `#FB923C` |
| Any color: R/G/B > 0xCC and saturation > 50% | — |

**✅ Allowed as background:**

| Color | Hex | Usage |
|-------|-----|-------|
| Ice blue | `#EFF6FF`, `#DBEAFE` | Normal step nodes |
| Mint green | `#F0FDF4`, `#D1FAE5` | Success/pass nodes |
| Light amber | `#FFF7ED`, `#FEF3C7` | Decision/warning nodes |
| Lavender | `#F5F3FF`, `#EDE9FE` | End/terminal nodes |
| Light gray | `#F8FAFC`, `#F1F5F9` | Group containers |
| White | `#FFFFFF` | Default canvas |

**Rule: Saturated colors go on BORDERS (2px) and TEXT only. Backgrounds stay pale.**
