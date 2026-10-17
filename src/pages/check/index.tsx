import { useState } from "react";
import {
  Alert, Button, Card, Col, DatePicker, Descriptions, Form, Input,
  InputNumber, List, Row, Select, Statistic, Typography,
} from "antd";
import type { Dayjs } from "dayjs";
import { http } from "../../lib/http";
import type { CheckResult, ClaimInput, Fund } from "../../types";
import { TraceTree, VerdictTag } from "../../components/TraceTree";

const { Text } = Typography;

type FormValues = Omit<ClaimInput, "date_of_service"> & { date_of_service: Dayjs };

export const CheckClaimPage = () => {
  const [result, setResult] = useState<CheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onFinish = async (v: FormValues) => {
    setLoading(true);
    setError(null);
    try {
      const payload: ClaimInput = {
        ...v,
        date_of_service: v.date_of_service.format("YYYY-MM-DD"),
      };
      const { data } = await http.post<CheckResult>("/v1/claims/check", payload);
      setResult(data);
    } catch {
      setError("Could not check this claim. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={10}>
        <Card title="Check a claim before submission">
          <Form layout="vertical" onFinish={onFinish} initialValues={{ fund: "SHIF" as Fund }}>
            <Form.Item name="patient_token" label="Patient token" rules={[{ required: true, max: 64 }]}>
              <Input placeholder="pat-77 (pseudonymised, no names)" />
            </Form.Item>
            <Form.Item name="facility_id" label="Facility ID" rules={[{ required: true, max: 32 }]}>
              <Input placeholder="fac-12" />
            </Form.Item>
            <Form.Item name="service_code" label="Service code" rules={[{ required: true, max: 32 }]}>
              <Input placeholder="svc-CS-01" />
            </Form.Item>
            <Form.Item name="fund" label="Fund" rules={[{ required: true }]}>
              <Select options={["PHC", "SHIF", "ECCIF"].map((f) => ({ value: f, label: f }))} />
            </Form.Item>
            <Form.Item name="date_of_service" label="Date of service" rules={[{ required: true }]}>
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="amount_kes" label="Amount (KES)" rules={[{ required: true }]}>
              <InputNumber min={0} max={100_000_000} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="preauth_ref" label="Pre-auth reference" rules={[{ max: 64 }]}>
              <Input placeholder="Optional" />
            </Form.Item>
            <Form.Item name="icd_code" label="ICD code" rules={[{ max: 16 }]}>
              <Input placeholder="Optional" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              Check claim
            </Button>
          </Form>
        </Card>
      </Col>

      <Col xs={24} lg={14}>
        {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}
        {!result && !error && (
          <Card>
            <Text type="secondary">
              The verdict, the fixes and the step-by-step reasoning appear here.
            </Text>
          </Card>
        )}
        {result && (
          <>
            <Card style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Text type="secondary">Verdict</Text>
                  <div style={{ marginTop: 8 }}>
                    <VerdictTag verdict={result.verdict} />
                  </div>
                </Col>
                <Col span={8}>
                  <Statistic title="Revenue at risk" value={result.revenue_at_risk_kes} prefix="KES" />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Strength / confidence"
                    value={`${result.truth_value.strength.toFixed(2)} / ${result.truth_value.confidence.toFixed(2)}`}
                  />
                </Col>
              </Row>
            </Card>

            {result.fixes.length > 0 && (
              <Card title="How to fix it" style={{ marginBottom: 16 }}>
                <List
                  dataSource={result.fixes}
                  renderItem={(f) => (
                    <List.Item>
                      {f.action} → <VerdictTag verdict={f.flips_to} />
                    </List.Item>
                  )}
                />
              </Card>
            )}

            <Card title="Glass Box trace" style={{ marginBottom: 16 }}>
              <TraceTree steps={result.trace} />
            </Card>

            <Card title="Audit">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Rulebook">{result.rulebook_version}</Descriptions.Item>
                <Descriptions.Item label="Trace hash">
                  <Text code copyable>{result.trace_hash}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Previous hash">
                  <Text code>{result.prev_hash}</Text>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </>
        )}
      </Col>
    </Row>
  );
};
