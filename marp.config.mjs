// Marp CLI config: render ```mermaid fences as <pre class="mermaid"> (drawn by the script in PRESENTATION.md)
export default {
  html: true,
  allowLocalFiles: true,
  engine: ({ marp }) =>
    marp.use((md) => {
      const fence = md.renderer.rules.fence;
      md.renderer.rules.fence = (tokens, idx, options, env, self) => {
        const token = tokens[idx];
        if (token.info.trim() === "mermaid") {
          return `<pre class="mermaid">${md.utils.escapeHtml(token.content)}</pre>`;
        }
        return fence(tokens, idx, options, env, self);
      };
    }),
};
