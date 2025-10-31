from flask import Flask
from flask_caching import Cache


# Create a single Cache instance to be shared across modules
cache = Cache()


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Basic config
    app.config.from_mapping(
        CACHE_TYPE="SimpleCache",
        CACHE_DEFAULT_TIMEOUT=600,
    )

    # Initialize cache with the app
    cache.init_app(app)

    # Blueprints
    from .blueprints.main import bp as main_bp
    from .blueprints.pages import bp as pages_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(pages_bp)

    return app


