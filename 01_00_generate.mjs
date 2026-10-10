import { llmGenerate, printAssistant, isDebug } from "./utils.mjs";

printAssistant(await llmGenerate("Explain recursion in one sentence.", isDebug()));
process.exit(0);
