# Architecture

## 1. System context

```mermaid
flowchart TB
    analyst([Security Analyst]) --> dash[React Dashboard<br/>:5173]
    attacker([Attacker / Simulator]) --> proxy
    dash <-->|REST + WebSocket| api
    subgraph api[FastAPI Backend :8000]
      proxy[Inspecting Proxy<br/>/api/v1/proxy/*]
      analyze[/api/v1/analyze/]
      engine[Detection Engine]
      store[(SQLite<br/>threats.db)]
      proxy --> engine
      analyze --> engine
      engine --> store
    end
    proxy -->|safe traffic| target[Protected Site<br/>demo_site :8090]
```

## 2. Request flow (detection)

```mermaid
sequenceDiagram
    participant C as Client / Simulator
    participant A as /analyze (or /proxy)
    participant R as Rate limiter + blocklist
    participant E as Engine (signatures + ML)
    participant D as SQLite
    participant W as WebSocket
    participant U as Dashboard

    C->>A: payload + source_ip + user_agent
    A->>R: blocked? rate exceeded?
    alt blocked / rate abuse
        R-->>C: 403 / 429 (+ log Brute Force)
    else allowed
        A->>E: evaluate(payload, user_agent)
        E->>E: signatures.analyze() + ml.predict()
        E-->>A: (threat_type, severity, confidence) | safe
        alt threat
            A->>D: insert threat
            A->>W: broadcast new_threat
            W-->>U: live row
        end
        A-->>C: verdict
    end
```

## 3. Backend components

```mermaid
flowchart LR
    main[main.py<br/>app + middleware] --> router[api/v1 routers]
    router --> analyze & threats & config & stats & proxy & ws & meta
    analyze & proxy --> engine[detection/engine.py]
    engine --> sig[detection/signatures.py]
    engine --> pipe[ml/pipeline.py]
    pipe --> classical[ml/classical.py<br/>model.pkl]
    analyze & threats & stats & meta --> repo[db/repository.py]
    repo --> dbf[(database.py / SQLite)]
    main --> core[core/*<br/>security · rate_limit · ws_manager<br/>metrics · logging · incidents]
```

## 4. Detection pipeline (verdict precedence)

```mermaid
flowchart TB
    p[payload] --> s{signature match?}
    s -->|yes| v[threat_type + severity<br/>confidence = max ML,65]
    s -->|no| m{ML prob >= 0.70?}
    m -->|yes| an[Anomalous Payload<br/>medium]
    m -->|no| safe[SAFE]
```

Signature rules are evaluated first-match in order **SQLi → XSS → Path Traversal
→ Command Injection → Suspicious User-Agent**, then the ML model. See
[API.md](API.md) for the resulting `threat_type` values.

## 5. Deployment topology

```mermaid
flowchart LR
    subgraph host[docker compose / local]
      fe[frontend<br/>nginx :5173]
      be[backend<br/>uvicorn :8000→7860]
      dm[demo_site :8090]
    end
    fe -->|/api/v1| be
    be -->|proxy forward| dm
    cloud[Hugging Face Space<br/>backend only :7860] -.optional.- be
```
