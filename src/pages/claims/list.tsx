import { List, useTable } from "@refinedev/antd";
import { Table } from "antd";
import dayjs from "dayjs";
import type { ClaimRow } from "../../types";
import { VerdictTag } from "../../components/TraceTree";

export const ClaimList = () => {
  const { tableProps } = useTable<ClaimRow>({
    sorters: { initial: [{ field: "checked_at", order: "desc" }] },
  });

  return (
    <List title="Checked claims">
      <Table {...tableProps} rowKey="id">
        <Table.Column dataIndex="id" title="Claim" />
        <Table.Column dataIndex="service_code" title="Service" />
        <Table.Column dataIndex="fund" title="Fund" />
        <Table.Column
          dataIndex="amount_kes"
          title="Amount (KES)"
          render={(v: number) => v.toLocaleString("en-KE")}
        />
        <Table.Column
          dataIndex="verdict"
          title="Verdict"
          render={(v: ClaimRow["verdict"]) => <VerdictTag verdict={v} />}
        />
        <Table.Column
          dataIndex="checked_at"
          title="Checked"
          sorter
          render={(v: string) => dayjs(v).format("DD MMM YYYY, HH:mm")}
        />
      </Table>
    </List>
  );
};
