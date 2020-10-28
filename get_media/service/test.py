from django.http import JsonResponse


def test(request):
    return JsonResponse(status=200, data={"message": "OK"})
