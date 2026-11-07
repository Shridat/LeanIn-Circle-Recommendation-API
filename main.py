import sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from recommender import recommend

app = FastAPI(
    title = "Circle Recommendation API"
)

DB_PATH = (Path(__file__).resolve().parent/"database"/"leanin.db")

@app.get("/api/users/{user_id}/recommendations")
def get_recommendations(user_id:int, limit:int = Query(default=5)):
    if not DB_PATH.exists():
        raise HTTPException(status_code=503,detail="Database not Found. Run ingestion file first!!")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        users = conn.execute("""
            SELECT * FROM USERS WHERE id=?
        """,(user_id,)).fetchone()
        #print(users)
        if not users:
            raise HTTPException(status_code=404,detail="User not found")

        rows = conn.execute("""
            SELECT topic FROM USER_INTERESTS WHERE user_id=?
        """,(user_id,)).fetchall()

        interests = {row['topic'] for row in rows}
        #print(interests)

        rows = conn.execute("""
            SELECT c.* FROM circles c WHERE LOWER(c.join_policy) = 'open' AND LOWER(c.access)='public'
            AND (
                c.max_members IS NULL
                OR COALESCE(c.member_count,0)<c.max_members
            )
            AND (
                COALESCE(c.feed_posts_30d,0)>0
                OR COALESCE(c.chat_messages_30d,0)>0
            )
            AND NOT EXISTS(
                SELECT 1 FROM memberships m WHERE m.user_id=? AND m.circle_id = c.id 
            )
        """,(user_id,)).fetchall()

        circles = [dict(row) for row in rows]

        tags = {}
        tag_rows = conn.execute("""SELECT circle_id, tag from circle_tags""")

        for row in tag_rows:
            tags.setdefault(row['circle_id'],set()).add(row['tag'].lower())

        for circle in circles:
            circle["tags"] = tags.get(circle["id"],set())
        
        recommendations = recommend(circles,interests,limit)
        return {
            "user_id":user_id,
            "strategy": ("Based on interests" if interests else "cold start"),
            "recommendations":recommendations
        }
