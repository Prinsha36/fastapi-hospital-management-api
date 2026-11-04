from fastapi import Query

# Shared paging options for list endpoints.
# limit  = how many rows to return (1-100, default 20)
# offset = how many rows to skip first (default 0)
# Example: page 3 with 20 per page -> ?limit=20&offset=40


def pagination(
    limit: int = Query(20, ge=1, le=100, description="How many rows to return (max 100)"),
    offset: int = Query(0, ge=0, description="How many rows to skip"),
):
    return {"limit": limit, "offset": offset}
