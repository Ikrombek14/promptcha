// SSE oʻquvchi va job API testi: node --test (Node 24 TypeScript'ni oʻzi oʻqiydi)
import { test } from "node:test";
import assert from "node:assert/strict";
import { jobEvents, startGenerate, cancelJob } from "../lib/api.ts";

function sseResponse(body, { status = 200, chunkSize = 7 } = {}) {
  const bytes = new TextEncoder().encode(body);
  const stream = new ReadableStream({
    start(controller) {
      for (let i = 0; i < bytes.length; i += chunkSize) controller.enqueue(bytes.slice(i, i + chunkSize));
      controller.close();
    },
  });
  return new Response(status === 200 ? stream : JSON.stringify({ detail: "yoʻq" }), {
    status,
    headers: { "content-type": status === 200 ? "text/event-stream" : "application/json" },
  });
}

test("startGenerate job id qaytaradi", async () => {
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    return new Response(JSON.stringify({ job_id: "abc" }), { status: 200 });
  };
  const id = await startGenerate({ text: "asal", ai: "midjourney", locale: "uz" });
  assert.equal(id, "abc");
  assert.equal(calls[0].url, "/api/prompts/generate");
  assert.equal(calls[0].init.method, "POST");
});

test("CRLF bilan kelgan SSE (sse-starlette) hodisalari oʻqiladi", async () => {
  const sse =
    ": ping\r\n\r\n" +
    'event: classify\r\ndata: {"kind": "image", "confidence": 0.9, "ask": false}\r\n\r\n' +
    'event: delta\r\ndata: {"text": "salom "}\r\n\r\n' +
    'event: delta\r\ndata: {"text": "dunyo"}\r\n\r\n' +
    'event: done\r\ndata: {"status": "ok", "kind": "image", "prompt": "salom dunyo"}\r\n\r\n';
  globalThis.fetch = async (url) => {
    assert.equal(url, "/api/prompts/jobs/abc");
    return sseResponse(sse);
  };
  const events = [];
  for await (const e of jobEvents("abc")) events.push(e);
  assert.deepEqual(
    events.map((e) => e.event),
    ["classify", "delta", "delta", "done"],
  );
  assert.equal(events.at(-1).data.prompt, "salom dunyo");
});

test("LF bilan kelgan SSE ham, oxirgi blok boʻsh qatorsiz boʻlsa ham oʻqiladi", async () => {
  const sse = 'event: clarify\ndata: {"questions": []}\n\nevent: done\ndata: {"status": "needs_clarification", "kind": "text", "prompt": ""}';
  globalThis.fetch = async () => sseResponse(sse, { chunkSize: 3 });
  const events = [];
  for await (const e of jobEvents("x")) events.push(e);
  assert.equal(events.length, 2);
  assert.equal(events[1].data.status, "needs_clarification");
});

test("job topilmasa (404) ApiError detail bilan chiqadi", async () => {
  globalThis.fetch = async () => sseResponse("", { status: 404 });
  await assert.rejects(
    async () => {
      for await (const _ of jobEvents("eski")) void _;
    },
    (e) => e.name === "ApiError" && e.message === "yoʻq" && e.status === 404,
  );
});

test("cancelJob tarmoq xatosini yutadi", async () => {
  globalThis.fetch = async () => {
    throw new Error("offline");
  };
  await cancelJob("abc");
});
