# 🔴 ROOT CAUSE ANALYSIS - Jobs Not Triggering

## Issues Identified

### 1. **LLM Hallucination - Returning JSON Examples Instead of Tool Calls** ⚠️
**Problem**: When user asks "Could you trigger all the jobs?", the LLM returns:
```json
{ "tool": "trigger_build", "arguments": { "job_names": ["Job1", "Job2", ...] } }
```

This is a JSON EXAMPLE from the system prompt, not an actual tool call!

**Root Cause**: 
- System prompt shows examples like this
- LLM learns the pattern and copies it
- The agent code only handles single `job_name`, not `job_names`
- `safe_parse_json()` successfully parses it, but then agent can't find `job_name` key

**Evidence**:
- "Could you trigger all the jobs?" → Returns the JSON template as-is
- `args.get("job_name", "")` returns empty string → no match found

---

### 2. **No Support for Multiple Job Triggering** ❌
**Problem**: User asks "Run all the jobs" but the agent can't handle it
- Code only looks for `args.get("job_name", "")` (singular)
- No logic for `job_names` (plural) array
- No batch job trigger support

---

### 3. **System Prompt Too Generic** ❌
**Problems**:
- Doesn't have guardrails against hallucination
- Doesn't explicitly forbid returning examples
- No instructions on edge cases
- No instructions for handling user requests that don't match expected patterns
- Examples are TOO similar to what LLM might output

**Current Prompt Says**:
```
Respond **only** with valid JSON using the following format:
{
  "tool": "<tool_name>",
  "arguments": {"key": "value"}
}
```

But doesn't explain what happens when:
- User asks for multiple jobs
- User makes unclear requests
- LLM doesn't understand

---

### 4. **JSON Parsing Accepts Invalid Arguments** ⚠️
**Problem**: `safe_parse_json()` successfully parses the JSON, but structure is wrong
```python
parsed = safe_parse_json(llm_response)
tool_name = parsed.get("tool", "chat")       # Gets "trigger_build" ✓
args = parsed.get("arguments", {})
requested_job = args.get("job_name", "")     # Gets "" (empty!) ✗
```

When LLM returns `{"job_names": [...]}` instead of `{"job_name": "..."}`, the key lookup fails silently.

---

### 5. **Streamlit Doesn't Handle Batch Responses** ❌
**Problem**: No UI handler for batch job triggers
- Only handles single-job trigger with `status: "QUEUED"`
- No logic for `batch_jobs` or multiple results
- Falls back to "Unexpected response format"

---

## Examples of Failures

### Failure #1: "Run all the jobs"
```
User Input: "Run all the jobs"
↓
LLM Call: Calls system prompt
↓
LLM Response: { "tool": "trigger_build", "arguments": { "job_names": [...] } }
(This is from the system prompt example!)
↓
Agent Code:
  tool_name = "trigger_build" ✓
  args = { "job_names": [...] }
  requested_job = args.get("job_name", "") → "" (EMPTY!)
↓
find_best_job_match("", available_jobs) → None
↓
Response: "Could not find a matching Jenkins job for ''."
```

### Failure #2: "Lamma could you run few jobs for me?"
```
User Input: "Lamma could you run few jobs for me?"
↓
LLM Call: Vague request, LLM might return:
  { "tool": "chat", "arguments": {"message": "Sure, which jobs?"} }
  OR
  Malformed JSON
↓
If malformed, safe_parse_json catches it and returns chat tool
↓
Response: "None" (because message is empty/malformed)
```

---

## Solution Required

1. **Rewrite System Prompt** with:
   - Strict guardrails against hallucination
   - Explicit "DO NOT" statements
   - Support for single AND multiple job triggers
   - Clear edge case handling
   - NO examples that show array syntax (use single job examples only)
   - Emphasis on ONLY returning tool calls, never examples

2. **Add Batch Job Support**:
   - New tool: `trigger_builds` (plural) for multiple jobs
   - OR enhanced `trigger_build` that accepts both single and array
   - Code to handle `job_names` array

3. **Improve Input Validation**:
   - Validate that required keys exist
   - Log errors when structure is wrong
   - Provide fallback suggestions

4. **Update Streamlit UI**:
   - Handler for batch job responses
   - Better error messaging

5. **Add Better Logging**:
   - Log what the LLM returned
   - Log why parsing failed
   - Help debug issues

