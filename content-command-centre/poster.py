"""
poster.py — Post approved content directly to Instagram, Facebook and X (Twitter).

Instagram: Uses Instagram Graph API via Meta.
  - Requires a connected Instagram Professional account.
  - Images are uploaded to Imgur first (free, anonymous) to get a public URL,
    then posted via the Graph API.

Facebook: Uses Meta Graph API to post photos to a Facebook Page.
  - Reuses the same INSTAGRAM_ACCESS_TOKEN (system user token).
  - Requires FACEBOOK_PAGE_ID and pages_manage_posts permission on the token.

X (Twitter): Uses Tweepy v2 API.
  - Requires a Twitter Developer app with Read+Write permissions.

Environment variables needed (add to .env):
  INSTAGRAM_ACCESS_TOKEN        — Long-lived user access token from Meta
  INSTAGRAM_BUSINESS_ACCOUNT_ID — Your IG Professional account ID
  FACEBOOK_PAGE_ID              — Facebook Page ID to post to
  TWITTER_API_KEY               — App consumer key
  TWITTER_API_SECRET            — App consumer secret
  TWITTER_ACCESS_TOKEN          — User access token
  TWITTER_ACCESS_TOKEN_SECRET   — User access token secret
  IMGUR_CLIENT_ID               — Anonymous upload client ID (free at api.imgur.com)
"""

from __future__ import annotations

import logging
import os
import time
import requests

