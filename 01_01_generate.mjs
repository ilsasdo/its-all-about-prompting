import { llmGenerate, printAssistant, input, isDebug } from "./utils.mjs";

const debug = isDebug();
console.log("Welcome to 01_01_generate.mjs (type 'exit' or 'quit' to stop)");
while (true) {
  const userInput = await input("Prompt: ");
  if (userInput === null || ["exit", "quit"].includes(userInput.toLowerCase())) break;
  if (!userInput.trim()) continue;
  try {
    printAssistant(await llmGenerate(userInput, debug));
  } catch (e) {
    console.error(`Error: ${e.message}`);
  }
}
process.exit(0);
