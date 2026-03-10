# Coding Agent - JSON Tool Call Improvements

## Summary of Changes

The coding agent has been upgraded from string-based function call parsing to structured JSON-based tool calling for more reliable and maintainable code.

## Before (String-based parsing)

### Format
```
tool_name("arg1", "arg2", "arg3")
```

### Problems
- Difficult to parse reliably with regex
- Hard to handle complex strings with quotes
- No clear argument naming
- Parsing errors with nested quotes or special characters
- Ambiguous argument order

### Example
```python
write_file("test.py", """def hello():
    print("Hello, World!")""")
```

**Parsing issues:**
- Nested quotes break the regex
- Triple quotes cause problems
- Multi-line content is hard to extract

## After (JSON-based parsing)

### Format
```json
{
  "tool": "tool_name",
  "args": {
    "arg1": "value1",
    "arg2": "value2"
  }
}
```

### Benefits
✓ Uses standard `json.loads()` - battle-tested parsing
✓ Clear argument naming (no positional confusion)
✓ Handles complex strings, newlines, quotes automatically
✓ Easy to extend with new arguments
✓ Better error messages
✓ More maintainable code

### Example
```json
{
  "tool": "write_file",
  "args": {
    "path": "test.py",
    "content": "def hello():\n    print(\"Hello, World!\")"
  }
}
```

**Parsing advantages:**
- JSON escaping handled automatically
- Clear argument names
- No ambiguity
- Standard format LLMs understand well

## Implementation Details

### Parsing Function
The new parser handles:
1. JSON in markdown code blocks: ` ```json {...} ``` `
2. Raw JSON objects in response
3. Nested braces (properly balanced)
4. Validates tool name against declared tools
5. Returns structured `(tool_name, args_dict)` tuple

### Tool Execution
All tools now use named arguments:

```python
# OLD
def execute_tool(tool_name: str, args: list[str]) -> str:
    path = args[0]  # Which arg is this?
    
# NEW  
def execute_tool(tool_name: str, args: dict) -> str:
    path = args.get("path")  # Clear and explicit
```

## System Prompt Update

The new system prompt:
- Clearly defines JSON format
- Provides examples for each tool
- Specifies argument names and types
- Shows proper JSON structure
- More guidance for the LLM

## Testing Results

All parsing scenarios tested and working:
✓ JSON in markdown code blocks
✓ Raw JSON responses
✓ Write file with complex content
✓ Non-tool responses (returns None correctly)
✓ All 6 tools work with new format
✓ No linter errors

## Migration Notes

No breaking changes for users:
- Interactive interface unchanged
- Still requires confirmation for tool execution
- Same command-line usage
- Backward compatible (old agent007.py still works)

## Future Improvements

Possible enhancements:
- Add JSON schema validation
- Support for optional arguments
- Tool result structured responses
- Multiple tool calls in one response
- Streaming support for long outputs
