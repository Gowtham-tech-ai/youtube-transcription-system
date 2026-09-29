import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings, STORAGE_DIR


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    MongoDB Atlas database manager with automatic local JSON fallback.

    Behaviour:
    - Uses MongoDB Atlas when available.
    - If Atlas fails during any operation, automatically switches
      to local persistent JSON storage.
    - Local data is persisted in storage/local_db.json.
    - The application/API should not crash simply because Atlas
      becomes unavailable.
    """

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.is_atlas_connected = False

        self.fallback_file = STORAGE_DIR / "local_db.json"

        self._local_cache: Dict[str, List[Dict[str, Any]]] = {
            "videos": [],
            "transcripts": [],
            "translations": [],
            "users": [],
            "jobs": [],
        }

        self._load_local_cache()

    # ============================================================
    # LOCAL STORAGE
    # ============================================================

    def _load_local_cache(self):
        """
        Load persistent local JSON database.
        """

        if not self.fallback_file.exists():
            return

        try:
            with open(
                self.fallback_file,
                "r",
                encoding="utf-8",
            ) as f:
                data = json.load(f)

            if isinstance(data, dict):
                self._local_cache.update(data)

            logger.info(
                "Loaded local persistent database from %s",
                self.fallback_file,
            )

        except Exception as e:
            logger.warning(
                "Could not load local database cache: %s",
                e,
            )

    def _save_local_cache(self):
        """
        Persist local database to disk.
        """

        try:
            self.fallback_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with open(
                self.fallback_file,
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(
                    self._local_cache,
                    f,
                    default=str,
                    indent=2,
                )

        except Exception as e:
            logger.error(
                "Failed to persist local database cache: %s",
                e,
            )

    def _disable_atlas(self, reason: Exception):
        """
        Disable Atlas after an operation fails.

        Atlas can be reachable during startup but fail later because
        of TLS/network/connection-pool problems.
        """

        logger.warning(
            "MongoDB Atlas operation failed. "
            "Switching to local persistent database. Error: %s",
            reason,
        )

        self.is_atlas_connected = False
        self.db = None

    # ============================================================
    # MONGODB CONNECTION
    # ============================================================

    async def connect(self):
        """
        Connect to MongoDB Atlas.

        If connection fails, application continues with local storage.
        """

        try:
            uri = settings.MONGODB_URI

            if not uri:
                logger.info(
                    "MongoDB URI is not configured. "
                    "Using local persistent database."
                )

                self.is_atlas_connected = False
                self.db = None
                return

            # Treat default placeholder URI as not configured.
            if uri.startswith(
                "mongodb+srv://admin:admin@"
            ):
                logger.info(
                    "MongoDB Atlas URI is still using "
                    "the placeholder credentials. "
                    "Using local persistent database."
                )

                self.is_atlas_connected = False
                self.db = None
                return

            # Close an old client before creating a new one.
            if self.client is not None:
                try:
                    self.client.close()
                except Exception:
                    pass

            self.client = AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=10000,
                retryWrites=True,
            )

            await self.client.admin.command("ping")

            self.db = self.client[
                settings.MONGODB_DB_NAME
            ]

            self.is_atlas_connected = True

            logger.info(
                "Successfully connected to MongoDB Atlas!"
            )

            await self._create_indexes()

        except Exception as e:
            self.is_atlas_connected = False
            self.db = None

            logger.warning(
                "MongoDB Atlas connection unavailable (%s). "
                "Using local persistent database.",
                e,
            )

    async def reconnect(self) -> bool:
        """
        Try to reconnect to MongoDB Atlas.

        Returns:
            True  -> Atlas connection successful
            False -> local storage remains active
        """

        if not settings.MONGODB_URI:
            return False

        try:
            await self.connect()
            return self.is_atlas_connected

        except Exception as e:
            logger.warning(
                "MongoDB Atlas reconnect failed: %s",
                e,
            )

            return False

    async def _create_indexes(self):
        """
        Create MongoDB indexes.
        """

        if (
            not self.is_atlas_connected
            or self.db is None
        ):
            return

        try:
            await self.db.videos.create_index(
                "video_id",
                unique=True,
            )

            await self.db.transcripts.create_index(
                [
                    ("video_id", 1),
                    ("language", 1),
                ]
            )

            await self.db.translations.create_index(
                [
                    ("video_id", 1),
                    ("target_language", 1),
                ]
            )

            await self.db.transcripts.create_index(
                [
                    ("full_text", "text"),
                ]
            )

        except Exception as e:
            logger.warning(
                "Failed to create MongoDB indexes: %s",
                e,
            )

    # ============================================================
    # VIDEO METHODS
    # ============================================================

    async def save_video(
        self,
        video_data: Dict[str, Any],
    ):
        """
        Save or update a video.
        """

        video_data["updated_at"] = (
            datetime.utcnow().isoformat()
        )

        if (
            self.is_atlas_connected
            and self.db is not None
        ):
            try:
                await self.db.videos.update_one(
                    {
                        "video_id": video_data["video_id"],
                    },
                    {
                        "$set": video_data,
                    },
                    upsert=True,
                )

                return video_data

            except Exception as e:
                self._disable_atlas(e)

        # Local fallback
        existing = next(
            (
                v
                for v in self._local_cache["videos"]
                if v.get("video_id")
                == video_data["video_id"]
            ),
            None,
        )

        if existing:
            existing.update(video_data)

        else:
            self._local_cache["videos"].append(
                video_data
            )

        self._save_local_cache()

        return video_data

    async def get_video(
        self,
        video_id: str,
    ) -> Optional[Dict[str, Any]]:

        if (
            self.is_atlas_connected
            and self.db is not None
        ):
            try:
                doc = await self.db.videos.find_one(
                    {
                        "video_id": video_id,
                    }
                )

                if doc:
                    doc["_id"] = str(
                        doc.get("_id", "")
                    )

                    return doc

                return None

            except Exception as e:
                self._disable_atlas(e)

        return next(
            (
                v
                for v in self._local_cache["videos"]
                if v.get("video_id") == video_id
            ),
            None,
        )

    async def list_videos(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:

        if (
            self.is_atlas_connected
            and self.db is not None
        ):
            try:
                cursor = (
                    self.db.videos
                    .find()
                    .sort("created_at", -1)
                    .limit(limit)
                )

                items = []

                async for doc in cursor:
                    doc["_id"] = str(
                        doc.get("_id", "")
                    )

                    items.append(doc)

                return items

            except Exception as e:
                self._disable_atlas(e)

        return sorted(
            self._local_cache["videos"],
            key=lambda x: str(
                x.get("created_at", "")
            ),
            reverse=True,
        )[:limit]

    # ============================================================
    # TRANSCRIPT METHODS
    # ============================================================

    async def save_transcript(
        self,
        transcript_data: Dict[str, Any],
    ):
        """
        Save or update a transcript.

        A transcript is identified by:
            video_id + language
        """

        transcript_data["updated_at"] = (
            datetime.utcnow().isoformat()
        )

        video_id = transcript_data["video_id"]

        language = transcript_data.get(
            "language",
            "en",
        )

        if (
            self.is_atlas_connected
            and self.db is not None
        ):
            try:
                await self.db.transcripts.update_one(
                    {
                        "video_id": video_id,
                        "language": language,
                    },
                    {
                        "$set": transcript_data,
                    },
                    upsert=True,
                )

                return transcript_data

            except Exception as e:
                self._disable_atlas(e)

        # Local fallback
        existing = next(
            (
                transcript
                for transcript
                in self._local_cache["transcripts"]
                if (
                    transcript.get("video_id")
                    == video_id
                    and transcript.get("language")
                    == language
                )
            ),
            None,
        )

        if existing:
            existing.update(
                transcript_data
            )

        else:
            self._local_cache[
                "transcripts"
            ].append(
                transcript_data
            )

        self._save_local_cache()

        return transcript_data

    async def get_transcript(
        self,
        video_id: str,
        language: str = "en",
    ) -> Optional[Dict[str, Any]]:
        """
        Get a transcript.

        Lookup order:

        1. Exact video_id + language.
        2. Source transcript for the same video.
        3. None.

        This prevents a 404 when the frontend requests
        ?lang=en but the stored source transcript uses
        another detected language.
        """

        # ========================================================
        # MongoDB Atlas
        # ========================================================

        if (
            self.is_atlas_connected
            and self.db is not None
        ):
            try:
                # ----------------------------------------------
                # Exact language lookup
                # ----------------------------------------------

                doc = await self.db.transcripts.find_one(
                    {
                        "video_id": video_id,
                        "language": language,
                    }
                )

                if doc:
                    doc["_id"] = str(
                        doc.get("_id", "")
                    )

                    return doc

                # ----------------------------------------------
                # Source transcript fallback
                # ----------------------------------------------

                source_doc = (
                    await self.db.transcripts.find_one(
                        {
                            "video_id": video_id,
                            "is_source": True,
                        }
                    )
                )

                if source_doc:
                    source_doc["_id"] = str(
                        source_doc.get("_id", "")
                    )

                    logger.info(
                        "Exact transcript language '%s' "
                        "not found for video '%s'. "
                        "Returning source transcript.",
                        language,
                        video_id,
                    )

                    return source_doc

                return None

            except Exception as e:
                logger.warning(
                    "MongoDB transcript lookup failed: %s. "
                    "Falling back to local database.",
                    e,
                )

                self._disable_atlas(e)

        # ========================================================
        # Local persistent database
        # ========================================================

        # ----------------------------------------------
        # Exact language lookup
        # ----------------------------------------------

        exact_transcript = next(
            (
                transcript
                for transcript
                in self._local_cache["transcripts"]
                if (
                    transcript.get("video_id")
                    == video_id
                    and transcript.get("language")
                    == language
                )
            ),
            None,
        )

        if exact_transcript:
            return exact_transcript

        # ----------------------------------------------
        # Source transcript fallback
        # ----------------------------------------------

        source_transcript = next(
            (
                transcript
                for transcript
                in self._local_cache["transcripts"]
                if (
                    transcript.get("video_id")
                    == video_id
                    and transcript.get("is_source")
                    is True
                )
            ),
            None,
        )

        if source_transcript:
            logger.info(
                "Exact local transcript language '%s' "
                "not found for video '%s'. "
                "Returning source transcript.",
                language,
                video_id,
            )

            return source_transcript

        return None

    # ============================================================
    # TRANSLATION METHODS
    # ============================================================

    async def save_translation(
        self,
        translation_data: Dict[str, Any],
    ):
        """
        Save or update a translation.
        """

        translation_data["updated_at"] = (
            datetime.utcnow().isoformat()
        )

        video_id = translation_data[
            "video_id"
        ]

        target_language = translation_data[
            "target_language"
        ]

        if (
            self.is_atlas_connected
            and self.db is not None
        ):
            try:
                await self.db.translations.update_one(
                    {
                        "video_id": video_id,
                        "target_language":
                            target_language,
                    },
                    {
                        "$set": translation_data,
                    },
                    upsert=True,
                )

                return translation_data

            except Exception as e:
                self._disable_atlas(e)

        # Local fallback
        existing = next(
            (
                translation
                for translation
                in self._local_cache["translations"]
                if (
                    translation.get("video_id")
                    == video_id
                    and translation.get(
                        "target_language"
                    )
                    == target_language
                )
            ),
            None,
        )

        if existing:
            existing.update(
                translation_data
            )

        else:
            self._local_cache[
                "translations"
            ].append(
                translation_data
            )

        self._save_local_cache()

        return translation_data

    async def get_translation(
        self,
        video_id: str,
        target_language: str,
    ) -> Optional[Dict[str, Any]]:

        if (
            self.is_atlas_connected
            and self.db is not None
        ):
            try:
                doc = (
                    await self.db.translations.find_one(
                        {
                            "video_id": video_id,
                            "target_language":
                                target_language,
                        }
                    )
                )

                if doc:
                    doc["_id"] = str(
                        doc.get("_id", "")
                    )

                    return doc

                return None

            except Exception as e:
                self._disable_atlas(e)

        return next(
            (
                translation
                for translation
                in self._local_cache["translations"]
                if (
                    translation.get("video_id")
                    == video_id
                    and translation.get(
                        "target_language"
                    )
                    == target_language
                )
            ),
            None,
        )

    # ============================================================
    # JOB METHODS
    # ============================================================

    async def update_job(
        self,
        job_data: Dict[str, Any],
    ):
        """
        Create or update a processing job.
        """

        job_data["updated_at"] = (
            datetime.utcnow().isoformat()
        )

        job_id = job_data["job_id"]

        if (
            self.is_atlas_connected
            and self.db is not None
        ):
            try:
                await self.db.jobs.update_one(
                    {
                        "job_id": job_id,
                    },
                    {
                        "$set": job_data,
                    },
                    upsert=True,
                )

                return job_data

            except Exception as e:
                self._disable_atlas(e)

        # Local fallback
        existing = next(
            (
                job
                for job in self._local_cache["jobs"]
                if job.get("job_id")
                == job_id
            ),
            None,
        )

        if existing:
            existing.update(job_data)

        else:
            self._local_cache[
                "jobs"
            ].append(
                job_data
            )

        self._save_local_cache()

        return job_data

    async def get_job(
        self,
        job_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a processing job.

        Atlas failures automatically fall back
        to the local persistent database.
        """

        if (
            self.is_atlas_connected
            and self.db is not None
        ):
            try:
                doc = await self.db.jobs.find_one(
                    {
                        "job_id": job_id,
                    }
                )

                if doc:
                    doc["_id"] = str(
                        doc.get("_id", "")
                    )

                    return doc

                return None

            except Exception as e:
                self._disable_atlas(e)

        # Local persistent database fallback
        return next(
            (
                job
                for job in self._local_cache["jobs"]
                if job.get("job_id")
                == job_id
            ),
            None,
        )


# ============================================================
# GLOBAL DATABASE MANAGER
# ============================================================

db_manager = DatabaseManager()