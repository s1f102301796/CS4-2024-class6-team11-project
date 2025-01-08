from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # ログイン画面にリダイレクト
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/register.html', {'form': form})
