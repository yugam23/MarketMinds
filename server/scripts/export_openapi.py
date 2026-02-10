import json
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.openapi.utils import get_openapi
from server.main import app


def export_openapi():
    """Export OpenAPI schema to JSON file."""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    output_path = os.path.join(os.path.dirname(__file__), "../openapi.json")
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"OpenAPI schema exported to {output_path}")


if __name__ == "__main__":
    export_openapi()
