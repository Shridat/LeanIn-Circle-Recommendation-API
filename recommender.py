import math


def get_score(circle,interests):
    tags = set(circle["tags"])
    topic = (circle["topic"] or "").lower()

    matches = sorted(interests & (tags | {topic}))
    #1)Interest relevance
    topic_match = 1.0 if topic in interests else 0.0

    tag_match = len(interests & tags)/max(1,len(interests))

    relevance = 0.7*topic_match + 0.3*tag_match

    #2)recent activity
    posts = max(0,circle["feed_posts_30d"] or 0)
    chats = max(0,circle["chat_messages_30d"] or 0)

    activity = (0.5*min(1.0,math.log1p(posts)/math.log1p(30)) + 0.5*min(1.0,math.log1p(chats)/math.log1p(30)))
    #3) Engagement
    members = max(1.0,circle["member_count"] or 0)
    engagement = min(1.0,(posts+chats *0.1)/members/2)

    if interests:
        score = 0.6*relevance + 0.3*activity + 0.1*engagement
    else:
        score = 0.75*activity + 0.25*engagement

    return score,matches

def recommend(circles,interests,limit):
    ranked = []

    for circle in circles:
        score,matches = get_score(circle,interests)
        ranked.append((score,circle,matches))
    ranked.sort(key=lambda item: (-item[0],item[1]["id"]))
    
    #Choose top2 from each recommended circles gropued by topics
    selected = []
    topic_by_count = {}
    for item in ranked:
        score,circle,matches = item
        topic = (circle["topic"] or "").lower()

        if topic_by_count.get(topic,0)>=2:
            continue

        selected.append(item)
        topic_by_count[topic] = topic_by_count.get(topic,0)+1
        if len(selected)>limit:
            break
    results = []
    for score,circle,matches in selected:
        if matches:
            reason = ("Matches your interest in " + ",".join(matches) + ".")
        elif not interests:
            reason = ("An active circle you may want to explore")
        else:
            reason = ("Explore something new beyond your interests")
        reason+=("Members have been active in past 30 days")

        results.append({
            "circle_id":circle["id"],
            "name":circle["name"],
            "score":round(score,3),
            "reason":reason
        })
    return results
        

