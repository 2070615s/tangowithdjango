from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    content =   """Hello world from Rango!
                <br/><a href=\"/rango/about/\">About</a>"""
    return HttpResponse(content)

def about(request):
    content =   """This tutorial has been put together by Christian Shtarkov, 2070615
                <br/><a href=\"/rango/\">Main</a>"""
    return HttpResponse(content)