import config

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _upload_image_public(image_path: str) -> str | None:
    """
    Upload a local image to catbox.moe anonymously and return a public URL.
    No API key or registration required.
    Instagram Graph API requires a publicly accessible URL.
    """
    try:
        with open(image_path, "rb") as f:
            response = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=60,
            )
        if response.ok and response.text.startswith("https://"):
            url = response.text.strip()
            logger.info(f"  Image upload OK: {url}")
            return url
        else:
            logger.error(f"  catbox.moe upload failed: {response.status_code} {response.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"  Image upload error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Instagram
# ─────────────────────────────────────────────────────────────────────────────

class InstagramPoster:
    """Posts images to Instagram via the Graph API."""

    BASE = "https://graph.facebook.com/v19.0"

    def __init__(self):
        self.token      = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        self.account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")

    def is_configured(self) -> bool:
        return bool(self.token and self.account_id)

    def post(self, image_path: str, caption: str) -> dict:
        """
        Post a single image to Instagram feed.
        Returns {"success": bool, "post_id": str | None, "error": str | None}
        """
        if not self.is_configured():
            return {"success": False, "error": "Instagram credentials not configured"}

        # 1. Upload to Imgur for a public URL
        image_url = _upload_image_public(image_path)
        if not image_url:
            return {"success": False, "error": "Failed to upload image for Instagram"}

        # 2. Create media container
        # Note: media_type must be "IMAGE" for single-image posts — some account
        # configs reject the request without it (causes "unsupported media type" errors)
        container_resp = requests.post(
            f"{self.BASE}/{self.account_id}/media",
            params={
                "image_url":  image_url,
                "media_type": "IMAGE",
                "caption":    caption,
                "access_token": self.token,
            },
            timeout=30,
        )

        if not container_resp.ok:
            try:
                err_body = container_resp.json()
                err = err_body.get("error", {}).get("message", container_resp.text)
                err_code = err_body.get("error", {}).get("code", "")
                logger.error(f"  Instagram container creation failed [{err_code}]: {err}")
            except Exception:
                err = container_resp.text
                logger.error(f"  Instagram container creation failed: {err}")
            return {"success": False, "error": err}

        creation_id = container_resp.json().get("id")
        logger.info(f"  Instagram container created: {creation_id}")

        # 3. Brief pause (Meta recommends waiting before publish)
        time.sleep(3)

        # 4. Publish
        publish_resp = requests.post(
            f"{self.BASE}/{self.account_id}/media_publish",
            params={
                "creation_id":  creation_id,
                "access_token": self.token,
            },
            timeout=30,
        )

        if publish_resp.ok:
            post_id = publish_resp.json().get("id")
            logger.info(f"  Instagram published: {post_id}")
            return {"success": True, "post_id": post_id, "error": None}
        else:
            err = publish_resp.json().get("error", {}).get("message", publish_resp.text)
            logger.error(f"  Instagram publish failed: {err}")
            return {"success": False, "error": err}


# ─────────────────────────────────────────────────────────────────────────────
# X (Twitter)
# ─────────────────────────────────────────────────────────────────────────────

class XPoster:
    """Posts text + image to X (Twitter) via API v2 using Tweepy."""

    def __init__(self):
        self.api_key    = os.getenv("TWITTER_API_KEY", "")
        self.api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.token      = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.secret     = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

    def is_configured(self) -> bool:
        return all([self.api_key, self.api_secret, self.token, self.secret])

    def post(self, image_path: str, caption: str) -> dict:
        """
        Post a tweet with an image.
        Returns {"success": bool, "post_id": str | None, "error": str | None}
        """
        if not self.is_configured():
            return {"success": False, "error": "X/Twitter credentials not configured"}

        try:
            import tweepy
        except ImportError:
            return {"success": False, "error": "tweepy not installed — run: pip install tweepy"}

        try:
            # v1.1 API for media upload (v2 doesn't support direct media upload yet)
            auth = tweepy.OAuth1UserHandler(
                self.api_key, self.api_secret,
                self.token,   self.secret,
            )
            v1_api = tweepy.API(auth)
            media  = v1_api.media_upload(filename=image_path)
            media_id = str(media.media_id)
            logger.info(f"  X media uploaded: {media_id}")

            # v2 client for creating the tweet
            client = tweepy.Client(
                consumer_key        = self.api_key,
                consumer_secret     = self.api_secret,
                access_token        = self.token,
                access_token_secret = self.secret,
            )
            tweet = client.create_tweet(text=caption, media_ids=[media_id])
            post_id = str(tweet.data["id"])
            logger.info(f"  X tweet posted: {post_id}")
            return {"success": True, "post_id": post_id, "error": None}

        except Exception as e:
            logger.error(f"  X posting failed: {e}")
            return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Facebook
# ─────────────────────────────────────────────────────────────────────────────

class FacebookPoster:
    """Posts photos to a Facebook Page via the Graph API.

    Uses the same system-user token as Instagram (INSTAGRAM_ACCESS_TOKEN).
    The token must have the pages_manage_posts permission in addition to the
    standard Instagram permissions.
    """

    BASE = "https://graph.facebook.com/v19.0"

    def __init__(self):
        # Reuse the Meta system-user token — it covers both IG and FB pages
        self.token   = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID", "")

    def is_configured(self) -> bool:
        return bool(self.token and self.page_id)

    def _get_page_token(self) -> str | None:
        """Exchange system user token for a Page Access Token."""
        try:
            resp = requests.get(
                f"{self.BASE}/{self.page_id}",
                params={"fields": "access_token", "access_token": self.token},
                timeout=15,
            )
            return resp.json().get("access_token") if resp.ok else None
        except Exception:
            return None

    def post(self, image_path: str, caption: str) -> dict:
        """
        Upload a photo and publish it to the Facebook Page feed.
        Returns {"success": bool, "post_id": str | None, "error": str | None}
        """
        if not self.is_configured():
            return {"success": False, "error": "Facebook credentials not configured — set FACEBOOK_PAGE_ID in .env"}

        try:
            # Facebook page photo posts require a Page Access Token, not a system user token
            page_token = self._get_page_token()
            if not page_token:
                return {"success": False, "error": "Could not obtain Facebook Page Access Token"}

            with open(image_path, "rb") as img_file:
                resp = requests.post(
                    f"{self.BASE}/{self.page_id}/photos",
                    params={"access_token": page_token},
                    files={"source": img_file},
                    data={"caption": caption},
                    timeout=60,
                )

            if resp.ok:
                data    = resp.json()
                post_id = data.get("post_id") or data.get("id")
                logger.info(f"  Facebook photo posted: {post_id}")
                return {"success": True, "post_id": str(post_id), "error": None}
            else:
                err = resp.json().get("error", {}).get("message", resp.text[:200])
                logger.error(f"  Facebook post failed: {err}")
                return {"success": False, "error": err}

        except Exception as e:
            logger.error(f"  Facebook posting failed: {e}")
            return {"success": False, "error": str(e)}
