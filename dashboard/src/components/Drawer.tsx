import { useEffect, useRef, type ReactNode } from "react";
import { Icon } from "./Icon";

interface Props {
  open: boolean;
  onClose: () => void;
  label: string;
  children: ReactNode;
}

export function Drawer({ open, onClose, label, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      className="dialog"
      aria-label={label}
      onClose={onClose}
      onClick={(event) => event.target === ref.current && onClose()}
    >
      {open && (
        <div className="dialog__body">
          <button type="button" className="btn btn--ghost dialog__close" onClick={onClose}>
            <Icon name="cross" size={18} /> Close
          </button>
          {children}
        </div>
      )}
    </dialog>
  );
}
