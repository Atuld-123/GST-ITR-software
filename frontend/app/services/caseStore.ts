export type ServiceCase = {
  id: string;
  service: string;
  serviceTitle: string;
  clientName: string;
  clientId?: string;
  priority: string;
  note: string;
  createdAt: string;
  steps: string[];
  documents: string[];
  completedStep: number;
  receivedDocuments: string[];
};

export const serviceCasesStorageKey = "taxsphere_training_service_cases";

export function loadServiceCases(): ServiceCase[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(serviceCasesStorageKey) ?? "[]");
    return Array.isArray(value) ? value as ServiceCase[] : [];
  } catch {
    return [];
  }
}

export function saveServiceCases(cases: ServiceCase[]) {
  localStorage.setItem(serviceCasesStorageKey, JSON.stringify(cases));
}
