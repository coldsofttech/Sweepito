export const RISK = { custom: -1, safe: 0, configurable: 1, "high-impact": 2 };

export function parseRisk(value) {
    const key = String(value).trim().toLowerCase().replace(/_/g, "-");
    if (!(key in RISK)) {
        throw new Error(`Invalid risk level '${value}'; expected safe, configurable or high-impact.`);
    }
    return key;
}

export function formatSize(size) {
    const units = ["B", "KB", "MB", "GB", "TB"];
    let value = size;
    for (let i = 0; i < units.length; i++) {
        if (value < 1024 || i === units.length - 1) {
            return i === 0 ? `${Math.trunc(value)} B` : `${value.toFixed(1)} ${units[i]}`;
        }
        value /= 1024;
    }
    return `${size} B`;
}
