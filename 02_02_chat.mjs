import { llmGenerate, printUser, printSystem, printError, printAssistant, input, isDebug } from "./utils.mjs";

// Llama 3.2 Chat tokens
const BEGIN = "<|begin_of_text|>";
const START_HEADER = "<|start_header_id|>";
const END_HEADER = "<|end_header_id|>\n\n";
const EOT = "<|eot_id|>";

const debug = isDebug();
let history = BEGIN;
// Optional: system message
// history += `${START_HEADER}system${END_HEADER}You are a helpful assistant.${EOT}`;
console.log("Chat with LLM (type 'exit' or 'quit' to stop)");

while (true) {
  printUser("You: ", "");
  const userInput = await input();
  if (userInput === null || ["exit", "quit"].includes(userInput.toLowerCase())) break;

  const userBlock = `${START_HEADER}user${END_HEADER}${userInput}${EOT}`;
  history += userBlock;
  try {
    const reply = await llmGenerate(history + `${START_HEADER}assistant${END_HEADER}`, debug);
    printSystem("Assistant: ", "");
    printAssistant(reply);
    history += `${reply}${EOT}`;
  } catch (e) {
    printError(`Error: ${e.message}`);
    history = history.slice(0, history.lastIndexOf(userBlock));
  }
}
process.exit(0);
