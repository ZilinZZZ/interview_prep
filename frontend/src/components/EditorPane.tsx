import Editor, { type OnMount } from "@monaco-editor/react";
import { useRef } from "react";

interface Props {
  code: string;
  language: string;
  onChange: (v: string) => void;
  onRun: () => void;
  onSubmit: () => void;
  onReset: () => void;
  running: boolean;
}

export function EditorPane({ code, language, onChange, onRun, onSubmit, onReset, running }: Props) {
  // keep latest handlers so Monaco commands (bound once) never go stale
  const handlers = useRef({ onRun, onSubmit });
  handlers.current = { onRun, onSubmit };

  const onMount: OnMount = (editor, monaco) => {
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () =>
      handlers.current.onRun(),
    );
    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter,
      () => handlers.current.onSubmit(),
    );
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-gray-700 px-2 py-1">
        <button
          onClick={onRun}
          disabled={running}
          className="rounded bg-blue-600 px-3 py-1 text-sm font-semibold hover:bg-blue-500 disabled:opacity-50"
        >
          {running ? "Running…" : "Run"}
        </button>
        <button
          onClick={onSubmit}
          disabled={running}
          className="rounded bg-green-600 px-3 py-1 text-sm font-semibold hover:bg-green-500 disabled:opacity-50"
        >
          Submit
        </button>
        <span className="text-xs text-gray-500">Ctrl+Enter · Ctrl+Shift+Enter</span>
        <button
          onClick={onReset}
          className="ml-auto rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-800"
        >
          Reset to starter
        </button>
      </div>
      <div className="flex-1">
        <Editor
          language={language}
          theme="vs-dark"
          value={code}
          onChange={(v) => onChange(v ?? "")}
          onMount={onMount}
          options={{
            tabSize: 4,
            insertSpaces: true,
            minimap: { enabled: false },
            fontSize: 14,
            scrollBeyondLastLine: false,
            matchBrackets: "always",
          }}
        />
      </div>
    </div>
  );
}
