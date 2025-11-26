/**
 * Vitest 테스트 설정 파일
 */
import '@testing-library/jest-dom';
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// 각 테스트 후 정리
afterEach(() => {
  cleanup();
});

// 전역 matcher 추가
expect.extend({});

