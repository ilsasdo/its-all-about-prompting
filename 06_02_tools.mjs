// Tool calling implemented purely via prompting (the model answers with JSON)
import { llmChat, loadRules, PLAN_PROMPT, SUMMARIZE_PROMPT, printUser, printSystem, printError, printAssistant, printDebug, input, isDebug } from "./utils.mjs";
import { runTool } from "./tools.mjs";

const TOOLS_PROMPT = `You have access to two tools: 'read_file' and 'write_file'.

1. 'read_file': Obtain the content of a file from disk.
   To use it, respond with a correct json: {"name": "read_file", "parameters": {"path": "FILE_PATH"}}

2. 'write_file': Write content to a file on disk.
   To use it, respond with a correct json: {"name": "write_file", "parameters": {"path": "FILE_PATH", "content": "FILE_CONTENT"}}

When you need to use a tool, provide the required parameters in the JSON object and ANSWER ONLY with a single valid JSON string.
If you are not calling a tool, do not use JSON format.`;

function extractJson(text) {
  let clean = text.trim();
  if (clean.includes("```json")) clean = clean.split("```json")[1].split("```")[0].trim();
  else if (clean.includes("```")) clean = clean.split("```")[1].split("```")[0].trim();
  return JSON.parse(clean);
}

const debug = isDebug();
let history = loadRules();
console.log("Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan, '/summarize' to summarize chat)");
history.push({ role: "system", content: TOOLS_PROMPT });

while (true) {
  printUser("You: ", "");
  const userInput = await input();
  if (userInput === null || ["exit", "quit"].includes(userInput.toLowerCase())) break;

  let isSummarize = false;
  const cmd = userInput.trim().toLowerCase();
  if (cmd === "/plan") history.push({ role: "user", content: PLAN_PROMPT });
  else if (cmd === "/summarize") {
    history.push({ role: "user", content: SUMMARIZE_PROMPT });
    isSummarize = true;
  } else history.push({ role: "user", content: userInput });

  try {
    let data = await llmChat(history, null, debug);
    let reply = data.message.content;
    printSystem("Assistant: ", "");
    printAssistant(reply);

    let call = null;
    try {
      const parsed = extractJson(reply);
      if (parsed && typeof parsed === "object" && ["read_file", "write_file"].includes(parsed.name)) call = parsed;
    } catch {
      // not a tool call
    }

    if (call) {
      const params = call.parameters || {};
      printDebug(`Tool call: ${call.name}(${JSON.stringify(params)})`);
      const result = runTool(call.name, params);
      printDebug(`Tool result: ${result}`);

      history.push({ role: "tool", tool_name: call.name, content: result });
      history.push({ role: "user", content: "Tell me what you just did." });

      data = await llmChat(history, null, debug);
      reply = data.message.content;
      printSystem("Assistant: ", "");
      printAssistant(reply);
    }

    if (isSummarize) {
      history = loadRules();
      history.push({ role: "assistant", content: `Summary of previous chat history:\n${reply}` });
    } else {
      history.push({ role: "assistant", content: reply });
    }
  } catch (e) {
    printError(`Error: ${e.message}`);
    if (history.at(-1)?.role === "user") history.pop();
  }
}

// chats:
// I want to build a simple chess engine in python. what should I do?
process.exit(0);
