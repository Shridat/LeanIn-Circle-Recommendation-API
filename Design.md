Lean In Take Home Assesment - Circle Recommendation API

Overview & architecture

A small recommendation system that suggests relavant, active Circles to users and provide short explanation for each suggestion. The provided JSON datasets into relational light weight SQLite database using scripts/ingestion.py. A FastAPI endpoint, GET "/api/users/{user_id}/recommendations" retrieves eligible circles and user interests. "recommender.py" scores and ranks the circles. Responses are JSON. The implementation is intentionally scoped to a 3–4 hour take-home.

Data Model

- users and circles store profile and Circle attributes
- memberships links users to Circles
- user_interests and circle_tags normalize multi-valued topics. 
- topics and activity retain imported source data, while Circle-level 30-day activity aggregates drive ranking. 
- Primary/composite keys enforce identity
- Foreign keys express membership and interest relationships.
- SQLite is suitable for a locally runnable seeded dataset.

Candidate selection & ranking

- Validate the user; retrieve their stated interests.
- Include Circles that are publically accessible and open to join
- Exclude Circles that are full in capacity, Circles that are not that active in last 30 days, Circles that users has already is member of. 
- Calculate three normalized heuristic signals: interest relevance, activity and engagment per member
- Interest relavance heavily weighted for direct topic matching with interest and lightly weighted for interest and tags matching
- Recent Activity calculated by (log-scaled posts and messages).
- Engagenement score calculated by total post and chats divided my members.
- For members with interests: score = 0.60 × relevance + 0.30 × activity + 0.10 × engagement. For cold-start members without interests: score = 0.75 × activity + 0.25 × engagement.
- Sort by score, breaking ties by Circle ID. Limit output to two Circles per primary topic to reduce repetitive recommendations. Return the top requested results with a short, rule-based explanation of matched interests and recent activity.
- Also choose top 2 selections from each matched topic for diversification. 

Scores are ranking heuristics, not calibrated probabilities. This design addresses clear interest matches, cold-start members, near-duplicate topics, and unavailable or inactive Circles without introducing a model-training pipeline.

Key Tradeoffs

| Decision | Benefit | Limitation |
|---|---|---|
| SQLite instead of PostgreSQL | No database service; simple local evaluation | Not suited for high write concurrency or distributed scale |
| Exact topic/tag matching instead of embeddings | Fast, transparent, reproducible | Misses semantically related topics with different labels |
| Weighted rules instead of ML or an LLM | Explainable scores and reasons; no training data or inference cost | Weights are subjective and do not adapt from feedback |
| Score candidates in Python | Easy to inspect and test in a small dataset | Would need candidate pruning for a large Circle catalog |
| At most two Circles per topic | Simple diversity control | May return fewer than the requested limit or miss strong same-topic options |

Production improvements

- Migrate to PostgreSQL 
- Paginate or preselect candidates before application-side scoring 
- Keep activity aggregates fresh via scheduled updates
- Add structured logging, latency/error monitoring, and API authentication. 
- Validate recommendation quality using join/conversion and retention signals.
- Creating Unsupervised ML model for recommendation
