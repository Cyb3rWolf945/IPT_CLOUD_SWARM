# Vegeta Load Test Results — Docker Compose Architecture

**Date:** 2026-06-23  
**Target:** `http://localhost` (Docker bridge network, Nginx reverse proxy)  
**Tool:** vegeta v12.12.0  

---

## Architecture Under Test

```
vegeta → localhost:80 (Docker bridge)
           ├── Nginx :80 (reverse proxy)
           │     └── web (Apache/PHP, 2 replicas)
           │           └── Nginx stream :5000 → PgBouncer :6432 → PostgreSQL :5432
           │                 └── PostgreSQL 14 + Patroni + Consul (HA)
           ├── Redis Sentinel Cluster (3 Redis + 3 Sentinels)
           └── WebSocket (RatchetPHP, 1 replica)
```

---

## Test 1: Load Balancing — Main Page (`/`)

**Command:** `echo "GET http://localhost/" | vegeta attack -duration=30s -rate=50 -timeout=5s`

**Focus:** Nginx load balancing across web replicas, Apache serving static HTML.

### Summary

```
Requests      [total, rate, throughput]         1500, 50.03, 50.03
Duration      [total, attack, wait]             29.982s, 29.98s, 2.638ms
Latencies     [min, mean, 50, 90, 95, 99, max]  1.536ms, 2.798ms, 2.808ms, 3.3ms, 3.58ms, 4.413ms, 12.641ms
Bytes In      [total, mean]                     6063000, 4042.00
Success       [ratio]                           100.00%
Status Codes  [code:count]                      200:1500
```

### Phase 1 Comparison

| Metric | Phase 1 (VMs) | Phase 2 (Docker) | Delta |
|--------|--------------|------------------|-------|
| Mean   | 2.68ms       | 2.80ms           | +0.12ms (+4%) |
| p99    | 4.53ms       | 4.41ms           | -0.12ms (−3%) |
| Max    | 44.06ms      | 12.64ms          | −31.42ms (−71%) |

**✅ Static page performance nearly identical to VM baseline. Docker max latency actually better.**

---

## Test 2: Database Query — `/db.php` (50 req/s)

**Command:** `echo "GET http://localhost/db.php" | vegeta attack -duration=30s -rate=50 -timeout=5s`

### Summary

```
Requests      [total, rate, throughput]         1500, 50.03, 50.02
Duration      [total, attack, wait]             29.988s, 29.981s, 7.242ms
Latencies     [min, mean, 50, 90, 95, 99, max]  3.467ms, 6.755ms, 6.769ms, 8.136ms, 8.623ms, 10.133ms, 19.455ms
Bytes In      [total, mean]                     9685500, 6457.00
Success       [ratio]                           100.00%
Status Codes  [code:count]                      200:1500
```

### Phase 1 Comparison

| Metric | Phase 1 (VMs) | Phase 2 (Docker) | Delta |
|--------|--------------|------------------|-------|
| Mean   | 2.48ms       | 6.76ms           | +4.28ms (+172%) |
| p99    | 5.17ms       | 10.13ms          | +4.96ms (+96%) |
| Max    | 42.65ms      | 19.46ms          | −23.19ms (−54%) |

**⚠️ DB queries ~2.7× slower. Docker bridge network + Nginx stream proxy add ~4ms per DB request.**

---

## Test 3: Database Query — `/db.php` (200 req/s)

**Command:** `echo "GET http://localhost/db.php" | vegeta attack -duration=15s -rate=200 -timeout=5s`

### Summary

```
Requests      [total, rate, throughput]         3000, 200.07, 199.96
Duration      [total, attack, wait]             15.003s, 14.995s, 7.958ms
Latencies     [min, mean, 50, 90, 95, 99, max]  3.063ms, 5.144ms, 4.912ms, 7.029ms, 7.653ms, 8.721ms, 12.807ms
Bytes In      [total, mean]                     19371000, 6457.00
Success       [ratio]                           100.00%
Status Codes  [code:count]                      200:3000
```

### Phase 1 Comparison

| Metric | Phase 1 (VMs) | Phase 2 (Docker) | Delta |
|--------|--------------|------------------|-------|
| Mean   | 2.21ms       | 5.14ms           | +2.93ms (+133%) |
| p99    | 3.66ms       | 8.72ms           | +5.06ms (+138%) |

