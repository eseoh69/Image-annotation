# EC530 Project 2 — Event-Driven Image Annotation and Retrieval System

## Architecture Overview

This system is a modular, event-driven pipeline where image processing is broken into independent services that communicate exclusively via Redis pub-sub. No service talks directly to another service's database.

## Services & Data Ownership

| Service | Owns | Publishes | Subscribes |
|---|---|---|---|
| UploadService | Raw image files | `image.submitted` | — |
| InferenceService | Nothing (stateless) | `inference.completed` | `image.submitted` |
| AnnotationService | Document DB | `annotation.stored` | `inference.completed` |
| EmbeddingService | Vector index (FAISS) | `embedding.created` | `annotation.stored` |
| CLIService | Nothing | `image.submitted` | `embedding.created` |

## Event Flow

image.submitted → InferenceService
inference.completed → AnnotationService
annotation.stored → EmbeddingService
embedding.created → CLIService

## Topics

Defined in `broker/topics.py`:
- `image.submitted`
- `inference.completed`
- `annotation.stored`
- `embedding.created`
- `annotation.corrected`
- `query.submitted`
- `query.completed`

## Running Tests

```bash
pytest tests/ -v
```

## Tech Stack
- Redis (pub-sub messaging)
- Python (services)
- pytest (unit testing)
- MongoDB (document DB — week 2)
- FAISS (vector index — week 2)