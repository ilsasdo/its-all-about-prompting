// Native tool calling via the Ollama "tools" API parameter
import { llmChat, loadRules, PLAN_PROMPT, SUMMARIZE_PROMPT, printUser, printSystem, printError, printAssistant, printDebug, input, isDebug } from "./utils.mjs";
import { runTool } from "./tools.mjs";

const TOOLS = [
  {
    type: "function",
    function: {
      name: "read_file",
      description: "Read the content of a file from disk.",
      parameters: {
        type: "object",
        properties: { path: { type: "string", description: "The path to the file to read." } },
        required: ["path"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "write_file",
      description: "Write content to a file on disk.",
      parameters: {
        type: "object",
        properties: {
          path: { type: "string", description: "The path to the file to write to." },
          content: { type: "string", description: "The content to write to the file." },
        },
        required: ["path", "content"],
      },
    },
  },
];

const debug = isDebug();
let history = loadRules();
console.log("Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan, '/summarize' to summarize chat)");

while (true) {
  try {
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

    let data = await llmChat(history, TOOLS, debug);
    const message = data.message;
    let reply = message.content || "";

    if (reply) {
      printSystem("Assistant: ", "");
      printAssistant(reply);
    }

    if (message.tool_calls?.length) {
      history.push(message);
      for (const call of message.tool_calls) {
        const name = call.function.name;
        const params = call.function.arguments;
        printDebug(`Tool call: ${name}(${JSON.stringify(params)})`);
        const result = runTool(name, params);
        printDebug(`Tool result: ${result}`);
        history.push({ role: "tool", tool_name: name, content: result });
      }
      history.push({ role: "user", content: "Tell me what you just did." });
      data = await llmChat(history, TOOLS, debug);
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
process.exit(0);