**Connection pooling warming improves latency (6.76→5.14ms) but still higher than VM.**

---

## Test 4: Database Stress — `/db.php` (500 req/s)

**Command:** `echo "GET http://localhost/db.php" | vegeta attack -duration=10s -rate=500 -timeout=5s`

### Summary

```
Requests      [total, rate, throughput]         5000, 500.10, 499.77
Duration      [total, attack, wait]             10.005s, 9.998s, 6.688ms
Latencies     [min, mean, 50, 90, 95, 99, max]  3.087ms, 6.776ms, 6.148ms, 10.557ms, 11.998ms, 15.398ms, 23.877ms
Bytes In      [total, mean]                     32285000, 6457.00
Success       [ratio]                           100.00%
Status Codes  [code:count]                      200:5000
```

### Phase 1 Comparison

| Metric | Phase 1 (VMs) | Phase 2 (Docker) | Delta |
|--------|--------------|------------------|-------|
| Mean   | 2.03ms       | 6.78ms           | +4.75ms (+234%) |
| p99    | 4.99ms       | 15.40ms          | +10.41ms (+209%) |

**At peak load, Docker latency degrades (connection queuing via Nginx stream). Still 100% success.**

---

## Test 5: Database Failover — Kill db1 Mid-Load

**Command:** `echo "GET http://localhost/db.php" | vegeta attack -duration=60s -rate=10 -timeout=10s`

**Scenario:** db1 killed at T+10s via `docker kill`

### Summary

```
Requests      [total, rate, throughput]         600, 10.02, 10.00
Duration      [total, attack, wait]             59.906s, 59.901s, 5.369ms
Latencies     [min, mean, 50, 90, 95, 99, max]  3.891ms, 23.567ms, 6.761ms, 8.363ms, 8.914ms, 12.143ms, 10.001s
Bytes In      [total, mean]                     2632010, 4386.68
Success       [ratio]                           99.83%
Status Codes  [code:count]                      0:1  200:599
```

### Failover Summary

| Metric | Result |
|--------|--------|
| Requests | 600 (10 req/s × 60s) |
| **Success** | **99.83% — 599/600 succeeded** |
| Failed | 1 request (10s timeout) |
| db1 killed | T+10s |
| db2 promoted | Automatic via Patroni + Consul |
| db1 recovery | Manual restart, auto-rejoined as replica |

---

## Overall Performance Summary

| Test | Endpoint | Rate | Phase 1 Mean | Docker Mean | Phase 1 p99 | Docker p99 | Success |
|------|----------|------|-------------|-------------|------------|------------|---------|
| 1 — Static | `/` | 50/s | 2.68ms | **2.80ms** | 4.53ms | **4.41ms** | 100% |
| 2 — DB light | `/db.php` | 50/s | 2.48ms | **6.76ms** | 5.17ms | **10.13ms** | 100% |
| 3 — DB high | `/db.php` | 200/s | 2.21ms | **5.14ms** | 3.66ms | **8.72ms** | 100% |
| 4 — DB stress | `/db.php` | 500/s | 2.03ms | **6.78ms** | 4.99ms | **15.40ms** | 100% |
| 5 — Failover | `/db.php` | 10/s | 100% | **99.83%** | — | — | 99.83% |

### Key Findings

1. **Static page performance is nearly identical** — Docker bridge adds only 0.12ms overhead
2. **DB queries are 2-3× slower** — Nginx stream proxy + Docker bridge adds ~4ms per DB hop
3. **100% success across 9,500 baseline requests** — functionally identical to Phase 1
4. **Failover succeeds** — 599/600 requests succeeded during db1 kill. 1 request timed out (10s window)
5. **Patroni + Consul HA works in Docker** — failover + auto-rejoin as replica confirmed
6. **Docker's main overhead is DB routing** — Nginx stream module is slower than HAProxy for TCP proxying

### Latency Analysis

The DB latency increase is caused by the extra network hops:
- Phase 1: PHP → HAProxy:5000 (local LB) → PgBouncer:6432 (same host as PG) → PG:5432
- Phase 2: PHP → DNS resolve `nginx` → bridge network → Nginx stream:5000 → bridge network → PgBouncer:6432 → bridge network → PostgreSQL:5432

Each Docker bridge hop adds ~0.5-1ms. With 3 bridge hops for DB traffic vs 1-2 in Phase 1, this explains the +4ms difference.
