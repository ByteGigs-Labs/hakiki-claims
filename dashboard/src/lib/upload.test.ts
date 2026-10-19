import { MAX_UPLOAD_BYTES, validateUpload } from "./upload";

describe("validateUpload", () => {
  it("accepts a normal csv", () => {
    expect(validateUpload({ name: "Claims.CSV", size: 1200 })).toBeNull();
  });

  it.each([
    [{ name: "claims.xlsx", size: 100 }, "Choose a .csv file"],
    [{ name: "claims.csv", size: 0 }, "This file is empty"],
    [{ name: "claims.csv", size: MAX_UPLOAD_BYTES + 1 }, "The file is larger than 2 MB"],
  ])("rejects %j", (file, message) => {
    expect(validateUpload(file)).toBe(message);
  });
});
