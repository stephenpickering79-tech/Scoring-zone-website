# 40 Social Designs — Production Plan

## Design Categories (4 formats × 10 topics = 40 designs)

### Format A: App Screenshot Showcase (10 designs)
Phone mockup with actual app screen + floating stat cards

1. A01 — Putting Drills list (done)
2. A02 — Chipping Drills list
3. A03 — Practice Assistant main screen
4. A04 — Round Stats tracker (hole entry)
5. A05 — Sim Lab drills list
6. A06 — Challenge Complete screen (trophy)
7. A07 — Benchmark levels / Score to Beat
8. A08 — Elite Mode challenge screen
9. A09 — Stats dashboard overview
10. A10 — Pressure Combine screen

### Format B: Before/After Stats (10 designs)
Red-to-green improvement data comparison

11. B01 — Putting improvement (done)
12. B02 — Chipping / Up-and-down improvement
13. B03 — Overall scoring improvement (break 90)
14. B04 — Bunker escape rate improvement
15. B05 — 3-putt elimination stats
16. B06 — Practice consistency stats (sessions/week)
17. B07 — Short game HCP drop over 8 weeks
18. B08 — Lag putting distance control
19. B09 — Scrambling % improvement
20. B10 — GIR proximity improvement

### Format C: Drill Explainer (10 designs)
Step-by-step breakdown of specific drills

21. C01 — Lag King (done)
22. C02 — Clock Drill (putting)
23. C03 — One-Club Wizard (chipping)
24. C04 — Streak Survivor (putting)
25. C05 — Par in 2 (chipping - Elite)
26. C06 — Knockout Ladder (putting)
27. C07 — 21 Shots (short game)
28. C08 — Pitching Accuracy Ladder (sim)
29. C09 — Speed Master (putting)
30. C10 — Pressure Combine (mixed)

### Format D: Feature Highlight (10 designs)
Dual-phone or feature showcase with app context

31. D01 — Elite Mode (done)
32. D02 — Practice Assistant overview
33. D03 — XP & Leveling system
34. D04 — Round Stats tracking
35. D05 — Sim Lab for simulator sessions
36. D06 — Structured Practice (guided sessions)
37. D07 — Short Game HCP system
38. D08 — Benchmarks vs Tour/Pro/Amateur
39. D09 — Practice Notepad & Goals
40. D10 — Pressure Test mode

## Integration Plan

### How it works:
- All 40 designs stored as pre-rendered PNGs in `social-designs/library/`
- Each design has matching captions in `social-designs/captions/` (IG, FB, X)
- Packager modified to include 1 app-focused design per cycle
- Rotation: `cycle_number % 40` selects which design to include
- The app design is added as `image_app.jpg` alongside the existing image_01-03.jpg
- Dashboard shows it as an additional variant with label "APP FEATURE"
