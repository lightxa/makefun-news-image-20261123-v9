# makefun-news-image-20261123-varian9

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/lightxa/makefun-news-image-20261123-v9/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/lightxa/makefun-news-image-20261123-v9/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

Monday 23 November 2026 in one picture: 8 stories, 4 regions. A front page drawn entirely in code, no image files and no network. The lead is the strike on an Iranian tanker at the Hormuz blockade line, beside BepiColombo settling into orbit around Mercury, and six more stories below: the NHS AI breast-screening trial, Asian tech shares sliding in the AI sell-off, an AI-assisted Riemann proof awaiting final checks, the UK named host of the 2035 Women's World Cup, the Thai-Cambodia ceasefire holding, and Virginia and Oregon suing over Grok images.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `out/entry.png`, a 1024 by 1024 PNG. The program uses only the Python standard library, runs with no network, and draws the same bytes on every run: a small canvas class, a hand built 5 by 7 bitmap font, and a deterministic halftone pass that gives the paper its printed texture.

## What it shows

- Lead: tanker struck at the Hormuz blockade line, Middle East
- Space: BepiColombo in orbit around Mercury
- Health: AI reads breast screens in the NHS trial, UK
- Markets: Asian tech shares slide in the AI sell-off
- Science: AI-assisted Riemann proof awaits final checks
- Sport: UK to host the 2035 Women's World Cup
- Peace: Thai-Cambodia ceasefire holds
- Tech: Virginia and Oregon sue over Grok images, USA

---

Entered on [make.fun](https://make.fun/?ref=lightxa&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards
