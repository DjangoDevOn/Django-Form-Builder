from django.shortcuts import render

def landing(request):
    return render(request, 'landing/landing.html', {})


################################### ERROR PAGES ###################################
def custom_error_404(request, exception):
    return render(request, 'landing/404.html', {})

def custom_error_500(request):
    return render(request, 'landing/500.html', {})

def custom_error_403(request, exception):
    return render(request, 'landing/403.html', {})