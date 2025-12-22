from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from account.forms import UserForm

def signup(
    request: HttpRequest
) -> HttpResponse:
    '''
    회원가입 페이지.
    GET 요청시 회원가입 Form 페이지 렌더.
    POST 요청시 회원가입 절차 진행.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse
    '''
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)  # 사용자 인증
            login(request, user)  # 로그인
            return redirect('main')
    else:
        form = UserForm()
    return render(request, 'account/signup.html', {'form': form})