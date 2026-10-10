import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";

const GRAY = "\x1b[90m";
const RESET = "\x1b[0m";
const BLACK = "\x1b[30m";
const GREEN = "\x1b[32m";
const YELLOW = "\x1b[33m";
const RED = "\x1b[31m";

const color = (c) => (text, end = "\n") => process.stdout.write(`${c}${text}${RESET}${end}`);

export const printYellow = color(YELLOW);
export const printGreen = color(GREEN);
export const printBlack = color(BLACK);
export const printGray = color(GRAY);
export const printRed = color(RED);
export const printSystem = printGreen;
export const printError = printRed;
export const printUser = printBlack;
export const printDebug = printGray;
export const printAssistant = printYellow;

const OLLAMA_URL = process.env.OLLAMA_URL || "http://localhost:11434";
const MODEL = process.env.OLLAMA_MODEL || "llama3.2";

export async function llmPostRequest(url, payload, debug = false) {
  if (debug) printDebug(`Request: ${JSON.stringify(payload, null, 2)}`);

  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status} ${r.statusText}`);
  const responseData = await r.json();

  if (debug) printDebug(`Response: ${JSON.stringify(responseData, null, 2)}`);

  printTokenUsage(responseData);
  return responseData;
}

export async function llmGenerate(prompt, debug = false) {
  const data = await llmPostRequest(`${OLLAMA_URL}/api/generate`, {
    model: MODEL,
    prompt,
    stream: false,
  }, debug);
  return data.response;
}

export async function llmChat(messages, tools = null, debug = false) {
  const payload = { model: MODEL, messages, stream: false };
  if (tools) payload.tools = tools;
  return llmPostRequest(`${OLLAMA_URL}/api/chat`, payload, debug);
}

function printTokenUsage(data) {
  const p = data.prompt_eval_count || 0;
  const e = data.eval_count || 0;
  printDebug(`[Prompt: ${p}, Response: ${e}, Total: ${p + e}]`);
}

// Line reader that resolves to null on EOF (like Python's EOFError)
const rl = readline.createInterface({ input: process.stdin, terminal: false });
const queue = [];
const waiters = [];
let closed = false;
rl.on("line", (line) => {
  if (waiters.length) waiters.shift()(line);
  else queue.push(line);
});
rl.on("close", () => {
  closed = true;
  while (waiters.length) waiters.shift()(null);
});

export function input(prompt = "") {
  process.stdout.write(prompt);
  if (queue.length) return Promise.resolve(queue.shift());
  if (closed) return Promise.resolve(null);
  return new Promise((resolve) => waiters.push(resolve));
}

export function loadRules(rulesDir = "./rules") {
  const parts = ["Follow these rules:"];
  if (fs.existsSync(rulesDir)) {
    for (const f of fs.readdirSync(rulesDir).filter((f) => f.endsWith(".txt")).sort()) {
      const content = fs.readFileSync(path.join(rulesDir, f), "utf8").trim();
      if (content) parts.push(content);
    }
  }
  return parts.length > 1 ? [{ role: "system", content: parts.join("\n") }] : [];
}

export const PLAN_PROMPT = `Analyze the task and provide a detailed step-by-step plan for its execution.
Identify potential risks, dependencies, and key milestones.
Format the output as a numbered list with clear explanations for each step.`;

export const SUMMARIZE_PROMPT = `Summarize the current chat history into a concise yet detailed summary.
Retain the most relevant information and current task context.
The summary will be used to reduce the context size, so it must capture the essence of the entire conversation.`;

export const isDebug = () => process.argv.includes("--debug");
