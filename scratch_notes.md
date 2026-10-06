## Pass 2 Extraction and Spend Control (October 1, 2026)
### Pilot Phase
- **Model:** claude-sonnet-5
- **Drop Rates:** REMEMBERED: 2.3% (1 dropped out of 43 returned). FORGOTTEN: 0.0% (0 dropped out of 1 returned). Max drop rate: 2.3%.
- **Measured Cost:** The measured cost per unit was $0.0113 ($0.3403 for 30 units).
- **Span Length Cap:** Added explicit constraint to the schema and prompt restricting span length to a maximum of 20 words to ensure minimal verbatim substring extraction.

### Target Selection and Stratification
- **Budget constraints:** The total remaining budget was $8.16 (total $8.50 limit minus $0.34 pilot). At $0.0113 per unit, this afforded 722 more units.
- **Final Unit Count:** Rather than capping at a smaller number, we ran all eligible units. The total number of valid units in the "yes" pool with length > 250 characters was exactly 720 units.
- **Stratification:** Because the total pool (720) was smaller than the affordable budget limit (752), we processed the entire population of the eligible "yes" pool rather than drawing a sample. The pool was naturally stratified as: Help Community (505), Reddit Assisted (186), StackExchange (20), Hacker News (8), and Play Store (1).
