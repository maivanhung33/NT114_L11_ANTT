from django.http import JsonResponse

BAD_REQUEST = JsonResponse(data={'message': 'Bad request'}, status=400)

MUST_HAVE_URL = JsonResponse(data={'message': 'must have url'}, status=400)

NOT_ENOUGH_INFO = JsonResponse(data={'message': 'must fill full info'}, status=400)

VALIDATE_ERROR = JsonResponse(data={'message': 'Request data error'}, status=400)

HAD_LIKED = JsonResponse(data={'message': 'Pic has been liked before'}, status=400)

ALL_READY_EXITS = JsonResponse(data={'message': 'Username is already exist'}, status=400)

MUST_LOGIN = JsonResponse(data={'message': 'you must login'}, status=401)

TOKEN_EXPIRED = JsonResponse(data={'message': 'token expire'}, status=401)

AUTHENTICATION_FAIL = JsonResponse(data={'message': 'Authentication fail'}, status=401)

LOGIN_FAIL = JsonResponse(data={'message': 'Username or password error'}, status=401)

NOT_FOUND = JsonResponse(data={'message': 'Data request not found'}, status=404)

METHOD_NOT_ALLOW = JsonResponse(data={"message": "Method not allow"}, status=405)
