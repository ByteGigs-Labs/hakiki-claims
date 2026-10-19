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
      {!data.verified && (
        <p className="citation__note">
          Section reference pending verification against the original SHA text. Treat this rule as a demonstration.
        </p>
      )}
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
