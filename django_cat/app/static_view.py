from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = "base/base.html"

class Error403View(TemplateView):
    template_name = "errors/403.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['back_link'] = self.request.META.get('HTTP_REFERER')
        return context

class Error404View(TemplateView):
    template_name = "errors/404.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['back_link'] = self.request.META.get('HTTP_REFERER')
        return context

class Error500View(TemplateView):
    template_name = "errors/500.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['back_link'] = self.request.META.get('HTTP_REFERER')
        return context

