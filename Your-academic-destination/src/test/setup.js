import '@testing-library/jest-dom';
import { vi } from 'vitest';

// ثابت لجميع الاختبارات حتى ما نعتمد على localhost أو ملفات .env
vi.stubEnv('VITE_API_URL', 'http://test-backend');