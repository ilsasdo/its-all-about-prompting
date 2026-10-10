import { llmGenerate, printUser, printSystem, printError, printAssistant, input, isDebug } from "./utils.mjs";

const debug = isDebug();
let history = "";
console.log("Chat with LLM (type 'exit' or 'quit' to stop)");

while (true) {
  printUser("You: ", "");
  const userInput = await input();
  if (userInput === null || ["exit", "quit"].includes(userInput.toLowerCase())) break;

  // Append user input to history with USER: prefix
  const userLine = `USER: ${userInput}\n`;
  history += userLine;
  try {
    const reply = await llmGenerate(history + "SYSTEM: ", debug);
    printSystem("Assistant: ", "");
    printAssistant(reply);
    history += `SYSTEM: ${reply}\n`;
  } catch (e) {
    printError(`Error: ${e.message}`);
    history = history.slice(0, history.lastIndexOf(userLine));
  }
}

// describe recursion with one sentence
// in italian
// in french
// with html formatting
process.exit(0);
