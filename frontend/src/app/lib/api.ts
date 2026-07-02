export type GraphNode = {
  id: string;
  label: string;
  type: string;
};

export type GraphEdge = {
  from: string;
  to: string;
  label: string;
};

export type QuizQuestion = {
  q: string;
  options: string[];
  answer: number;
};

export type GraphContract = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  explanation?: string;
  quiz?: QuizQuestion[];
};

const API_BASE = import.meta.env.VITE_ARCHVIZ_API_URL || "http://localhost:8000";
const CONTRACT_STORAGE_KEY = "archviz-xr-latest-contract";

type WrappedContract = GraphContract | { contract: GraphContract };

function unwrapContract(data: WrappedContract): GraphContract {
  return "contract" in data ? data.contract : data;
}

export function saveContract(contract: GraphContract) {
  localStorage.setItem(CONTRACT_STORAGE_KEY, JSON.stringify(contract));
}

export function loadStoredContract(): GraphContract | null {
  const raw = localStorage.getItem(CONTRACT_STORAGE_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as GraphContract;
  } catch {
    localStorage.removeItem(CONTRACT_STORAGE_KEY);
    return null;
  }
}

export async function analyzeDiagram(file: File): Promise<GraphContract> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || `Analyze failed with HTTP ${response.status}`);
  }

  const contract = unwrapContract(await response.json());
  saveContract(contract);
  return contract;
}

export async function loadDemoContract(): Promise<GraphContract> {
  const response = await fetch(`${API_BASE}/demo`);
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || `Demo failed with HTTP ${response.status}`);
  }

  const contract = unwrapContract(await response.json());
  saveContract(contract);
  return contract;
}

export async function fetchLatestContract(): Promise<GraphContract> {
  const response = await fetch(`${API_BASE}/contract`);
  if (!response.ok) {
    throw new Error(`No latest contract available`);
  }

  const contract = unwrapContract(await response.json());
  saveContract(contract);
  return contract;
}

export async function askVoiceQuestion(
  question: string,
  activeNodeId: string,
  contract: GraphContract,
) {
  const response = await fetch(`${API_BASE}/voice-query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      active_node_id: activeNodeId,
      contract,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || `Question failed with HTTP ${response.status}`);
  }

  return response.json();
}

export function getArViewerUrl() {
  return `${API_BASE}/ar/index.html`;
}
