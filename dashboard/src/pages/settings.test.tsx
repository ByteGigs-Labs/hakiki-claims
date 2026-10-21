import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { AccountPage } from "./account";
import { KeysPage } from "./keys";
import { TeamPage } from "./team";

const api = vi.hoisted(() => ({
  fetchUsers: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  fetchApiKeys: vi.fn(),
  createApiKey: vi.fn(),
  revokeApiKey: vi.fn(),
  changePassword: vi.fn(),
}));

vi.mock("@refinedev/core", () => ({ useGetIdentity: () => ({ data: { id: "u1", role: "admin" } }) }));
vi.mock("../lib/api", () => ({
  ...api,
  errorMessage: (error: { message?: string }, fallback: string) => error.message ?? fallback,
}));

const person = (over = {}) => ({
  id: "u2",
  name: "Wanjiru Kamau",
  email: "wanjiru@mercy.test",
  role: "clerk",
  is_active: true,
  created_at: "2026-10-01T08:00:00Z",
  ...over,
});

beforeEach(() => vi.resetAllMocks());

describe("TeamPage", () => {
  it("lists people and stops admins switching themselves off", async () => {
    api.fetchUsers.mockResolvedValue([person({ id: "u1", name: "Me Admin", role: "admin" }), person()]);
    render(<TeamPage />);
    const mine = (await screen.findByText("Me Admin")).closest("li")!;
    expect(within(mine).getByRole("button", { name: /switch off/i })).toBeDisabled();
    expect(within(mine).getByRole("combobox")).toBeDisabled();
    const theirs = screen.getByText("Wanjiru Kamau").closest("li")!;
    expect(within(theirs).getByRole("button", { name: /switch off/i })).toBeEnabled();
  });

  it("adds a person and reloads the list", async () => {
    api.fetchUsers.mockResolvedValue([]);
    api.createUser.mockResolvedValue(person());
    render(<TeamPage />);
    await userEvent.type(await screen.findByLabelText("Full name"), "Wanjiru Kamau");
    await userEvent.type(screen.getByLabelText("Email"), "wanjiru@mercy.test");
    await userEvent.type(screen.getByLabelText(/first password/i), "a-long-passphrase");
    await userEvent.click(screen.getByRole("button", { name: /add person/i }));
    await waitFor(() =>
      expect(api.createUser).toHaveBeenCalledWith({
        name: "Wanjiru Kamau",
        email: "wanjiru@mercy.test",
        role: "clerk",
        password: "a-long-passphrase",
      }),
    );
    await waitFor(() => expect(api.fetchUsers).toHaveBeenCalledTimes(2));
  });

  it("shows the server's reason when the change is refused", async () => {
    api.fetchUsers.mockResolvedValue([person()]);
    api.updateUser.mockRejectedValue({ message: "A facility needs at least one active admin" });
    render(<TeamPage />);
    await userEvent.click(await screen.findByRole("button", { name: /switch off/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("at least one active admin");
  });
});

describe("KeysPage", () => {
  const summary = { id: "k1", name: "Billing", prefix: "ab12cd34", created_at: "2026-10-01T08:00:00Z", last_used_at: null, revoked_at: null };

  it("shows the full key once, right after creation", async () => {
    api.fetchApiKeys.mockResolvedValue([]);
    api.createApiKey.mockResolvedValue({ ...summary, key: "hk_ab12cd34_secretsecret" });
    render(<KeysPage />);
    await userEvent.type(await screen.findByLabelText(/what will use it/i), "Billing");
    await userEvent.click(screen.getByRole("button", { name: /create key/i }));
    expect(await screen.findByText("hk_ab12cd34_secretsecret")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /i have saved it/i }));
    expect(screen.queryByText("hk_ab12cd34_secretsecret")).toBeNull();
  });

  it("lists keys by prefix only and revokes on request", async () => {
    api.fetchApiKeys.mockResolvedValue([summary]);
    api.revokeApiKey.mockResolvedValue(undefined);
    render(<KeysPage />);
    expect(await screen.findByText("hk_ab12cd34…")).toBeInTheDocument();
    expect(screen.getByText("Never used")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /revoke/i }));
    expect(api.revokeApiKey).toHaveBeenCalledWith("k1");
  });
});

describe("AccountPage", () => {
  it("changes the password and confirms it", async () => {
    api.changePassword.mockResolvedValue(undefined);
    render(<AccountPage />);
    await userEvent.type(screen.getByLabelText("Current password"), "old-passphrase");
    await userEvent.type(screen.getByLabelText(/new password/i), "new-passphrase-1");
    await userEvent.click(screen.getByRole("button", { name: /change password/i }));
    expect(api.changePassword).toHaveBeenCalledWith("old-passphrase", "new-passphrase-1");
    expect(await screen.findByRole("status")).toHaveTextContent("has been changed");
  });

  it("shows why it failed", async () => {
    api.changePassword.mockRejectedValue({ message: "Current password is incorrect" });
    render(<AccountPage />);
    await userEvent.type(screen.getByLabelText("Current password"), "wrong");
    await userEvent.type(screen.getByLabelText(/new password/i), "new-passphrase-1");
    await userEvent.click(screen.getByRole("button", { name: /change password/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Current password is incorrect");
  });
});
