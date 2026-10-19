import { Icon } from "./Icon";

interface Props {
  page: number;
  pageSize: number;
  total: number;
  onPage: (page: number) => void;
}

export function Pagination({ page, pageSize, total, onPage }: Props) {
  const pages = Math.max(Math.ceil(total / pageSize), 1);
  const first = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, total);
  return (
    <nav className="pagination" aria-label="Pages">
      <span className="pagination__range tabular">
        {first}–{last} of {total}
      </span>
      <div className="pagination__buttons">
        <button type="button" className="btn btn--soft btn--small" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          <span className="flip-x">
            <Icon name="arrow" size={16} />
          </span>
          Previous
        </button>
        <button type="button" className="btn btn--soft btn--small" disabled={page >= pages} onClick={() => onPage(page + 1)}>
          Next <Icon name="arrow" size={16} />
        </button>
      </div>
    </nav>
  );
}
