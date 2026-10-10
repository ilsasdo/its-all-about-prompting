import { llmChat, loadRules, printUser, printSystem, printError, printAssistant, input, isDebug } from "./utils.mjs";

const debug = isDebug();
const history = loadRules();
console.log("Chat with LLM (type 'exit' or 'quit' to stop)");

while (true) {
  printUser("You: ", "");
  const userInput = await input();
  if (userInput === null || ["exit", "quit"].includes(userInput.toLowerCase())) break;

  history.push({ role: "user", content: userInput });
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
process.exit(0);
