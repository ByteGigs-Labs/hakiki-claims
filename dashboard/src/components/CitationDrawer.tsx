import { fetchCitation } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { formatDate } from "../lib/format";
import { Drawer } from "./Drawer";
import { Icon } from "./Icon";

interface Props {
  rule: string | null;
  onClose: () => void;
}

function Body({ rule }: { rule: string }) {
  const { data, loading, error } = useAsync(() => fetchCitation(rule), [rule]);
  if (loading) return <div className="skeleton" style={{ height: 220 }} />;
  if (error || !data) return <p>This source could not be loaded.</p>;
  return (
    <article className="citation">
      <p className="eyebrow">Rule {data.rule} · source</p>
      <h3>{data.name}</h3>
      <p className="citation__condition">{data.condition}</p>
      <dl className="citation__facts">
        <div>
          <dt>Document</dt>
          <dd>{data.document}</dd>
        </div>
        <div>
          <dt>Section</dt>
          <dd>{data.section}</dd>
        </div>
        <div>
          <dt>Effective</dt>
          <dd>{formatDate(data.effective)}</dd>
        </div>
      </dl>
      <blockquote className="citation__quote">{data.quote}</blockquote>
      <p className={`citation__note${data.verified ? " citation__note--ok" : ""}`}>
        <b>{data.verified ? "Legal basis read in the source document." : "Legal basis not found in the source documents."}</b>{" "}
        {data.note}
      </p>
      <a className="btn btn--soft" href={data.url} target="_blank" rel="noopener noreferrer">
        <Icon name="link" size={18} /> Open the document
      </a>
    </article>
  );
}

export function CitationDrawer({ rule, onClose }: Props) {
  return (
    <Drawer open={rule !== null} onClose={onClose} label="Rule source">
      {rule && <Body rule={rule} />}
    </Drawer>
  );
}
