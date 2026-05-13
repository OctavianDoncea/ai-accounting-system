const API_BASE = "http://localhost:8000/api"

export async function createSession(name: string) {
    const res = await fetch(`${API_BASE}/sessions/?name=${encodeURIComponent(name)}`, {
        method: "POST"
    });
    if (!res.ok) throw new Error("Failed to create session");

    return res.json();
}

export async function listSessions() {
    const res = await fetch(`${API_BASE}/sessions/`);
    if (!res.ok) throw new Error("Failed to fetch sessions");
    return res.json();
}