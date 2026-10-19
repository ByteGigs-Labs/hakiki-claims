import { useState, type DragEvent } from "react";
import { validateUpload } from "../lib/upload";
import { Icon } from "./Icon";

interface Props {
  disabled: boolean;
  onFile: (file: File) => void;
}

export function Dropzone({ disabled, onFile }: Props) {
  const [over, setOver] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const accept = (file: File | undefined) => {
    if (!file) return;
    const issue = validateUpload(file);
    setProblem(issue);
    if (!issue) onFile(file);
  };

  const drop = (event: DragEvent) => {
    event.preventDefault();
    setOver(false);
    if (!disabled) accept(event.dataTransfer.files[0]);
  };

  return (
    <label
      className={`dropzone${over ? " is-over" : ""}${disabled ? " is-disabled" : ""}`}
      onDragOver={(event) => {
        event.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={drop}
    >
      <input
        className="sr-only"
        type="file"
        accept=".csv,text/csv"
        disabled={disabled}
        onChange={(event) => {
          accept(event.target.files?.[0]);
          event.target.value = "";
        }}
      />
      <span className="dropzone__icon">
        <Icon name="upload" size={30} />
      </span>
      <strong>Drop your claims file here</strong>
      <span className="dropzone__sub">or click to browse · CSV up to 2 MB · 500 rows</span>
      {problem && (
        <span className="dropzone__problem" role="alert">
          {problem}
        </span>
      )}
    </label>
  );
}
