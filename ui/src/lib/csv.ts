type CsvRow = Record<string, string>;

function splitLine(line: string, delimiter: string): string[] {
  const fields: string[] = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"') {
      if (quoted && line[index + 1] === '"') {
        value += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (char === delimiter && !quoted) {
      fields.push(value.trim());
      value = "";
    } else {
      value += char;
    }
  }
  fields.push(value.trim());
  return fields;
}

export function parseOhlcvCsv(text: string): CsvRow[] {
  const lines = text
    .replace(/^\uFEFF/, "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length < 2) throw new Error("CSV 至少需要表头和一行数据");
  const delimiter = lines[0].includes("\t") ? "\t" : ",";
  const headers = splitLine(lines[0], delimiter).map((item) => item.toLowerCase());
  const aliases: Record<string, string> = {
    datetime: "date",
    time: "date",
    timestamp: "date",
    o: "open",
    h: "high",
    l: "low",
    c: "close",
    v: "volume",
    vol: "volume",
  };
  const normalized = headers.map((item) => aliases[item] ?? item);
  for (const required of ["date", "open", "high", "low", "close"]) {
    if (!normalized.includes(required)) throw new Error(`CSV 缺少必填列 ${required}`);
  }
  return lines.slice(1).map((line) => {
    const values = splitLine(line, delimiter);
    const row: CsvRow = {};
    normalized.forEach((key, index) => {
      row[key] = values[index] ?? "";
    });
    return row;
  });
}
