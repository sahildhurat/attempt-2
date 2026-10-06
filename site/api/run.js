import { GoogleGenAI } from "@google/genai";

/* Runs a piece of text through the same two prompts the corpus went through.
   These are read verbatim from prompts/pass1_relevance_gate.md and
   prompts/pass2_extraction.md. If those change, regenerate this file. */

const GATE_PROMPT = "# System Prompt\nYou are a classifier. Your task is to determine whether a piece of user feedback\nis about someone trying to find a specific photo or video they believe already\nexists in their Google Photos library.\n\n# Decision procedure\n\nApply these steps in order.\n\nSTEP 1 \u2014 Is the person trying to reach a photo or video they believe exists in\ntheir own Google Photos library?\n  If no, the decision is \"no\". This includes questions about the search feature\n  itself (its placement, how to disable it), general feature discussion,\n  problems on other platforms or other apps, and app issues where no attempt to\n  reach a photo is described.\n  Step 1 excludes a text only if NO attempt to reach a photo is described. A\n  bug report, complaint or feature question that ALSO describes someone\n  trying and failing to reach a photo passes step 1. The framing does not\n  matter; the attempt does.\n  If yes, continue to step 2.\n\nSTEP 2 \u2014 Do they name a specific target?\n  A specific target is a photo identified by its content, subject, event,\n  date, place, document type, or by a concrete query the person ran and what\n  they expected it to return. A browsing MODE is not a target \u2014 \"photos in\n  reverse chronological order\", \"my uploaded photos\", \"everything from the\n  last ten years\" fail step 2 and are \"partial\".\n  If yes, the decision is \"yes\".\n  If no, but they describe attempting retrieval, the decision is \"partial\".\n\nSTEP 3 \u2014 OVERRIDE. If the person states the photo or video was deleted, by them\nor anyone else, or asks about recovery or restoration, the decision is \"no\",\nregardless of steps 1 and 2.\n  Step 3 applies only when the person STATES the photo was deleted, or asks\n  how to recover or restore something they know was deleted. It does NOT\n  apply when they are asking whether photos were deleted, or cannot tell\n  whether an item is deleted or merely hidden. Uncertainty is not a statement\n  of deletion.\n\nNotes:\n- The CAUSE of the failure is not the criterion. Someone who cannot reach photos\n  they believe exist has a retrieval problem whether the cause is search, sync,\n  indexing or a display bug.\n- A person who describes a query they ran and what they expected back has named\n  a specific target, even if they give it as an example of a broader problem.\n- Inventory requests (\"find all duplicates\", \"photos not in any album\") pass\n  step 1 but fail step 2, so they are \"partial\".\n- Where the person does not know whether a photo is deleted or merely hidden,\n  step 3 does not apply \u2014 their searching behaviour is still evidence.\n\nGive your reason before your decision. Keep your reason brief (maximum 25 words).\n\n# Examples\n\n**Example 1**\nText: \"I wrong delete vedio. I want recovery vedio\"\nReason: User explicitly states they wrongly deleted a video and asks for recovery. Step 3 override applies.\nDecision: no\n\n**Example 2**\nText: \"How to search and delete exact duplicate photos and videos\"\nReason: User is asking about finding duplicates as a category, an inventory request. Fails step 2 as no specific target is named.\nDecision: partial\n\n**Example 3**\nText: \"How to remove the search feature? I keep accidently clicking it...\"\nReason: User asks how to disable the search feature itself, not trying to find a specific photo.\nDecision: no\n\n**Example 4**\nText: \"where are all the shared pictures and videos? videos people shared are gone\"\nReason: User is trying to find shared pictures and videos they believe exist. They name a specific target collection.\nDecision: yes\n\n# Special rule for replies\nIf this text is a reply to a relevant parent post, and this reply describes\nhow to find something (e.g., suggests a workaround, a search tip, or a\nmethod), classify it as \"yes\" \u2014 even if it does not restate the target photo.\n\n# Language\nIn addition, return the ISO 639-1 two-letter code for the language of the text in the `language` field (e.g. \"en\" for English, \"es\" for Spanish).\n";
const EXTRACT_PROMPT = "You are an expert qualitative researcher analyzing user reports about Google Photos search. \n\nYour task is to extract exactly what the user was trying to retrieve (their target) and what specific search cues they remembered or forgot. \n\nSchema:\n```json\n{\n  \"target\": \"A concise description of the photos they were trying to find\",\n  \"evidence_quote\": \"A single exact quote from the text supporting this extraction\",\n  \"remembered\": [\n    {\n      \"cue\": \"short phrase describing what they remembered\",\n      \"span\": \"exact verbatim substring of the source text supporting this cue\"\n    }\n  ],\n  \"forgotten\": [\n    {\n      \"cue\": \"short phrase describing what they could not remember\",\n      \"span\": \"exact verbatim substring of the source text supporting this cue\"\n    }\n  ],\n  \"workaround\": \"Any alternative method they used to find the photo when search failed\",\n  \"breakdown\": \"The reason the search failed, if stated\"\n}\n```\n\nFor every item in \"remembered\" and \"forgotten\", you must supply a \"span\":\nan exact substring copied character-for-character from the source text that\nsupports that specific cue.\n\n- The span must appear verbatim in the text. Do not paraphrase, correct\n  spelling, expand abbreviations, or alter punctuation.\n- The span must be the SHORTEST verbatim substring that supports the cue \u2014\n  maximum 20 words. Do not quote a whole sentence when a phrase suffices.\n- If you cannot find a verbatim span supporting a cue, do not output that cue\n  at all. An omitted cue is correct; an ungrounded cue is a failure.\n- Spans may overlap between cues. A single sentence can ground two cues.\n";

