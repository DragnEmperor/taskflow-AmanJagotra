from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PageSizePaginator(PageNumberPagination):
    page_size = 10
    page_size_query_param = "size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "pages": self.page.paginator.num_pages,
                "results": data,
            }
        )

    # For OpenAPI schema generation.
    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "required": ["count", "results"],
            "properties": {
                "count": {"type": "integer", "example": 123},
                "pages": {"type": "integer", "example": 123},
                "results": schema,
            },
        }
