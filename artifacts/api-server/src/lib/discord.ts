const BASE = "https://discord.com/api/v10";
const TOKEN = process.env.DISCORD_BOT_TOKEN;
export const GUILD_ID = "1485175801887326339";

function headers(): Record<string, string> {
  return {
    Authorization: `Bot ${TOKEN}`,
    "Content-Type": "application/json",
  };
}

export async function discordGet(path: string) {
  const res = await fetch(`${BASE}${path}`, { headers: headers() });
  if (!res.ok) throw new Error(`Discord API error ${res.status}: ${path}`);
  return res.json();
}

export async function discordPost(path: string, body: object) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Discord POST error ${res.status}: ${err}`);
  }
  if (res.status === 204) return {};
  return res.json();
}

export async function discordPut(path: string, body?: object) {
  const res = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Discord PUT error ${res.status}: ${err}`);
  }
  if (res.status === 204) return {};
  return res.json();
}

export async function discordDelete(path: string, body?: object) {
  const res = await fetch(`${BASE}${path}`, {
    method: "DELETE",
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Discord DELETE error ${res.status}: ${err}`);
  }
  if (res.status === 204) return {};
  return res.json();
}

export async function discordPatch(path: string, body: object) {
  const res = await fetch(`${BASE}${path}`, {
    method: "PATCH",
    headers: headers(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Discord PATCH error ${res.status}: ${err}`);
  }
  if (res.status === 204) return {};
  return res.json();
}