const gateSchema = {
  type: "object",
  properties: {
    decision: { type: "string", enum: ["yes", "partial", "no"] },
    reason: { type: "string" }
  },
  required: ["decision", "reason"]
};

const cueItem = {
  type: "object",
  properties: { cue: { type: "string" }, span: { type: "string" } },
  required: ["cue", "span"]
};

const extractSchema = {
  type: "object",
  properties: {
    target: { type: "string" },
    evidence_quote: { type: "string" },
    remembered: { type: "array", items: cueItem },
    forgotten: { type: "array", items: cueItem },
    breakdown: { type: "string" }
  },
  required: ["target", "remembered", "forgotten"]
};

const MODELS = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"];
const delay = (ms) => new Promise((r) => setTimeout(r, ms));

async function call(ai, systemInstruction, text, responseSchema) {
  let lastError;
  for (const model of MODELS) {
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const r = await ai.models.generateContent({
          model,
          contents: [{ role: "user", parts: [{ text }] }],
          config: {
            systemInstruction,
            temperature: 0,
            responseMimeType: "application/json",
            responseSchema
          }
        });
        const raw = String(r.text).replace(/^```json\s*/, "").replace(/\s*```$/, "").trim();
        return JSON.parse(raw);
      } catch (e) {
        lastError = e;
        const code = e.status || e.code;
        if (!(code === 503 || code === 429 || code === 500)) throw e;
        if (attempt === 0) await delay(700);
      }
    }
  }
  throw lastError;
}

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "Method Not Allowed" });

  const key = process.env.GEMINI_API_KEY;
  if (!key) return res.status(500).json({ error: "GEMINI_API_KEY is not set on this deployment." });

  const body = req.body || {};
  const text = String(body.text || "").slice(0, 4000).trim();
  if (!text) return res.status(400).json({ error: "No text supplied." });

  try {
    const ai = new GoogleGenAI({ apiKey: key });

    const gate = await call(ai, GATE_PROMPT, text, gateSchema);
    if (gate.decision === "no") {
      return res.status(200).json({ gate_decision: "no", gate_reason: gate.reason });
    }

    const ex = await call(ai, EXTRACT_PROMPT, text, extractSchema);

    // The grounding rule is enforced here rather than trusted to the model:
    // a cue whose span is not a verbatim substring of the input is discarded.
    const grounded = (list) => (list || []).filter((c) => c && c.span && text.includes(c.span));
    const dropped = []
      .concat(ex.remembered || [], ex.forgotten || [])
      .filter((c) => !c || !c.span || !text.includes(c.span))
      .map((c) => (c && c.cue) || "");

    return res.status(200).json({
      gate_decision: gate.decision,
      gate_reason: gate.reason,
      target: ex.target,
      evidence_quote: ex.evidence_quote,
      remembered: grounded(ex.remembered),
      forgotten: grounded(ex.forgotten),
      breakdown: ex.breakdown || null,
      dropped
    });
  } catch (e) {
    const code = e.status || e.code;
    if (code === 503 || code === 429 || code === 500) {
      return res.status(503).json({ error: "The model is busy. Give it a few seconds and try again." });
    }
    return res.status(502).json({ error: e.message || "Unknown error" });
  }
}
