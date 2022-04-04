from starlette.config import Config

config = Config(".env")

DATABASE_URL = config("MOANS_DATABASE_URL", cast=str, default="")
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ALGORITHM = "HS256"
SECRET_KEY = config("EE_SECRET_KEY", cast=str, default="167ecc1387bf59ef798e78e897beb32d87da335c5e3f60dc0f532b838a6e9a99")
MEDIA_FORMAT = "audio/mpeg"
IMAGE_FORMAT = "image/png"
AUDIO_FORMAT = "mp3"
RECORD_ERROR_DETAIL = "Record is not found"
RECORD_NAME_ERROR_DETAIL = ""
MAIN_URL = "https://moans2.pagekite.me"#"http://localhost:8000"
NOREPLY_EMAIL = "noreply.moans@gmail.com"
EMAIL_PASS = "d0ntTr8t0h2cKtH1spL32S3"