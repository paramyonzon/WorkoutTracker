from app import app
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 0))  # Use port 0 to let the OS assign an available port
    logger.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
