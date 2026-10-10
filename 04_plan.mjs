import { llmChat, loadRules, PLAN_PROMPT, printUser, printSystem, printError, printAssistant, input, isDebug } from "./utils.mjs";

const debug = isDebug();
const history = loadRules();
console.log("Chat with LLM (type 'exit' or 'quit' to stop, '/plan' to generate a plan)");

while (true) {
  printUser("You: ", "");
  const userInput = await input();
  if (userInput === null || ["exit", "quit"].includes(userInput.toLowerCase())) break;

  if (userInput.trim().toLowerCase() === "/plan") {
    history.push({ role: "user", content: PLAN_PROMPT });
  } else {
    history.push({ role: "user", content: userInput });
  }
  try {
    const data = await llmChat(history, null, debug);
    const reply = data.message.content;
    printSystem("Assistant: ", "");
    printAssistant(reply);
    history.push({ role: "assistant", content: reply });
  } catch (e) {
    printError(`Error: ${e.message}`);
    if (history.at(-1)?.role === "user") history.pop();
  }
}

// chats:
// I want to build a simple chess engine in python. what should I do?
process.exit(0);
