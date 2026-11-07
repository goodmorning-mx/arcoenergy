export type Installation = {
  id: string;
  folio?: string | null;
  scheduled_at: string | null;
  lead_installer: string;
  status: string;
  notes: string;
  customer?: { name: string; city: string };
  checklist?: Array<{ task: string; done: boolean }>;
  materials?: Array<{ item_id: string; item_name: string; requested_quantity: number; consumed_quantity: number; remaining_quantity: number }>;
};

export type ChecklistQueueItem = {
  key: string;
  owner: string;
  installation_id: string;
  task: string;
  done: boolean;
  queued_at: string;
};

export type FieldActionQueueItem = {
  operation_id: string;
  owner: string;
  kind: 'consume' | 'return' | 'expense';
  path: string;
  payload: Record<string, string | number>;
  summary: string;
  queued_at: string;
};

const DATABASE = 'arcoenergy-field-cache';
const VERSION = 2;
const INSTALLATIONS = 'installations';
const CHECKLIST_QUEUE = 'checklist-queue';
const ACTION_QUEUE = 'actions-queue';
const INVENTORY = 'inventory';
const MOVEMENTS = 'movements';

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE, VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(INSTALLATIONS)) database.createObjectStore(INSTALLATIONS, { keyPath: 'owner' });
      if (!database.objectStoreNames.contains(CHECKLIST_QUEUE)) database.createObjectStore(CHECKLIST_QUEUE, { keyPath: 'key' });
      if (!database.objectStoreNames.contains(ACTION_QUEUE)) database.createObjectStore(ACTION_QUEUE, { keyPath: 'operation_id' });
      if (!database.objectStoreNames.contains(INVENTORY)) database.createObjectStore(INVENTORY, { keyPath: 'owner' });
      if (!database.objectStoreNames.contains(MOVEMENTS)) database.createObjectStore(MOVEMENTS, { keyPath: 'owner' });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('No se pudo abrir el almacenamiento local.'));
  });
}

async function withStore<T>(storeName: string, mode: IDBTransactionMode, action: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(storeName, mode);
    const request = action(transaction.objectStore(storeName));
    let result: T;
    let failed = false;
    request.onsuccess = () => { result = request.result; };
    request.onerror = () => { failed = true; database.close(); reject(request.error || new Error('No se pudo acceder al almacenamiento local.')); };
    transaction.oncomplete = () => { database.close(); if (!failed) resolve(result!); };
    transaction.onerror = () => { failed = true; database.close(); reject(transaction.error || new Error('Falló la operación local.')); };
    transaction.onabort = () => { failed = true; database.close(); reject(transaction.error || new Error('Se canceló la operación local.')); };
  });
}

export async function cacheInstallations(owner: string, rows: Installation[]): Promise<void> {
  await withStore(INSTALLATIONS, 'readwrite', store => store.put({ owner, rows, saved_at: new Date().toISOString() }));
}

export async function readCachedInstallations(owner: string): Promise<Installation[] | null> {
  const value = await withStore<{ owner: string; rows: Installation[] } | undefined>(INSTALLATIONS, 'readonly', store => store.get(owner));
  return value?.rows || null;
}

export async function clearCachedInstallations(owner: string): Promise<void> {
  await withStore(INSTALLATIONS, 'readwrite', store => store.delete(owner));
}

export async function cacheInventory<T>(owner: string, rows: T[]): Promise<void> {
  await withStore(INVENTORY, 'readwrite', store => store.put({ owner, rows, saved_at: new Date().toISOString() }));
}

export async function readCachedInventory<T>(owner: string): Promise<T[] | null> {
  const value = await withStore<{ owner: string; rows: T[] } | undefined>(INVENTORY, 'readonly', store => store.get(owner));
  return value?.rows || null;
}

export async function cacheMovements<T>(owner: string, rows: T[]): Promise<void> {
  await withStore(MOVEMENTS, 'readwrite', store => store.put({ owner, rows, saved_at: new Date().toISOString() }));
}

export async function readCachedMovements<T>(owner: string): Promise<T[] | null> {
  const value = await withStore<{ owner: string; rows: T[] } | undefined>(MOVEMENTS, 'readonly', store => store.get(owner));
  return value?.rows || null;
}

export async function queueChecklistChange(item: ChecklistQueueItem): Promise<void> {
  await withStore(CHECKLIST_QUEUE, 'readwrite', store => store.put(item));
}

export async function readChecklistQueue(owner: string): Promise<ChecklistQueueItem[]> {
  const rows = await withStore<ChecklistQueueItem[]>(CHECKLIST_QUEUE, 'readonly', store => store.getAll());
  return rows.filter(row => row.owner === owner).sort((a, b) => a.queued_at.localeCompare(b.queued_at));
}

export async function removeChecklistChange(key: string): Promise<void> {
  await withStore(CHECKLIST_QUEUE, 'readwrite', store => store.delete(key));
}

export async function removeChecklistChangeIfCurrent(key: string, done: boolean): Promise<boolean> {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(CHECKLIST_QUEUE, 'readwrite');
    const store = transaction.objectStore(CHECKLIST_QUEUE);
    let removed = false;
    const read = store.get(key);
    read.onsuccess = () => {
      if (read.result?.done === done) {
        store.delete(key);
        removed = true;
      }
    };
    read.onerror = () => { database.close(); reject(read.error || new Error('No se pudo comprobar el cambio local.')); };
    transaction.oncomplete = () => { database.close(); resolve(removed); };
    transaction.onerror = () => { database.close(); reject(transaction.error || new Error('Falló la sincronización local.')); };
    transaction.onabort = () => { database.close(); reject(transaction.error || new Error('Se canceló la sincronización local.')); };
  });
}

export async function queueFieldAction(item: FieldActionQueueItem): Promise<void> {
  await withStore(ACTION_QUEUE, 'readwrite', store => store.put(item));
}

export async function readFieldActionQueue(owner: string): Promise<FieldActionQueueItem[]> {
  const rows = await withStore<FieldActionQueueItem[]>(ACTION_QUEUE, 'readonly', store => store.getAll());
  return rows.filter(row => row.owner.toLocaleLowerCase() === owner.toLocaleLowerCase()).sort((a, b) => a.queued_at.localeCompare(b.queued_at));
}

export async function removeFieldAction(operationId: string): Promise<void> {
  await withStore(ACTION_QUEUE, 'readwrite', store => store.delete(operationId));
}

export function checklistQueueKey(owner: string, installationId: string, task: string): string {
  return `${owner.toLocaleLowerCase()}:${installationId}:${task}`;
}
