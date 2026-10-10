import { llmChat, loadRules, PLAN_PROMPT, SUMMARIZE_PROMPT, printUser, printSystem, printError, printAssistant, input, isDebug } from "./utils.mjs";

const debug = isDebug();
let history = loadRules();
console.log("Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan, '/summarize' to summarize chat)");

while (true) {
  printUser("You: ", "");
  const userInput = await input();
  if (userInput === null || ["exit", "quit"].includes(userInput.toLowerCase())) break;

  let isSummarize = false;
  const cmd = userInput.trim().toLowerCase();
  if (cmd === "/plan") {
    history.push({ role: "user", content: PLAN_PROMPT });
  } else if (cmd === "/summarize") {
    history.push({ role: "user", content: SUMMARIZE_PROMPT });
    isSummarize = true;
  } else {
    history.push({ role: "user", content: userInput });
  }
  try {
    const data = await llmChat(history, null, debug);
    const reply = data.message.content;
    printSystem("Assistant: ", "");
    printAssistant(reply);
    if (isSummarize) {
      // Replace history with the summary while keeping rules
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
