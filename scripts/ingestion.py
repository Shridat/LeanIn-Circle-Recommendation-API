import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR/"data"
DB_PATH = BASE_DIR/"database"/"leanin.db"

def load_json(filename):
    with open(DATA_DIR/filename,encoding="utf-8") as f:
        return json.load(f)

def create_tables(cursor):
    try:
        cursor.executescript("""
            create table if not exists users (
                id integer primary key,
                first_name text,
                last_name text,
                has_photo boolean,
                bio text,
                job_title text,
                company text,
                industry text,
                location text,
                joined_at text,
                profile_completeness real
            );
            
            create table if not exists circles(
                id integer primary key,
                name text, slug text, description text,
                topic text,
                cover_image_url text,
                format text,
                access text,
                join_policy text,
                max_members integer,
                member_count integer,
                created_at text,
                last_activity_at text,
                feed_posts_30d integer,
                chat_messages_30d integer
            );

            create table if not exists user_interests (
                user_id integer not null,
                topic text not null,
                primary key (user_id, topic),
                foreign key (user_id) references users(id)
            );

            create table if not exists circle_tags ( 
                circle_id integer not null,
                tag text not null,
                primary key (circle_id, tag)
                foreign key (circle_id) references circles(id)
            );
            
            create table if not exists topics (
                id integer primary key,
                slug text,
                label text,
                domain text
            );

            create table if not exists memberships (
                user_id integer not null,
                circle_id integer not null,
                role text,
                joined_at text,
                primary key (user_id, circle_id)
                foreign key (user_id) references users(id),
                foreign key (circle_id) references circles(id)
            );

            create table if not exists activity (
                id integer primary key,
                circle_id integer,
                user_id integer,
                body text,
                reaction_count integer,
                comment_count integer,
                save_count integer,
                created_at text
            );
        """)
        print("Tables have created successfully!!")
    except Exception as err:
        print("Unable to create tables",err)

def ingest_users(conn):
    users = load_json("users.json")
    try:
        for user in users:
            user_id = user['id']
            conn.execute("""
                INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                has_photo = excluded.has_photo,
                bio = excluded.bio,
                job_title = excluded.job_title,
                company = excluded.company,
                industry = excluded.industry,
                location = excluded.location,
                joined_at = excluded.joined_at,
                profile_completeness = excluded.profile_completeness
            """,(
                user_id,
                user.get("first_name"),
                user.get("last_name"),
                user.get("has_photo"),
                user.get("bio"),
                user.get("job_title"),
                user.get("company"),
                user.get("industry"),
                user.get("location"),
                user.get("joined_at"),
                user.get("profile_completeness")
            ))
            conn.execute(
                "DELETE FROM user_interests WHERE user_id = ?",
                (user_id,)
            )
            interests = set(user.get("topic_interests") or [])

            conn.executemany("""
                INSERT INTO user_interests (user_id, topic)
                VALUES (?, ?)
            """, [(user_id, topic) for topic in interests])
        conn.commit()
        print("User ingestion is done!")
    except Exception as e:
        print("The users are not inserted!!",e)
    

def ingest_circles(conn):
    circles = load_json("circles.json")
    try:
        for circle in circles:
            circle_id = circle["id"]
            conn.execute("""
                INSERT INTO circles VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                slug = excluded.slug,
                description = excluded.description,
                topic = excluded.topic,
                cover_image_url = excluded.cover_image_url,
                format = excluded.format,
                access = excluded.access,
                join_policy = excluded.join_policy,
                max_members = excluded.max_members,
                member_count = excluded.member_count,
                created_at = excluded.created_at,
                last_activity_at = excluded.last_activity_at,
                feed_posts_30d = excluded.feed_posts_30d,
                chat_messages_30d = excluded.chat_messages_30d
            """,(
                circle_id,
                circle["name"],
                circle.get("slug"),
                circle.get("description"),
                circle.get("topic"),
                circle.get("cover_image_url"),
                circle.get("format"),
                circle.get("access"),
                circle.get("join_policy"),
                circle.get("max_members"),
                circle.get("member_count"),
                circle.get("created_at"),
                circle.get("last_activity_at"),
                circle.get("feed_posts_30d"),
                circle.get("chat_messages_30d")
            ))
            conn.execute(
                "DELETE FROM circle_tags WHERE circle_id = ?",
                (circle_id,)
            )

            tags = set(circle.get('tags')) or []

            conn.executemany("""
                INSERT INTO circle_tags (circle_id, tag)
                VALUES (?, ?)
            """, [(circle_id, tag) for tag in tags])
        conn.commit()
        print("Circles ingestion done!!!")
    except Exception as e:
        print("Unable to insert circles",e)
    

def ingest_membership(conn):
    memberships = load_json("memberships.json")
    try:
        for membership in memberships:
            conn.execute("""
                INSERT INTO memberships (
                    user_id, circle_id, role, joined_at
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, circle_id) DO UPDATE SET
                role = excluded.role,
                joined_at = excluded.joined_at
            """, (
                membership["user_id"],
                membership["circle_id"],
                membership.get("role"),
                membership.get("joined_at")
            ))
        conn.commit()
        print("Memberships ingestion done!!")
    except Exception as e:
        print("Unable to insert the memberships", e)

def ingest_topics(conn):
    topics = load_json("topics.json")
    try:
        for topic in topics:
            conn.execute("""
                INSERT INTO topics (
                    id, slug, label, domain
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                slug = excluded.slug,
                label = excluded.label,
                domain = excluded.domain
            """,(
                topic["id"],
                topic.get("slug"),
                topic.get("label"),
                topic.get("domain")
            ))
        conn.commit()
        print("topic ingestion done!")
    except Exception as e:
        print("Unable to ingest topic")

def ingest_activity(conn):
    activities = load_json("activity.json")
    try:
        for activity in activities:
            conn.execute("""
                INSERT INTO activity (
                    id,
                    circle_id,
                    user_id,
                    body,
                    reaction_count,
                    comment_count,
                    save_count,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,(
                activity["id"],
                activity.get("circle_id"),
                activity.get("user_id"),
                activity.get("body"),
                activity.get("reaction_count"),
                activity.get("comment_count"),
                activity.get("save_count"),
                activity.get("created_at")
            ))
        conn.commit()
        print("activity ingestion is done")
    except Exception as e:
        print("Unable to insert activity",e)
def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        create_tables(conn)
        ingest_users(conn)
        ingest_circles(conn)
        ingest_membership(conn)
        ingest_topics(conn)
        ingest_activity(conn)

if __name__=="__main__":
    main()

