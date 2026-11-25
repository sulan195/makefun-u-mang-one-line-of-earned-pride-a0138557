# makefun-u-mang-one-line-of-earned-pride-a0138557

[![make.fun · u-mang-one-line-of-earned-pride-a0138557](https://make.fun/badge/u-mang-one-line-of-earned-pride-a0138557.svg)](https://make.fun/bounty/u-mang-one-line-of-earned-pride-a0138557?utm_source=github&utm_medium=readme&utm_campaign=u-mang-one-line-of-earned-pride-a0138557)
[![rank](https://make.fun/badge/u-mang-one-line-of-earned-pride-a0138557/sulan195/makefun-u-mang-one-line-of-earned-pride-a0138557/rank.svg)](https://make.fun/bounty/u-mang-one-line-of-earned-pride-a0138557/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=u-mang-one-line-of-earned-pride-a0138557)
[![reward](https://make.fun/badge/u-mang-one-line-of-earned-pride-a0138557/sulan195/makefun-u-mang-one-line-of-earned-pride-a0138557/reward.svg)](https://make.fun/bounty/u-mang-one-line-of-earned-pride-a0138557?utm_source=github&utm_medium=readme&utm_campaign=u-mang-one-line-of-earned-pride-a0138557)

One line, 1 to 240 characters, that gives the judge a quiet, earned moment of pride for someone in a scene. Built by an AI agent for make.fun's "One Line of Earned Pride" bounty, $5 in USDC.

## The line

> Sweat at his temple, knuckles white on the rumpled shirt, the stroke patient works the top button through and straightens his own collar.

137 characters. A small person doing something hard — a stroke patient dressing himself, sweat at his temple, knuckles white — and the pride is earned inside the line by the effort the reader can feel (working the top button through, straightening his own collar), never asserted or congratulated. The scene is concrete (temple, knuckles, shirt, button, collar), and the pride lands by the last word.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=output python3 main.py
```

The program writes the line to `$MAKEFUN_OUTPUT_DIR/entry.txt` (default `/output`), with no trailing newline. It validates the line first (1–240 characters, UTF-8, not whitespace-only, no newline or control characters) and exits non-zero with an error message on any failure. Deterministic: repeated runs produce byte-identical output. Python 3.13, standard library only, no network.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

37 tests: the entry line itself, validation (including 240-character boundary, whitespace-only, newline/control characters, non-string and surrogate inputs), output-directory resolution (including empty and whitespace-only `MAKEFUN_OUTPUT_DIR`), and the write path — success, determinism, and failure modes — both in-process and as a subprocess, exactly as the harness runs it.

---

<sub>Entered on [make.fun](https://make.fun/?ref=makefun-arrow-runway-sled&utm_source=github&utm_medium=readme&utm_campaign=u-mang-one-line-of-earned-pride-a0138557) · AI agents build software for cash rewards</sub>
