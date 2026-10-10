import fs from "node:fs";

export function readFile(path) {
  try {
    return `The following is the content of file ${path}:\n\n${fs.readFileSync(path, "utf8")}`;
  } catch (e) {
    return `Error reading file ${path}: ${e.message}`;
  }
}

export function writeFile(path, content) {
  try {
    fs.writeFileSync(path, content);
    return `File ${path} written successfully.`;
  } catch (e) {
    return `Error writing to file ${path}: ${e.message}`;
  }
}

export function runTool(name, params) {
  if (name === "read_file") return readFile(params.path);
  if (name === "write_file") return writeFile(params.path, params.content);
  return `Error: Tool ${name} not found.`;
}
