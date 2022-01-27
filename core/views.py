from django.shortcuts import render, redirect

def maintenance(req):
    return render(req,'maintenance.html')