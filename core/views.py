from threading import Thread
import uuid
from pydoc import Doc
import re
import os
from django.shortcuts import render, redirect

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login as add_to_session, logout as view_logout
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.http import JsonResponse
from s3_upload.storage_backends import MediaStorage
from django.contrib import messages



from .models import Document
from core import models
def is_admin(view):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponse('Unauthorized', status=401)
        return view(request, *args, **kwargs)
    return wrapper

@is_admin
@login_required
def approveVideo(request, id):
    document = Document.objects.get(id=id)
    try:
        document.make_public_read()
        document.status = "Approved" 
        document.save()
    except Exception as err:
        messages.add_message(request, messages.ERROR, "%s"%err)
    return redirect("/draftVideos/")

@is_admin
@login_required
def disApproveVideo(request, id):
    document = Document.objects.get(id=id)
    if request.method == "POST":
        reason = request.POST.get("reason")
        document.dis_approve_reason = reason 
        document.delete_from_s3()
        document.status = "DisApproved" 
        document.save()
        return redirect("/videos/?status=Draft")
    return render(request, "disapprovereason.html", {"doc": document})

@is_admin
@login_required
def unPublishVideo(request, id):
    document = Document.objects.get(id=id)
    if request.method == "POST":
        reason = request.POST.get("reason")
        document.unpublish_reason = reason 
        document.status = "UnPublished" 
        document.save()
        return redirect("/approvedVideos")
    return render(request, "unpublishreason.html", {"doc": document})

@is_admin
@login_required
def draftVideos(request):
    videos = Document.objects.filter(status="Draft")
    return render(request, "videos.html", {"videos": videos})

@login_required
def allVideos(request):
    videos = Document.objects.all()
    return render(request, "allvideos.html", {"videos": videos})

@login_required
def approvedVideos(request):
    videos = Document.objects.filter(status="Approved")
    return render(request, "approvedvideos.html", {"videos": videos})

@login_required
def disApprovedVideos(request):
    videos = Document.objects.filter(status="DisApproved")
    return render(request, "disApprovedvideos.html", {"videos": videos})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            add_to_session(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            add_to_session(request, user)
            return redirect('/')
    return render(request, "login.html")

def logout(request):
    view_logout(request)
    return redirect("/login")

class DocumentListView(ListView):
    model = Document
    fields = ['name','number','email','upload' ]
    template_name = "videos.html"
    def get_queryset(self, *args, **kwargs):
        qs = super(DocumentListView, self).get_queryset(*args, **kwargs)
        search_args = self.request.GET
        status = search_args.get('status')
        name = search_args.get("name")
        if status:
            qs = qs.filter(status=status)
        if name:
            qs = qs.filter(name__contains=name)
        qs = qs.order_by("-id")
        return qs

class ApprovedDocumentListView(DocumentListView):
    template_name = "approvedvideos.html"
    def get_queryset(self, *args, **kwargs):
        qs = super(ApprovedDocumentListView, self).get_queryset(*args, **kwargs)
        search_args = self.request.GET
        name = search_args.get("name")
        qs = qs.filter(status="Approved")
        if name:
            qs = qs.filter(name__contains=name)
        qs = qs.order_by("-id")
        return qs

class DisApprovedDocumentListView(DocumentListView):
    template_name = "disapprovedvideos.html"
    def get_queryset(self, *args, **kwargs):
        qs = super(DisApprovedDocumentListView, self).get_queryset(*args, **kwargs)
        search_args = self.request.GET
        name = search_args.get("name")
        qs = qs.filter(status="DisApproved")
        if name:
            qs = qs.filter(name__contains=name)
        qs = qs.order_by("-id")
        return qs

class UnPublishedDocumentListView(DocumentListView):
    template_name = "unpublishedvideos.html"
    def get_queryset(self, *args, **kwargs):
        qs = super(UnPublishedDocumentListView, self).get_queryset(*args, **kwargs)
        search_args = self.request.GET
        name = search_args.get("name")
        qs = qs.filter(status="UnPublished")
        if name:
            qs = qs.filter(name__contains=name)
        qs = qs.order_by("-id")
        return qs


class DocumentCreateView(CreateView):
    model = Document
    fields = ['name','number','email','upload' ]
    success_url = reverse_lazy('home')


    def post(self, request, **kwargs):
        file_obj = request.FILES.get('upload', '')
        *exist_name,ext = file_obj.name.split(".")
        exist_name = ".".join(exist_name)
        file_path_within_bucket = "%s%s.%s"%(exist_name,uuid.uuid4(),ext)

        media_storage = MediaStorage()

        # if not media_storage.exists(file_path_within_bucket): # avoid overwriting existing file
        media_storage.save(file_path_within_bucket, file_obj)
        file_url = media_storage.url(file_path_within_bucket)
        data = request.POST
        doc = models.Document(s3_bucket_url=file_url,
                name=data.get("name"), email=data.get("email"),
                upload=file_path_within_bucket, number=data.get("number"),
                created_by=request.user)
        doc.save()
        message = f'Hi Team, video %s uploaded.' % file_path_within_bucket
        messages.add_message(request, messages.INFO, message)
        subject = 'notification'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = ["anil.kumar@euphoricthought.com",]
        thr = Thread(target=send_mail, args=(subject, message, email_from, recipient_list))
        thr.start()
        thr1 = Thread(target=doc.make_public_read)
        thr1.start()
        return redirect("/")
        

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['created_by'] = self.request.user
        return context

    def form_valid(self, form):
        
        return super().form_valid(form)

    