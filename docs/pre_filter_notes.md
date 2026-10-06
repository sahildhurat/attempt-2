## Pre-Filter Logic and Recall

**Date:** 28 September 2026

To reduce the number of units passed to the relevance gate, we implemented a deterministic keyword pre-filter. A unit is retained only if its combined `text` and `context` contain at least one token from BOTH sets (case-insensitive):
- **Photo Tokens**: photo, photos, pic, picture, image, album, memories
- **Retrieval Tokens**: find, search, look for, locate, remember, recall, where is, where are, scroll, can't see, missing

### Pre-Filter Loss by Source
- **appstore**: 29/30 lost (96.67%)
- **help_community**: 5794/7811 lost (74.18%)
- **hn**: 1193/1978 lost (60.31%)
- **playstore**: 2348/2996 lost (78.37%)
- **stackexchange**: 301/459 lost (65.58%)
- **youtube**: 2779/3087 lost (90.02%)

**Total accepted**: 3917 (passed to Pass 1 Gate)  
**Total rejected**: 12444

*Note on False-Negative Rate*: The measurement of the false-negative rate on 200 random rejected units is currently blocked by the strict 20 request/day free tier API quota on `gemini-3.8-flash`. The script is designed to wait and resume, so the rate will be recorded once API access is restored.
