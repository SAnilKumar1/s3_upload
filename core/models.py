from sys import settrace
from django.db import models
from django.contrib.auth.models import User
from s3_upload.storage_backends import MediaStorage
from django.conf import settings

# Create your models here.

class Document(models.Model):
    statuses = [("Draft","Draft"),("Approved", "Approved"),("DisApproved","DisApproved"),("UnPublished","UnPublished")]
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField(storage=MediaStorage())
    name = models.CharField(max_length=50)
    number = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT,
                blank=True, null=True)
    status = models.CharField(max_length=20, choices=statuses, default="Draft")
    s3_bucket_url = models.CharField(max_length=1000, default="")
    dis_approve_reason = models.CharField(max_length=250, default="")
    unpublish_reason = models.CharField(max_length=250, default="")
    @property
    def is_approved(self):
        return self.status == "Approved"
    
    @property 
    def bucket(self):
        return MediaStorage().bucket

    @property
    def s3_video_object(self):
        for s3_video_inst in MediaStorage().bucket.objects.all():
            key = s3_video_inst.key
            con = False
            for ext in [".js",".css",".html",".txt",".png",".md"]:
                if key.endswith(ext):
                    con = True
                    break 
            if con:
                continue
            name = s3_video_inst.key.split("/")[-1]
            if name==self.upload:
                return s3_video_inst
    
    def make_public_read(self):
        video_object = self.s3_video_object
        if video_object:
            video_object.Acl().put(ACL='public-read')
        else:
            raise Exception("Video instance not found")

    def delete_from_s3(self):
        video_object = self.s3_video_object
        if video_object:
            video_object.delete()
        else:
            raise Exception("Video instance not found")

    @property
    def bucket_instance(self):
        import pdb;pdb.set_trace()
        print("hello")



    # @property
    # def s3_bucket_url(self):
    #     return "https://%s/%s/%s" %(settings.self.upload, settings.MEDIA_LOCATION, self.upload)
    