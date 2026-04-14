from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        response.data = {"error": "unauthorized"}
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        response.data = {"error": "forbidden"}
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        response.data = {"error": "not found"}
    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        fields = {}
        for field, errors in response.data.items():
            if isinstance(errors, list):
                fields[field] = errors[0] if len(errors) == 1 else errors
            else:
                fields[field] = errors
        response.data = {"error": "validation failed", "fields": fields}

    return response


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
