import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import { app, startServer } from '../../src/api/server';

let server: ReturnType<typeof startServer> | undefined;

describe('HTTP API', () => {
  beforeAll(() => {
    process.env.NODE_ENV = 'test';
    server = app.listen(0);
  });
  afterAll(() => {
    server?.close();
  });

  it('returns 400 for invalid request', async () => {
    const res = await request(app).post('/mcp/checkCostImpact').send({});
    expect(res.status).toBe(400);
    expect(res.body.error).toBeDefined();
  });
});


