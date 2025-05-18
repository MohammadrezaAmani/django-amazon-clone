from django.contrib.postgres.search import SearchQuery, SearchRank
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Product

from .serializers import SearchResultSerializer


class SearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response([])

        search_query = SearchQuery(query, config="english")
        products = (
            Product.objects.annotate(  # type: ignore
                rank=SearchRank("search_index__search_vector", search_query)
            )
            .filter(search_index__search_vector=search_query)
            .order_by("-rank")
        )

        serializer = SearchResultSerializer(products, many=True)
        return Response(serializer.data)
