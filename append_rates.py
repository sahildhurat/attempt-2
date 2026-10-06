with open("docs/method_notes.md", "a", encoding="utf-8") as f:
    f.write("\n### Batching Validation Results (30 September 2026)\n")
    f.write("Batch processing (batch-25) vs Single-call validation was run on two distinct samples using the finalized rules:\n")
    f.write("- **78.00% agreement** on a random sample (100 units drawn at random from the full corpus, seed 43, no stratification and no length floor).\n")
    f.write("- **84.00% agreement** on a sample enriched for boundary cases (the original 100-unit adversarial sample filtered for >250 chars and stratified across sources).\n")
    f.write("Because the random sample did not clear the 97% threshold, batching is deemed unsafe. The pipeline will proceed unbatched to avoid dropping relevant units.\n")
