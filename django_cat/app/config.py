# Add here your custom settings

# Example with Sentry

# import sentry_sdk
# from decouple import config
# from app.pre_utils import get_version_from_file
# from django.conf import settings

# # Initialize Sentry
# sentry_sdk.init(
#     dsn=config("SENTRY_DNS"),
#     environment=settings.ENVIRONMENT_TYPE,
#     # Set traces_sample_rate to 1.0 to capture 100%
#     # of transactions for performance monitoring.
#     traces_sample_rate=config("SENTRY_traces_sample_rate", cast=float, default=1.0),
#     # Set profiles_sample_rate to 1.0 to profile 100%
#     # of sampled transactions.
#     # We recommend adjusting this value in production.
#     profiles_sample_rate=config("SENTRY_profiles_sample_rate", cast=float, default=1.0),
#     send_default_pii=True,
#     release=get_version_from_file()
# )