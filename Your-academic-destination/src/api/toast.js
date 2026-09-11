let listeners = [];
let idCounter = 0;

export function showToast(message, type = 'error', duration = 4000) {
  const id = idCounter++;
  const toast = { id, message, type };

  listeners.forEach((fn) => fn((prev) => [...prev, toast]));

  setTimeout(() => {
    listeners.forEach((fn) => fn((prev) => prev.filter((t) => t.id !== id)));
  }, duration);
}

export function subscribeToasts(fn) {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter((l) => l !== fn);
  };
}