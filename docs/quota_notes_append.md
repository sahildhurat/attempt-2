## API Quota Diagnosis

**Date:** 28 September 2026

The Google GenAI SDK automatically handles 429 quota exhaustion errors with an exponential backoff. To identify the exact limits, we triggered a 429 using raw HTTP requests.

The verbatim `error.details` array returned:
```json
[
  {
    "@type": "type.googleapis.com/google.rpc.Help",
    "links": [
      {
        "description": "Learn more about Gemini API quotas",
        "url": "https://ai.google.dev/gemini-api/docs/rate-limits"
      }
    ]
  },
  {
    "@type": "type.googleapis.com/google.rpc.QuotaFailure",
    "violations": [
      {
        "quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests",
        "quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
        "quotaDimensions": {
          "model": "gemini-3.8-flash",
          "location": "global"
        },
        "quotaValue": "20"
      }
    ]
  },
  {
    "@type": "type.googleapis.com/google.rpc.RetryInfo",
    "retryDelay": "17s"
  }
]
```

**Analysis**:
- The limit encountered is `quotaValue: 20` for `gemini-3.8-flash`. Although the `quotaId` references "PerDay", the `retryDelay` of 17s suggests this behaves as a per-minute burst rate limit on the free tier for this specific model/project combination, or the rate limit triggers in very tight intervals.
- To safely navigate this limit in the pipeline, all scripts must be designed to either batch requests (reducing total API calls) or properly respect `RetryInfo.retryDelay` when a 429 error is hit.

