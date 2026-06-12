"""Official X API v2 via tweepy. Bearer token for search, OAuth 1.0a user
context for posting/replying/DMs."""

import tweepy

from .config import Settings


class TierError(RuntimeError):
    pass


class XClient:
    def __init__(self, settings: Settings):
        s = settings
        missing = [k for k, v in {
            "X_API_KEY": s.x_api_key, "X_API_SECRET": s.x_api_secret,
            "X_ACCESS_TOKEN": s.x_access_token, "X_ACCESS_TOKEN_SECRET": s.x_access_token_secret,
        }.items() if not v]
        if missing:
            raise RuntimeError(f"Missing X credentials in .env: {', '.join(missing)}")
        self.client = tweepy.Client(
            bearer_token=s.x_bearer_token,
            consumer_key=s.x_api_key,
            consumer_secret=s.x_api_secret,
            access_token=s.x_access_token,
            access_token_secret=s.x_access_token_secret,
            wait_on_rate_limit=True,
        )

    def me(self):
        return self.client.get_me().data

    def search_recent(self, keywords: list[str], max_results: int) -> list[dict]:
        if not keywords:
            raise RuntimeError("No keywords configured in config.yaml.")
        query = "(" + " OR ".join(f'"{k}"' if " " in k else k for k in keywords) + ") -is:retweet -is:reply lang:en"
        try:
            resp = self.client.search_recent_tweets(
                query=query,
                max_results=min(max(max_results, 10), 100),
                tweet_fields=["author_id", "created_at", "public_metrics"],
                expansions=["author_id"],
                user_fields=["username", "description"],
            )
        except tweepy.errors.Forbidden as e:
            raise TierError(
                "Recent search needs the Basic (paid) X API tier — your app's tier doesn't include it. "
                "compose/send for original posts still work on the Free tier."
            ) from e
        if not resp.data:
            return []
        users = {u.id: u for u in (resp.includes or {}).get("users", [])}
        out = []
        for t in resp.data:
            u = users.get(t.author_id)
            out.append({
                "tweet_id": str(t.id),
                "text": t.text,
                "author": u.username if u else str(t.author_id),
                "author_id": str(t.author_id),
                "author_bio": (u.description or "") if u else "",
            })
        return out

    def post(self, text: str, in_reply_to: str | None = None) -> str:
        resp = self.client.create_tweet(text=text, in_reply_to_tweet_id=in_reply_to)
        return str(resp.data["id"])

    def get_user(self, handle: str) -> dict:
        resp = self.client.get_user(username=handle.lstrip("@"), user_fields=["description"])
        if not resp.data:
            raise RuntimeError(f"User @{handle} not found.")
        return {"id": str(resp.data.id), "username": resp.data.username,
                "bio": resp.data.description or ""}

    def send_dm(self, user_id: str, text: str) -> None:
        try:
            self.client.create_direct_message(participant_id=user_id, text=text)
        except tweepy.errors.Forbidden as e:
            raise TierError(
                "Sending DMs needs the Basic (paid) X API tier and DM permissions on your app."
            ) from e
