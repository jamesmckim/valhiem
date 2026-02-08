# Server Hosting Service

A node:22-alpine container frontend using a REST API to communicate with a python backend, that has access to a mongoDB, that launches a game server in a pod that is expossed to the internet.

```mermaid
flowchart LR
  A@{ shape: rect, label: "node:22-alpine" }
  B@{ shape: rect, label: "python:3.12-alpine"}
  C@{ shape: processes, label: "Gamer Servers" }
  D@{ shape: cyl, label: "mongoDB" }
  E@{ shape: cloud, label: "internet" }
  U@{ shape: circle, label: "👤 User"}
A-->B;
B-->C;
B<-->D;
C-->E;
U-.->A;
