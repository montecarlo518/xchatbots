# Rating & price discrepancies — page schema vs Notion directory

Generated 2026-08-13 while adding structured data. **Nothing here was auto-corrected.**

The `aggregateRating` and `Offer.price` values already embedded in these pages disagree with the
`Xchatbots Directory` Notion database. They also match the *visible* rating/price shown on their own
page, so silently syncing the schema to the directory would have made the markup contradict the
page body — which is exactly what Google and Bing penalise.

Pick one source of truth, update the page copy and the schema together, then rerun the audit.

| Page | Tool | rating (page) | rating (directory) | reviews (page) | reviews (directory) | price (page) | price (directory) |
|---|---|---|---|---|---|---|---|
| /ai-boyfriend | CandyAI | 4.8 | 4.5 | 5063 | 5063 | 3.99 | 3.99 |
| /ai-boyfriend | Joi AI | 4.8 | 4.7 | 624 | 624 | 2.38 | 2.38 |
| /ai-boyfriend | Secrets AI | 4.7 | 4.8 | 1240 | 1240 | 19.99 | 19.99 |
| /ai-boyfriend | Xotic AI | 4.0 | 4.5 | 532 | 832 | 7.49 | 12.50 |
| /ai-boyfriend | ourdream.ai | 4.4 | 4.6 | 4031 | 4031 | 9.99 | 9.99 |
| /ai-boyfriend | Darlink AI | 4.6 | 4.6 | 891 | 890 | 12.99 | 12.99 |
| /nsfw-video-generation | Xotic AI | 4.7 | 4.5 | 532 | 832 | 12.50 | 12.50 |
| /nsfw-video-generation | Joi AI | 4.4 | 4.7 | 624 | 624 | 2.38 | 2.38 |
| /nsfw-video-generation | CandyAI | 4.3 | 4.5 | 5063 | 5063 | 3.99 | 3.99 |
| /nsfw-video-generation | Secrets AI | 4.1 | 4.8 | 1240 | 1240 | 19.99 | 19.99 |
| /nsfw-video-generation | FlirtCam AI | 4.5 | 4.4 | 312 | 56 | 19.99 | 19.99 |
| /nsfw-video-generation | OhChat | 4.3 | 4.3 | 204 | 23 | 9.99 | 9.99 |
| /nsfw-video-generation | Golove AI | 4.2 | 4.2 | 187 | 12 | 4.80 | 4.80 |
| /nsfw-video-generation | Dreamz AI | 4.4 | 4.1 | 168 | 32 | 14.99 | 14.99 |

**14 mismatches** across 2 pages.

Newly added `SoftwareApplication` entries in this change set deliberately carry **no**
`aggregateRating` and **no** `offers` for the same reason — structure only, until this is resolved.
